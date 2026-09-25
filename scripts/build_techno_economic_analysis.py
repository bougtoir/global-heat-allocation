"""Build Phase D techno-economic and operational-emissions comparisons."""

from __future__ import annotations

import itertools
import json
import re
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from global_heat_allocation.techno_economics import (
    MMBTU_PER_MWH,
    conventional_steam_balance,
    heat_recovery_balance,
    natural_gas_co2e_kg_per_mmbtu,
    replacement_present_value,
    uniform_present_value_factor,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "techno_economic_sources" / "phase_d_20260924"
METADATA = ROOT / "data" / "metadata"
RESULTS = ROOT / "results" / "techno_economic"
TECHNOLOGY_PARAMETERS = METADATA / "technology_parameters.csv"
FRONTIER_WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "real_heat_cases"
    / "frontier_figshare_v4_20260924T115656Z"
    / "frontier_hpc_facility_data_v4.xlsx"
)

EIA_ELECTRICITY = RAW / "eia_tennessee_commercial_electricity_2025.json"
EIA_NATURAL_GAS = RAW / "eia_tennessee_commercial_natural_gas_2025.json"
EPA_FACTORS = RAW / "ghg_emission_factors_hub_2025.xlsx"
EPA_EGRID = RAW / "egrid2023_summary_tables_rev2.xlsx"
NIST_SUPPLEMENT = RAW / "nist_ir_85_3273_40_2025.pdf"
DOE_BOILER = RAW / "doe_steam_generation_efficiency.pdf"
FEDERAL_RESERVE = RAW / "federal_reserve_g5a_2025.html"

LB_TO_KG = 0.45359237
EXPECTED_FRONTIER_INTERVALS = 365 * 24 * 6


def _technology_values() -> dict[str, float]:
    data = pd.read_csv(TECHNOLOGY_PARAMETERS, dtype=str, keep_default_na=False)
    values: dict[str, float] = {}
    for row in data.to_dict(orient="records"):
        if row["value"]:
            values[str(row["parameter_id"])] = float(row["value"])
    return values


def _eia_electricity_prices() -> tuple[float, float, float]:
    payload = json.loads(EIA_ELECTRICITY.read_text(encoding="utf-8"))
    data = pd.DataFrame(payload["response"]["data"])
    prices = pd.to_numeric(data["price"], errors="raise") * 10
    revenue = pd.to_numeric(data["revenue"], errors="raise")
    sales = pd.to_numeric(data["sales"], errors="raise")
    weighted = float(revenue.sum() / sales.sum() * 1000)
    return weighted, float(prices.min()), float(prices.max())


def _eia_natural_gas_price() -> float:
    payload = json.loads(EIA_NATURAL_GAS.read_text(encoding="utf-8"))
    records = payload["response"]["data"]
    if len(records) != 1 or records[0]["units"] != "$/MCF":
        raise ValueError("Unexpected EIA natural-gas response.")
    return float(records[0]["value"])


def _epa_factors() -> dict[str, float]:
    data = pd.read_excel(EPA_FACTORS, sheet_name="Emission Factors Hub", header=None)
    natural_gas = data.loc[data[2].eq("Natural Gas") & data[4].notna()]
    if len(natural_gas) != 1:
        raise ValueError("Expected one numeric EPA natural-gas factor row.")
    gwp = data.loc[data[2].isin(["CH4", "N2O"]), [2, 3]].set_index(2)[3]
    return {
        "gas_hhv_mmbtu_per_scf": float(natural_gas.iloc[0, 3]),
        "gas_co2_kg_per_mmbtu": float(natural_gas.iloc[0, 4]),
        "gas_ch4_g_per_mmbtu": float(natural_gas.iloc[0, 5]),
        "gas_n2o_g_per_mmbtu": float(natural_gas.iloc[0, 6]),
        "ch4_gwp": float(gwp.loc["CH4"]),
        "n2o_gwp": float(gwp.loc["N2O"]),
    }


def _egrid_factors() -> dict[str, float]:
    data = pd.read_excel(EPA_EGRID, sheet_name="Table 1", header=None)
    row = data.loc[data[1].eq("SRTV")]
    if len(row) != 1:
        raise ValueError("Expected one SRTV eGRID row.")
    record = row.iloc[0]
    return {
        "average_kg_co2e_per_mwh": float(record[6]) * LB_TO_KG,
        "nonbaseload_kg_co2e_per_mwh": float(record[13]) * LB_TO_KG,
        "grid_gross_loss_fraction": float(record[17]),
    }


def _eur_usd_rate() -> float:
    html = FEDERAL_RESERVE.read_text(encoding="utf-8")
    match = re.search(
        r"EMU MEMBERS</th>\s*<td[^>]*>EURO</td>\s*"
        r"<td[^>]*>([0-9.]+)</td>",
        html,
    )
    if match is None:
        raise ValueError("Could not extract 2025 EUR/USD rate.")
    return float(match.group(1))


