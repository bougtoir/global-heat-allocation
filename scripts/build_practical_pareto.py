# ruff: noqa: E501
"""Build evidence-gated practical Pareto and mode-decision outputs."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv"
EVIDENCE = ROOT / "provenance" / "case_specific_evidence.csv"
OUTPUT = ROOT / "results" / "techno_economic" / "practical_pareto_modes.csv"
DOCUMENT = ROOT / "docs" / "PRACTICAL_MODE_DECISION.md"

FIELDS = [
    "scenario_id",
    "pathway_id",
    "mode_label",
    "demand_basis",
    "storage_basis",
    "eligibility",
    "evidence_gap_count",
    "evidence_gap_ids",
    "useful_heat_delivered_mwh",
    "demand_served_fraction",
    "residual_source_rejection_mwh",
    "heat_pump_electricity_mwh",
    "storage_capacity_mwh",
    "storage_loss_mwh",
    "pareto_efficient_within_demand_basis",
    "least_assumption_mode_within_demand_basis",
    "mode_decision",
    "selected_practical_mode",
]

CANDIDATES = {
    "direct_lower_demand_bound": ("C", "Local direct reuse"),
    "direct_upper_demand_bound": ("C", "Local direct reuse"),
    "minimum_formula_storage_lower_demand": (
        "B",
        "Formula-sized temporal storage and reuse",
    ),
    "minimum_formula_storage_upper_demand": (
        "B",
        "Formula-sized temporal storage and reuse",
    ),
    "generic_storage_lower_demand": (
        "B",
        "Generic-reference temporal storage and reuse",
    ),
    "generic_storage_upper_demand": (
        "B",
        "Generic-reference temporal storage and reuse",
    ),
}

COMMON_GAPS = (
    "ornl_receiving_hourly_demand_profile",
    "source_capture_efficiency",
    "balance_of_plant_auxiliary_electricity",
    "hydraulic_network_design_inputs",
    "cost_and_price_year",
)
STORAGE_GAPS = ("case_storage_design",)


def _gap_ids(evidence: pd.DataFrame, storage_basis: str) -> list[str]:
    ids = list(COMMON_GAPS)
    if storage_basis != "none":
        ids.extend(STORAGE_GAPS)
    statuses = evidence.set_index("evidence_id")["status"]
    resolved = {"FOUND_MEASURED", "FOUND_DERIVABLE"}
    return [evidence_id for evidence_id in ids if statuses[evidence_id] not in resolved]


def _dominates(left: pd.Series, right: pd.Series) -> bool:
    maximize = ("useful_heat_delivered_mwh", "demand_served_fraction")
    minimize = (
        "residual_source_rejection_mwh",
        "heat_pump_electricity_mwh",
        "storage_capacity_mwh",
        "storage_loss_mwh",
    )
    at_least_as_good = all(left[column] >= right[column] for column in maximize)
    at_least_as_good &= all(left[column] <= right[column] for column in minimize)
    strictly_better = any(left[column] > right[column] for column in maximize)
    strictly_better |= any(left[column] < right[column] for column in minimize)
    return at_least_as_good and strictly_better


def _pareto_flags(candidates: pd.DataFrame) -> pd.Series:
    flags: dict[str, bool] = {}
    for index, candidate in candidates.iterrows():
        dominated = any(
            _dominates(other, candidate)
            for other_index, other in candidates.iterrows()
            if other_index != index
        )
        flags[str(candidate["scenario_id"])] = not dominated
    return candidates["scenario_id"].map(flags).astype(bool)


def _build_rows(dispatch: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    candidates = dispatch.loc[dispatch["scenario_id"].isin(CANDIDATES)].copy()
    if len(candidates) != len(CANDIDATES):
        raise ValueError("Missing required practical Pareto scenarios")

    candidates["pathway_id"] = candidates["scenario_id"].map(
        lambda scenario_id: CANDIDATES[str(scenario_id)][0]
    )
    candidates["mode_label"] = candidates["scenario_id"].map(
        lambda scenario_id: CANDIDATES[str(scenario_id)][1]
    )
    candidates["eligibility"] = "CONDITIONAL"
    candidates["storage_loss_mwh"] = (
        candidates["storage_charge_loss_mwh"]
        + candidates["storage_discharge_loss_mwh"]
        + candidates["storage_standing_loss_mwh"]
    )
    candidates["evidence_gap_ids"] = candidates["storage_basis"].map(
        lambda storage_basis: ";".join(_gap_ids(evidence, str(storage_basis)))
    )
    candidates["evidence_gap_count"] = candidates["evidence_gap_ids"].map(
        lambda value: len(value.split(";"))
    )
    candidates["pareto_efficient_within_demand_basis"] = False
    candidates["least_assumption_mode_within_demand_basis"] = False

    for _, indices in candidates.groupby("demand_basis").groups.items():
        group = candidates.loc[indices]
        candidates.loc[indices, "pareto_efficient_within_demand_basis"] = _pareto_flags(
            group
        ).to_numpy()
        minimum_gaps = int(group["evidence_gap_count"].min())
        least_assumption = group["evidence_gap_count"].eq(minimum_gaps) & group[
            "storage_capacity_mwh"
        ].eq(
            group.loc[
                group["evidence_gap_count"].eq(minimum_gaps), "storage_capacity_mwh"
            ].min()
        )
        candidates.loc[indices, "least_assumption_mode_within_demand_basis"] = (
            least_assumption.to_numpy()
        )

    candidates["mode_decision"] = candidates.apply(
        lambda row: (
            "CONDITIONAL_LEAST_ASSUMPTION"
            if row["least_assumption_mode_within_demand_basis"]
            else "CONDITIONAL_SENSITIVITY"
        ),
        axis=1,
    )
    candidates["selected_practical_mode"] = False
    return candidates[FIELDS].sort_values(["demand_basis", "storage_capacity_mwh"])


def _write_csv(rows: pd.DataFrame) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows.to_dict(orient="records"))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)


def _write_document(rows: pd.DataFrame) -> None:
    table_lines = "\n".join(
        (
            f"| `{row.scenario_id}` | {row.pathway_id} | "
            f"{float(row.useful_heat_delivered_mwh):,.1f} | "
            f"{float(row.demand_served_fraction):.3%} | "
            f"{float(row.residual_source_rejection_mwh):,.1f} | "
            f"{float(row.heat_pump_electricity_mwh):,.1f} | "
            f"{float(row.storage_capacity_mwh):,.1f} | "
            f"{int(row.evidence_gap_count)} | "
            f"{'yes' if row.pareto_efficient_within_demand_basis else 'no'} | "
            f"`{row.mode_decision}` |"
        )
        for row in rows.itertuples()
    )
    text = f"""# Practical Pareto and mode decision

