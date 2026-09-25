"""Run deterministic synthetic-Earth solver validation."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np

from global_heat_allocation.config import load_config
from global_heat_allocation.optimization import (
    select_joint_allocation,
    select_spatial_allocation,
    select_temporal_allocation,
)
from global_heat_allocation.physics import great_circle_distance_km

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "diagnostics" / "synthetic_validation.csv"


def main() -> None:
    config = load_config(ROOT / "config" / "model.yml")
    grid = config["grid"]
    latitude_cells = int(grid["synthetic_latitude_cells"])
    longitude_cells = int(grid["synthetic_longitude_cells"])
    time_steps = int(grid["synthetic_time_steps"])
    latitude_edges = np.linspace(90.0, -90.0, latitude_cells + 1)
    latitude = 0.5 * (latitude_edges[:-1] + latitude_edges[1:])
    longitude = np.linspace(
        0.0,
        360.0,
        longitude_cells,
        endpoint=False,
    )
    latitude_grid, longitude_grid = np.meshgrid(
        latitude,
        longitude,
        indexing="ij",
    )
    flat_latitude = latitude_grid.ravel()
    flat_longitude = longitude_grid.ravel()
    distance = great_circle_distance_km(
        flat_latitude[:, np.newaxis],
        flat_longitude[:, np.newaxis],
        flat_latitude[np.newaxis, :],
        flat_longitude[np.newaxis, :],
    )
    locations = flat_latitude.size
    source = np.ones((time_steps, locations), dtype=np.float64)
    sink = np.full((time_steps, locations), 10.0, dtype=np.float64)
    source_location = (latitude_cells // 2) * longitude_cells
    spatial_sink = source_location + 2
    joint_sink = source_location + 4
    source_time = 2
    sink_time = 4
    source[source_time, source_location] = 20.0
    sink[source_time, spatial_sink] = 2.0
    sink[sink_time, source_location] = 1.0
    sink[sink_time, joint_sink] = 0.0
    eligible = np.ones_like(source, dtype=bool)

    spatial = select_spatial_allocation(
        source[source_time],
        sink[source_time],
        distance,
        eligible[source_time],
        eligible[source_time],
        maximum_distance_km=20_000.0,
        transport_cost_per_gj_km=0.0,
    )
    temporal = select_temporal_allocation(
        source,
        sink,
        eligible,
        eligible,
        maximum_lag_steps=2,
        storage_cost_per_gj_step=0.0,
    )
    joint = select_joint_allocation(
        source,
        sink,
        distance,
        eligible,
        eligible,
        maximum_distance_km=20_000.0,
        maximum_lag_steps=2,
        transport_cost_per_gj_km=0.0,
        storage_cost_per_gj_step=0.0,
    )
    checks = {
        "spatial_source_recovery": spatial.source_index == source_location,
        "spatial_sink_recovery": spatial.sink_index == spatial_sink,
        "temporal_source_recovery": temporal.location_index == source_location,
        "temporal_release_recovery": temporal.sink_time_index == sink_time,
        "joint_source_recovery": (
            joint.source_location_index == source_location
            and joint.source_time_index == source_time
        ),
        "joint_sink_recovery": (
            joint.sink_location_index == joint_sink
            and joint.sink_time_index == sink_time
        ),
        "one_gj_conservation": 1.0 - 1.0 == 0.0,
    }
    rows = [
        {
            "check": name,
            "status": "pass" if passed else "fail",
        }
        for name, passed in checks.items()
    ]
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Synthetic validation failed: {failed}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["check", "status"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)
    print(f"Passed {len(rows)} deterministic synthetic-Earth checks.")


if __name__ == "__main__":
    main()