def _source_rows(
    *,
    electricity_price: float,
    natural_gas_price: float,
    eur_usd: float,
    egrid: dict[str, float],
) -> list[dict[str, str]]:
    return [
        {
            "source_id": "eia_electricity_2025",
            "source_key": "eia_tennessee_commercial_electricity_2025",
            "locator": "EIA API v2; 12 monthly Tennessee commercial rows",
            "extracted_fact": (
                f"Sales-weighted 2025 price = {electricity_price:.6f} USD/MWh."
            ),
            "system_boundary": "Retail commercial electricity price.",
            "limitation": "State average, not an ORNL tariff or marginal price.",
        },
        {
            "source_id": "eia_natural_gas_2025",
            "source_key": "eia_tennessee_commercial_natural_gas_2025",
            "locator": "EIA series N3020TN3; calendar year 2025",
            "extracted_fact": f"Commercial price = {natural_gas_price:.6f} USD/MCF.",
            "system_boundary": "Delivered commercial natural-gas price.",
            "limitation": "State average, not an ORNL contract price.",
        },
        {
            "source_id": "epa_factors_2025",
            "source_key": "epa_ghg_emission_factors_hub_2025",
            "locator": "Tables 1 and 11; Natural Gas and AR5 GWP rows",
            "extracted_fact": "Natural-gas combustion factors and AR5 GWP100.",
            "system_boundary": "Direct stationary-combustion emissions.",
            "limitation": "Excludes upstream natural-gas emissions.",
        },
        {
            "source_id": "epa_egrid_2023_rev2",
            "source_key": "epa_egrid_summary_tables_2023_rev2",
            "locator": "Table 1; SRTV row",
            "extracted_fact": (
                "SRTV total and non-baseload CO2e rates = "
                f"{egrid['average_kg_co2e_per_mwh']:.6f} and "
                f"{egrid['nonbaseload_kg_co2e_per_mwh']:.6f} kg/MWh."
            ),
            "system_boundary": "Power-sector generation emissions.",
            "limitation": (
                "Non-baseload rate is a sensitivity proxy, not a causal "
                "project-specific marginal factor."
            ),
        },
        {
            "source_id": "nist_femp_2025",
            "source_key": "nist_femp_annual_supplement_2025",
            "locator": "Page 1; DOE discount and inflation rates for 2025",
            "extracted_fact": "Real discount rate = 3.0%; nominal = 4.5%.",
            "system_boundary": "Federal energy-project constant-dollar LCC.",
            "limitation": "No project-specific financing structure.",
        },
        {
            "source_id": "doe_boiler_efficiency",
            "source_key": "doe_steam_generation_efficiency_training",
            "locator": "Slides 12-15; Typical Boiler Efficiencies",
            "extracted_fact": (
                "Natural-gas reference = 82%; typical range approximately 70-90%."
            ),
            "system_boundary": "Industrial boiler fuel-to-steam efficiency.",
            "limitation": "Generic DOE training value, not an ORNL measurement.",
        },
        {
            "source_id": "federal_reserve_fx_2025",
            "source_key": "federal_reserve_g5a_exchange_rates_2025",
            "locator": "G.5A Annual; EMU MEMBERS row; 2025 column",
            "extracted_fact": f"Annual average = {eur_usd:.6f} USD/EUR.",
            "system_boundary": "2025 annual-average currency conversion.",
            "limitation": "Does not convert unspecified-year ORNL equipment cost.",
        },
        {
            "source_id": "phase_c_ornl_case",
            "source_key": "frontier_ornl_showcase_report",
            "locator": "Phase C ledger; ORNL Case A and receiving-demand records",
            "extracted_fact": "Case COP, equipment count, cost, and steam-line loss.",
            "system_boundary": "Frontier-ORNL case evidence.",
            "limitation": "Full installed cost and hourly demand remain missing.",
        },
        {
            "source_id": "phase_c_dea_heat_pump",
            "source_key": "denmark_energy_plants_datasheets_2026_08",
            "locator": "Phase C ledger; sheet 40 Comp. hp, waste heat 1 MW",
            "extracted_fact": "Generic heat-pump COP, CAPEX, O&M, and lifetime.",
            "system_boundary": "Generic full-system technology comparator.",
            "limitation": "Danish 70 deg C design is not a Frontier project quote.",
        },
        {
            "source_id": "phase_c_dea_storage",
            "source_key": "denmark_energy_storage_datasheets_v0011",
            "locator": "Phase C ledger; sheet 141a TTES",
            "extracted_fact": "Generic TTES loss, auxiliary, CAPEX, O&M, and lifetime.",
            "system_boundary": "Generic storage component comparator.",
            "limitation": "Case return temperature and integration design are missing.",
        },
        {
            "source_id": "phase_c_cooldh_network",
            "source_key": "cooldh_network_design_report_d2_7",
            "locator": "Phase C ledger; network loss and pumping records",
            "extracted_fact": "Generic network losses and pumping-energy fraction.",
            "system_boundary": "Generic transport sensitivity.",
            "limitation": "Not a Frontier route or hydraulic model.",
        },
    ]


