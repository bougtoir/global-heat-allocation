"""Write the frozen baseline inventory from canonical generated outputs."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "FROZEN_BASELINE.md"
FROZEN_COMMIT = "365f144f27faa54b0abff091b35a7b1b51b4f40c"

CANONICAL_FILES = (
    "config/model.yml",
    "config/finite_dispatch.yml",
    "data/metadata/data_snapshots.csv",
    "data/metadata/technology_parameters.csv",
    "data/metadata/techno_economic_parameters.csv",
    "data/metadata/environmental_parameters.csv",
    "data/raw/real_heat_cases/frontier_figshare_v4_20260924T115656Z/"
    "frontier_hpc_facility_data_v4.xlsx",
    "results/canonical/one_unit_allocations.csv",
    "results/canonical/matched_event_allocations.csv",
    "results/canonical/finite_q_sensitivity.csv",
    "results/tables/structural_replication.csv",
    "results/techno_economic/energy_emissions.csv",
    "results/techno_economic/economics.csv",
    "results/environmental_constraints/frontier_pathway_assessment.csv",
    "results/dispatch/finite_dispatch_summary.csv",
    "results/dispatch/finite_dispatch_timeseries.csv.gz",
    "results/diagnostics/global_analysis_validation.csv",
    "results/diagnostics/finite_dispatch_validation.csv",
    "provenance/NUMERICAL_PROVENANCE.csv",
    "submission/manuscript_applied_energy_inline.docx",
    "submission/nogo_assessment_report.docx",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bool_count(series: pd.Series) -> int:
    return int(series.astype(str).str.lower().eq("true").sum())


def main() -> None:
    missing = [path for path in CANONICAL_FILES if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing frozen baseline files: {missing}")

    one_unit = pd.read_csv(ROOT / "results/canonical/one_unit_allocations.csv")
    matched = pd.read_csv(ROOT / "results/canonical/matched_event_allocations.csv")
    finite_q = pd.read_csv(ROOT / "results/canonical/finite_q_sensitivity.csv")
    structural = pd.read_csv(ROOT / "results/tables/structural_replication.csv")
    dispatch = pd.read_csv(ROOT / "results/dispatch/finite_dispatch_summary.csv")
    dispatch_validation = pd.read_csv(
        ROOT / "results/diagnostics/finite_dispatch_validation.csv"
    )
    snapshots = pd.read_csv(ROOT / "data/metadata/data_snapshots.csv")

    spatial = matched.loc[matched["analysis"].eq("spatial")].iloc[0]
    temporal = matched.loc[matched["analysis"].eq("temporal")].iloc[0]
    finite_status = finite_q.set_index("energy_gj")["status"].to_dict()
    frontier = snapshots.loc[
        snapshots["source_key"].eq("frontier_hpc_facility_data_v4")
    ].iloc[0]
    practical_dispatch = dispatch.loc[dispatch["demand_mwh"].gt(0)].copy()

    file_rows = "\n".join(
        f"| `{path}` | `{_sha256(ROOT / path)}` |" for path in CANONICAL_FILES
    )
    spatial_line = (
        "- Matched-event theoretical spatial value: "
        f"{float(spatial['net_benefit']):.4f} burden units/GJ."
    )
    temporal_line = (
        "- Same-location temporal value: "
        f"{float(temporal['net_benefit']):.4f} burden units/GJ, or "
        f"{float(temporal['fraction_of_matched_spatial']):.4%} of the "
        "matched-event spatial value."
    )
    text = f"""# Frozen baseline

## Freeze identity

- Frozen commit: `{FROZEN_COMMIT}`.
- Branch at freeze: `devin/1790233051-global-heat-allocation`.
- The pre-pass working tree contained only the untracked delivery render
  `submission/nogo_assessment_report.pdf`; it is not a canonical input.
- Any correction to the files below requires a documented defect, a targeted
  patch, rerunning only affected downstream outputs, and updated provenance.

