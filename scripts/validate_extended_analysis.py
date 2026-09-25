"""Validate extended canonical analyses and physical diagnostics."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "results" / "canonical"
DIAGNOSTICS = ROOT / "results" / "diagnostics"
OUTPUT = DIAGNOSTICS / "extended_analysis_validation.csv"


def _write_rows(rows: list[dict[str, object]]) -> None:
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["check", "passed", "value", "criterion"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)


def main() -> None:
    ablation = pd.read_csv(CANONICAL / "safety_ablation.csv")
    finite_q = pd.read_csv(CANONICAL / "finite_q_sensitivity.csv")
    seasonal = pd.read_csv(CANONICAL / "seasonal_day_night_summary.csv")
    matched = pd.read_csv(CANONICAL / "matched_event_allocations.csv")
    redistribution = pd.read_csv(CANONICAL / "natural_redistribution_summary.csv")
    trajectory = pd.read_csv(DIAGNOSTICS / "wind_trajectory_7d.csv")
    radiation = pd.read_csv(DIAGNOSTICS / "surface_radiation_context.csv")
    with xr.open_dataset(
        ROOT / "data" / "processed" / "analysis_cube_2023.nc"
    ) as dataset:
        heat_capacity = dataset["atmospheric_heat_capacity_j_per_k"].values.astype(
            np.float64
        )
        maximum_capacity = float(np.max(heat_capacity * 0.1 / 1.0e9))

    feasible = finite_q[finite_q["status"] == "feasible"].copy()
    net_identity_error = np.max(
        np.abs(
            feasible["net_benefit_total"]
            - (
                feasible["source_benefit_total"]
                - feasible["sink_burden_total"]
                - feasible["transport_penalty_total"]
            )
        )
    )
    checks = [
        {
            "check": "matched_event_common_source",
            "passed": bool(
                matched["source_time"].nunique() == 1
                and matched["source_latitude"].nunique() == 1
                and matched["source_longitude"].nunique() == 1
            ),
            "value": matched["source_time"].nunique(),
            "criterion": "all modes use one source cell-time",
        },
        {
            "check": "matched_event_objective_identity",
            "passed": bool(
                np.allclose(
                    matched["net_benefit"],
                    matched["source_marginal_benefit"]
                    - matched["sink_marginal_burden"],
                )
            ),
            "value": float(
                np.max(
                    np.abs(
                        matched["net_benefit"]
                        - (
                            matched["source_marginal_benefit"]
                            - matched["sink_marginal_burden"]
                        )
                    )
                )
            ),
            "criterion": "net benefit equals source minus sink burden",
        },
        {
            "check": "matched_event_candidate_multiplicity",
            "passed": bool(
                (
                    matched.loc[
                        matched["analysis"].isin(["spatial", "temporal"]),
                        [
                            "cooptimal_candidate_count",
                            "near_optimal_candidate_count",
                        ],
                    ]
                    >= 1
                )
                .all()
                .all()
            ),
            "value": int(
                matched.loc[
                    matched["analysis"] == "spatial",
                    "cooptimal_candidate_count",
                ].iloc[0]
            ),
            "criterion": "report at least one optimal and near-optimal candidate",
        },
        {
            "check": "safety_ablation_scenario_count",
            "passed": len(ablation) == 5,
            "value": len(ablation),
            "criterion": "five progressive safety scenarios",
        },
        {
            "check": "ocean_exclusion_removes_ocean_sink",
            "passed": not bool(
                ablation.loc[
                    ablation["scenario"].str.contains("ocean_exclusion"),
                    "sink_is_ocean",
                ].any()
            ),
            "value": int(
                ablation.loc[
                    ablation["scenario"].str.contains("ocean_exclusion"),
                    "sink_is_ocean",
                ].sum()
            ),
            "criterion": "zero ocean sinks after ocean exclusion",
        },
        {
            "check": "finite_q_objective_identity",
            "passed": net_identity_error < 1.0e-6,
            "value": net_identity_error,
            "criterion": "absolute error below 1e-6",
        },
        {
            "check": "finite_q_per_gj_nonincreasing",
            "passed": bool(np.all(np.diff(feasible["net_benefit_per_gj"]) <= 1.0e-9)),
            "value": ";".join(
                f"{value:.9g}" for value in feasible["net_benefit_per_gj"]
            ),
            "criterion": "convex burden prevents increasing per-GJ benefit",
        },
        {
            "check": "one_million_gj_capacity_infeasible",
            "passed": bool(
                (
                    finite_q.loc[
                        finite_q["energy_gj"] == 1_000_000.0,
                        "status",
                    ]
                    == "infeasible_under_local_capacity"
                ).all()
            ),
            "value": maximum_capacity,
            "criterion": "maximum 0.1-K cell capacity below 1e6 GJ",
        },
        {
            "check": "seasonal_local_period_coverage",
            "passed": len(seasonal) == 8,
            "value": len(seasonal),
            "criterion": "four seasons by day/night",
        },
        {
            "check": "seasonal_summary_nonnegative",
            "passed": bool(
                (
                    seasonal[
                        [
                            "marginal_burden_median",
                            "marginal_burden_p95",
                            "marginal_burden_p99",
                            "marginal_burden_max",
                            "total_human_burden",
                        ]
                    ]
                    >= 0.0
                )
                .all()
                .all()
            ),
            "value": float(seasonal["marginal_burden_max"].min()),
            "criterion": "all summary burdens nonnegative",
        },
        {
            "check": "redistribution_horizon_coverage",
            "passed": redistribution["horizon_hours"].tolist() == [24, 72, 168],
            "value": ";".join(str(value) for value in redistribution["horizon_hours"]),
            "criterion": "24, 72, and 168 hours",
        },
        {
            "check": "trajectory_energy_conservation",
            "passed": bool(np.allclose(trajectory["energy_retained_fraction"], 1.0)),
            "value": float(trajectory["energy_retained_fraction"].min()),
            "criterion": "unit energy retained in diagnostic trajectory",
        },
        {
            "check": "trajectory_flags_cryosphere_encounter",
            "passed": bool(trajectory["nearest_cell_cryosphere"].any()),
            "value": int(trajectory["nearest_cell_cryosphere"].sum()),
            "criterion": "diagnostic retains, rather than suppresses, encounter",
        },
        {
            "check": "radiation_is_explicitly_noncausal",
            "passed": bool(
                radiation["interpretation"]
                .str.contains("not TOA radiative escape or a causal response")
                .all()
            ),
            "value": len(radiation),
            "criterion": "every row carries noncausal interpretation",
        },
    ]
    _write_rows(checks)
    failed = [row["check"] for row in checks if not row["passed"]]
    if failed:
        raise AssertionError(f"Extended validation failed: {failed}")
    print(f"Validated {len(checks)} extended-analysis invariants.")


if __name__ == "__main__":
    main()
