# ruff: noqa: E501
"""Build burden-space and physical-energy global-to-real constraint waterfalls."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MATCHED = ROOT / "results" / "canonical" / "matched_event_allocations.csv"
DISPATCH = ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv"
PATHWAY = ROOT / "docs" / "PATHWAY_ELIGIBILITY.md"
OUTPUT = ROOT / "results" / "tables" / "global_to_real_constraint_waterfall.csv"
DOCUMENT = ROOT / "docs" / "CONSTRAINT_WATERFALL.md"

FIELDS = [
    "waterfall_id",
    "scenario_id",
    "stage_order",
    "stage_id",
    "stage_label",
    "value",
    "unit",
    "numeric_status",
    "evidence_status",
    "eligibility",
    "interpretation",
]

DISPATCH_SCENARIOS = (
    "direct_lower_demand_bound",
    "direct_upper_demand_bound",
    "minimum_formula_storage_lower_demand",
    "minimum_formula_storage_upper_demand",
    "generic_storage_lower_demand",
    "generic_storage_upper_demand",
)


def _write_csv(rows: list[dict[str, object]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)


def _row(
    waterfall_id: str,
    scenario_id: str,
    stage_order: int,
    stage_id: str,
    stage_label: str,
    value: float | None,
    unit: str,
    numeric_status: str,
    evidence_status: str,
    eligibility: str,
    interpretation: str,
) -> dict[str, object]:
    return {
        "waterfall_id": waterfall_id,
        "scenario_id": scenario_id,
        "stage_order": stage_order,
        "stage_id": stage_id,
        "stage_label": stage_label,
        "value": "" if value is None else value,
        "unit": unit,
        "numeric_status": numeric_status,
        "evidence_status": evidence_status,
        "eligibility": eligibility,
        "interpretation": interpretation,
    }


def _burden_rows(matched: pd.DataFrame) -> list[dict[str, object]]:
    spatial = matched.loc[matched["analysis"].eq("spatial")].iloc[0]
    temporal = matched.loc[matched["analysis"].eq("temporal")].iloc[0]
    rows = [
        _row(
            "burden_space",
            "canonical_matched_event",
            1,
            "global_theoretical_spatial_bound",
            "Global theoretical spatial screening bound",
            float(spatial["net_benefit"]),
            "burden_units_per_GJ",
            "quantified",
            "MODEL_OUTPUT",
            "THEORETICAL_ONLY",
            "One-unit marginal pair-search value; not a practical energy-delivery result.",
        ),
        _row(
            "burden_space",
            "canonical_matched_event",
            2,
            "same_location_temporal_bound",
            "Same-location temporal screening bound",
            float(temporal["net_benefit"]),
            "burden_units_per_GJ",
            "quantified",
            "MODEL_OUTPUT",
            "THEORETICAL_ONLY",
            "Temporal relocation retains heat at the source location and shifts release by 18 hours.",
        ),
    ]
    nonnumeric_stages = [
        (
            3,
            "environmental_admissibility",
            "Environmental admissibility",
            "External ambient relocation is excluded without receiving-capacity evidence; no burden-space derating is identifiable.",
        ),
        (
            4,
            "geographic_locality_constraint",
            "Geographic/locality constraint",
            "The global source-sink pair is not mapped to the local Frontier-to-ORNL thermal-energy case.",
        ),
        (
            5,
            "pathway_eligibility",
            "Pathway eligibility",
            "Only closed-loop reuse sensitivities remain conditional; no supported practical pathway converts burden units to delivered heat.",
        ),
        (
            6,
            "calibrated_technology_losses",
            "Calibrated technology losses",
            "Capture, auxiliary electricity, and network losses are not case-calibrated.",
        ),
        (
            7,
            "storage_capacity_demand",
            "Storage, capacity, and demand constraint",
            "Storage and demand are modeled only as physical-unit bounds and cannot be subtracted from burden units.",
        ),
        (
            8,
            "finite_dispatch",
            "Finite dispatch",
            "Finite dispatch produces MWh quantities rather than burden-unit values.",
        ),
        (
            9,
            "practical_supported_endpoint",
            "Practical supported endpoint",
            "No burden-space practical endpoint is identified under current public evidence.",
        ),
    ]
    for order, stage_id, label, interpretation in nonnumeric_stages:
        rows.append(
            _row(
                "burden_space",
                "canonical_matched_event",
                order,
                stage_id,
                label,
                None,
                "burden_units_per_GJ",
                "not_quantifiable_without_unit_bridge",
                "EVIDENCE_GAP",
                "EXCLUDED",
                interpretation,
            )
        )
    return rows


def _physical_rows(dispatch: pd.DataFrame) -> list[dict[str, object]]:
    selected = dispatch.loc[dispatch["scenario_id"].isin(DISPATCH_SCENARIOS)].copy()
    if len(selected) != len(DISPATCH_SCENARIOS):
        raise ValueError("Missing required finite-dispatch scenarios")

    rows: list[dict[str, object]] = []
    for scenario_id in DISPATCH_SCENARIOS:
        scenario = selected.loc[selected["scenario_id"].eq(scenario_id)].iloc[0]
        common = (
            "physical_energy",
            scenario_id,
            "MWh_th",
        )
        rows.extend(
            [
                _row(
                    common[0],
                    common[1],
                    1,
                    "measured_source_heat",
                    "Measured observed Frontier source heat",
                    float(scenario["source_heat_available_mwh"]),
                    common[2],
                    "quantified",
                    "FOUND_MEASURED",
                    "SUPPORTED_INPUT",
                    "Observed valid intervals only; unavailable intervals contribute no imputed heat.",
                ),
                _row(
                    common[0],
                    common[1],
                    2,
                    "environmental_admissibility",
                    "Closed-loop reuse environmental screen",
                    float(scenario["source_heat_available_mwh"]),
                    common[2],
                    "no_numeric_derating",
                    "BOUND_ONLY",
                    "CONDITIONAL",
                    "Closed-loop reuse avoids a new external thermal discharge, but residual rejection remains in the existing system.",
                ),
                _row(
                    common[0],
                    common[1],
                    3,
                    "geographic_pathway_eligibility",
                    "Geographic/pathway eligibility",
                    None,
                    common[2],
                    "not_case_calibrated",
                    "ROUTE_AND_HYDRAULICS_NOT_FOUND",
                    "CONDITIONAL",
                    "Local reuse is conceptually eligible, but no calibrated hot-water route or hydraulic design exists.",
                ),
                _row(
                    common[0],
                    common[1],
                    4,
                    "calibrated_technology_losses",
                    "Calibrated capture, network, and auxiliary losses",
                    None,
                    common[2],
                    "not_case_calibrated",
                    "CAPTURE_AND_BOP_BOUND_ONLY",
                    "CONDITIONAL",
                    "COP and unit capacity are bounded, but source capture, transport, and auxiliary electricity are not case-calibrated.",
                ),
                _row(
                    common[0],
                    common[1],
                    5,
                    "finite_dispatch_source_used",
                    "Conditional finite-dispatch source heat used",
                    float(scenario["source_heat_used_mwh"]),
                    common[2],
                    "quantified_sensitivity",
                    "DEMAND_BOUND_SCENARIO",
                    "CONDITIONAL",
                    "Source-side heat admitted by the stated capacity, demand-bound, and storage sensitivity.",
                ),
                _row(
                    common[0],
                    common[1],
                    6,
                    "finite_dispatch_useful_delivery",
                    "Conditional useful heat delivered",
                    float(scenario["useful_heat_delivered_mwh"]),
                    common[2],
                    "quantified_sensitivity",
                    "DEMAND_BOUND_SCENARIO",
                    "CONDITIONAL",
                    "Useful delivery includes heat-pump electricity and is not a subtraction from source-side heat.",
                ),
                _row(
                    common[0],
                    common[1],
                    7,
                    "finite_dispatch_residual_rejection",
                    "Conditional residual source rejection",
                    float(scenario["residual_source_rejection_mwh"]),
                    common[2],
                    "quantified_sensitivity",
                    "DEMAND_BOUND_SCENARIO",
                    "CONDITIONAL",
                    "Residual source heat remains assigned to the existing rejection baseline.",
                ),
                _row(
                    common[0],
                    common[1],
                    8,
                    "practical_supported_endpoint",
                    "Practical supported useful-heat endpoint",
                    None,
                    common[2],
                    "not_identified",
                    "RECEIVING_TRACE_AND_CALIBRATION_NOT_FOUND",
                    "EXCLUDED",
                    "No observed/calibrated annual Frontier-to-ORNL delivery endpoint is supported.",
                ),
            ]
        )
    return rows


def _write_document(rows: pd.DataFrame) -> None:
    burden = rows.loc[rows["waterfall_id"].eq("burden_space")]
    quantified_burden = burden.loc[burden["numeric_status"].eq("quantified")]
    dispatch = pd.read_csv(DISPATCH).set_index("scenario_id")

    burden_lines = "\n".join(
        f"| {int(row.stage_order)} | {row.stage_label} | {float(row.value):.4f} | {row.eligibility} |"
        for row in quantified_burden.itertuples()
    )
    physical_lines = "\n".join(
        (
            f"| `{scenario_id}` | "
            f"{float(dispatch.loc[scenario_id, 'source_heat_used_mwh']):,.1f} | "
            f"{float(dispatch.loc[scenario_id, 'useful_heat_delivered_mwh']):,.1f} | "
            f"{float(dispatch.loc[scenario_id, 'residual_source_rejection_mwh']):,.1f} | "
            f"{float(dispatch.loc[scenario_id, 'demand_served_fraction']):.3%} |"
        )
        for scenario_id in DISPATCH_SCENARIOS
    )
    text = f"""# Global-to-real constraint waterfall