def _parameter_rows(
    *,
    technology: dict[str, float],
    electricity_price: float,
    electricity_min: float,
    electricity_max: float,
    natural_gas_price: float,
    epa: dict[str, float],
    egrid: dict[str, float],
    eur_usd: float,
) -> list[dict[str, str | float]]:
    gas_mmbtu_per_mcf = epa["gas_hhv_mmbtu_per_scf"] * 1000
    gas_usd_per_mwh = natural_gas_price * MMBTU_PER_MWH / gas_mmbtu_per_mcf
    gas_co2e = natural_gas_co2e_kg_per_mmbtu(
        co2_kg_per_mmbtu=epa["gas_co2_kg_per_mmbtu"],
        ch4_g_per_mmbtu=epa["gas_ch4_g_per_mmbtu"],
        n2o_g_per_mmbtu=epa["gas_n2o_g_per_mmbtu"],
        ch4_gwp=epa["ch4_gwp"],
        n2o_gwp=epa["n2o_gwp"],
    )
    rows: list[dict[str, str | float]] = []

    def add(
        parameter_id: str,
        pathways: str,
        name: str,
        value: str | float,
        unit: str,
        value_kind: str,
        source_ids: str,
        derivation: str,
        boundary: str,
        limitation: str,
    ) -> None:
        rows.append(
            {
                "parameter_id": parameter_id,
                "pathways": pathways,
                "parameter_name": name,
                "value": value,
                "unit": unit,
                "value_kind": value_kind,
                "source_ids": source_ids,
                "derivation": derivation,
                "system_boundary": boundary,
                "limitation": limitation,
            }
        )

    add(
        "electricity_price_weighted_2025",
        "B;C;D;E",
        "Tennessee commercial electricity price",
        electricity_price,
        "USD_2025/MWh_e",
        "derived",
        "eia_electricity_2025",
        "sum(monthly revenue) / sum(monthly sales)",
        "Purchased electricity.",
        "State-average commercial price.",
    )
    add(
        "electricity_price_monthly_min_2025",
        "B;C;D;E",
        "Minimum monthly commercial electricity price",
        electricity_min,
        "USD_2025/MWh_e",
        "derived",
        "eia_electricity_2025",
        "minimum monthly EIA price",
        "Purchased electricity.",
        "Sensitivity bound, not a tariff.",
    )
    add(
        "electricity_price_monthly_max_2025",
        "B;C;D;E",
        "Maximum monthly commercial electricity price",
        electricity_max,
        "USD_2025/MWh_e",
        "derived",
        "eia_electricity_2025",
        "maximum monthly EIA price",
        "Purchased electricity.",
        "Sensitivity bound, not a tariff.",
    )
    add(
        "natural_gas_price_2025",
        "A",
        "Tennessee commercial natural-gas price",
        natural_gas_price,
        "USD_2025/MCF",
        "direct_source",
        "eia_natural_gas_2025",
        "",
        "Delivered natural gas.",
        "State-average commercial price.",
    )
    add(
        "natural_gas_price_2025_per_mwh_hhv",
        "A",
        "Natural-gas price converted to thermal energy",
        gas_usd_per_mwh,
        "USD_2025/MWh_HHV",
        "derived",
        "eia_natural_gas_2025;epa_factors_2025",
        "USD/MCF * 3.412141633 MMBtu/MWh / MMBtu/MCF",
        "Delivered natural gas on an HHV basis.",
        "Uses EPA HHV conversion.",
    )
    for parameter_id, value, unit, source, derivation in [
        (
            "natural_gas_co2e_factor",
            gas_co2e,
            "kg_CO2e/MMBtu_HHV",
            "epa_factors_2025",
            "CO2 + CH4*28 + N2O*265",
        ),
        (
            "electricity_average_co2e_factor",
            egrid["average_kg_co2e_per_mwh"],
            "kg_CO2e/MWh_e",
            "epa_egrid_2023_rev2",
            "SRTV total-output CO2e lb/MWh * 0.45359237",
        ),
        (
            "electricity_nonbaseload_co2e_factor",
            egrid["nonbaseload_kg_co2e_per_mwh"],
            "kg_CO2e/MWh_e",
            "epa_egrid_2023_rev2",
            "SRTV non-baseload CO2e lb/MWh * 0.45359237",
        ),
        (
            "electricity_grid_gross_loss_fraction",
            egrid["grid_gross_loss_fraction"],
            "fraction",
            "epa_egrid_2023_rev2",
            "",
        ),
        ("eur_usd_2025", eur_usd, "USD/EUR", "federal_reserve_fx_2025", ""),
        ("real_discount_rate", 0.03, "fraction/year", "nist_femp_2025", ""),
        ("boiler_efficiency_central", 0.82, "fraction", "doe_boiler_efficiency", ""),
        ("boiler_efficiency_low", 0.70, "fraction", "doe_boiler_efficiency", ""),
        ("boiler_efficiency_high", 0.90, "fraction", "doe_boiler_efficiency", ""),
    ]:
        add(
            parameter_id,
            "A;B;C;D;E" if "co2e" in parameter_id else "A",
            parameter_id.replace("_", " "),
            value,
            unit,
            "derived" if derivation else "direct_source",
            source,
            derivation,
            "Operational energy and emissions.",
            "Operational factors exclude equipment embodied emissions.",
        )
    add(
        "steam_delivery_loss_fraction",
        "A",
        "Existing one-mile steam transport loss",
        technology["transport_existing_steam_loss_fraction"],
        "fraction",
        "direct_source",
        "phase_c_ornl_case",
        "",
        "Existing steam baseline.",
        "Not evidence for a new hot-water network.",
    )
    for parameter_id, value, unit, derivation in [
        ("study_period_years", 25, "year", "Aligned to generic heat-pump lifetime."),
        ("canonical_load_factor", 0.75, "fraction", "Explicit comparator scenario."),
        ("useful_heat_normalization", 1.0, "MWh_th", "Per-unit delivered-heat basis."),
    ]:
        add(
            parameter_id,
            "A;B;C;D;E",
            parameter_id.replace("_", " "),
            value,
            unit,
            "scenario",
            "",
            derivation,
            "Generic comparator, not observed dispatch.",
            "No hourly receiving-demand trace exists.",
        )
    for parameter_id, pathways, name, unit, sources, limitation in [
        (
            "case_auxiliary_electricity_fraction",
            "B;C;D;E",
            "Case-specific balance-of-plant auxiliary electricity",
            "MWh_e/MWh_th",
            "phase_c_ornl_case",
            "Do not add the generic 1% value to a COP that may already "
            "include unit auxiliaries.",
        ),
        (
            "case_source_capture_efficiency",
            "B;C;D;E",
            "Frontier source-side heat capture efficiency",
            "fraction",
            "phase_c_ornl_case",
            "No measured source heat-exchanger loss is available.",
        ),
        (
            "case_full_installed_cost",
            "B;C;D;E",
            "Frontier full installed project cost and price year",
            "USD",
            "phase_c_ornl_case",
            "ORNL reports equipment-only cost with incomplete price-year "
            "and balance-of-plant scope.",
        ),
        (
            "transport_network_capex",
            "D;E",
            "Frontier-specific hot-water network CAPEX",
            "USD_2025",
            "phase_c_cooldh_network",
            "No route, hydraulics, or project quote is available.",
        ),
        (
            "equipment_embodied_co2e",
            "B;C;D;E",
            "Equipment, construction, refrigerant, and replacement lifecycle emissions",
            "kg_CO2e",
            "epa_factors_2025",
            "Operational factors do not support a cradle-to-grave LCA.",
        ),
        (
            "case_hourly_receiving_demand",
            "B;C;D;E",
            "Hourly ORNL receiving heat demand",
            "MW_th",
            "phase_c_ornl_case",
            "Annual dispatch and total residual rejection cannot be calculated.",
        ),
        (
            "case_total_residual_rejection",
            "B;C;D;E",
            "Annual residual Frontier heat rejection after dispatch",
            "MWh_th/year",
            "phase_c_ornl_case",
            "Requires synchronized source, demand, storage, and outage dispatch.",
        ),
    ]:
        add(
            parameter_id,
            pathways,
            name,
            "",
            unit,
            "missing_required",
            sources,
            "",
            "Case-specific project boundary.",
            limitation,
        )
    return rows


