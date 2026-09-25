"""Build the Phase E environmental receiving-capacity constraint model."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pandas as pd

from global_heat_allocation.environmental_constraints import (
    scaled_tank_storage_capacity_mwh,
)

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "data" / "metadata"
RESULTS = ROOT / "results" / "environmental_constraints"
TECHNOLOGY_PARAMETERS = METADATA / "technology_parameters.csv"
SOURCES_OUTPUT = METADATA / "environmental_parameter_sources.csv"
PARAMETERS_OUTPUT = METADATA / "environmental_parameters.csv"
RECEIVING_OUTPUT = RESULTS / "receiving_class_constraints.csv"
PATHWAY_OUTPUT = RESULTS / "frontier_pathway_assessment.csv"
STORAGE_OUTPUT = RESULTS / "storage_capacity_sensitivity.csv"

SOURCE_FIELDS = [
    "source_id",
    "source_key",
    "source_type",
    "source_location",
    "extracted_fact",
    "applicability",
    "limitations",
]
PARAMETER_FIELDS = [
    "parameter_id",
    "component",
    "parameter_name",
    "value",
    "unit",
    "value_kind",
    "source_ids",
    "derivation",
    "applicability",
    "limitation",
]
RECEIVING_FIELDS = [
    "receiving_class",
    "global_screening_role",
    "practical_default",
    "capacity_rule",
    "required_evidence",
    "rationale",
    "source_ids",
]
PATHWAY_FIELDS = [
    "pathway_id",
    "pathway_label",
    "receiving_mode",
    "new_external_thermal_discharge",
    "assessment_status",
    "binding_constraints",
    "cumulative_load_metric",
    "cumulative_load_value",
    "unit",
    "conclusion",
]
STORAGE_FIELDS = [
    "scenario_id",
    "tank_volume_m3",
    "operating_delta_temperature_k",
    "capacity_mwh_th",
    "value_kind",
    "source_ids",
    "limitation",
]


def _write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _technology_value(parameters: pd.DataFrame, parameter_id: str) -> float:
    matches = parameters.loc[parameters["parameter_id"].eq(parameter_id), "value"]
    if len(matches) != 1 or not matches.iloc[0]:
        raise ValueError(f"Expected one numeric technology parameter: {parameter_id}")
    return float(matches.iloc[0])


def _sources() -> list[dict[str, str]]:
    return [
        {
            "source_id": "epa_npdes_thermal_framework",
            "source_key": "epa_thermal_discharges_npdes_2023",
            "source_type": "federal_regulatory_guidance",
            "source_location": "PDF pp. 3-6, Sections 2.1.2-2.1.4",
            "extracted_fact": (
                "Thermal discharge limits are generally based on receiving-water "
                "standards; mixing zones are site-specific; a Section 316(a) "
                "variance requires a demonstration protecting the balanced "
                "indigenous community and considering cumulative impacts."
            ),
            "applicability": (
                "Defines the evidence required before assigning receiving-water "
                "capacity to a new thermal discharge."
            ),
            "limitations": (
                "Guidance does not provide a transferable site capacity or permit."
            ),
        },
        {
            "source_id": "tn_surface_water_temperature",
            "source_key": "epa_tennessee_water_quality_standards_2024",
            "source_type": "state_water_quality_standard",
            "source_location": "Rule 0400-40-03-.03(1)(g), (3)(e), and (6)(e)",
            "extracted_fact": (
                "Maximum change is 3 deg C relative to upstream control; maximum "
                "water temperature is 30.5 deg C; maximum rate is 2 deg C/h; "
                "recognized trout waters have a 20 deg C maximum."
            ),
            "applicability": (
                "Tennessee surface-water criteria for screening any proposed "
                "Frontier or ORNL thermal discharge."
            ),
            "limitations": (
                "The criteria do not by themselves define an allowable heat load."
            ),
        },
        {
            "source_id": "tn_mixing_zone_protections",
            "source_key": "epa_tennessee_water_quality_standards_2024",
            "source_type": "state_water_quality_standard",
            "source_location": "Rule 0400-40-03-.05(2)",
            "extracted_fact": (
                "Mixing zones must be restricted and must not cause mortality, "
                "impair uses, adversely affect nursery or spawning areas, or "
                "adversely affect specially protected species."
            ),
            "applicability": (
                "Requires ecological and site-specific review in addition to "
                "numeric temperature criteria."
            ),
            "limitations": "No candidate outfall or mixing zone has been defined.",
        },
        {
            "source_id": "orr_sensitive_environment",
            "source_key": "doe_orr_aser_2024",
            "source_type": "federal_site_environmental_report",
            "source_location": "PDF Sections 1.3.6.1-1.3.6.3",
            "extracted_fact": (
                "The Oak Ridge Reservation reports about 235 hectares of potential "
                "wetlands and documents protected wildlife and plant resources."
            ),
            "applicability": (
                "Establishes that sparse or federally managed land near the case "
                "cannot be treated as environmentally unconstrained."
            ),
            "limitations": (
                "Project-level route and footprint screening remain necessary."
            ),
        },
        {
            "source_id": "ornl_npdes_context",
            "source_key": "doe_orr_aser_2024",
            "source_type": "federal_site_environmental_report",
            "source_location": "PDF Table 5.4 and Section 5.3.4",
            "extracted_fact": (
                "ORNL operates under sitewide NPDES permit TN0002941; the "
                "February 2023 permit was administratively extended while renewal "
                "was pending during 2024."
            ),
            "applicability": (
                "Existing discharge compliance is baseline context, not approval "
                "for a new thermal outfall."
            ),
            "limitations": (
                "The report does not assign the proposed heat-recovery residual "
                "load to an outfall or define a new thermal limit."
            ),
        },
        {
            "source_id": "dea_ttes_capacity_basis",
            "source_key": "denmark_energy_storage_datasheets_v0011",
            "source_type": "official_technology_datasheet",
            "source_location": "Workbook sheet '141a TTES', 2025 control column",
            "extracted_fact": (
                "The generic atmospheric tank example stores 290 MWh in 5,000 m3 "
                "at a 55 K temperature difference and 90% availability."
            ),
            "applicability": (
                "Provides a sourced physical scaling basis for storage sensitivity."
            ),
            "limitations": (
                "ORNL tank volume and operating temperature difference are unknown."
            ),
        },
        {
            "source_id": "global_land_water_mask",
            "source_key": "ncep_land_mask",
            "source_type": "reanalysis_invariant_field",
            "source_location": "NCEP/NCAR Reanalysis 1 Gaussian-grid land mask",
            "extracted_fact": "Separates land from water on the global screening grid.",
            "applicability": "Global diagnostic receiving-class separation.",
            "limitations": (
                "Does not separate inland, coastal, and open-ocean ecology."
            ),
        },
        {
            "source_id": "global_sea_ice_mask",
            "source_key": "ncep_sea_ice_concentration_2023",
            "source_type": "reanalysis_field",
            "source_location": "2023 NCEP/NCAR Reanalysis 1 sea-ice concentration",
            "extracted_fact": (
                "Sea-ice concentration of at least 0.15 is used for the existing "
                "cryosphere exclusion."
            ),
            "applicability": "Global cryosphere exclusion.",
            "limitations": "Screening classification, not an impact model.",
        },
        {
            "source_id": "global_snow_mask",
            "source_key": "ncep_snow_water_equivalent_2023",
            "source_type": "reanalysis_field",
            "source_location": "2023 NCEP/NCAR Reanalysis 1 snow water equivalent",
            "extracted_fact": (
                "Snow water equivalent of at least 1 kg/m2 is used for the "
                "existing cryosphere exclusion."
            ),
            "applicability": "Global cryosphere exclusion.",
            "limitations": "Screening classification, not an impact model.",
        },
    ]


def _parameters(technology: pd.DataFrame) -> list[dict[str, str]]:
    rows = [
        {
            "parameter_id": "tn_max_temperature_change_c",
            "component": "surface_water",
            "parameter_name": "maximum temperature change",
            "value": "3",
            "unit": "deg_C",
            "value_kind": "direct_source",
            "source_ids": "tn_surface_water_temperature",
            "derivation": "",
            "applicability": "Tennessee receiving-water screening.",
            "limitation": "Not a standalone discharge capacity.",
        },
        {
            "parameter_id": "tn_max_water_temperature_c",
            "component": "surface_water",
            "parameter_name": "maximum water temperature",
            "value": "30.5",
            "unit": "deg_C",
            "value_kind": "direct_source",
            "source_ids": "tn_surface_water_temperature",
            "derivation": "",
            "applicability": "Tennessee receiving-water screening.",
            "limitation": "Upstream temperature is required.",
        },
        {
            "parameter_id": "tn_max_temperature_rate_c_per_hour",
            "component": "surface_water",
            "parameter_name": "maximum temperature change rate",
            "value": "2",
            "unit": "deg_C/hour",
            "value_kind": "direct_source",
            "source_ids": "tn_surface_water_temperature",
            "derivation": "",
            "applicability": "Tennessee receiving-water screening.",
            "limitation": "A discharge time series is required.",
        },
        {
            "parameter_id": "tn_trout_water_max_temperature_c",
            "component": "surface_water",
            "parameter_name": "recognized trout-water maximum temperature",
            "value": "20",
            "unit": "deg_C",
            "value_kind": "direct_source",
            "source_ids": "tn_surface_water_temperature",
            "derivation": "",
            "applicability": "Only if a candidate receiving water is trout water.",
            "limitation": "Receiving-water classification is not established.",
        },
        {
            "parameter_id": "orr_potential_wetland_area_ha",
            "component": "sensitive_environment",
            "parameter_name": "potential wetland area on Oak Ridge Reservation",
            "value": "235",
            "unit": "hectare",
            "value_kind": "direct_source",
            "source_ids": "orr_sensitive_environment",
            "derivation": "",
            "applicability": "Site-level environmental context.",
            "limitation": "Not a project footprint or route map.",
        },
        {
            "parameter_id": "ornl_npdes_permit_id",
            "component": "surface_water",
            "parameter_name": "ORNL sitewide NPDES permit",
            "value": "TN0002941",
            "unit": "identifier",
            "value_kind": "direct_source",
            "source_ids": "ornl_npdes_context",
            "derivation": "",
            "applicability": "Existing site discharge context.",
            "limitation": "Does not authorize a new thermal discharge by inference.",
        },
    ]
    copied_parameters = {
        "storage_generic_capacity_mwh": "generic TTES reference capacity",
        "storage_generic_volume_m3": "generic TTES reference volume",
        "storage_generic_temperature_difference_k": (
            "generic TTES reference temperature difference"
        ),
        "storage_generic_max_hot_temperature_c": (
            "generic TTES maximum hot temperature"
        ),
        "storage_cost_formula_min_volume_m3": ("generic TTES minimum modeled volume"),
        "storage_cost_formula_max_volume_m3": ("generic TTES maximum modeled volume"),
        "storage_generic_temperature_difference_k_minimum": (
            "generic TTES minimum temperature difference"
        ),
        "storage_generic_temperature_difference_k_maximum": (
            "generic TTES maximum temperature difference"
        ),
    }
    indexed = technology.set_index("parameter_id")
    for parameter_id, parameter_name in copied_parameters.items():
        record = indexed.loc[parameter_id]
        rows.append(
            {
                "parameter_id": parameter_id,
                "component": "thermal_storage",
                "parameter_name": parameter_name,
                "value": record["value"],
                "unit": record["unit"],
                "value_kind": "derived",
                "source_ids": "dea_ttes_capacity_basis",
                "derivation": (
                    "Copied from the validated Phase C technology parameter table."
                ),
                "applicability": "Generic storage sensitivity only.",
                "limitation": (
                    "Not a Frontier or ORNL storage design unless case inputs "
                    "are supplied."
                ),
            }
        )
    missing = [
        (
            "case_surface_water_flow_m3_s",
            "surface_water",
            "candidate receiving-water flow",
            "m3/s",
            "Required to convert temperature criteria to a hydraulic heat-load bound.",
        ),
        (
            "case_surface_water_upstream_temperature_c",
            "surface_water",
            "candidate receiving-water upstream temperature",
            "deg_C",
            "Required to evaluate the 30.5 deg C absolute criterion.",
        ),
        (
            "case_surface_water_mixing_zone",
            "surface_water",
            "approved thermal mixing-zone definition",
            "site_specific",
            "No candidate outfall or approved mixing zone exists.",
        ),
        (
            "case_aquatic_biological_assessment",
            "surface_water",
            "aquatic biological and cumulative-impact assessment",
            "site_specific",
            "Required before any practical thermal-discharge recommendation.",
        ),
        (
            "case_storage_volume_m3",
            "thermal_storage",
            "case-specific tank volume",
            "m3",
            "Required to fix the practical storage capacity.",
        ),
        (
            "case_storage_operating_delta_temperature_k",
            "thermal_storage",
            "case-specific storage temperature difference",
            "K",
            "ORNL return temperature and storage design remain unavailable.",
        ),
        (
            "case_route_sensitive_area_clearance",
            "sensitive_environment",
            "route and footprint environmental clearance",
            "site_specific",
            "No hot-water route or project footprint has been defined.",
        ),
        (
            "case_cumulative_residual_heat_mwh",
            "cumulative_load",
            "annual residual rejected heat",
            "MWh_th/year",
            "Requires synchronized source, demand, storage, and outage dispatch.",
        ),
    ]
    for parameter_id, component, name, unit, limitation in missing:
        rows.append(
            {
                "parameter_id": parameter_id,
                "component": component,
                "parameter_name": name,
                "value": "",
                "unit": unit,
                "value_kind": "missing_required",
                "source_ids": (
                    "epa_npdes_thermal_framework;tn_mixing_zone_protections"
                    if component == "surface_water"
                    else ""
                ),
                "derivation": "",
                "applicability": "Case-specific environmental gate.",
                "limitation": limitation,
            }
        )
    return rows


def _receiving_classes() -> list[dict[str, str]]:
    return [
        {
            "receiving_class": "populated_land",
            "global_screening_role": "burden-weighted diagnostic",
            "practical_default": "conditional_closed_loop_only",
            "capacity_rule": (
                "Useful heat must be bounded by measured demand or enclosed "
                "storage; ambient dumping receives no safety credit."
            ),
            "required_evidence": (
                "Demand trace, equipment limits, residual rejection, and local permits."
            ),
            "rationale": "Population weights burden, not ecological capacity.",
            "source_ids": "epa_npdes_thermal_framework",
        },
        {
            "receiving_class": "sparse_land",
            "global_screening_role": "diagnostic_only",
            "practical_default": "excluded_ambient_release",
            "capacity_rule": "No positive practical ambient capacity is assigned.",
            "required_evidence": (
                "Site-specific land, habitat, route, and local-climate assessment."
            ),
            "rationale": "Population absence is not evidence of environmental safety.",
            "source_ids": "orr_sensitive_environment",
        },
        {
            "receiving_class": "sensitive_ecosystem",
            "global_screening_role": "unresolved_in_current_global_mask",
            "practical_default": "excluded",
            "capacity_rule": (
                "Exclude unless project-level regulatory and ecological review "
                "authorizes the pathway."
            ),
            "required_evidence": (
                "Wetland, protected-species, habitat, and cumulative-impact review."
            ),
            "rationale": "The case region contains wetlands and protected resources.",
            "source_ids": "orr_sensitive_environment;tn_mixing_zone_protections",
        },
        {
            "receiving_class": "cryosphere",
            "global_screening_role": "categorical_exclusion",
            "practical_default": "excluded",
            "capacity_rule": "No practical receiving capacity is assigned.",
            "required_evidence": "Not applicable; excluded by design.",
            "rationale": (
                "Sea ice and snow are climate-sensitive and are not disposal sinks."
            ),
            "source_ids": "global_sea_ice_mask;global_snow_mask",
        },
        {
            "receiving_class": "inland_water",
            "global_screening_role": "water_class_diagnostic_only",
            "practical_default": "excluded_without_site_specific_permit",
            "capacity_rule": (
                "No capacity without flow, upstream temperature, permit limits, "
                "mixing-zone analysis, biology, and cumulative-load assessment."
            ),
            "required_evidence": (
                "NPDES pathway, receiving-water data, thermal model, and ecology."
            ),
            "rationale": (
                "Numeric temperature criteria are necessary but not sufficient."
            ),
            "source_ids": (
                "epa_npdes_thermal_framework;tn_surface_water_temperature;"
                "tn_mixing_zone_protections"
            ),
        },
        {
            "receiving_class": "coastal_water",
            "global_screening_role": "water_class_diagnostic_only",
            "practical_default": "excluded_without_site_specific_permit",
            "capacity_rule": (
                "No generic capacity; require site hydrodynamics, ecology, permit, "
                "and cumulative-impact evidence."
            ),
            "required_evidence": (
                "Outfall, plume model, sensitive-species review, and permit limits."
            ),
            "rationale": "Coastal mixing does not establish environmental safety.",
            "source_ids": "epa_npdes_thermal_framework",
        },
        {
            "receiving_class": "open_ocean",
            "global_screening_role": "theoretical_pathology_diagnostic",
            "practical_default": "excluded",
            "capacity_rule": "No engineering or environmental capacity is assigned.",
            "required_evidence": (
                "A defined pathway, transport system, permits, and ocean-impact model."
            ),
            "rationale": (
                "The global mathematical sink is not a practical disposal option."
            ),
            "source_ids": "epa_npdes_thermal_framework;global_land_water_mask",
        },
    ]


def _pathways() -> list[dict[str, str]]:
    missing_cumulative = "case_cumulative_residual_heat_mwh"
    return [
        {
            "pathway_id": "A",
            "pathway_label": "Conventional rejection",
            "receiving_mode": "existing_facility_rejection_system",
            "new_external_thermal_discharge": "no",
            "assessment_status": "baseline_only",
            "binding_constraints": (
                "Existing permit and cooling-system scope; residual stream not "
                "isolated."
            ),
            "cumulative_load_metric": missing_cumulative,
            "cumulative_load_value": "",
            "unit": "MWh_th/year",
            "conclusion": (
                "Retain as the observed-system baseline; do not infer capacity for "
                "a new sink."
            ),
        },
        {
            "pathway_id": "B",
            "pathway_label": "Same-location temporal storage and later reuse",
            "receiving_mode": "closed_loop_tank_storage_and_end_use",
            "new_external_thermal_discharge": "no",
            "assessment_status": "conditional_open",
            "binding_constraints": (
                "Tank volume; operating delta T; demand trace; residual rejection."
            ),
            "cumulative_load_metric": missing_cumulative,
            "cumulative_load_value": "",
            "unit": "MWh_th/year",
            "conclusion": (
                "Generic tank capacity can be screened, but no case-specific "
                "environmental recommendation is permitted."
            ),
        },
        {
            "pathway_id": "C",
            "pathway_label": "Local direct reuse",
            "receiving_mode": "closed_loop_building_heat_service",
            "new_external_thermal_discharge": "no",
            "assessment_status": "conditional_open",
            "binding_constraints": (
                "Measured demand; heat-pump limits; residual returned to the "
                "existing rejection system."
            ),
            "cumulative_load_metric": missing_cumulative,
            "cumulative_load_value": "",
            "unit": "MWh_th/year",
            "conclusion": (
                "Can be evaluated as a conditional least-assumption sensitivity; "
                "no environmental preference or project recommendation is permitted."
            ),
        },
        {
            "pathway_id": "D",
            "pathway_label": "Near-distance transport without storage",
            "receiving_mode": "closed_loop_hot_water_network",
            "new_external_thermal_discharge": "no",
            "assessment_status": "excluded_pending_route_review",
            "binding_constraints": (
                "Undefined route, footprint, habitat clearance, hydraulics, and demand."
            ),
            "cumulative_load_metric": missing_cumulative,
            "cumulative_load_value": "",
            "unit": "MWh_th/year",
            "conclusion": (
                "Exclude from practical recommendations until a route exists."
            ),
        },
        {
            "pathway_id": "E",
            "pathway_label": "Storage plus near-distance transport",
            "receiving_mode": "closed_loop_storage_and_hot_water_network",
            "new_external_thermal_discharge": "no",
            "assessment_status": "excluded_pending_design",
            "binding_constraints": (
                "All storage, route, footprint, demand, and residual-load gaps."
            ),
            "cumulative_load_metric": missing_cumulative,
            "cumulative_load_value": "",
            "unit": "MWh_th/year",
            "conclusion": "Exclude until storage and route designs are auditable.",
        },
        {
            "pathway_id": "W",
            "pathway_label": "New direct surface-water thermal discharge",
            "receiving_mode": "inland_or_coastal_water",
            "new_external_thermal_discharge": "yes",
            "assessment_status": "excluded",
            "binding_constraints": (
                "No outfall, flow, upstream temperature, permit, mixing-zone, "
                "biology, or cumulative-impact assessment."
            ),
            "cumulative_load_metric": missing_cumulative,
            "cumulative_load_value": "",
            "unit": "MWh_th/year",
            "conclusion": "Not an admissible Frontier practical pathway.",
        },
        {
            "pathway_id": "G",
            "pathway_label": "New ambient land or atmospheric relocation",
            "receiving_mode": "populated_or_sparse_land",
            "new_external_thermal_discharge": "yes",
            "assessment_status": "excluded",
            "binding_constraints": (
                "No evidence-based ecological or local-climate receiving capacity."
            ),
            "cumulative_load_metric": missing_cumulative,
            "cumulative_load_value": "",
            "unit": "MWh_th/year",
            "conclusion": (
                "The global theoretical slab result is not a disposal recommendation."
            ),
        },
    ]


def _storage_sensitivity(technology: pd.DataFrame) -> list[dict[str, object]]:
    reference_capacity = _technology_value(
        technology,
        "storage_generic_capacity_mwh",
    )
    reference_volume = _technology_value(
        technology,
        "storage_generic_volume_m3",
    )
    reference_delta = _technology_value(
        technology,
        "storage_generic_temperature_difference_k",
    )
    volumes = [
        _technology_value(technology, "storage_cost_formula_min_volume_m3"),
        reference_volume,
        _technology_value(technology, "storage_cost_formula_max_volume_m3"),
    ]
    delta_temperatures = [
        _technology_value(
            technology,
            "storage_generic_temperature_difference_k_minimum",
        ),
        reference_delta,
        _technology_value(
            technology,
            "storage_generic_temperature_difference_k_maximum",
        ),
    ]
    rows: list[dict[str, object]] = []
    for volume in volumes:
        for delta_temperature in delta_temperatures:
            rows.append(
                {
                    "scenario_id": (f"tank_{volume:g}m3_delta_{delta_temperature:g}K"),
                    "tank_volume_m3": volume,
                    "operating_delta_temperature_k": delta_temperature,
                    "capacity_mwh_th": scaled_tank_storage_capacity_mwh(
                        reference_capacity_mwh=reference_capacity,
                        reference_volume_m3=reference_volume,
                        reference_delta_temperature_k=reference_delta,
                        volume_m3=volume,
                        delta_temperature_k=delta_temperature,
                    ),
                    "value_kind": "generic_sensitivity",
                    "source_ids": "dea_ttes_capacity_basis",
                    "limitation": (
                        "Linear sensible-heat scaling at the source catalogue's "
                        "medium and availability; not a Frontier storage design."
                    ),
                }
            )
    return rows


def main() -> None:
    technology = pd.read_csv(
        TECHNOLOGY_PARAMETERS,
        dtype=str,
        keep_default_na=False,
    )
    _write_csv(SOURCES_OUTPUT, SOURCE_FIELDS, _sources())
    _write_csv(PARAMETERS_OUTPUT, PARAMETER_FIELDS, _parameters(technology))
    _write_csv(RECEIVING_OUTPUT, RECEIVING_FIELDS, _receiving_classes())
    _write_csv(PATHWAY_OUTPUT, PATHWAY_FIELDS, _pathways())
    _write_csv(
        STORAGE_OUTPUT,
        STORAGE_FIELDS,
        _storage_sensitivity(technology),
    )
    print("Built Phase E environmental receiving-capacity model.")


if __name__ == "__main__":
    main()
