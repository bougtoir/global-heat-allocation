"""Build the reproducible numerical-value ledger used by the manuscript."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "provenance" / "manuscript_values.csv"

ONE_UNIT = ROOT / "results" / "canonical" / "one_unit_allocations.csv"
MATCHED = ROOT / "results" / "canonical" / "matched_event_allocations.csv"
FINITE_Q = ROOT / "results" / "canonical" / "finite_q_sensitivity.csv"
STRUCTURAL = ROOT / "results" / "tables" / "structural_replication.csv"
SOURCE_POTENTIAL = (
    ROOT / "results" / "techno_economic" / "frontier_source_potential.csv"
)
TECHNOLOGY = ROOT / "data" / "metadata" / "technology_parameters.csv"
DEMAND = ROOT / "data" / "metadata" / "ornl_demand_summary.csv"
DISPATCH = ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv"
DISPATCH_METADATA = ROOT / "results" / "dispatch" / "finite_dispatch_metadata.json"
ENERGY_EMISSIONS = ROOT / "results" / "techno_economic" / "energy_emissions.csv"
ECONOMICS = ROOT / "results" / "techno_economic" / "economics.csv"
SENSITIVITY = ROOT / "results" / "techno_economic" / "sensitivity.csv"
PARETO = ROOT / "results" / "techno_economic" / "practical_pareto_modes.csv"

FIELDS = [
    "value_id",
    "manuscript_section",
    "claim_label",
    "value",
    "unit",
    "display_value",
    "evidence_status",
    "eligibility",
    "source_artifact",
    "source_selector",
    "source_sha256",
    "derivation",
    "claim_limit",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _display(value: float, decimals: int, suffix: str = "") -> str:
    return f"{value:,.{decimals}f}{suffix}"


def _row(
    value_id: str,
    section: str,
    claim_label: str,
    value: float | int,
    unit: str,
    display_value: str,
    evidence_status: str,
    eligibility: str,
    source: Path,
    selector: str,
    derivation: str,
    claim_limit: str,
) -> dict[str, str]:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"Non-finite manuscript value: {value_id}")
    return {
        "value_id": value_id,
        "manuscript_section": section,
        "claim_label": claim_label,
        "value": f"{numeric:.15g}",
        "unit": unit,
        "display_value": display_value,
        "evidence_status": evidence_status,
        "eligibility": eligibility,
        "source_artifact": str(source.relative_to(ROOT)),
        "source_selector": selector,
        "source_sha256": _sha256(source),
        "derivation": derivation,
        "claim_limit": claim_limit,
    }


def _selected(frame: pd.DataFrame, column: str, value: str) -> pd.Series:
    matches = frame.loc[frame[column].eq(value)]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one row where {column}={value}; found {len(matches)}"
        )
    return matches.iloc[0]


def _metric(frame: pd.DataFrame, metric: str) -> float:
    return float(_selected(frame, "metric", metric)["value"])


def _parameter(frame: pd.DataFrame, parameter_id: str) -> float:
    value = _selected(frame, "parameter_id", parameter_id)["value"]
    if value == "":
        raise ValueError(f"Missing technology parameter: {parameter_id}")
    return float(value)


def _demand(frame: pd.DataFrame, record_id: str) -> float:
    return float(_selected(frame, "record_id", record_id)["value_mw_th"])


def _rows() -> list[dict[str, str]]:
    one_unit = pd.read_csv(ONE_UNIT)
    matched = pd.read_csv(MATCHED)
    finite_q = pd.read_csv(FINITE_Q)
    structural = pd.read_csv(STRUCTURAL)
    source = pd.read_csv(SOURCE_POTENTIAL)
    technology = pd.read_csv(TECHNOLOGY).fillna("")
    demand = pd.read_csv(DEMAND)
    dispatch = pd.read_csv(DISPATCH)
    energy = pd.read_csv(ENERGY_EMISSIONS)
    economics = pd.read_csv(ECONOMICS)
    sensitivity = pd.read_csv(SENSITIVITY)
    pareto = pd.read_csv(PARETO)
    with DISPATCH_METADATA.open(encoding="utf-8") as handle:
        dispatch_metadata = json.load(handle)

    spatial = _selected(matched, "analysis", "spatial")
    temporal = _selected(matched, "analysis", "temporal")
    time_step_hours = float(
        _selected(
            structural,
            "scenario_id",
            "ncep1_2023_worldpop_native_humidex",
        )["time_step_hours"]
    )
    feasible_q = finite_q.loc[finite_q["status"].eq("feasible")]
    infeasible_q = finite_q.loc[
        finite_q["status"].eq("infeasible_under_local_capacity")
    ]

    rows = [
        _row(
            "global_scenarios_evaluated",
            "Global theoretical screening",
            "Canonical one-unit scenarios evaluated",
            len(one_unit),
            "count",
            f"{len(one_unit):,}",
            "MODEL_OUTPUT",
            "THEORETICAL",
            ONE_UNIT,
            "row_count",
            "Number of canonical scenario rows.",
            "Scenario count is not a sample size for a population inference.",
        ),
        _row(
            "global_relocation_positive_scenarios",
            "Global theoretical screening",
            "Canonical scenarios with relocation-positive results",
            int(one_unit["relocation_dominates"].sum()),
            "count",
            f"{int(one_unit['relocation_dominates'].sum()):,}",
            "MODEL_OUTPUT",
            "THEORETICAL",
            ONE_UNIT,
            "sum(relocation_dominates == true)",
            "Count of canonical scenarios whose relocation solution dominates.",
            "Positive screening value is not practical environmental admissibility.",
        ),
        _row(
            "matched_spatial_value",
            "Global theoretical screening",
            "Matched-event spatial screening bound",
            spatial["net_benefit"],
            "burden_units_per_GJ",
            _display(float(spatial["net_benefit"]), 4),
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; net_benefit",
            "Direct selection of the matched-event spatial row.",
            "Marginal burden-space screening bound; not physical heat delivery.",
        ),
        _row(
            "matched_temporal_value",
            "Global theoretical screening",
            "Same-location temporal screening bound",
            temporal["net_benefit"],
            "burden_units_per_GJ",
            _display(float(temporal["net_benefit"]), 4),
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == temporal; net_benefit",
            "Direct selection of the matched-event temporal row.",
            "Marginal burden-space screening bound; not physical heat delivery.",
        ),
        _row(
            "matched_temporal_fraction",
            "Global theoretical screening",
            "Temporal value relative to matched spatial value",
            temporal["fraction_of_matched_spatial"],
            "fraction",
            _display(
                float(temporal["fraction_of_matched_spatial"]) * 100,
                4,
                "%",
            ),
            "DERIVED_MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == temporal; fraction_of_matched_spatial",
            "Temporal net benefit divided by spatial net benefit.",
            "Ratio compares burden-space bounds only.",
        ),
        _row(
            "matched_source_latitude",
            "Global theoretical screening",
            "Matched-event source latitude",
            spatial["source_latitude"],
            "degree_north",
            _display(float(spatial["source_latitude"]), 2),
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; source_latitude",
            "Direct selection of the matched spatial source cell.",
            "Grid-cell coordinate, not a site-selection recommendation.",
        ),
        _row(
            "matched_source_longitude",
            "Global theoretical screening",
            "Matched-event source longitude",
            spatial["source_longitude"],
            "degree_east",
            _display(float(spatial["source_longitude"]), 2),
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; source_longitude",
            "Direct selection of the matched spatial source cell.",
            "Grid-cell coordinate, not a site-selection recommendation.",
        ),
        _row(
            "matched_sink_latitude",
            "Global theoretical screening",
            "Matched-event zero-penalty sink latitude",
            spatial["sink_latitude"],
            "degree_north",
            _display(float(spatial["sink_latitude"]), 2),
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; sink_latitude",
            "Direct selection of the matched spatial sink cell.",
            "Mathematical sink is not automatically environmentally safe.",
        ),
        _row(
            "matched_sink_longitude",
            "Global theoretical screening",
            "Matched-event zero-penalty sink longitude",
            spatial["sink_longitude"],
            "degree_east",
            _display(float(spatial["sink_longitude"]), 2),
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; sink_longitude",
            "Direct selection of the matched spatial sink cell.",
            "Mathematical sink is not automatically environmentally safe.",
        ),
        _row(
            "matched_source_sink_distance",
            "Global theoretical screening",
            "Matched-event source-to-sink distance",
            spatial["distance_km"],
            "km",
            _display(float(spatial["distance_km"]), 1),
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; distance_km",
            "Great-circle distance between selected grid cells.",
            "Distance does not define an engineering transport route.",
        ),
        _row(
            "matched_temporal_lag",
            "Global theoretical screening",
            "Matched-event temporal lag",
            float(temporal["lag_steps"]) * time_step_hours,
            "hour",
            _display(float(temporal["lag_steps"]) * time_step_hours, 0),
            "DERIVED_MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == temporal; lag_steps",
            (
                "Matched temporal lag_steps multiplied by the canonical "
                "time_step_hours from structural_replication.csv."
            ),
            "Storage window in the screening model, not a case storage design.",
        ),
        _row(
            "matched_cooptimal_sink_count",
            "Global theoretical screening",
            "Exactly co-optimal matched-event sink candidates",
            spatial["cooptimal_candidate_count"],
            "count",
            f"{int(spatial['cooptimal_candidate_count']):,}",
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; cooptimal_candidate_count",
            "Direct count using the configured co-optimality tolerance.",
            "Non-uniqueness weakens any single-site interpretation.",
        ),
        _row(
            "matched_near_optimal_sink_count",
            "Global theoretical screening",
            "Matched-event sink candidates within 1% of the optimum",
            spatial["near_optimal_candidate_count"],
            "count",
            f"{int(spatial['near_optimal_candidate_count']):,}",
            "MODEL_OUTPUT",
            "THEORETICAL",
            MATCHED,
            "analysis == spatial; near_optimal_candidate_count",
            "Direct count using the configured within-1% criterion.",
            "Non-uniqueness weakens any single-site interpretation.",
        ),
        _row(
            "finite_q_largest_feasible",
            "Global theoretical screening",
            "Largest evaluated heat quantity feasible under the local cap",
            feasible_q["energy_gj"].max(),
            "GJ",
            _display(float(feasible_q["energy_gj"].max()), 0),
            "MODEL_OUTPUT",
            "THEORETICAL",
            FINITE_Q,
            "max(energy_gj where status == feasible)",
            "Maximum among evaluated finite-Q sensitivity rows.",
            "Local feasibility is not practical transport or disposal feasibility.",
        ),
        _row(
            "finite_q_smallest_infeasible",
            "Global theoretical screening",
            "Smallest evaluated heat quantity infeasible under the local cap",
            infeasible_q["energy_gj"].min(),
            "GJ",
            _display(float(infeasible_q["energy_gj"].min()), 0),
            "MODEL_OUTPUT",
            "THEORETICAL",
            FINITE_Q,
            "min(energy_gj where status == infeasible_under_local_capacity)",
            "Minimum among evaluated infeasible finite-Q sensitivity rows.",
            "Threshold is bracketed only by evaluated quantities.",
        ),
        _row(
            "structural_replication_scenario_count",
            "Structural replication",
            "Structural replication scenarios",
            len(structural),
            "count",
            f"{len(structural):,}",
            "MODEL_OUTPUT",
            "THEORETICAL",
            STRUCTURAL,
            "row_count",
            "Count of predefined structural-replication scenarios.",
            "A structured robustness panel, not an exhaustive uncertainty analysis.",
        ),
        _row(
            "structural_spatial_value_min",
            "Structural replication",
            "Minimum spatial screening value across structural replications",
            structural["spatial_zero_penalty_net_benefit_per_gj"].min(),
            "burden_units_per_GJ",
            _display(
                float(structural["spatial_zero_penalty_net_benefit_per_gj"].min()),
                4,
            ),
            "MODEL_OUTPUT",
            "THEORETICAL",
            STRUCTURAL,
            "min(spatial_zero_penalty_net_benefit_per_gj)",
            "Minimum across the predefined structural-replication panel.",
            "Values differ in proxy definition and are not practical benefits.",
        ),
        _row(
            "structural_spatial_value_max",
            "Structural replication",
            "Maximum spatial screening value across structural replications",
            structural["spatial_zero_penalty_net_benefit_per_gj"].max(),
            "burden_units_per_GJ",
            _display(
                float(structural["spatial_zero_penalty_net_benefit_per_gj"].max()),
                4,
            ),
            "MODEL_OUTPUT",
            "THEORETICAL",
            STRUCTURAL,
            "max(spatial_zero_penalty_net_benefit_per_gj)",
            "Maximum across the predefined structural-replication panel.",
            "Values differ in proxy definition and are not practical benefits.",
        ),
        _row(
            "frontier_expected_intervals",
            "Measured source case",
            "Expected Frontier 10-minute calendar intervals",
            _metric(source, "expected_10_minute_intervals"),
            "count",
            f"{int(_metric(source, 'expected_10_minute_intervals')):,}",
            "DERIVED_MEASURED_DATA",
            "MEASURED_SOURCE",
            SOURCE_POTENTIAL,
            "metric == expected_10_minute_intervals; value",
            "Non-leap calendar count at 10-minute resolution.",
            "Expected timestamps are not observed heat values.",
        ),
        _row(
            "frontier_valid_intervals",
            "Measured source case",
            "Valid measured Frontier source intervals",
            _metric(source, "valid_waste_heat_observations"),
            "count",
            f"{int(_metric(source, 'valid_waste_heat_observations')):,}",
            "DERIVED_MEASURED_DATA",
            "MEASURED_SOURCE",
            SOURCE_POTENTIAL,
            "metric == valid_waste_heat_observations; value",
            "Count of numeric measured waste-heat observations.",
            "Missing observations remain unavailable and are not imputed.",
        ),
        _row(
            "frontier_missing_intervals",
            "Measured source case",
            "Missing Frontier calendar intervals",
            _metric(source, "missing_timestamps"),
            "count",
            f"{int(_metric(source, 'missing_timestamps')):,}",
            "DERIVED_MEASURED_DATA",
            "MEASURED_SOURCE",
            SOURCE_POTENTIAL,
            "metric == missing_timestamps; value",
            "Expected calendar intervals minus unique workbook timestamps.",
            "Does not isolate facility downtime from acquisition downtime.",
        ),
        _row(
            "frontier_observed_heat",
            "Measured source case",
            "Observed valid Frontier waste heat",
            _metric(source, "observed_waste_heat_energy"),
            "MWh_th",
            _display(_metric(source, "observed_waste_heat_energy"), 1),
            "DERIVED_MEASURED_DATA",
            "MEASURED_SOURCE",
            SOURCE_POTENTIAL,
            "metric == observed_waste_heat_energy; value",
            "Sum of measured MW values multiplied by 1/6 hour.",
            "Observed valid intervals only; not a complete-year estimate.",
        ),
    ]

    technology_values = [
        ("frontier_waste_heat_min", "source_waste_heat_min_mw", "MW_th", 1),
        ("frontier_waste_heat_median", "source_waste_heat_median_mw", "MW_th", 4),
        ("frontier_waste_heat_mean", "source_waste_heat_mean_mw", "MW_th", 4),
        ("frontier_waste_heat_p95", "source_waste_heat_p95_mw", "MW_th", 4),
        ("frontier_waste_heat_max", "source_waste_heat_max_mw", "MW_th", 4),
        (
            "frontier_supply_temperature_median",
            "source_supply_temperature_median_c",
            "deg_C",
            1,
        ),
        (
            "frontier_return_temperature_median",
            "source_return_temperature_median_c",
            "deg_C",
            3,
        ),
        ("heat_pump_case_cop", "heat_pump_case_cop", "MW_heat_per_MW_electric", 2),
        (
            "heat_pump_case_total_capacity",
            "heat_pump_case_total_capacity_mw",
            "MW_th",
            1,
        ),
        (
            "heat_pump_case_sink_temperature",
            "heat_pump_case_sink_temperature_c",
            "deg_C",
            0,
        ),
        (
            "heat_pump_case_unit_equipment_cost",
            "heat_pump_case_unit_equipment_cost_usd",
            "USD_unspecified_year_per_unit",
            0,
        ),
    ]
    for value_id, parameter_id, unit, decimals in technology_values:
        value = _parameter(technology, parameter_id)
        measured = parameter_id.startswith("source_")
        rows.append(
            _row(
                value_id,
                "Measured source case" if measured else "Conditional technology case",
                parameter_id.replace("_", " "),
                value,
                unit,
                _display(value, decimals),
                "DERIVED_MEASURED_DATA" if measured else "CASE_SOURCE_VALUE",
                "MEASURED_SOURCE" if measured else "CONDITIONAL",
                TECHNOLOGY,
                f"parameter_id == {parameter_id}; value",
                _selected(technology, "parameter_id", parameter_id)["derivation"]
                or "Direct selection of the documented case-source value.",
                _selected(technology, "parameter_id", parameter_id)["limitation"]
                or (
                    "Source-side measured context only."
                    if measured
                    else (
                        "Technology value does not close missing demand, route, "
                        "or cost gates."
                    )
                ),
            )
        )

    for record_id, label in [
        ("case_a_average", "Case A average recorded space-heating demand"),
        ("case_a_maximum", "Case A maximum recorded space-heating demand"),
        ("case_b_selected_average", "Selected Case B average demand bound"),
        ("case_b_selected_maximum", "Selected Case B maximum demand bound"),
    ]:
        value = _demand(demand, record_id)
        rows.append(
            _row(
                f"ornl_{record_id}",
                "Receiving-demand evidence",
                label,
                value,
                "MW_th",
                _display(value, 2),
                "OFFICIAL_MEASURED_SUMMARY",
                "BOUND_ONLY",
                DEMAND,
                f"record_id == {record_id}; value_mw_th",
                _selected(demand, "record_id", record_id)["extraction_method"],
                _selected(demand, "record_id", record_id)["limitation"],
            )
        )

    for scenario_id in [
        "direct_lower_demand_bound",
        "direct_upper_demand_bound",
        "minimum_formula_storage_lower_demand",
        "minimum_formula_storage_upper_demand",
        "generic_storage_lower_demand",
        "generic_storage_upper_demand",
    ]:
        scenario = _selected(dispatch, "scenario_id", scenario_id)
        for column, suffix, unit, decimals, percent in [
            ("source_heat_used_mwh", "source_heat_used", "MWh_th", 1, False),
            (
                "useful_heat_delivered_mwh",
                "useful_heat_delivered",
                "MWh_th",
                1,
                False,
            ),
            (
                "residual_source_rejection_mwh",
                "residual_source_rejection",
                "MWh_th",
                1,
                False,
            ),
            ("demand_served_fraction", "demand_served", "fraction", 3, True),
        ]:
            value = float(scenario[column])
            display = (
                _display(value * 100, decimals, "%")
                if percent
                else _display(value, decimals)
            )
            rows.append(
                _row(
                    f"dispatch_{scenario_id}_{suffix}",
                    "Finite dispatch sensitivity",
                    f"{scenario_id} {suffix.replace('_', ' ')}",
                    value,
                    unit,
                    display,
                    "DEMAND_BOUND_MODEL_OUTPUT",
                    "CONDITIONAL",
                    DISPATCH,
                    f"scenario_id == {scenario_id}; {column}",
                    "Direct selection of the finite-dispatch scenario output.",
                    (
                        "Demand-bound sensitivity; not an observed or calibrated "
                        "annual Frontier-to-ORNL operation."
                    ),
                )
            )

    served = dispatch.loc[dispatch["demand_mwh"].gt(0), "demand_served_fraction"]
    timeseries_rows = int(dispatch_metadata["scenario_count"]) * int(
        dispatch_metadata["intervals_per_scenario"]
    )
    rows.extend(
        [
            _row(
                "dispatch_scenario_count",
                "Finite dispatch sensitivity",
                "Finite-dispatch scenarios",
                dispatch_metadata["scenario_count"],
                "count",
                f"{int(dispatch_metadata['scenario_count']):,}",
                "MODEL_CONFIGURATION",
                "CONDITIONAL",
                DISPATCH_METADATA,
                "scenario_count",
                "Direct metadata value.",
                (
                    "Includes a zero-demand rejection baseline and six "
                    "demand-bound sensitivities."
                ),
            ),
            _row(
                "dispatch_timeseries_rows",
                "Finite dispatch sensitivity",
                "Finite-dispatch timestep rows",
                timeseries_rows,
                "count",
                f"{timeseries_rows:,}",
                "DERIVED_MODEL_OUTPUT",
                "CONDITIONAL",
                DISPATCH_METADATA,
                "scenario_count * intervals_per_scenario",
                "Product of scenario count and calendar intervals per scenario.",
                "Row count is not independent empirical replication.",
            ),
            _row(
                "dispatch_served_fraction_min",
                "Finite dispatch sensitivity",
                "Minimum nonzero-demand served fraction",
                served.min(),
                "fraction",
                _display(float(served.min()) * 100, 4, "%"),
                "DEMAND_BOUND_MODEL_OUTPUT",
                "CONDITIONAL",
                DISPATCH,
                "min(demand_served_fraction where demand_mwh > 0)",
                "Minimum across the six nonzero-demand dispatch sensitivities.",
                (
                    "Demand is represented by bounds rather than a measured "
                    "synchronized trace."
                ),
            ),
            _row(
                "dispatch_served_fraction_max",
                "Finite dispatch sensitivity",
                "Maximum nonzero-demand served fraction",
                served.max(),
                "fraction",
                _display(float(served.max()) * 100, 4, "%"),
                "DEMAND_BOUND_MODEL_OUTPUT",
                "CONDITIONAL",
                DISPATCH,
                "max(demand_served_fraction where demand_mwh > 0)",
                "Maximum across the six nonzero-demand dispatch sensitivities.",
                (
                    "Demand is represented by bounds rather than a measured "
                    "synchronized trace."
                ),
            ),
            _row(
                "dispatch_residual_rejection_min",
                "Finite dispatch sensitivity",
                "Minimum residual source rejection",
                dispatch["residual_source_rejection_mwh"].min(),
                "MWh_th",
                _display(float(dispatch["residual_source_rejection_mwh"].min()), 1),
                "DEMAND_BOUND_MODEL_OUTPUT",
                "CONDITIONAL",
                DISPATCH,
                "min(residual_source_rejection_mwh)",
                "Minimum across all seven finite-dispatch scenarios.",
                "Does not establish an environmentally admissible rejection pathway.",
            ),
            _row(
                "dispatch_residual_rejection_max",
                "Finite dispatch sensitivity",
                "Maximum residual source rejection",
                dispatch["residual_source_rejection_mwh"].max(),
                "MWh_th",
                _display(float(dispatch["residual_source_rejection_mwh"].max()), 1),
                "DEMAND_BOUND_MODEL_OUTPUT",
                "CONDITIONAL",
                DISPATCH,
                "max(residual_source_rejection_mwh)",
                "Maximum across all seven finite-dispatch scenarios.",
                "Does not establish an environmentally admissible rejection pathway.",
            ),
            _row(
                "dispatch_max_balance_error",
                "Finite dispatch sensitivity",
                "Maximum absolute timestep thermal-balance error",
                dispatch["maximum_absolute_thermal_balance_error_mwh"].max(),
                "MWh_th",
                f"{float(dispatch['maximum_absolute_thermal_balance_error_mwh'].max()):.3e}",
                "NUMERICAL_DIAGNOSTIC",
                "VALIDATION",
                DISPATCH,
                "max(maximum_absolute_thermal_balance_error_mwh)",
                "Maximum absolute scenario-level timestep balance diagnostic.",
                "Numerical closure does not validate missing empirical inputs.",
            ),
        ]
    )

    case_c = _selected(energy, "scenario_id", "C_case_cop_SRTV_total_output")
    generic_economics = _selected(economics, "scenario_id", "C_generic_full_system")
    case_c_avoided_per_mwh = float(
        case_c["avoided_operational_co2e_kg"] / case_c["useful_heat_delivered_mwh"]
    )
    rows.extend(
        [
            _row(
                "case_c_avoided_operational_emissions",
                "Conditional techno-economics",
                "Normalized Case-C avoided operational emissions",
                case_c_avoided_per_mwh,
                "kg_CO2e_per_MWh_useful_heat",
                _display(case_c_avoided_per_mwh, 2),
                "GENERIC_COMPARATOR_OUTPUT",
                "CONDITIONAL",
                ENERGY_EMISSIONS,
                (
                    "scenario_id == C_case_cop_SRTV_total_output; "
                    "avoided_operational_co2e_kg / useful_heat_delivered_mwh"
                ),
                "Avoided operational emissions divided by useful heat delivered.",
                "Operational energy comparison only; not case-specific lifecycle CO2e.",
            ),
            _row(
                "generic_full_system_lcoh",
                "Conditional techno-economics",
                "Generic full-system comparator LCOH",
                generic_economics["lcoh_usd2025_per_mwh_th"],
                "USD_2025_per_MWh_th",
                _display(float(generic_economics["lcoh_usd2025_per_mwh_th"]), 2),
                "GENERIC_COMPARATOR_OUTPUT",
                "CONDITIONAL",
                ECONOMICS,
                "scenario_id == C_generic_full_system; lcoh_usd2025_per_mwh_th",
                "Direct selection of the generic full-system comparator.",
                "Not a Frontier-specific installed-cost estimate.",
            ),
            _row(
                "techno_economic_sensitivity_count",
                "Conditional techno-economics",
                "Techno-economic sensitivity cases",
                len(sensitivity),
                "count",
                f"{len(sensitivity):,}",
                "MODEL_OUTPUT",
                "CONDITIONAL",
                SENSITIVITY,
                "row_count",
                "Number of predefined sensitivity combinations.",
                "Sensitivity coverage does not replace case-specific calibration.",
            ),
            _row(
                "sensitivity_avoided_emissions_min",
                "Conditional techno-economics",
                "Minimum avoided operational emissions sensitivity",
                sensitivity["avoided_operational_co2e_kg_per_mwh"].min(),
                "kg_CO2e_per_MWh_useful_heat",
                _display(
                    float(sensitivity["avoided_operational_co2e_kg_per_mwh"].min()),
                    2,
                ),
                "GENERIC_SENSITIVITY_OUTPUT",
                "CONDITIONAL",
                SENSITIVITY,
                "min(avoided_operational_co2e_kg_per_mwh)",
                "Minimum across the predefined techno-economic sensitivity grid.",
                "Operational energy comparison only; not lifecycle CO2e.",
            ),
            _row(
                "sensitivity_avoided_emissions_max",
                "Conditional techno-economics",
                "Maximum avoided operational emissions sensitivity",
                sensitivity["avoided_operational_co2e_kg_per_mwh"].max(),
                "kg_CO2e_per_MWh_useful_heat",
                _display(
                    float(sensitivity["avoided_operational_co2e_kg_per_mwh"].max()),
                    2,
                ),
                "GENERIC_SENSITIVITY_OUTPUT",
                "CONDITIONAL",
                SENSITIVITY,
                "max(avoided_operational_co2e_kg_per_mwh)",
                "Maximum across the predefined techno-economic sensitivity grid.",
                "Operational energy comparison only; not lifecycle CO2e.",
            ),
            _row(
                "sensitivity_incremental_npc_min",
                "Conditional techno-economics",
                "Minimum incremental NPC sensitivity",
                sensitivity["incremental_npc_usd2025"].min(),
                "USD_2025",
                _display(float(sensitivity["incremental_npc_usd2025"].min()), 0),
                "GENERIC_SENSITIVITY_OUTPUT",
                "CONDITIONAL",
                SENSITIVITY,
                "min(incremental_npc_usd2025)",
                "Minimum across the predefined techno-economic sensitivity grid.",
                "Not a Frontier-specific project NPC.",
            ),
            _row(
                "sensitivity_incremental_npc_max",
                "Conditional techno-economics",
                "Maximum incremental NPC sensitivity",
                sensitivity["incremental_npc_usd2025"].max(),
                "USD_2025",
                _display(float(sensitivity["incremental_npc_usd2025"].max()), 0),
                "GENERIC_SENSITIVITY_OUTPUT",
                "CONDITIONAL",
                SENSITIVITY,
                "max(incremental_npc_usd2025)",
                "Maximum across the predefined techno-economic sensitivity grid.",
                "Not a Frontier-specific project NPC.",
            ),
            _row(
                "supported_practical_mode_count",
                "Practical endpoint",
                "Practical modes selected as supported",
                int(pareto["selected_practical_mode"].sum()),
                "count",
                f"{int(pareto['selected_practical_mode'].sum()):,}",
                "EVIDENCE_GATE_OUTPUT",
                "EXCLUDED",
                PARETO,
                "sum(selected_practical_mode == true)",
                "Count of practical modes passing the current evidence gates.",
                "Zero means no calibrated practical annual endpoint is supported.",
            ),
        ]
    )
    return rows


def _write(rows: list[dict[str, str]]) -> None:
    ids = [row["value_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate manuscript value IDs")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)


def main() -> None:
    rows = _rows()
    _write(rows)
    print(f"Wrote {len(rows)} manuscript values to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