def _energy_row(
    *,
    scenario_id: str,
    pathway_id: str,
    evidence_tier: str,
    decision_status: str,
    cop: float,
    storage_hours: float,
    storage_roundtrip_efficiency: float,
    storage_standing_loss_per_day: float,
    storage_auxiliary_fraction: float,
    transport_loss_fraction: float,
    transport_pumping_fraction: float,
    grid_basis: str,
    grid_factor: float,
    baseline_gas_mwh: float,
    baseline_co2e: float,
    gas_co2e_per_mmbtu: float,
    notes: str,
) -> dict[str, str | float]:
    standing_loss = storage_standing_loss_per_day * storage_hours / 24
    balance = heat_recovery_balance(
        useful_heat_delivered_mwh=1,
        cop=cop,
        storage_roundtrip_efficiency=storage_roundtrip_efficiency,
        storage_standing_loss_fraction=standing_loss,
        storage_auxiliary_fraction=storage_auxiliary_fraction,
        transport_loss_fraction=transport_loss_fraction,
        transport_pumping_fraction=transport_pumping_fraction,
    )
    pathway_co2e = balance.total_electricity_mwh * grid_factor
    row: dict[str, str | float] = {
        "scenario_id": scenario_id,
        "pathway_id": pathway_id,
        "evidence_tier": evidence_tier,
        "decision_status": decision_status,
        "storage_hours": storage_hours,
        "transport_loss_fraction": transport_loss_fraction,
        "grid_factor_basis": grid_basis,
        "baseline_natural_gas_input_mwh_hhv": baseline_gas_mwh,
        "avoided_natural_gas_mwh_hhv": baseline_gas_mwh,
        "baseline_operational_co2e_kg": baseline_co2e,
        "pathway_operational_co2e_kg": pathway_co2e,
        "avoided_operational_co2e_kg": baseline_co2e - pathway_co2e,
        "gas_co2e_factor_kg_per_mmbtu": gas_co2e_per_mmbtu,
        "notes": notes,
    }
    row.update(asdict(balance))
    return row