Burden-space and physical-energy quantities are separated because the
population-weighted thermal-stress burden has no defensible conversion to MWh,
money, mortality, or environmental capacity.

## Burden-space screening waterfall

| Stage | Bound | Value (burden units/GJ) | Eligibility |
|---:|---|---:|---|
{burden_lines}
| 3-9 | Environmental, locality, pathway, technology, storage/demand, dispatch, and practical endpoint | not quantifiable | `EXCLUDED` |

The canonical temporal bound is
{float(quantified_burden.iloc[1]["value"]) / float(quantified_burden.iloc[0]["value"]):.4%}
of the matched-event spatial screening bound. No later practical stage is
assigned a burden-space number because doing so would require an unsupported
unit bridge.

## Physical-energy conditional branches

All rows below are demand-bound sensitivities, not observed/calibrated annual
operation.

| Scenario | Source heat used (MWh-th) | Useful heat delivered (MWh-th) | Residual rejection (MWh-th) | Demand served |
|---|---:|---:|---:|---:|
{physical_lines}

The observed source input is
{float(dispatch.iloc[0]["source_heat_available_mwh"]):,.1f} MWh-th over valid
2023 intervals. The useful-delivery column can exceed source heat used because
the heat pump adds electricity; it is not a source-energy subtraction.

