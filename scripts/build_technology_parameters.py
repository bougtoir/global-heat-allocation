"""Build auditable Phase C technology pathways and parameter tables."""

from __future__ import annotations

import csv
from functools import cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "data" / "metadata"
PLANT_WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "technology_sources"
    / "phase_c_20260924"
    / "denmark_energy_plants_datasheets_2026-08.xlsx"
)
STORAGE_WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "technology_sources"
    / "phase_c_20260924"
    / "denmark_energy_storage_datasheets_v0011.xlsx"
)
FRONTIER_WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "real_heat_cases"
    / "frontier_figshare_v4_20260924T115656Z"
    / "frontier_hpc_facility_data_v4.xlsx"
)

PATHWAY_FIELDS = [
    "pathway_id",
    "pathway_label",
    "mode",
    "case_definition",
    "phase_d_use",
    "finite_dispatch_ready",
    "components",
    "evidence_basis",
    "exclusion_or_limitation",
]
PARAMETER_FIELDS = [
    "parameter_id",
    "pathways",
    "component",
    "parameter_name",
    "value",
    "unit",
    "value_kind",
    "case_role",
    "source_ids",
    "derivation",
    "scope",
    "limitation",
]
SOURCE_FIELDS = [
    "source_id",
    "source_key",
    "source_type",
    "source_location",
    "extracted_fact",
    "applicability",
    "limitations",
]


@cache
def _read_sheet(path: Path, sheet: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet, header=None)


def _sheet_value(path: Path, sheet: str, parameter: str, column: int = 2) -> float:
    data = _read_sheet(path, sheet)
    matches = data.index[data[1].eq(parameter)].tolist()
    if len(matches) != 1:
        raise ValueError(f"Expected one {parameter!r} row in {sheet}, found {matches}")
    value = data.loc[matches[0], column]
    if pd.isna(value):
        raise ValueError(f"Missing {parameter!r} value in {sheet} column {column}")
    return float(value)


@cache
def _frontier_data() -> pd.DataFrame:
    return pd.read_excel(FRONTIER_WORKBOOK, sheet_name="Frontier2023")


@cache
def _frontier_series(column: str) -> pd.Series:
    return pd.to_numeric(_frontier_data()[column], errors="coerce").dropna()


def _format_value(value: float | int | str) -> str:
    if isinstance(value, str):
        return value
    return f"{float(value):.12g}"


def _parameter(
    parameter_id: str,
    pathways: str,
    component: str,
    parameter_name: str,
    value: float | int | str,
    unit: str,
    value_kind: str,
    case_role: str,
    source_ids: str = "",
    derivation: str = "",
    scope: str = "",
    limitation: str = "",
) -> dict[str, str]:
    return {
        "parameter_id": parameter_id,
        "pathways": pathways,
        "component": component,
        "parameter_name": parameter_name,
        "value": _format_value(value),
        "unit": unit,
        "value_kind": value_kind,
        "case_role": case_role,
        "source_ids": source_ids,
        "derivation": derivation,
        "scope": scope,
        "limitation": limitation,
    }