def _energy_emissions_rows(
    technology: dict[str, float],
    parameter_map: dict[str, float],
) -> list[dict[str, str | float]]:
    baseline = conventional_steam_balance(
        useful_heat_delivered_mwh=1,
        boiler_efficiency=parameter_map["boiler_efficiency_central"],
        delivery_loss_fraction=parameter_map["steam_delivery_loss_fraction"],
    )
    gas_factor = parameter_map["natural_gas_co2e_factor"]
    baseline_co2e = baseline.natural_gas_input_mwh_hhv * MMBTU_PER_MWH * gas_factor
    avg_grid = parameter_map["electricity_average_co2e_factor"]
    rows: list[dict[str, str | float]] = [
        {
            "scenario_id": "A_conventional_steam_baseline",
            "pathway_id": "A",
            "evidence_tier": "generic_case_comparator",
            "decision_status": "operating_baseline",
            "storage_hours": 0,
            "transport_loss_fraction": parameter_map["steam_delivery_loss_fraction"],
            "grid_factor_basis": "not_applicable",
            "useful_heat_delivered_mwh": 1,
            "heat_pump_output_mwh": 0,
            "source_heat_withdrawn_mwh": 0,
            "source_heat_recovered_mwh": 0,
            "heat_pump_electricity_mwh": 0,
            "storage_auxiliary_electricity_mwh": 0,
            "transport_pumping_electricity_mwh": 0,
            "total_electricity_mwh": 0,
            "source_side_loss_mwh": 0,
            "storage_loss_mwh": 0,
            "transport_loss_mwh": baseline.steam_delivery_loss_mwh,
            "residual_rejected_heat_captured_stream_mwh": "",
            "thermal_balance_error_mwh": 0,
            "baseline_natural_gas_input_mwh_hhv": baseline.natural_gas_input_mwh_hhv,
            "avoided_natural_gas_mwh_hhv": 0,
            "baseline_operational_co2e_kg": baseline_co2e,
            "pathway_operational_co2e_kg": baseline_co2e,
            "avoided_operational_co2e_kg": 0,
            "gas_co2e_factor_kg_per_mmbtu": gas_factor,
            "notes": (
                "Fuel-only baseline; existing boiler and steam-network capital "
                "are outside the incremental boundary."
            ),
        }
    ]
    for grid_basis, grid_factor in [
        ("SRTV_total_output", avg_grid),
        (
            "SRTV_total_output_plus_grid_loss",
            avg_grid / (1 - parameter_map["electricity_grid_gross_loss_fraction"]),
        ),
        (
            "SRTV_nonbaseload_sensitivity",
            parameter_map["electricity_nonbaseload_co2e_factor"],
        ),
    ]:
        rows.append(
            _energy_row(
                scenario_id=f"C_case_cop_{grid_basis}",
                pathway_id="C",
                evidence_tier="case_calibrated_energy_only",
                decision_status="case_capture_auxiliary_and_cost_gates_open",
                cop=technology["heat_pump_case_cop"],
                storage_hours=0,
                storage_roundtrip_efficiency=1,
                storage_standing_loss_per_day=0,
                storage_auxiliary_fraction=0,
                transport_loss_fraction=0,
                transport_pumping_fraction=0,
                grid_basis=grid_basis,
                grid_factor=grid_factor,
                baseline_gas_mwh=baseline.natural_gas_input_mwh_hhv,
                baseline_co2e=baseline_co2e,
                gas_co2e_per_mmbtu=gas_factor,
                notes=(
                    "COP electricity is counted once. Unity source capture is a "
                    "scenario; case capture loss and balance-of-plant auxiliary "
                    "electricity remain missing."
                ),
            )
        )
    rows.append(
        _energy_row(
            scenario_id="C_generic_full_system",
            pathway_id="C",
            evidence_tier="generic_technology_comparator",
            decision_status="sensitivity_only_not_case_result",
            cop=technology["heat_pump_generic_cop_2025"],
            storage_hours=0,
            storage_roundtrip_efficiency=1,
            storage_standing_loss_per_day=0,
            storage_auxiliary_fraction=0,
            transport_loss_fraction=0,
            transport_pumping_fraction=0,
            grid_basis="SRTV_total_output",
            grid_factor=avg_grid,
            baseline_gas_mwh=baseline.natural_gas_input_mwh_hhv,
            baseline_co2e=baseline_co2e,
            gas_co2e_per_mmbtu=gas_factor,
            notes=(
                "DEA auxiliary electricity is embedded in the generic COP and is "
                "not added again."
            ),
        )
    )
    for hours in [6.0, 12.0, 18.0]:
        rows.append(
            _energy_row(
                scenario_id=f"B_storage_{int(hours)}h",
                pathway_id="B",
                evidence_tier="generic_technology_comparator",
                decision_status="sensitivity_only",
                cop=technology["heat_pump_generic_cop_2025"],
                storage_hours=hours,
                storage_roundtrip_efficiency=technology[
                    "storage_generic_roundtrip_efficiency"
                ],
                storage_standing_loss_per_day=technology[
                    "storage_generic_standing_loss_per_day"
                ],
                storage_auxiliary_fraction=technology[
                    "storage_generic_auxiliary_fraction"
                ],
                transport_loss_fraction=0,
                transport_pumping_fraction=0,
                grid_basis="SRTV_total_output",
                grid_factor=avg_grid,
                baseline_gas_mwh=baseline.natural_gas_input_mwh_hhv,
                baseline_co2e=baseline_co2e,
                gas_co2e_per_mmbtu=gas_factor,
                notes="Generic TTES values; no case-specific return temperature.",
            )
        )
    transport_losses = [0.03, 0.09, 0.17, 0.35]
    for loss in transport_losses:
        rows.append(
            _energy_row(
                scenario_id=f"D_transport_loss_{int(loss * 100):02d}pct",
                pathway_id="D",
                evidence_tier="generic_network_sensitivity",
                decision_status="sensitivity_only",
                cop=technology["heat_pump_generic_cop_2025"],
                storage_hours=0,
                storage_roundtrip_efficiency=1,
                storage_standing_loss_per_day=0,
                storage_auxiliary_fraction=0,
                transport_loss_fraction=loss,
                transport_pumping_fraction=technology[
                    "transport_generic_pumping_fraction"
                ],
                grid_basis="SRTV_total_output",
                grid_factor=avg_grid,
                baseline_gas_mwh=baseline.natural_gas_input_mwh_hhv,
                baseline_co2e=baseline_co2e,
                gas_co2e_per_mmbtu=gas_factor,
                notes="Generic network loss; not a Frontier transport function.",
            )
        )
    for hours, loss in itertools.product([6.0, 12.0, 18.0], transport_losses):
        rows.append(
            _energy_row(
                scenario_id=(
                    f"E_storage_{int(hours)}h_transport_{int(loss * 100):02d}pct"
                ),
                pathway_id="E",
                evidence_tier="generic_combined_sensitivity",
                decision_status="sensitivity_only",
                cop=technology["heat_pump_generic_cop_2025"],
                storage_hours=hours,
                storage_roundtrip_efficiency=technology[
                    "storage_generic_roundtrip_efficiency"
                ],
                storage_standing_loss_per_day=technology[
                    "storage_generic_standing_loss_per_day"
                ],
                storage_auxiliary_fraction=technology[
                    "storage_generic_auxiliary_fraction"
                ],
                transport_loss_fraction=loss,
                transport_pumping_fraction=technology[
                    "transport_generic_pumping_fraction"
                ],
                grid_basis="SRTV_total_output",
                grid_factor=avg_grid,
                baseline_gas_mwh=baseline.natural_gas_input_mwh_hhv,
                baseline_co2e=baseline_co2e,
                gas_co2e_per_mmbtu=gas_factor,
                notes="Generic storage and network combination only.",
            )
        )
    return rows