## Supported endpoint

No practical annual Frontier-to-ORNL delivery endpoint is currently
`SUPPORTED`. The finite-dispatch branches remain `CONDITIONAL` because the
receiving-demand trace, route/hydraulics, source capture, balance-of-plant
electricity, and complete installed-cost evidence are unresolved. External
ambient and receiving-water disposal pathways remain `EXCLUDED`.

The machine-readable stage ledger is
`results/tables/global_to_real_constraint_waterfall.csv`.
"""
    DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
    temporary = DOCUMENT.with_name(f".{DOCUMENT.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, DOCUMENT)


def main() -> None:
    pathway = PATHWAY.read_text(encoding="utf-8")
    required = [
        "Observed or calibrated annual Frontier-to-ORNL useful-heat delivery | `EXCLUDED`",
        "Calibrated Frontier hot-water thermal-network transport | `EXCLUDED`",
        "New external receiving-water residual-heat discharge | `EXCLUDED`",
    ]
    if not all(item in pathway for item in required):
        raise ValueError("Pathway eligibility document lacks required exclusions")

    matched = pd.read_csv(MATCHED)
    dispatch = pd.read_csv(DISPATCH)
    rows = _burden_rows(matched) + _physical_rows(dispatch)
    _write_csv(rows)
    _write_document(pd.DataFrame(rows))
    print(f"Wrote {OUTPUT.relative_to(ROOT)} and {DOCUMENT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