def _sources() -> list[dict[str, str]]:
    waste_heat = _frontier_series("Overall_WasteHeat")
    supply_temperature = _frontier_series("Overall Coolant Supply Temp")
    return_temperature = _frontier_series("Overall-average Coolant Return Temp")
    return [
        {
            "source_id": "frontier_article_envelope",
            "source_key": "frontier_scientific_data_article",
            "source_type": "peer_reviewed_article",
            "source_location": "PDF pp. 1-2",
            "extracted_fact": (
                "Frontier draws 8-30 MW; waste heat is 30-38 deg C; campus "
                "heating applications require up to 85 deg C."
            ),
            "applicability": "Case-specific source and sink temperature envelope.",
            "limitations": (
                "Narrative operating envelope, not the dispatch time series."
            ),
        },
        {
            "source_id": "frontier_article_measurements",
            "source_key": "frontier_scientific_data_article",
            "source_type": "peer_reviewed_article",
            "source_location": "PDF pp. 5-6",
            "extracted_fact": (
                "The cooling loop carries 97-99% of waste heat; measurements are "
                "10-minute data; coolant is 50/50 water-ethylene glycol."
            ),
            "applicability": (
                "Case-specific measurement method and temporal resolution."
            ),
            "limitations": "The measured workbook remains the dispatch input.",
        },
        {
            "source_id": "frontier_workbook_summary",
            "source_key": "frontier_hpc_facility_data_v4",
            "source_type": "measured_workbook",
            "source_location": "Worksheet Frontier2023; validated Phase B inventory",
            "extracted_fact": (
                f"Waste heat mean {waste_heat.mean():.4f} MW and maximum "
                f"{waste_heat.max():.4f} MW; supply temperature "
                f"{supply_temperature.min():.4f}-{supply_temperature.max():.4f} "
                f"deg C; return temperature {return_temperature.min():.4f}-"
                f"{return_temperature.max():.4f} deg C."
            ),
            "applicability": "Case-specific observed source profile.",
            "limitations": (
                "Missing timestamps and return temperatures are retained; summary "
                "statistics must not replace the time series."
            ),
        },
        {
            "source_id": "ornl_receiving_demand",
            "source_key": "frontier_ornl_showcase_report",
            "source_type": "engineering_report",
            "source_location": "PDF p. 8 (report p. 2)",
            "extracted_fact": (
                "The 5600-5700-5800 complex uses up to 1-2 MW of 125 deg C "
                "steam to produce 80-90 deg C hot water."
            ),
            "applicability": "Case-specific receiving-demand magnitude and grade.",
            "limitations": (
                "The report does not publish a measured hourly demand trace."
            ),
        },
        {
            "source_id": "ornl_carrier_performance",
            "source_key": "frontier_ornl_showcase_report",
            "source_type": "engineering_report",
            "source_location": "PDF p. 16 (report p. 10), commercial MTHP table",
            "extracted_fact": (
                "Carrier AquaForce 61XWHZE has COP 3.08 at approximately "
                "30 deg C source and 85 deg C sink; capacity range 0.2-2.5 MW."
            ),
            "applicability": "Selected case heat-pump performance point.",
            "limitations": (
                "Only the stated operating point is used; no COP map is inferred."
            ),
        },
        {
            "source_id": "ornl_case_a_configuration",
            "source_key": "frontier_ornl_showcase_report",
            "source_type": "engineering_report",
            "source_location": "PDF pp. 25-26 (report pp. 19-20)",
            "extracted_fact": (
                "Case A uses three 1,000 kW Carrier units; reported unit capital "
                "cost is USD 200,000; the existing one-mile steam line loses about 8%."
            ),
            "applicability": "Case-specific equipment count and equipment-only cost.",
            "limitations": (
                "The cost scope and price year are not fully specified; the steam-line "
                "loss is not a hot-water-network parameter."
            ),
        },
        {
            "source_id": "ornl_demand_data_gap",
            "source_key": "frontier_ornl_showcase_report",
            "source_type": "engineering_report",
            "source_location": "PDF p. 29 (report p. 23)",
            "extracted_fact": (
                "Collecting building heating and hot-water demand data posed "
                "notable difficulties and was deferred to a subsequent phase."
            ),
            "applicability": "Case-specific evidence gate for finite dispatch.",
            "limitations": "No hourly receiving-demand trace is available.",
        },
        {
            "source_id": "carrier_product_envelope",
            "source_key": "carrier_61xwhze_brochure",
            "source_type": "manufacturer_brochure",
            "source_location": "PDF pp. 1, 3-4, and 7",
            "extracted_fact": (
                "61XWHZE delivers up to 85 deg C, spans 200-2,500 kW, can be "
                "cascaded to at least 12 MW, uses R-1234ze, and reports COP >=3."
            ),
            "applicability": "Manufacturer operating envelope for the selected model.",
            "limitations": "Marketing brochure; case COP is taken from the ORNL table.",
        },
        {
            "source_id": "carrier_bearing_life",
            "source_key": "carrier_61xwhze_brochure",
            "source_type": "manufacturer_brochure",
            "source_location": "PDF pp. 4-5",
            "extracted_fact": (
                "Compressor bearing life is stated as 100,000 operating hours "
                "without expensive mechanical revision and oil renewal."
            ),
            "applicability": "Reliability context for the selected model.",
            "limitations": "Bearing life is not equivalent to full-system lifetime.",
        },
        {
            "source_id": "dea_heat_pump_2025",
            "source_key": "denmark_energy_plants_datasheets_2026_08",
            "source_type": "official_technology_datasheet",
            "source_location": (
                "Workbook sheet '40 Comp. hp, waste heat 1 MW', 2025 control column"
            ),
            "extracted_fact": (
                "Generic 1 MW waste-heat heat pump: COP 3.1, auxiliary electricity "
                "1%, lifetime 25 years, total CAPEX 1.13 MEUR2025/MW, and O&M."
            ),
            "applicability": (
                "Current generic comparator for installed-system parameters."
            ),
            "limitations": (
                "Reference conditions are 13/8 deg C source and 35/70 deg C "
                "district heat, with ammonia refrigerant; not the 30/85 deg C "
                "Carrier case."
            ),
        },
        {
            "source_id": "dea_heat_pump_scope",
            "source_key": "denmark_energy_plants_datasheets_2026_08",
            "source_type": "official_technology_datasheet",
            "source_location": (
                "Workbook sheet '40 Comp. hp, waste heat 1 MW', notes A, A1, "
                "D, O, P, and T"
            ),
            "extracted_fact": (
                "Auxiliary electricity is included in COP; other costs include "
                "installation, controls, consultancy and connections; 80 deg C "
                "systems are estimated to cost 15% more."
            ),
            "applicability": "Defines scope and prevents double counting.",
            "limitations": "The 15% factor is not extrapolated from 80 to 85 deg C.",
        },
        {
            "source_id": "dea_ttes_2025",
            "source_key": "denmark_energy_storage_datasheets_v0011",
            "source_type": "official_technology_datasheet",
            "source_location": "Workbook sheet '141a TTES', 2025 control column",
            "extracted_fact": (
                "5,000 m3 TTES example: 290 MWh, 29 MW input/output, 98% "
                "round-trip efficiency, 0.15%/day storage loss, 0.4% auxiliary "
                "electricity, and 40-year lifetime."
            ),
            "applicability": "Current generic steel tank thermal-storage comparator.",
            "limitations": (
                "Reference temperatures are 99/97 deg C hot-side and 55 K "
                "hot/cold difference, not a designed Frontier integration."
            ),
        },
        {
            "source_id": "dea_ttes_cost_formula",
            "source_key": "denmark_energy_storage_catalogue_v0011",
            "source_type": "official_technology_catalogue",
            "source_location": "PDF pp. 61-62, Figure 9 and economy-of-scale text",
            "extracted_fact": (
                "For 900-12,000 m3 TTES, specific CAPEX in EUR2025/m3 is "
                "P = 3,055 * V^-0.309."
            ),
            "applicability": "Generic atmospheric TTES cost sensitivity.",
            "limitations": (
                "Excludes external pumps, heat exchangers and network connection; "
                "must not be extrapolated outside the stated volume range."
            ),
        },
        {
            "source_id": "dea_ttes_scope",
            "source_key": "denmark_energy_storage_datasheets_v0011",
            "source_type": "official_technology_datasheet",
            "source_location": "Workbook sheet '141a TTES', notes A-M",
            "extracted_fact": (
                "Capacity assumes 55 K and 90% availability; charge/discharge "
                "power is a design choice; 2025 control assumes a 10-hour cycle."
            ),
            "applicability": "Storage parameter definitions and integration scope.",
            "limitations": (
                "ORNL heating-water return temperature and hydraulic design are "
                "unknown."
            ),
        },
        {
            "source_id": "cooldh_generic_network",
            "source_key": "cooldh_network_design_report_d2_7",
            "source_type": "public_project_report",
            "source_location": "PDF pp. 3 and 9",
            "extracted_fact": (
                "Traditional networks lose around 17% in high-density areas and "
                "up to 35% in low-density areas; pumping is around 2% of supplied heat."
            ),
            "applicability": "Generic district-heating sensitivity bounds.",
            "limitations": "Not measured for a Frontier-to-ORNL route.",
        },
        {
            "source_id": "cooldh_osterby_network",
            "source_key": "cooldh_network_design_report_d2_7",
            "source_type": "public_project_report",
            "source_location": "PDF p. 24",
            "extracted_fact": "Optimized Osterby network heat loss is about 10.8%.",
            "applicability": "Optimized-network sensitivity comparator.",
            "limitations": (
                "Different site, load density, temperatures and pipe geometry."
            ),
        },
        {
            "source_id": "cooldh_brunnshog_network",
            "source_key": "cooldh_network_design_report_d2_7",
            "source_type": "public_project_report",
            "source_location": "PDF pp. 28 and 30",
            "extracted_fact": (
                "Brunnshog network loss is about 9% initially and about 3% at "
                "full build-out."
            ),
            "applicability": "Low-temperature network sensitivity comparator.",
            "limitations": "Different site and future build-out assumptions.",
        },
    ]


