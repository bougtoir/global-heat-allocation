# ruff: noqa: E501
"""Build the case-specific evidence ledger for the Frontier-to-ORNL pathway."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "provenance" / "case_specific_evidence.csv"
TECHNOLOGY_PARAMETERS = ROOT / "data" / "metadata" / "technology_parameters.csv"
ENVIRONMENTAL_PARAMETERS = ROOT / "data" / "metadata" / "environmental_parameters.csv"
DISPATCH_SUMMARY = ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv"
SOURCE_POTENTIAL = (
    ROOT / "results" / "techno_economic" / "frontier_source_potential.csv"
)
DEMAND_SUMMARY = ROOT / "data" / "metadata" / "ornl_demand_summary.csv"

STATUS_VALUES = {
    "FOUND_MEASURED",
    "FOUND_DERIVABLE",
    "FOUND_BOUND_ONLY",
    "NOT_FOUND",
}

FIELDS = [
    "evidence_id",
    "required_item",
    "status",
    "value_summary",
    "unit",
    "source_keys",
    "source_locations",
    "derivation_or_extraction",
    "claim_limit",
    "downstream_decision",
]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _row(
    evidence_id: str,
    required_item: str,
    status: str,
    value_summary: str,
    unit: str,
    source_keys: str,
    source_locations: str,
    derivation_or_extraction: str,
    claim_limit: str,
    downstream_decision: str,
) -> dict[str, str]:
    if status not in STATUS_VALUES:
        raise ValueError(f"Invalid evidence status for {evidence_id}: {status}")
    return {
        "evidence_id": evidence_id,
        "required_item": required_item,
        "status": status,
        "value_summary": value_summary,
        "unit": unit,
        "source_keys": source_keys,
        "source_locations": source_locations,
        "derivation_or_extraction": derivation_or_extraction,
        "claim_limit": claim_limit,
        "downstream_decision": downstream_decision,
    }


def _technology_value(parameters: pd.DataFrame, parameter_id: str) -> str:
    matches = parameters.loc[parameters["parameter_id"].eq(parameter_id), "value"]
    if len(matches) != 1 or pd.isna(matches.iloc[0]):
        raise ValueError(f"Expected one value for {parameter_id}")
    return str(matches.iloc[0])


def _source_metric(source: pd.DataFrame, metric: str) -> float:
    matches = source.loc[source["metric"].eq(metric), "value"]
    if len(matches) != 1:
        raise ValueError(f"Expected one source metric: {metric}")
    return float(matches.iloc[0])


def _demand_value(demand: pd.DataFrame, record_id: str) -> float:
    matches = demand.loc[demand["record_id"].eq(record_id), "value_mw_th"]
    if len(matches) != 1:
        raise ValueError(f"Expected one demand summary value: {record_id}")
    return float(matches.iloc[0])


def _rows() -> list[dict[str, str]]:
    technology = pd.read_csv(TECHNOLOGY_PARAMETERS).fillna("")
    environmental = pd.read_csv(ENVIRONMENTAL_PARAMETERS).fillna("")
    dispatch = pd.read_csv(DISPATCH_SUMMARY)
    source = pd.read_csv(SOURCE_POTENTIAL)
    demand = pd.read_csv(DEMAND_SUMMARY)

    baseline = dispatch.loc[
        dispatch["scenario_id"].eq("zero_demand_rejection_baseline")
    ].iloc[0]
    observed_intervals = int(baseline["observed_source_intervals"])
    unavailable_intervals = int(baseline["unavailable_source_intervals"])
    observed_energy = float(baseline["source_heat_available_mwh"])
    expected_intervals = int(_source_metric(source, "expected_10_minute_intervals"))
    missing_timestamps = int(_source_metric(source, "missing_timestamps"))
    mean_waste_heat = float(_technology_value(technology, "source_waste_heat_mean_mw"))
    max_waste_heat = float(_technology_value(technology, "source_waste_heat_max_mw"))
    total_capacity = float(
        _technology_value(technology, "heat_pump_case_total_capacity_mw")
    )
    cop = float(_technology_value(technology, "heat_pump_case_cop"))
    unit_cost = float(
        _technology_value(technology, "heat_pump_case_unit_equipment_cost_usd")
    )
    surface_flow_missing = environmental.loc[
        environmental["parameter_id"].eq("case_surface_water_flow_m3_s"),
        "value_kind",
    ].iloc[0]
    if surface_flow_missing != "missing_required":
        raise ValueError("Unexpected surface-water evidence state")
    case_a_average = _demand_value(demand, "case_a_average")
    case_a_maximum = _demand_value(demand, "case_a_maximum")
    case_b_average = _demand_value(demand, "case_b_selected_average")
    case_b_maximum = _demand_value(demand, "case_b_selected_maximum")

    return [
        _row(
            "frontier_source_timeseries",
            "Measured Frontier source heat quantity, temperature grade, and temporal profile",
            "FOUND_MEASURED",
            (
                f"{observed_intervals:,} valid 10-minute source intervals, "
                f"{unavailable_intervals:,} unavailable intervals, "
                f"{observed_energy:,.1f} MWh-th observed heat; mean "
                f"{mean_waste_heat:.4f} MW and maximum {max_waste_heat:.4f} MW."
            ),
            "MW_th; MWh_th; count",
            "frontier_hpc_facility_data_v4;frontier_scientific_data_article",
            (
                "Workbook Frontier2023; Scientific Data article dataset description "
                "and data-record sections"
            ),
            (
                "Workbook numeric Overall_WasteHeat values summed with a 10-minute "
                "timestep; unavailable timestamps remain explicit."
            ),
            "Measured source availability only; not a receiving-demand trace.",
            "Use as measured source input for bounded dispatch scenarios.",
        ),
        _row(
            "ornl_receiving_hourly_demand_profile",
            "ORNL hourly or sub-hourly receiving heat-demand profile or auditable reconstruction",
            "NOT_FOUND",
            "No public hourly or sub-hourly receiving-demand trace or auditable reconstruction input was found.",
            "MW_th time series",
            "frontier_ornl_showcase_report",
            "Report Section 6 states collection of building heating/hot-water demand data posed notable difficulties.",
            "Search covered the ORNL/OSTI report, ORNL publication page, Figshare, OSTI, and web-indexed HP ShowCase terms.",
            "Do not claim observed or calibrated annual delivery.",
            "Retain only constant lower/upper demand-bound dispatch scenarios.",
        ),
        _row(
            "ornl_receiving_demand_summary",
            "ORNL receiving heat-demand measured summary bounds",
            "FOUND_MEASURED",
            (
                "Figure 13 reports one-year recorded space-heating summaries: "
                f"Case A 5600-5700-5800 average {case_a_average:.2f} MW and "
                f"maximum {case_a_maximum:.2f} MW; selected Case B average "
                f"{case_b_average:.2f} MW and maximum {case_b_maximum:.2f} MW."
            ),
            "MW_th",
            "frontier_ornl_showcase_report",
            "Figure 13 Building Selection worksheet screenshot; Table 4 case definitions.",
            (
                "Manual transcription from the report figure; "
                f"{case_a_average:.2f} MW * 8,760 h is consistent with "
                ">6,640 MWh/year."
            ),
            "Summary bounds only; no timestamped profile or load-shape reconstruction.",
            "Use for narrative demand evidence and bounds, not calibrated dispatch.",
        ),
        _row(
            "source_capture_efficiency",
            "Frontier source-side heat-capture or heat-exchanger efficiency",
            "FOUND_BOUND_ONLY",
            "The article reports cooling distribution carries away up to 97%-99% of waste heat, but no new recovery heat-exchanger efficiency is reported.",
            "fraction",
            "frontier_scientific_data_article;frontier_ornl_showcase_report",
            "Scientific Data cooling-system description; ORNL report Frontier cooling-loop description.",
            "The 97%-99% statement bounds heat carried in the existing cooling loop, not recoverable heat across a proposed exchanger.",
            "Do not convert the bound into a measured case source-capture efficiency.",
            "Keep unity capture only as an explicit upper-bound sensitivity.",
        ),
        _row(
            "balance_of_plant_auxiliary_electricity",
            "Balance-of-plant auxiliary electricity for heat recovery",
            "FOUND_BOUND_ONLY",
            "Frontier accessory/cooling power is measured, but incremental heat-recovery pumps, controls, and exchangers are not isolated.",
            "MWh_e/MWh_th",
            "frontier_hpc_facility_data_v4;frontier_scientific_data_article",
            "Workbook accessory-power columns; Scientific Data Figures 4-5 discussion.",
            "Accessory power describes the existing facility cooling system, not the marginal auxiliary load of a new heat-recovery project.",
            "Do not use measured accessory power as project auxiliary electricity.",
            "Keep project auxiliary electricity missing; generic values remain labeled as generic sensitivities.",
        ),
        _row(
            "route_length_and_path",
            "Route length and plausible thermal-network path",
            "FOUND_BOUND_ONLY",
            "The report states existing steam travels about 1 mile with about 8% loss, and the official map locates relevant buildings; no designed Frontier hot-water route is published.",
            "mile; map context",
            "frontier_ornl_showcase_report;ornl_main_campus_map_2025",
            "ORNL report Case A discussion; ORNL Main Campus and Key map.",
            "Existing steam-line distance and campus building context are not a new hot-water route geometry.",
            "Do not claim calibrated thermal-network transport or a route-specific loss function.",
            "Treat near-distance transport as conditional/generic only.",
        ),
        _row(
            "hydraulic_network_design_inputs",
            "Hydraulic/network design inputs",
            "NOT_FOUND",
            "No pipe diameter, length-by-segment, insulation, pump head, flow, pressure-drop, trenching, or hydraulic profile was found for a new Frontier-to-ORNL hot-water network.",
            "site-specific design inputs",
            "frontier_ornl_showcase_report;ornl_main_campus_map_2025",
            "Report and official map provide concept and building context only.",
            "Absence confirmed after targeted route, pipeline, hydraulic, and HP ShowCase searches.",
            "Cannot calibrate transport losses, pumping energy, or network CAPEX.",
            "Exclude calibrated thermal-network transport claims.",
        ),
        _row(
            "case_storage_design",
            "Storage tank volume and operating temperature difference",
            "NOT_FOUND",
            "No case-specific storage tank volume or operating Delta-T was found.",
            "m3; K",
            "frontier_ornl_showcase_report;denmark_energy_storage_datasheets_v0011",
            "ORNL report contains no storage design; Danish TTES datasheet is generic comparator evidence.",
            "The reported 75-85 deg C heat-pump sink loop is not a storage-tank operating range.",
            "Do not present generic tank sensitivity as a Frontier/ORNL storage design.",
            "Retain storage only as formula/generic sensitivity.",
        ),
        _row(
            "source_outage_availability",
            "Outage/availability information for the measured source",
            "FOUND_MEASURED",
            (
                f"Scientific Data reports approximately 440 h lost to planned maintenance and unplanned downtime; "
                f"the aligned calendar contains {missing_timestamps:,} missing 10-minute timestamps out of "
                f"{expected_intervals:,} expected intervals."
            ),
            "hour; count",
            "frontier_scientific_data_article;frontier_hpc_facility_data_v4",
            "Scientific Data Data Records section; generated source-potential inventory.",
            "Calendar alignment rounds timestamp drift to nominal 10-minute timestamps and does not impute unavailable source heat.",
            "Source downtime is measured; heat-recovery equipment availability is not.",
            "Use missing intervals as unavailable source intervals in dispatch.",
        ),
        _row(
            "heat_recovery_system_availability",
            "Outage/availability information for the proposed heat-recovery system",
            "NOT_FOUND",
            "No case-specific heat-pump, storage, pump, exchanger, or network outage schedule was found.",
            "fraction; schedule",
            "frontier_ornl_showcase_report",
            "ORNL report case-study sections and Table 5.",
            "Generic technology outage assumptions exist but are not Frontier/ORNL project evidence.",
            "Do not claim observed annual heat-recovery-system availability.",
            "Use only explicit generic sensitivity assumptions.",
        ),
        _row(
            "heat_pump_cop_capacity",
            "Heat-pump technology capacity and COP used for bounded dispatch",
            "FOUND_DERIVABLE",
            f"Carrier 61XWHZE case COP {cop:.2f}; three 1 MW-th units imply {total_capacity:.1f} MW-th total capacity.",
            "MW_heat/MW_e; MW_th",
            "frontier_ornl_showcase_report;carrier_product_envelope",
            "ORNL report Table 4/Figure 16 discussion and Carrier product envelope.",
            "Total capacity = 3 units * 1 MW-th/unit.",
            "Unit performance evidence does not supply full balance-of-plant or installed project performance.",
            "Use for bounded technology and dispatch sensitivity.",
        ),
        _row(
            "cost_and_price_year",
            "Installed/project/equipment cost and price year",
            "FOUND_BOUND_ONLY",
            f"ORNL reports Carrier 61XWHZE-1000 capital cost of ${unit_cost:,.0f} per unit and payback times, but no full installed project cost or price year.",
            "USD/unit; year missing",
            "frontier_ornl_showcase_report",
            "Report Section 5.1 and Table 5.",
            "Equipment-only unit quote transcribed from the report; price year and balance-of-plant scope are not defined.",
            "Do not compute Frontier-specific LCOH, NPC, or payback from this partial cost.",
            "Keep economics as generic comparator or partial equipment context.",
        ),
        _row(
            "equipment_embodied_co2e",
            "Equipment, construction, refrigerant, and replacement lifecycle emissions",
            "NOT_FOUND",
            "No case-specific lifecycle inventory for heat pumps, storage, pipe network, refrigerant, construction, or replacements was found.",
            "kg_CO2e",
            "frontier_ornl_showcase_report;epa_egrid_2023_rev2;epa_factors_2025",
            "ORNL report has operating CO2 reductions; EPA/EIA factors support operational emissions only.",
            "Operational factors do not define cradle-to-grave equipment embodied emissions.",
            "Do not claim case-specific lifecycle CO2e.",
            "Limit emissions to operational comparator sensitivities.",
        ),
        _row(
            "receiving_water_flow_temperature",
            "Receiving-water flow and upstream temperature",
            "NOT_FOUND",
            "No candidate receiving-water flow and upstream-temperature pair for a proposed residual heat discharge was found.",
            "m3/s; deg_C",
            "tdec_tn0002941_compliance_inspection_2025;doe_orr_aser_2024;epa_tennessee_water_quality_standards_2024",
            "TDEC inspection confirms sitewide permit context; Tennessee criteria define temperature limits.",
            "Existing site monitoring and standards do not define a candidate outfall hydraulic heat capacity.",
            "Do not calculate a site-specific receiving-water thermal capacity.",
            "Exclude new external receiving-water discharge as practical pathway.",
        ),
        _row(
            "approved_mixing_zone_outfall",
            "Approved mixing-zone/outfall information",
            "NOT_FOUND",
            "No approved new thermal outfall or mixing-zone definition for the proposed residual heat was found.",
            "site-specific approval",
            "tdec_tn0002941_compliance_inspection_2025;epa_thermal_discharges_npdes_2023;epa_tennessee_water_quality_standards_2024",
            "TDEC inspection says TN0002941 covers existing discharges to White Oak Creek, Clinch River, and Melton Branch with more than 675 outfalls.",
            "Existing permit context is not approval for a new thermal discharge by inference.",
            "Do not treat existing NPDES coverage as residual-heat disposal permission.",
            "Exclude new receiving-water thermal discharge unless new permit evidence appears.",
        ),
        _row(
            "route_footprint_environmental_clearance",
            "Route/footprint environmental evidence",
            "FOUND_BOUND_ONLY",
            "Official campus map and Oak Ridge Reservation environmental reports establish site context and sensitive resources, but no project route or footprint clearance was found.",
            "site-specific clearance",
            "ornl_main_campus_map_2025;doe_orr_aser_2024",
            "ORNL Main Campus map; ASER wetland and protected-resource sections.",
            "General site context cannot substitute for a route-specific environmental review.",
            "Do not claim route clearance or absence of ecological conflict.",
            "Treat network/storage siting as conditional until route and footprint evidence exist.",
        ),
    ]


def main() -> None:
    rows = _rows()
    _write_csv(OUTPUT, rows)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(rows)} evidence rows.")


if __name__ == "__main__":
    main()