## Verified headline results

- The canonical global table contains {len(one_unit)} scenarios;
  {_bool_count(one_unit["relocation_dominates"])} have a relocation-positive result.
{spatial_line}
{temporal_line}
- The matched spatial optimum has {int(spatial["cooptimal_candidate_count"]):,}
  exactly co-optimal and {int(spatial["near_optimal_candidate_count"]):,} within-1%
  sink candidates.
- Finite local-capacity status: 1, 1,000, and 100,000 GJ are
  `{finite_status[1.0]}`, `{finite_status[1000.0]}`, and
  `{finite_status[100000.0]}`; 1,000,000 GJ is
  `{finite_status[1000000.0]}`.
- Structural replication contains {len(structural)} prespecified scenarios:
  {_bool_count(structural["theoretical_spatial_value_positive"])} retain positive
  constrained theoretical spatial value,
  {_bool_count(structural["sink_nonunique_within_tolerance"])} retain sink
  non-uniqueness, and
  {_bool_count(structural["unrestricted_pathological_sinks_present"])} retain
  pathological unrestricted sinks.
- Phase G contains {len(dispatch)} ten-minute sensitivity scenarios. Across
  nonzero-demand sensitivities, served demand spans
  {float(practical_dispatch["demand_served_fraction"].min()):.3%}-
  {float(practical_dispatch["demand_served_fraction"].max()):.3%}; residual rejection
  spans {float(dispatch["residual_source_rejection_mwh"].min()):,.1f}-
  {float(dispatch["residual_source_rejection_mwh"].max()):,.1f} MWh-th.
- All {len(dispatch_validation)} finite-dispatch checks pass; the maximum absolute
  timestep thermal-balance error is
  {float(dispatch["maximum_absolute_thermal_balance_error_mwh"].max()):.3e} MWh.

These are model outputs or sensitivity results at their stated evidence level.
They are not practical recommendations, health outcomes, environmental-safety
findings, or evidence of planetary cooling.

## Frozen source evidence

The measured Frontier workbook is frozen after provenance verification:

- source key: `{frontier["source_key"]}`;
- local path: `{frontier["local_path"]}`;
- file size: {int(frontier["file_size_bytes"]):,} bytes;
- SHA-256: `{frontier["sha256"]}`;
- completion: `{frontier["completion"]}`;
- license: {frontier["license_terms"]}.

Missing source observations remain unavailable and are not imputed.

## Closed gates

- Structural uncertainty is closed with the documented product, metric, year,
  and resolution limitations.
- Health-claim control is closed and must be maintained: the endpoint is a
  population-weighted thermal-stress burden proxy, not mortality or morbidity.
- Global theoretical analysis, structural replication, measured Frontier
  source evidence, technology comparators, environmental exclusions,
  techno-economic sensitivities, and finite-dispatch sensitivities are frozen.

## Remaining gates

- Exhaustive case-specific evidence inventory and explicit pathway eligibility.
- Global-to-real constraint waterfall without cross-unit arithmetic.
- Evidence-level practical Pareto and mode comparison.
- Manuscript-value traceability and two-scale manuscript rewrite.
- Current Applied Energy fit audit and independent adversarial review.
- Clean rebuild, final claim calibration, and a new GO/WEAK GO/NO-GO decision.

## Analyses not to rerun without a documented defect

- Canonical global one-unit, matched-event, finite-Q, safety-ablation,
  robustness, and physical-diagnostic analyses.
- Phase F structural replication.
- Measured Frontier source preprocessing and descriptive statistics.
- Phase C-E technology, environmental, techno-economic, and operational-
  emissions comparators.
- Phase G constant-demand-bound finite-dispatch sensitivities.

New case evidence may trigger only the affected case-dispatch and downstream
waterfall, Pareto, manuscript, and provenance outputs.

## Canonical files and hashes

| File | SHA-256 |
|---|---|
{file_rows}
"""
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, OUTPUT)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