def _pathways() -> list[dict[str, str]]:
    return [
        {
            "pathway_id": "A",
            "pathway_label": "Conventional rejection",
            "mode": "baseline",
            "case_definition": (
                "Measured Frontier waste heat is rejected through the existing "
                "cooling pathway; no useful heat is credited."
            ),
            "phase_d_use": "canonical_baseline",
            "finite_dispatch_ready": "true",
            "components": "existing cooling and rejection system",
            "evidence_basis": (
                "Frontier measured source time series and system description"
            ),
            "exclusion_or_limitation": (
                "Existing cooling auxiliary electricity is not separated from "
                "the facility accessory load."
            ),
        },
        {
            "pathway_id": "B",
            "pathway_label": "Same-location temporal storage and later reuse",
            "mode": "temporal",
            "case_definition": (
                "Heat is upgraded locally, charged to a steel hot-water TTES, "
                "and discharged later to a co-located demand."
            ),
            "phase_d_use": "sensitivity_only",
            "finite_dispatch_ready": "false",
            "components": "Carrier heat pump; atmospheric TTES",
            "evidence_basis": "ORNL heat-pump case plus current Danish TTES catalogue",
            "exclusion_or_limitation": (
                "ORNL return temperature, hydraulic design, tank sizing and hourly "
                "demand are unavailable; no canonical storage claim is permitted."
            ),
        },
        {
            "pathway_id": "C",
            "pathway_label": "Local direct reuse",
            "mode": "local_reuse",
            "case_definition": (
                "Three 1 MW Carrier heat pumps upgrade Frontier heat for the "
                "5600-5700-5800 complex without a dedicated transport model."
            ),
            "phase_d_use": "case_calibrated",
            "finite_dispatch_ready": "false",
            "components": "three Carrier 61XWHZE-1000 heat pumps",
            "evidence_basis": "ORNL case assessment and Carrier operating envelope",
            "exclusion_or_limitation": (
                "Hourly receiving demand and full installed project cost are missing."
            ),
        },
        {
            "pathway_id": "D",
            "pathway_label": "Near-distance transport without storage",
            "mode": "spatial",
            "case_definition": (
                "Upgraded hot water is transported no farther than the documented "
                "one-mile campus comparator before use."
            ),
            "phase_d_use": "sensitivity_only",
            "finite_dispatch_ready": "false",
            "components": "Carrier heat pump; hypothetical local hot-water network",
            "evidence_basis": "ORNL one-mile steam comparator and COOL DH loss ranges",
            "exclusion_or_limitation": (
                "No Frontier-specific route, pipe design or hot-water loss model "
                "exists; long-distance transport is excluded."
            ),
        },
        {
            "pathway_id": "E",
            "pathway_label": "Storage plus near-distance transport",
            "mode": "temporal_and_spatial",
            "case_definition": (
                "Upgraded heat is buffered in TTES and transported within the "
                "one-mile local sensitivity boundary."
            ),
            "phase_d_use": "sensitivity_only",
            "finite_dispatch_ready": "false",
            "components": (
                "Carrier heat pump; atmospheric TTES; hypothetical local "
                "hot-water network"
            ),
            "evidence_basis": "Combined evidence used for pathways B-D",
            "exclusion_or_limitation": (
                "All storage and route-design gaps apply; interactions cannot be "
                "claimed as a calibrated Frontier project."
            ),
        },
    ]