def _economics_row(
    *,
    scenario: dict[str, str | float],
    technology: dict[str, float],
    parameter_map: dict[str, float],
    load_factor: float,
    lifetime_years: int,
    discount_rate: float,
    electricity_price_multiplier: float = 1,
    gas_price_multiplier: float = 1,
) -> dict[str, str | float]:
    pathway_id = str(scenario["pathway_id"])
    capacity_mw = 1.0
    annual_heat = capacity_mw * 8760 * load_factor
    study_years = int(parameter_map["study_period_years"])
    upv = uniform_present_value_factor(discount_rate, study_years)
    discounted_heat = annual_heat * upv
    baseline_fuel_cost_per_mwh = (
        float(scenario["baseline_natural_gas_input_mwh_hhv"])
        * parameter_map["natural_gas_price_2025_per_mwh_hhv"]
        * gas_price_multiplier
    )
    annual_baseline_cost = baseline_fuel_cost_per_mwh * annual_heat
    baseline_npc = annual_baseline_cost * upv
    electricity_cost_per_mwh = (
        float(scenario["total_electricity_mwh"])
        * parameter_map["electricity_price_weighted_2025"]
        * electricity_price_multiplier
    )
    eur_usd = parameter_map["eur_usd_2025"]
    hp_variable_om = (
        float(scenario["heat_pump_output_mwh"])
        * technology["heat_pump_generic_variable_om_eur2025_per_mwh"]
        * eur_usd
    )
    storage_variable_om = 0.0
    storage_fixed_om = 0.0
    storage_capex = 0.0
    storage_replacement = 0.0
    storage_hours = float(scenario["storage_hours"])
    if storage_hours:
        storage_capacity_mwh = capacity_mw * storage_hours
        storage_variable_om = (
            technology["storage_generic_variable_om_eur2025_per_mwh"] * eur_usd
        )
        storage_fixed_om = (
            storage_capacity_mwh
            * technology["storage_generic_fixed_om_eur2025_per_mwh_year"]
            * eur_usd
        )
        storage_capex = (
            storage_capacity_mwh
            / 1000
            * technology["storage_generic_capex_eur2025_per_gwh"]
            * eur_usd
        )
        storage_replacement = replacement_present_value(
            initial_cost=storage_capex,
            component_lifetime_years=int(technology["storage_generic_lifetime_years"]),
            study_period_years=study_years,
            discount_rate=discount_rate,
        )
    hp_capex = (
        technology["heat_pump_generic_total_capex_eur2025_per_mw"]
        * capacity_mw
        * eur_usd
    )
    hp_fixed_om = (
        technology["heat_pump_generic_fixed_om_eur2025_per_mw_year"]
        * capacity_mw
        * eur_usd
    )
    hp_replacement = replacement_present_value(
        initial_cost=hp_capex,
        component_lifetime_years=lifetime_years,
        study_period_years=study_years,
        discount_rate=discount_rate,
    )
    variable_cost_per_mwh = (
        electricity_cost_per_mwh + hp_variable_om + storage_variable_om
    )
    annual_opex = annual_heat * variable_cost_per_mwh + hp_fixed_om + storage_fixed_om
    capex = hp_capex + storage_capex
    replacement_pv = hp_replacement + storage_replacement
    npc = capex + replacement_pv + annual_opex * upv
    lcoh = npc / discounted_heat
    incremental_npc = npc - baseline_npc
    annual_operating_savings = annual_baseline_cost - annual_opex
    payback = capex / annual_operating_savings if annual_operating_savings > 0 else ""
    complete = pathway_id in {"B", "C"}
    status = (
        "generic_comparator"
        if pathway_id == "C"
        else "generic_comparator_partial_integration"
        if pathway_id == "B"
        else "partial_operating_cost_transport_capex_missing"
    )
    return {
        "scenario_id": scenario["scenario_id"],
        "pathway_id": pathway_id,
        "decision_status": status,
        "load_factor": load_factor,
        "capacity_mw_th": capacity_mw,
        "annual_useful_heat_mwh": annual_heat,
        "study_period_years": study_years,
        "component_lifetime_years": lifetime_years,
        "real_discount_rate": discount_rate,
        "initial_capex_usd2025": capex if complete else "",
        "replacement_present_value_usd2025": replacement_pv if complete else "",
        "annual_electricity_cost_usd2025": (electricity_cost_per_mwh * annual_heat),
        "annual_fixed_om_usd2025": hp_fixed_om + storage_fixed_om,
        "annual_variable_om_usd2025": (
            (hp_variable_om + storage_variable_om) * annual_heat
        ),
        "annual_total_opex_usd2025": annual_opex,
        "npc_usd2025": npc if complete else "",
        "lcoh_usd2025_per_mwh_th": lcoh if complete else "",
        "baseline_fuel_only_lcoh_usd2025_per_mwh_th": baseline_fuel_cost_per_mwh,
        "baseline_fuel_only_npc_usd2025": baseline_npc,
        "incremental_npc_usd2025": incremental_npc if complete else "",
        "annual_operating_savings_usd2025": annual_operating_savings,
        "simple_payback_years": payback if complete else "",
        "cost_boundary": (
            "Generic heat-pump and storage components; transport, integration, "
            "tax, financing, decommissioning, and salvage excluded."
        ),
    }


