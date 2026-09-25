"""Generate the global-analysis handoff from canonical result files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "results" / "canonical"
OUTPUT = ROOT / "docs" / "GLOBAL_ANALYSIS_RESULTS.md"


def _allocation_row(row: pd.Series) -> str:
    return (
        f"- **{row['analysis'].title()}**: {row['source_country']} to "
        f"{row['sink_country']}, {row['distance_km']:.1f} km, "
        f"net benefit {row['net_benefit']:.1f} burden units per GJ."
    )


def _matched_row(row: pd.Series) -> str:
    candidate_note = ""
    if pd.notna(row["cooptimal_candidate_count"]):
        candidate_note = (
            f"; {int(row['cooptimal_candidate_count'])} co-optimal and "
            f"{int(row['near_optimal_candidate_count'])} within 1% of optimum"
        )
    return (
        f"- **{row['analysis'].title()}**: source "
        f"({row['source_latitude']:.2f}, {row['source_longitude']:.2f}) at "
        f"{row['source_time']}; sink "
        f"({row['sink_latitude']:.2f}, {row['sink_longitude']:.2f}) at "
        f"{row['sink_time']}; net benefit {row['net_benefit']:.1f} burden "
        f"units per GJ{candidate_note}."
    )


def main() -> None:
    allocations = pd.read_csv(CANONICAL / "one_unit_allocations.csv")
    robustness = pd.read_csv(CANONICAL / "source_hotspot_robustness.csv")
    safety = pd.read_csv(CANONICAL / "safety_ablation.csv")
    finite_q = pd.read_csv(CANONICAL / "finite_q_sensitivity.csv")
    redistribution = pd.read_csv(CANONICAL / "natural_redistribution_summary.csv")
    matched = pd.read_csv(CANONICAL / "matched_event_allocations.csv")
    selected = [
        allocations[
            (allocations["analysis"] == "spatial")
            & (allocations["scenario"] == "primary_land_noncryosphere")
            & (allocations["transport_penalty_per_gj_km"] == 0.0)
        ].iloc[0],
        allocations[
            (allocations["analysis"] == "temporal")
            & (allocations["maximum_lag_steps"] == 3)
            & (allocations["storage_penalty_per_gj_step"] == 0.0)
        ].iloc[0],
        allocations[
            (allocations["analysis"] == "joint")
            & (allocations["transport_penalty_per_gj_km"] == 0.0)
            & (allocations["storage_penalty_per_gj_step"] == 0.0)
        ].iloc[0],
    ]
    negative = allocations[~allocations["relocation_dominates"]]
    feasible_q = finite_q[finite_q["status"] == "feasible"]
    infeasible_q = finite_q[finite_q["status"] != "feasible"]
    cryosphere_horizons = redistribution.loc[
        redistribution["nearest_cell_cryosphere"], "horizon_hours"
    ].tolist()
    matched_temporal_fraction = matched.loc[
        matched["analysis"] == "temporal",
        "fraction_of_matched_spatial",
    ].iloc[0]
    temporal_lag_hours = int(
        (
            pd.Timestamp(
                matched.loc[matched["analysis"] == "temporal", "sink_time"].iloc[0]
            )
            - pd.Timestamp(
                matched.loc[
                    matched["analysis"] == "temporal",
                    "source_time",
                ].iloc[0]
            )
        )
        / pd.Timedelta(hours=1)
    )
    lines = [
        "# Global analysis results",
        "",
        "This file is generated from canonical result tables. Do not edit it manually.",
        "",
        "## Canonical search",
        "",
        f"The exact search produced {len(allocations)} scenarios; "
        f"{int(allocations['relocation_dominates'].sum())} favored relocation "
        "over the no-relocation baseline.",
        "",
        "The following are independently optimized annual maxima and must not "
        "be divided to infer storage retention:",
        "",
        *[_allocation_row(row) for row in selected],
        "",
        "## Matched-event comparison",
        "",
        *[_matched_row(row) for _, row in matched.iterrows()],
        "",
        (
            f"For this peak source cell-time, the {temporal_lag_hours}-hour "
            "same-location "
            f"candidate yielded "
            f"{matched_temporal_fraction:.1%} "
            "of the simultaneous spatial bound. This event-matched fraction "
            "must not be generalized to a technology without calibration."
        ),
        "",
        (
            f"The retained no-relocation-dominated set contains {len(negative)} "
            "scenario(s); these results are not clipped to zero."
        ),
        "",
        "## Parameter sweep and exclusion masks",
        "",
        (
            f"The limited one-year parameter sweep evaluated {len(robustness)} "
            "combinations and selected "
            f"{', '.join(sorted(robustness['source_country'].unique()))}. It "
            "does not test structural uncertainty across years, products, "
            "grids, or population surfaces."
        ),
        (
            f"Progressive mask ablation retained {len(safety)} scenarios. "
            f"{int(safety['sink_is_ocean'].sum())} selected representative "
            "ocean sinks before or without ocean exclusion; equal objective "
            "values make these sink locations non-unique."
        ),
        "",
        "## Finite energy and redistribution",
        "",
        (
            f"Finite-transfer analysis retained {len(feasible_q)} feasible "
            f"energy level(s), from {feasible_q['energy_gj'].min():g} to "
            f"{feasible_q['energy_gj'].max():g} GJ."
        ),
        (
            "Infeasible levels under the local temperature cap: "
            + (
                ", ".join(f"{value:g} GJ" for value in infeasible_q["energy_gj"])
                if not infeasible_q.empty
                else "none"
            )
            + "."
        ),
        (
            "The reduced-order wind trajectory entered cryosphere-classified "
            "cells at horizon(s): "
            + (
                ", ".join(f"{value:g} h" for value in cryosphere_horizons)
                if cryosphere_horizons
                else "none"
            )
            + "."
        ),
        "",
        "## Interpretation limits",
        "",
        "- The endpoint is population-weighted thermal-stress burden, not mortality.",
        "- Population absence is not evidence of environmental safety.",
        "- The wind trajectory is a reduced-order diagnostic, not a climate model.",
        (
            "- Surface radiation fields are descriptive context; they do not "
            "estimate causal radiative escape from added heat."
        ),
        "- Feasibility and engineering practicality are not established.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "make install",
        "make all",
        "```",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