def _parameters() -> list[dict[str, str]]:
    hp_sheet = "40 Comp. hp, waste heat 1 MW"
    ttes_sheet = "141a TTES"

    def hp(name: str, column: int = 2) -> float:
        return _sheet_value(PLANT_WORKBOOK, hp_sheet, name, column)

    def ttes(name: str, column: int = 2) -> float:
        return _sheet_value(STORAGE_WORKBOOK, ttes_sheet, name, column)

    ttes_example_volume = ttes("Tank volume of example [m3]")
    ttes_example_capacity = ttes("Energy storage capacity for one unit [MWh]")
    frontier_waste_heat = _frontier_series("Overall_WasteHeat")
    frontier_supply_temperature = _frontier_series("Overall Coolant Supply Temp")
    frontier_return_temperature = _frontier_series(
        "Overall-average Coolant Return Temp"
    )
    minimum_formula_volume = 900.0
    minimum_formula_capacity = (
        ttes_example_capacity / ttes_example_volume * minimum_formula_volume
    )
    minimum_formula_capex = (
        3055.0 * minimum_formula_volume**-0.309 * minimum_formula_volume
    )

    rows = [
        _parameter(
            "baseline_useful_heat_fraction",
            "A",
            "baseline",
            "useful heat credited",
            0,
            "fraction",
            "definition",
            "canonical",
            scope="No-intervention counterfactual.",
        ),
        _parameter(
            "baseline_residual_rejection_fraction",
            "A",
            "baseline",
            "source heat rejected",
            1,
            "fraction",
            "definition",
            "canonical",
            scope="Before accounting for existing cooling-system auxiliary energy.",
        ),
        _parameter(
            "source_waste_heat_mean_mw",
            "A;B;C;D;E",
            "source",
            "measured waste heat mean",
            float(frontier_waste_heat.mean()),
            "MW_th",
            "derived",
            "context_only",
            "frontier_workbook_summary",
            derivation=(
                "Arithmetic mean of numeric Overall_WasteHeat observations in "
                "worksheet Frontier2023; units row and missing cells excluded."
            ),
            scope="2023 Frontier workbook after preserving missing observations.",
        ),
        _parameter(
            "source_waste_heat_min_mw",
            "A;B;C;D;E",
            "source",
            "measured waste heat minimum",
            float(frontier_waste_heat.min()),
            "MW_th",
            "derived",
            "context_only",
            "frontier_workbook_summary",
            derivation=(
                "Minimum of numeric Overall_WasteHeat observations in worksheet "
                "Frontier2023; units row and missing cells excluded."
            ),
        ),
        _parameter(
            "source_waste_heat_median_mw",
            "A;B;C;D;E",
            "source",
            "measured waste heat median",
            float(frontier_waste_heat.median()),
            "MW_th",
            "derived",
            "context_only",
            "frontier_workbook_summary",
            derivation=(
                "Median of numeric Overall_WasteHeat observations in worksheet "
                "Frontier2023; units row and missing cells excluded."
            ),
        ),
        _parameter(
            "source_waste_heat_p95_mw",
            "A;B;C;D;E",
            "source",
            "measured waste heat 95th percentile",
            float(frontier_waste_heat.quantile(0.95)),
            "MW_th",
            "derived",
            "context_only",
            "frontier_workbook_summary",
            derivation=(
                "95th percentile of numeric Overall_WasteHeat observations in "
                "worksheet Frontier2023; units row and missing cells excluded."
            ),
        ),
        _parameter(
            "source_waste_heat_max_mw",
            "A;B;C;D;E",
            "source",
            "measured waste heat maximum",
            float(frontier_waste_heat.max()),
            "MW_th",
            "derived",
            "context_only",
            "frontier_workbook_summary",
            derivation=(
                "Maximum of numeric Overall_WasteHeat observations in worksheet "
                "Frontier2023; units row and missing cells excluded."
            ),
        ),
        _parameter(
            "source_supply_temperature_median_c",
            "B;C;D;E",
            "source",
            "measured coolant supply temperature median",
            float(frontier_supply_temperature.median()),
            "deg_C",
            "derived",
            "context_only",
            "frontier_workbook_summary",
            derivation=(
                "Median of numeric Overall Coolant Supply Temp observations in "
                "worksheet Frontier2023; units row and missing cells excluded."
            ),
        ),
        _parameter(
            "source_return_temperature_median_c",
            "B;C;D;E",
            "source",
            "measured coolant return temperature median",
            float(frontier_return_temperature.median()),
            "deg_C",
            "derived",
            "context_only",
            "frontier_workbook_summary",
            derivation=(
                "Median of numeric Overall-average Coolant Return Temp observations "
                "in worksheet Frontier2023; units row and missing cells excluded."
            ),
        ),
        _parameter(
            "source_temperature_article_min_c",
            "B;C;D;E",
            "source",
            "engineering source temperature minimum",
            30,
            "deg_C",
            "direct_source",
            "canonical",
            "frontier_article_envelope",
        ),
        _parameter(
            "source_temperature_article_max_c",
            "B;C;D;E",
            "source",
            "engineering source temperature maximum",
            38,
            "deg_C",
            "direct_source",
            "canonical",
            "frontier_article_envelope",
        ),
        _parameter(
            "source_timeseries_resolution_minutes",
            "A;B;C;D;E",
            "source",
            "nominal measurement interval",
            10,
            "minute",
            "direct_source",
            "canonical",
            "frontier_article_measurements",
            limitation="Missing timestamps remain missing.",
        ),
        _parameter(
            "demand_heat_min_mw",
            "B;C;D;E",
            "demand",
            "reported receiving heat demand lower bound",
            1,
            "MW_th",
            "direct_source",
            "canonical",
            "ornl_receiving_demand",
        ),
        _parameter(
            "demand_heat_max_mw",
            "B;C;D;E",
            "demand",
            "reported receiving heat demand upper bound",
            2,
            "MW_th",
            "direct_source",
            "canonical",
            "ornl_receiving_demand",
        ),
        _parameter(
            "demand_hot_water_min_c",
            "B;C;D;E",
            "demand",
            "reported hot-water temperature lower bound",
            80,
            "deg_C",
            "direct_source",
            "canonical",
            "ornl_receiving_demand",
        ),
        _parameter(
            "demand_hot_water_max_c",
            "B;C;D;E",
            "demand",
            "reported hot-water temperature upper bound",
            90,
            "deg_C",
            "direct_source",
            "canonical",
            "ornl_receiving_demand",
        ),
        _parameter(
            "demand_hourly_trace",
            "B;C;D;E",
            "demand",
            "measured hourly receiving-demand trace",
            "",
            "MW_th",
            "missing_required",
            "exclusion_gate",
            "ornl_demand_data_gap",
            limitation="Finite receiving-demand dispatch is not yet supported.",
        ),
        _parameter(
            "heat_pump_case_cop",
            "B;C;D;E",
            "heat_pump",
            "coefficient of performance",
            3.08,
            "MW_heat/MW_electric",
            "direct_source",
            "canonical",
            "ornl_carrier_performance",
            scope="Approximately 30 deg C source and 85 deg C sink.",
        ),
        _parameter(
            "heat_pump_case_sink_temperature_c",
            "B;C;D;E",
            "heat_pump",
            "delivered-water temperature",
            85,
            "deg_C",
            "direct_source",
            "canonical",
            "ornl_carrier_performance;carrier_product_envelope",
        ),
        _parameter(
            "heat_pump_case_unit_capacity_mw",
            "B;C;D;E",
            "heat_pump",
            "unit heating capacity",
            1,
            "MW_th",
            "direct_source",
            "canonical",
            "ornl_case_a_configuration",
        ),
        _parameter(
            "heat_pump_case_unit_count",
            "B;C;D;E",
            "heat_pump",
            "installed units",
            3,
            "count",
            "direct_source",
            "canonical",
            "ornl_case_a_configuration",
        ),
        _parameter(
            "heat_pump_case_total_capacity_mw",
            "B;C;D;E",
            "heat_pump",
            "total heating capacity",
            3,
            "MW_th",
            "derived",
            "canonical",
            "ornl_case_a_configuration",
            derivation="3 units * 1 MW_th/unit.",
        ),
        _parameter(
            "heat_pump_case_unit_equipment_cost_usd",
            "B;C;D;E",
            "heat_pump",
            "reported unit capital cost",
            200000,
            "USD_unspecified_year/unit",
            "direct_source",
            "sensitivity",
            "ornl_case_a_configuration",
            limitation="Equipment-only scope and price year are not fully specified.",
        ),
        _parameter(
            "heat_pump_manufacturer_capacity_min_mw",
            "B;C;D;E",
            "heat_pump",
            "manufacturer capacity range minimum",
            0.2,
            "MW_th",
            "direct_source",
            "context_only",
            "carrier_product_envelope",
        ),
        _parameter(
            "heat_pump_manufacturer_capacity_max_mw",
            "B;C;D;E",
            "heat_pump",
            "manufacturer capacity range maximum",
            2.5,
            "MW_th",
            "direct_source",
            "context_only",
            "carrier_product_envelope",
        ),
        _parameter(
            "heat_pump_compressor_bearing_life_hours",
            "B;C;D;E",
            "heat_pump",
            "compressor bearing life",
            100000,
            "operating_hour",
            "direct_source",
            "context_only",
            "carrier_bearing_life",
            limitation="Not a full-system technical lifetime.",
        ),
        _parameter(
            "heat_pump_generic_cop_2025",
            "B;C;D;E",
            "heat_pump",
            "generic annual-average heat efficiency",
            hp("Heat efficiency (net, annual average) []"),
            "MW_heat/MW_electric",
            "direct_source",
            "context_only",
            "dea_heat_pump_2025;dea_heat_pump_scope",
            scope="Generic 13/8 deg C source and 35/70 deg C district heat.",
        ),
        _parameter(
            "heat_pump_generic_auxiliary_fraction_2025",
            "B;C;D;E",
            "heat_pump",
            "generic auxiliary electricity share of heat",
            hp("Auxiliary Electricity consumption (share of heat gen.) []"),
            "fraction",
            "direct_source",
            "context_only",
            "dea_heat_pump_2025;dea_heat_pump_scope",
            limitation="Already included in generic COP; do not double count.",
        ),
        _parameter(
            "heat_pump_generic_lifetime_years",
            "B;C;D;E",
            "heat_pump",
            "generic technical lifetime",
            hp("Technical lifetime [years]"),
            "year",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_generic_lifetime_lower_years",
            "B;C;D;E",
            "heat_pump",
            "generic technical lifetime lower bound",
            hp("Technical lifetime [years]", 7),
            "year",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_generic_lifetime_upper_years",
            "B;C;D;E",
            "heat_pump",
            "generic technical lifetime upper bound",
            hp("Technical lifetime [years]", 8),
            "year",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_generic_minimum_load_fraction",
            "B;C;D;E",
            "heat_pump",
            "generic minimum load",
            hp("Minimum load (of full load) []"),
            "fraction",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_generic_forced_outage_fraction",
            "B;C;D;E",
            "heat_pump",
            "generic forced outage",
            hp("Forced outage []"),
            "fraction",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_generic_planned_outage_weeks",
            "B;C;D;E",
            "heat_pump",
            "generic planned outage",
            hp("Planned outage [weeks per year]"),
            "week/year",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_generic_total_capex_eur2025_per_mw",
            "B;C;D;E",
            "heat_pump",
            "generic total nominal investment",
            hp("Nominal investment (*total) [MEUR/MW_h]") * 1_000_000,
            "EUR_2025/MW_th",
            "derived",
            "sensitivity",
            "dea_heat_pump_2025;dea_heat_pump_scope",
            derivation="Published MEUR/MW_th value multiplied by 1,000,000.",
            limitation="70 deg C ammonia system; not a case-specific 85 deg C quote.",
        ),
        _parameter(
            "heat_pump_generic_equipment_capex_eur2025_per_mw",
            "B;C;D;E",
            "heat_pump",
            "generic heat-pump equipment investment",
            hp("Nominal investment (heat pump) [MEUR/MW_h]") * 1_000_000,
            "EUR_2025/MW_th",
            "derived",
            "sensitivity",
            "dea_heat_pump_2025",
            derivation="Published MEUR/MW_th value multiplied by 1,000,000.",
        ),
        _parameter(
            "heat_pump_generic_building_capex_eur2025_per_mw",
            "B;C;D;E",
            "heat_pump",
            "generic building investment",
            hp("Nominal investment (building) [MEUR/MW_h]") * 1_000_000,
            "EUR_2025/MW_th",
            "derived",
            "sensitivity",
            "dea_heat_pump_2025",
            derivation="Published MEUR/MW_th value multiplied by 1,000,000.",
        ),
        _parameter(
            "heat_pump_generic_other_capex_eur2025_per_mw",
            "B;C;D;E",
            "heat_pump",
            "generic other investment",
            hp("Nominal investment (other costs) [MEUR/MW_h]") * 1_000_000,
            "EUR_2025/MW_th",
            "derived",
            "sensitivity",
            "dea_heat_pump_2025;dea_heat_pump_scope",
            derivation="Published MEUR/MW_th value multiplied by 1,000,000.",
        ),
        _parameter(
            "heat_pump_generic_fixed_om_eur2025_per_mw_year",
            "B;C;D;E",
            "heat_pump",
            "generic fixed O&M",
            hp("Fixed O&M (*total) [EUR/MW_h/y]"),
            "EUR_2025/MW_th/year",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_generic_variable_om_eur2025_per_mwh",
            "B;C;D;E",
            "heat_pump",
            "generic variable O&M",
            hp("Variable O&M (*total) [EUR/MWh_h]"),
            "EUR_2025/MWh_th",
            "direct_source",
            "sensitivity",
            "dea_heat_pump_2025",
        ),
        _parameter(
            "heat_pump_full_installed_case_cost",
            "B;C;D;E",
            "heat_pump",
            "case-specific full installed capital cost",
            "",
            "USD_or_EUR",
            "missing_required",
            "exclusion_gate",
            "ornl_case_a_configuration;dea_heat_pump_scope",
            limitation=(
                "ORNL provides an equipment cost; the generic catalogue is a "
                "different refrigerant and temperature design."
            ),
        ),
        _parameter(
            "storage_generic_capacity_mwh",
            "B;E",
            "storage",
            "generic TTES capacity",
            ttes("Energy storage capacity for one unit [MWh]"),
            "MWh_th",
            "direct_source",
            "context_only",
            "dea_ttes_2025;dea_ttes_scope",
        ),
        _parameter(
            "storage_generic_volume_m3",
            "B;E",
            "storage",
            "generic TTES example volume",
            ttes("Tank volume of example [m3]"),
            "m3",
            "direct_source",
            "context_only",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_generic_charge_power_mw",
            "B;E",
            "storage",
            "generic TTES input capacity",
            ttes("Input capacity for one unit [MW]"),
            "MW_th",
            "direct_source",
            "context_only",
            "dea_ttes_2025;dea_ttes_scope",
        ),
        _parameter(
            "storage_generic_discharge_power_mw",
            "B;E",
            "storage",
            "generic TTES output capacity",
            ttes("Output capacity for one unit [MW]"),
            "MW_th",
            "direct_source",
            "context_only",
            "dea_ttes_2025;dea_ttes_scope",
        ),
        _parameter(
            "storage_generic_roundtrip_efficiency",
            "B;E",
            "storage",
            "generic TTES round-trip efficiency",
            ttes("Round trip efficiency [%]") / 100,
            "fraction",
            "derived",
            "context_only",
            "dea_ttes_2025",
            derivation="Published percentage divided by 100.",
            limitation=(
                "One-year-cycle metric; do not combine with standing loss blindly."
            ),
        ),
        _parameter(
            "storage_generic_charge_efficiency",
            "B;E",
            "storage",
            "generic TTES charge efficiency",
            ttes(" - Charge efficiency [%]") / 100,
            "fraction",
            "derived",
            "context_only",
            "dea_ttes_2025",
            derivation="Published percentage divided by 100.",
        ),
        _parameter(
            "storage_generic_discharge_efficiency",
            "B;E",
            "storage",
            "generic TTES discharge efficiency",
            ttes(" - Discharge efficiency [%]") / 100,
            "fraction",
            "derived",
            "context_only",
            "dea_ttes_2025",
            derivation="Published percentage divided by 100.",
        ),
        _parameter(
            "storage_generic_standing_loss_per_day",
            "B;E",
            "storage",
            "generic TTES storage loss",
            ttes("Energy losses during storage [%/day]") / 100,
            "fraction/day",
            "derived",
            "sensitivity",
            "dea_ttes_2025",
            derivation="Published percentage per day divided by 100.",
        ),
        _parameter(
            "storage_generic_auxiliary_fraction",
            "B;E",
            "storage",
            "generic TTES auxiliary electricity",
            ttes("Auxiliary electricity consumption [% of output]") / 100,
            "MWh_electric/MWh_th_output",
            "derived",
            "sensitivity",
            "dea_ttes_2025",
            derivation="Published percentage of output divided by 100.",
        ),
        _parameter(
            "storage_generic_lifetime_years",
            "B;E",
            "storage",
            "generic TTES technical lifetime",
            ttes("Technical lifetime [years]"),
            "year",
            "direct_source",
            "sensitivity",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_generic_forced_outage_fraction",
            "B;E",
            "storage",
            "generic TTES forced outage",
            ttes("Forced outage [%]") / 100,
            "fraction",
            "derived",
            "sensitivity",
            "dea_ttes_2025",
            derivation="Published percentage divided by 100.",
        ),
        _parameter(
            "storage_generic_planned_outage_weeks",
            "B;E",
            "storage",
            "generic TTES planned outage",
            ttes("Planned outage [weeks/year]"),
            "week/year",
            "direct_source",
            "sensitivity",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_generic_construction_time_years",
            "B;E",
            "storage",
            "generic TTES construction time",
            ttes("Construction time [years]"),
            "year",
            "direct_source",
            "sensitivity",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_generic_capex_eur2025_per_gwh",
            "B;E",
            "storage",
            "generic TTES specific investment",
            ttes("Specific investment [M€/GWhCapacity]") * 1_000_000,
            "EUR_2025/GWh_th",
            "derived",
            "sensitivity",
            "dea_ttes_2025",
            derivation="Published MEUR/GWh value multiplied by 1,000,000.",
        ),
        _parameter(
            "storage_generic_fixed_om_eur2025_per_mwh_year",
            "B;E",
            "storage",
            "generic TTES fixed O&M",
            ttes("Fixed O&M [€/MWh Capacity/year]"),
            "EUR_2025/MWh_th_capacity/year",
            "direct_source",
            "sensitivity",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_generic_variable_om_eur2025_per_mwh",
            "B;E",
            "storage",
            "generic TTES variable O&M",
            ttes("Variable O&M [€/MWh output]"),
            "EUR_2025/MWh_th_output",
            "direct_source",
            "sensitivity",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_generic_temperature_difference_k",
            "B;E",
            "storage",
            "generic TTES hot-cold temperature difference",
            ttes("Typical temperature difference in storage [hot/cold, K]"),
            "K",
            "direct_source",
            "context_only",
            "dea_ttes_2025;dea_ttes_scope",
            limitation="Not established for the ORNL heating-water loop.",
        ),
        _parameter(
            "storage_generic_max_hot_temperature_c",
            "B;E",
            "storage",
            "generic TTES maximum hot temperature",
            ttes("Max. storage temperature, hot [⁰C]"),
            "deg_C",
            "direct_source",
            "context_only",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_generic_discharged_temperature_c",
            "B;E",
            "storage",
            "generic TTES discharged temperature",
            ttes("Storage temperature, discharged [⁰C]"),
            "deg_C",
            "direct_source",
            "context_only",
            "dea_ttes_2025",
        ),
        _parameter(
            "storage_cost_formula_a",
            "B;E",
            "storage",
            "TTES cost power-law coefficient a",
            3055,
            "EUR_2025/m3",
            "direct_source",
            "sensitivity",
            "dea_ttes_cost_formula",
        ),
        _parameter(
            "storage_cost_formula_b",
            "B;E",
            "storage",
            "TTES cost power-law exponent b",
            -0.309,
            "dimensionless",
            "direct_source",
            "sensitivity",
            "dea_ttes_cost_formula",
        ),
        _parameter(
            "storage_cost_formula_min_volume_m3",
            "B;E",
            "storage",
            "TTES cost formula minimum valid volume",
            minimum_formula_volume,
            "m3",
            "direct_source",
            "sensitivity",
            "dea_ttes_cost_formula",
        ),
        _parameter(
            "storage_cost_formula_max_volume_m3",
            "B;E",
            "storage",
            "TTES cost formula maximum valid volume",
            12000,
            "m3",
            "direct_source",
            "sensitivity",
            "dea_ttes_cost_formula",
        ),
        _parameter(
            "storage_min_formula_volume_capacity_mwh",
            "B;E",
            "storage",
            "generic capacity at minimum formula volume",
            minimum_formula_capacity,
            "MWh_th",
            "derived",
            "sensitivity",
            "dea_ttes_2025;dea_ttes_cost_formula",
            derivation="290 MWh / 5,000 m3 * 900 m3.",
            limitation="Assumes the generic 55 K temperature difference.",
        ),
        _parameter(
            "storage_min_formula_volume_capex_eur2025",
            "B;E",
            "storage",
            "generic CAPEX at minimum formula volume",
            minimum_formula_capex,
            "EUR_2025",
            "derived",
            "sensitivity",
            "dea_ttes_cost_formula",
            derivation="3,055 * 900^-0.309 EUR/m3 * 900 m3.",
            limitation="Excludes external pumps, exchangers and network connection.",
        ),
        _parameter(
            "storage_shift_duration_6h",
            "B;E",
            "storage",
            "short-term storage duration",
            6,
            "hour",
            "scenario",
            "sensitivity",
            derivation="Prespecified continuity with the global 6-hour window.",
        ),
        _parameter(
            "storage_shift_duration_12h",
            "B;E",
            "storage",
            "short-term storage duration",
            12,
            "hour",
            "scenario",
            "sensitivity",
            derivation="Prespecified continuity with the global 12-hour window.",
        ),
        _parameter(
            "storage_shift_duration_18h",
            "B;E",
            "storage",
            "short-term storage duration",
            18,
            "hour",
            "scenario",
            "sensitivity",
            derivation="Prespecified continuity with the global 18-hour window.",
        ),
        _parameter(
            "storage_case_return_temperature_c",
            "B;E",
            "storage",
            "ORNL heating-water return temperature",
            "",
            "deg_C",
            "missing_required",
            "exclusion_gate",
            "ornl_demand_data_gap;dea_ttes_scope",
            limitation="Case-specific storage capacity cannot be fixed without it.",
        ),
        _parameter(
            "transport_reference_distance_mile",
            "D;E",
            "transport",
            "existing campus steam-line distance",
            1,
            "mile",
            "direct_source",
            "context_only",
            "ornl_case_a_configuration",
            limitation="Not a designed Frontier hot-water route.",
        ),
        _parameter(
            "transport_sensitivity_max_distance_km",
            "D;E",
            "transport",
            "maximum local transport sensitivity distance",
            1.609344,
            "km",
            "derived",
            "sensitivity",
            "ornl_case_a_configuration",
            derivation="1 mile * 1.609344 km/mile.",
            limitation="Does not establish a route or distance-loss function.",
        ),
        _parameter(
            "transport_existing_steam_loss_fraction",
            "D;E",
            "transport",
            "existing steam-line heat loss",
            0.08,
            "fraction",
            "direct_source",
            "context_only",
            "ornl_case_a_configuration",
            limitation="Must not be applied as a hot-water-network loss.",
        ),
        _parameter(
            "transport_generic_high_density_loss_fraction",
            "D;E",
            "transport",
            "traditional high-density network loss",
            0.17,
            "fraction",
            "direct_source",
            "sensitivity",
            "cooldh_generic_network",
        ),
        _parameter(
            "transport_generic_low_density_loss_fraction",
            "D;E",
            "transport",
            "traditional low-density network loss upper comparator",
            0.35,
            "fraction",
            "direct_source",
            "sensitivity",
            "cooldh_generic_network",
        ),
        _parameter(
            "transport_generic_pumping_fraction",
            "D;E",
            "transport",
            "generic network pumping energy",
            0.02,
            "MWh_electric/MWh_th_supplied",
            "direct_source",
            "sensitivity",
            "cooldh_generic_network",
        ),
        _parameter(
            "transport_optimized_osterby_loss_fraction",
            "D;E",
            "transport",
            "optimized Osterby network loss",
            0.108,
            "fraction",
            "direct_source",
            "sensitivity",
            "cooldh_osterby_network",
        ),
        _parameter(
            "transport_brunnshog_initial_loss_fraction",
            "D;E",
            "transport",
            "Brunnshog initial network loss",
            0.09,
            "fraction",
            "direct_source",
            "sensitivity",
            "cooldh_brunnshog_network",
        ),
        _parameter(
            "transport_brunnshog_full_build_loss_fraction",
            "D;E",
            "transport",
            "Brunnshog full-build network loss",
            0.03,
            "fraction",
            "direct_source",
            "sensitivity",
            "cooldh_brunnshog_network",
        ),
        _parameter(
            "transport_case_loss_function",
            "D;E",
            "transport",
            "Frontier-specific distance-loss function",
            "",
            "fraction/km",
            "missing_required",
            "exclusion_gate",
            "ornl_case_a_configuration;cooldh_generic_network",
            limitation=(
                "No route geometry, pipe specification or measured hot-water loss "
                "is available; generic percentages are not converted to per-km loss."
            ),
        ),
    ]
    storage_bound_specs = [
        (
            "storage_generic_capacity_mwh",
            "Energy storage capacity for one unit [MWh]",
            "generic TTES capacity",
            "MWh_th",
            1.0,
        ),
        (
            "storage_generic_charge_power_mw",
            "Input capacity for one unit [MW]",
            "generic TTES input capacity",
            "MW_th",
            1.0,
        ),
        (
            "storage_generic_discharge_power_mw",
            "Output capacity for one unit [MW]",
            "generic TTES output capacity",
            "MW_th",
            1.0,
        ),
        (
            "storage_generic_roundtrip_efficiency",
            "Round trip efficiency [%]",
            "generic TTES round-trip efficiency",
            "fraction",
            0.01,
        ),
        (
            "storage_generic_standing_loss_per_day",
            "Energy losses during storage [%/day]",
            "generic TTES storage loss",
            "fraction/day",
            0.01,
        ),
        (
            "storage_generic_auxiliary_fraction",
            "Auxiliary electricity consumption [% of output]",
            "generic TTES auxiliary electricity",
            "MWh_electric/MWh_th_output",
            0.01,
        ),
        (
            "storage_generic_forced_outage_fraction",
            "Forced outage [%]",
            "generic TTES forced outage",
            "fraction",
            0.01,
        ),
        (
            "storage_generic_planned_outage_weeks",
            "Planned outage [weeks/year]",
            "generic TTES planned outage",
            "week/year",
            1.0,
        ),
        (
            "storage_generic_lifetime_years",
            "Technical lifetime [years]",
            "generic TTES technical lifetime",
            "year",
            1.0,
        ),
        (
            "storage_generic_construction_time_years",
            "Construction time [years]",
            "generic TTES construction time",
            "year",
            1.0,
        ),
        (
            "storage_generic_capex_eur2025_per_gwh",
            "Specific investment [M€/GWhCapacity]",
            "generic TTES specific investment",
            "EUR_2025/GWh_th",
            1_000_000.0,
        ),
        (
            "storage_generic_fixed_om_eur2025_per_mwh_year",
            "Fixed O&M [€/MWh Capacity/year]",
            "generic TTES fixed O&M",
            "EUR_2025/MWh_th_capacity/year",
            1.0,
        ),
        (
            "storage_generic_variable_om_eur2025_per_mwh",
            "Variable O&M [€/MWh output]",
            "generic TTES variable O&M",
            "EUR_2025/MWh_th_output",
            1.0,
        ),
        (
            "storage_generic_temperature_difference_k",
            "Typical temperature difference in storage [hot/cold, K]",
            "generic TTES hot-cold temperature difference",
            "K",
            1.0,
        ),
    ]
    for (
        parameter_id,
        source_label,
        parameter_name,
        unit,
        multiplier,
    ) in storage_bound_specs:
        estimates = sorted(
            [
                ttes(source_label, 8) * multiplier,
                ttes(source_label, 9) * multiplier,
            ]
        )
        derivation = (
            "Numeric minimum/maximum of the workbook 2025 Lower and Upper "
            "estimate columns"
        )
        if multiplier != 1.0:
            derivation += f", multiplied by {multiplier:.12g}"
        derivation += "."
        for suffix, estimate in zip(("minimum", "maximum"), estimates, strict=True):
            rows.append(
                _parameter(
                    f"{parameter_id}_{suffix}",
                    "B;E",
                    "storage",
                    f"{parameter_name} {suffix}",
                    estimate,
                    unit,
                    "derived",
                    "sensitivity",
                    "dea_ttes_2025",
                    derivation=derivation,
                )
            )
    return rows


def _write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> None:
    METADATA.mkdir(parents=True, exist_ok=True)
    _write_csv(
        METADATA / "technology_parameter_sources.csv",
        SOURCE_FIELDS,
        _sources(),
    )
    _write_csv(
        METADATA / "technology_pathways.csv",
        PATHWAY_FIELDS,
        _pathways(),
    )
    _write_csv(
        METADATA / "technology_parameters.csv",
        PARAMETER_FIELDS,
        _parameters(),
    )
    print("Built Phase C technology pathways and parameter tables.")


if __name__ == "__main__":
    main()