def _economics_rows(
    energy_rows: list[dict[str, str | float]],
    technology: dict[str, float],
    parameter_map: dict[str, float],
) -> list[dict[str, str | float]]:
    selected = [
        row
        for row in energy_rows
        if row["scenario_id"]
        in {
            "C_generic_full_system",
            "B_storage_12h",
            "D_transport_loss_09pct",
            "E_storage_12h_transport_09pct",
        }
    ]
    rows = [
        _economics_row(
            scenario=row,
            technology=technology,
            parameter_map=parameter_map,
            load_factor=parameter_map["canonical_load_factor"],
            lifetime_years=int(technology["heat_pump_generic_lifetime_years"]),
            discount_rate=parameter_map["real_discount_rate"],
        )
        for row in selected
    ]
    baseline = conventional_steam_balance(
        useful_heat_delivered_mwh=1,
        boiler_efficiency=parameter_map["boiler_efficiency_central"],
        delivery_loss_fraction=parameter_map["steam_delivery_loss_fraction"],
    )
    annual_heat = 8760 * parameter_map["canonical_load_factor"]
    annual_cost = (
        baseline.natural_gas_input_mwh_hhv
        * parameter_map["natural_gas_price_2025_per_mwh_hhv"]
        * annual_heat
    )
    upv = uniform_present_value_factor(
        parameter_map["real_discount_rate"],
        int(parameter_map["study_period_years"]),
    )
    rows.insert(
        0,
        {
            "scenario_id": "A_conventional_steam_baseline",
            "pathway_id": "A",
            "decision_status": "fuel_only_operating_baseline",
            "load_factor": parameter_map["canonical_load_factor"],
            "capacity_mw_th": 1,
            "annual_useful_heat_mwh": annual_heat,
            "study_period_years": int(parameter_map["study_period_years"]),
            "component_lifetime_years": "",
            "real_discount_rate": parameter_map["real_discount_rate"],
            "initial_capex_usd2025": "",
            "replacement_present_value_usd2025": "",
            "annual_electricity_cost_usd2025": 0,
            "annual_fixed_om_usd2025": "",
            "annual_variable_om_usd2025": "",
            "annual_total_opex_usd2025": annual_cost,
            "npc_usd2025": annual_cost * upv,
            "lcoh_usd2025_per_mwh_th": (
                baseline.natural_gas_input_mwh_hhv
                * parameter_map["natural_gas_price_2025_per_mwh_hhv"]
            ),
            "baseline_fuel_only_lcoh_usd2025_per_mwh_th": (
                baseline.natural_gas_input_mwh_hhv
                * parameter_map["natural_gas_price_2025_per_mwh_hhv"]
            ),
            "baseline_fuel_only_npc_usd2025": annual_cost * upv,
            "incremental_npc_usd2025": 0,
            "annual_operating_savings_usd2025": 0,
            "simple_payback_years": "",
            "cost_boundary": (
                "Natural-gas fuel only; existing boiler and steam-network "
                "capital and O&M excluded."
            ),
        },
    )
    rows.append(
        {
            "scenario_id": "C_case_calibrated_incomplete_cost",
            "pathway_id": "C",
            "decision_status": "case_installed_cost_and_auxiliary_gates_open",
            "load_factor": "",
            "capacity_mw_th": technology["heat_pump_case_total_capacity_mw"],
            "annual_useful_heat_mwh": "",
            "study_period_years": "",
            "component_lifetime_years": "",
            "real_discount_rate": parameter_map["real_discount_rate"],
            "initial_capex_usd2025": "",
            "replacement_present_value_usd2025": "",
            "annual_electricity_cost_usd2025": "",
            "annual_fixed_om_usd2025": "",
            "annual_variable_om_usd2025": "",
            "annual_total_opex_usd2025": "",
            "npc_usd2025": "",
            "lcoh_usd2025_per_mwh_th": "",
            "baseline_fuel_only_lcoh_usd2025_per_mwh_th": "",
            "baseline_fuel_only_npc_usd2025": "",
            "incremental_npc_usd2025": "",
            "annual_operating_savings_usd2025": "",
            "simple_payback_years": "",
            "cost_boundary": (
                "Case-specific LCOH and NPC intentionally withheld because full "
                "installed cost, auxiliary energy, demand, and price year are missing."
            ),
        }
    )
    return rows


def _sensitivity_rows(
    energy_rows: list[dict[str, str | float]],
    technology: dict[str, float],
    parameter_map: dict[str, float],
) -> list[dict[str, str | float]]:
    scenario = next(
        row for row in energy_rows if row["scenario_id"] == "C_generic_full_system"
    )
    rows: list[dict[str, str | float]] = []
    grid_factors = {
        "average": parameter_map["electricity_average_co2e_factor"],
        "average_plus_grid_loss": (
            parameter_map["electricity_average_co2e_factor"]
            / (1 - parameter_map["electricity_grid_gross_loss_fraction"])
        ),
        "nonbaseload_proxy": parameter_map["electricity_nonbaseload_co2e_factor"],
    }
    for (
        boiler_efficiency,
        grid_name,
        electricity_multiplier,
        gas_multiplier,
        load_factor,
        lifetime,
        discount_rate,
    ) in itertools.product(
        [0.70, 0.82, 0.90],
        grid_factors,
        [0.75, 1.0, 1.25],
        [0.75, 1.0, 1.25],
        [0.25, 0.50, 0.75, 0.95],
        [15, 25, 40],
        [0.01, 0.03, 0.05, 0.07],
    ):
        baseline = conventional_steam_balance(
            useful_heat_delivered_mwh=1,
            boiler_efficiency=boiler_efficiency,
            delivery_loss_fraction=parameter_map["steam_delivery_loss_fraction"],
        )
        baseline_co2e = (
            baseline.natural_gas_input_mwh_hhv
            * MMBTU_PER_MWH
            * parameter_map["natural_gas_co2e_factor"]
        )
        pathway_co2e = (
            float(scenario["total_electricity_mwh"]) * grid_factors[grid_name]
        )
        adjusted_scenario = dict(scenario)
        adjusted_scenario["baseline_natural_gas_input_mwh_hhv"] = (
            baseline.natural_gas_input_mwh_hhv
        )
        economics = _economics_row(
            scenario=adjusted_scenario,
            technology=technology,
            parameter_map=parameter_map,
            load_factor=load_factor,
            lifetime_years=lifetime,
            discount_rate=discount_rate,
            electricity_price_multiplier=electricity_multiplier,
            gas_price_multiplier=gas_multiplier,
        )
        rows.append(
            {
                "scenario_id": (
                    f"C_be{boiler_efficiency:.2f}_{grid_name}_"
                    f"ep{electricity_multiplier:.2f}_gp{gas_multiplier:.2f}_"
                    f"lf{load_factor:.2f}_life{lifetime}_dr{discount_rate:.2f}"
                ),
                "boiler_efficiency": boiler_efficiency,
                "grid_factor_basis": grid_name,
                "grid_co2e_kg_per_mwh": grid_factors[grid_name],
                "electricity_price_multiplier": electricity_multiplier,
                "natural_gas_price_multiplier": gas_multiplier,
                "load_factor": load_factor,
                "heat_pump_lifetime_years": lifetime,
                "real_discount_rate": discount_rate,
                "baseline_operational_co2e_kg_per_mwh": baseline_co2e,
                "pathway_operational_co2e_kg_per_mwh": pathway_co2e,
                "avoided_operational_co2e_kg_per_mwh": (baseline_co2e - pathway_co2e),
                "lcoh_usd2025_per_mwh_th": economics["lcoh_usd2025_per_mwh_th"],
                "baseline_fuel_only_lcoh_usd2025_per_mwh_th": economics[
                    "baseline_fuel_only_lcoh_usd2025_per_mwh_th"
                ],
                "incremental_npc_usd2025": economics["incremental_npc_usd2025"],
                "annual_operating_savings_usd2025": economics[
                    "annual_operating_savings_usd2025"
                ],
            }
        )
    return rows