Only the evidence-eligible local direct-reuse (`C`) and temporal-storage (`B`)
branches are compared. Excluded transport, ambient-disposal, and
receiving-water pathways are not Pareto candidates.

## Objectives

Within each reported demand bound, the Pareto screen:

- maximizes useful heat delivered and demand served;
- minimizes residual source rejection, heat-pump electricity, storage
  capacity, and storage losses.

Case-specific cost and lifecycle CO2e are not objectives because the required
installed-cost and lifecycle inventories are absent.

| Scenario | Pathway | Useful delivery (MWh-th) | Demand served | Residual rejection (MWh-th) | HP electricity (MWh-e) | Storage (MWh-th) | Evidence gaps | Pareto | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
{table_lines}

## Decision

All six demand-bound candidates are Pareto-efficient because additional
delivery trades against electricity, storage capacity, and storage losses.
The direct-reuse branch is the least-assumption conditional mode within each
demand bound because it introduces no case-specific storage design.

No practical mode is selected as `SUPPORTED`. Direct reuse is retained as
`CONDITIONAL_LEAST_ASSUMPTION`; formula-sized and generic storage remain
`CONDITIONAL_SENSITIVITY`. A practical selection requires an auditable
receiving-demand trace, route/hydraulic design, source-capture calibration,
incremental auxiliary electricity, and complete installed-cost evidence.

The machine-readable output is
`results/techno_economic/practical_pareto_modes.csv`.
"""
    DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
    temporary = DOCUMENT.with_name(f".{DOCUMENT.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, DOCUMENT)


def main() -> None:
    dispatch = pd.read_csv(DISPATCH)
    evidence = pd.read_csv(EVIDENCE).fillna("")
    rows = _build_rows(dispatch, evidence)
    _write_csv(rows)
    _write_document(rows)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} and {DOCUMENT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
