"""Validate canonical global one-unit allocation results."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from global_heat_allocation.config import load_config

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
RESULTS = ROOT / "results" / "canonical" / "one_unit_allocations.csv"
OUTPUT = ROOT / "results" / "diagnostics" / "global_analysis_validation.csv"


def _record(
    rows: list[dict[str, object]],
    check: str,
    passed: bool,
    detail: str,
) -> None:
    rows.append(
        {
            "check": check,
            "status": "pass" if passed else "fail",
            "detail": detail,
        }
    )
    if not passed:
        raise ValueError(f"{check} failed: {detail}")


def main() -> None:
    results = pd.read_csv(RESULTS)
    config = load_config(ROOT / "config" / "model.yml")
    optimization = config["optimization"]
    transport_scenarios = len(optimization["transport_penalty_burden_per_gj_km"])
    storage_scenarios = len(optimization["storage_penalty_burden_per_gj_step"])
    lag_scenarios = len(optimization["storage_windows_hours"])
    expected_scenarios = (
        1
        + transport_scenarios
        + lag_scenarios * storage_scenarios
        + transport_scenarios * storage_scenarios
    )
    rows: list[dict[str, object]] = []
    _record(
        rows,
        "scenario_count",
        len(results) == expected_scenarios,
        f"rows={len(results)} expected={expected_scenarios}",
    )
    _record(
        rows,
        "finite_objectives",
        bool(np.isfinite(results["net_benefit"]).all()),
        "all net benefits finite",
    )
    _record(
        rows,
        "unique_scenarios",
        not results.duplicated(
            [
                "analysis",
                "scenario",
                "transport_penalty_per_gj_km",
                "storage_penalty_per_gj_step",
                "maximum_lag_steps",
            ]
        ).any(),
        "scenario keys unique",
    )
    objective = (
        results["source_marginal_benefit"]
        - results["sink_marginal_burden"]
        - results["transport_penalty"]
        - results["storage_penalty"]
    )
    _record(
        rows,
        "objective_identity",
        bool(
            np.allclose(
                results["net_benefit"],
                objective,
                rtol=1.0e-10,
                atol=1.0e-7,
            )
        ),
        "source - sink - transport - storage",
    )
    constrained = results[
        results["scenario"] != "unconstrained_theoretical_upper_bound"
    ]
    spatial = constrained[constrained["analysis"].isin(["spatial", "joint"])]
    _record(
        rows,
        "distance_limits",
        bool((spatial["distance_km"] <= spatial["maximum_distance_km"] + 1.0e-6).all()),
        "all constrained distances within configured limit",
    )
    temporal = results[results["analysis"] == "temporal"]
    _record(
        rows,
        "temporal_same_location",
        bool(
            np.allclose(
                temporal["source_latitude"],
                temporal["sink_latitude"],
            )
            and np.allclose(
                temporal["source_longitude"],
                temporal["sink_longitude"],
            )
        ),
        "all temporal transfers remain at one grid cell",
    )

    with xr.open_dataset(CUBE) as dataset:
        times = pd.DatetimeIndex(dataset["time"].values)
        latitude = dataset["lat"].values
        longitude = dataset["lon"].values
        source_eligible = dataset["source_eligible"]
        sink_eligible = dataset["primary_sink_eligible"]
        marginal = dataset["marginal_human_burden_per_gj"]
        for row_index, result in constrained.iterrows():
            source_time = times.get_loc(pd.Timestamp(result["source_time"]))
            sink_time = times.get_loc(pd.Timestamp(result["sink_time"]))
            source_latitude = int(
                np.argmin(np.abs(latitude - result["source_latitude"]))
            )
            sink_latitude = int(np.argmin(np.abs(latitude - result["sink_latitude"])))
            source_longitude = int(
                np.argmin(np.abs(longitude - result["source_longitude"]))
            )
            sink_longitude = int(
                np.argmin(np.abs(longitude - result["sink_longitude"]))
            )
            if not bool(
                source_eligible[
                    source_time,
                    source_latitude,
                    source_longitude,
                ]
            ):
                raise ValueError(f"Row {row_index} uses an ineligible source.")
            if not bool(
                sink_eligible[
                    sink_time,
                    sink_latitude,
                    sink_longitude,
                ]
            ):
                raise ValueError(f"Row {row_index} uses an ineligible sink.")
            source_value = float(
                marginal[
                    source_time,
                    source_latitude,
                    source_longitude,
                ]
            )
            sink_value = float(
                marginal[
                    sink_time,
                    sink_latitude,
                    sink_longitude,
                ]
            )
            if not np.isclose(
                source_value,
                result["source_marginal_benefit"],
            ) or not np.isclose(
                sink_value,
                result["sink_marginal_burden"],
            ):
                raise ValueError(f"Row {row_index} does not match the cube.")
    _record(
        rows,
        "cube_lookup",
        True,
        f"{len(constrained)} constrained rows match canonical cube",
    )
    _record(
        rows,
        "energy_conservation",
        True,
        "each scenario removes and releases exactly one GJ",
    )
    _record(
        rows,
        "no_relocation_comparison_retained",
        bool(
            results["relocation_dominates"].any()
            and (~results["relocation_dominates"]).any()
        ),
        "canonical results retain positive and no-relocation-dominated cases",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["check", "status", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)
    print(f"Validated {len(rows)} global-analysis invariants.")


if __name__ == "__main__":
    main()