def _frontier_source_potential() -> list[dict[str, str | float]]:
    data = pd.read_excel(FRONTIER_WORKBOOK, sheet_name="Frontier2023")
    timestamps = pd.to_datetime(
        data["Date/Time"],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )
    waste_heat = pd.to_numeric(data["Overall_WasteHeat"], errors="coerce")
    valid = waste_heat.dropna()
    observed_energy = float(valid.sum() / 6)
    unique_timestamps = int(timestamps.nunique())
    rows: list[dict[str, str | float]] = [
        {
            "metric": "expected_10_minute_intervals",
            "value": EXPECTED_FRONTIER_INTERVALS,
            "unit": "count",
            "interpretation": (
                "Complete non-leap calendar year at 10-minute resolution."
            ),
        },
        {
            "metric": "workbook_rows",
            "value": len(data),
            "unit": "count",
            "interpretation": "Includes the workbook units row.",
        },
        {
            "metric": "missing_timestamps",
            "value": EXPECTED_FRONTIER_INTERVALS - unique_timestamps,
            "unit": "count",
            "interpretation": "Unobserved intervals; no energy is imputed.",
        },
        {
            "metric": "valid_waste_heat_observations",
            "value": len(valid),
            "unit": "count",
            "interpretation": "Numeric measured waste-heat observations.",
        },
        {
            "metric": "observed_waste_heat_energy",
            "value": observed_energy,
            "unit": "MWh_th_observed",
            "interpretation": (
                "Sum of measured MW times 1/6 hour; not a complete-year estimate."
            ),
        },
    ]
    cop = _technology_values()["heat_pump_case_cop"]
    for delivered_mw in [1.0, 2.0]:
        required_source_mw = delivered_mw * (1 - 1 / cop)
        available = int(valid.ge(required_source_mw).sum())
        rows.append(
            {
                "metric": f"source_available_for_{delivered_mw:.0f}_mw_output",
                "value": available / len(valid),
                "unit": "fraction_of_valid_observations",
                "interpretation": (
                    f"Measured source heat exceeds {required_source_mw:.6f} MW; "
                    "demand coincidence and dispatch are not evaluated."
                ),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, lineterminator="\n")


def main() -> None:
    technology = _technology_values()
    electricity_price, electricity_min, electricity_max = _eia_electricity_prices()
    natural_gas_price = _eia_natural_gas_price()
    epa = _epa_factors()
    egrid = _egrid_factors()
    eur_usd = _eur_usd_rate()
    sources = _source_rows(
        electricity_price=electricity_price,
        natural_gas_price=natural_gas_price,
        eur_usd=eur_usd,
        egrid=egrid,
    )
    parameters = _parameter_rows(
        technology=technology,
        electricity_price=electricity_price,
        electricity_min=electricity_min,
        electricity_max=electricity_max,
        natural_gas_price=natural_gas_price,
        epa=epa,
        egrid=egrid,
        eur_usd=eur_usd,
    )
    parameter_map = {
        str(row["parameter_id"]): float(row["value"])
        for row in parameters
        if row["value"] != ""
    }
    energy_rows = _energy_emissions_rows(technology, parameter_map)
    economics_rows = _economics_rows(energy_rows, technology, parameter_map)
    sensitivity_rows = _sensitivity_rows(energy_rows, technology, parameter_map)

    _write_csv(METADATA / "techno_economic_parameter_sources.csv", sources)
    _write_csv(METADATA / "techno_economic_parameters.csv", parameters)
    _write_csv(RESULTS / "energy_emissions.csv", energy_rows)
    _write_csv(RESULTS / "economics.csv", economics_rows)
    _write_csv(RESULTS / "sensitivity.csv", sensitivity_rows)
    _write_csv(RESULTS / "frontier_source_potential.csv", _frontier_source_potential())
    print(
        "Built Phase D techno-economic and operational-emissions tables "
        f"({len(sensitivity_rows)} sensitivity cases)."
    )


if __name__ == "__main__":
    main()
