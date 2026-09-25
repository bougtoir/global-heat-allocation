"""Validate the canonical processed analysis cube."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from global_heat_allocation.config import load_config
from global_heat_allocation.physics import EARTH_RADIUS_M
from global_heat_allocation.provenance import sha256_file

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
RAW_INVENTORY = ROOT / "data" / "metadata" / "data_inventory.csv"
VALIDATION = ROOT / "data" / "metadata" / "processed_validation.csv"
ARTIFACTS = ROOT / "provenance" / "processed_artifacts.csv"


def _check(
    rows: list[dict[str, object]],
    name: str,
    value: float,
    expected: float,
    tolerance: float,
) -> None:
    difference = abs(value - expected)
    status = "pass" if difference <= tolerance else "fail"
    rows.append(
        {
            "check": name,
            "value": value,
            "expected": expected,
            "absolute_tolerance": tolerance,
            "status": status,
        }
    )
    if status == "fail":
        raise ValueError(
            f"{name} failed: value={value}, expected={expected}, tolerance={tolerance}"
        )


def _write_csv(
    path: Path,
    rows: list[dict[str, object]],
    fieldnames: list[str],
) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    config = load_config(ROOT / "config" / "model.yml")
    raw_inventory = pd.read_csv(RAW_INVENTORY).set_index("source_key")
    raw_population_total = float(raw_inventory.loc["worldpop_population_2020", "sum"])
    rows: list[dict[str, object]] = []

    with xr.open_dataset(CUBE) as dataset:
        _check(rows, "time_steps", dataset.sizes["time"], 1460, 0)
        _check(rows, "latitude_cells", dataset.sizes["lat"], 94, 0)
        _check(rows, "longitude_cells", dataset.sizes["lon"], 192, 0)
        population_total = float(dataset["population"].sum())
        _check(
            rows,
            "population_conservation",
            population_total,
            raw_population_total,
            raw_population_total * 1.0e-10,
        )
        area_total = float(dataset["cell_area_m2"].sum())
        expected_area = 4.0 * np.pi * EARTH_RADIUS_M**2
        _check(
            rows,
            "global_surface_area",
            area_total,
            expected_area,
            expected_area * 1.0e-12,
        )
        relative_humidity_min = float(dataset["relative_humidity"].min())
        relative_humidity_max = float(dataset["relative_humidity"].max())
        _check(rows, "relative_humidity_min", relative_humidity_min, 0.0, 0.0)
        _check(rows, "relative_humidity_max", relative_humidity_max, 100.0, 0.0)
        maximum_delta = float(
            (1.0e9 / dataset["atmospheric_heat_capacity_j_per_k"]).max()
        )
        safety_limit = float(config["safety"]["maximum_local_delta_temperature_k"])
        if maximum_delta > safety_limit:
            raise ValueError(
                "One-GJ perturbation exceeds configured local temperature limit."
            )
        rows.append(
            {
                "check": "maximum_one_gj_temperature_change",
                "value": maximum_delta,
                "expected": safety_limit,
                "absolute_tolerance": "",
                "status": "pass",
            }
        )
        invalid_source = (dataset["source_eligible"] == 1) & (
            (dataset["land_fraction"] < 0.5)
            | (dataset["population"] <= 0.0)
            | (dataset["stress_excess"] <= 0.0)
        )
        _check(rows, "invalid_source_cells", int(invalid_source.sum()), 0, 0)
        invalid_sink = (dataset["primary_sink_eligible"] == 1) & (
            (dataset["land_fraction"] < 0.5) | (dataset["cryosphere_mask"] == 1)
        )
        _check(rows, "invalid_sink_cells", int(invalid_sink.sum()), 0, 0)
        negative_burden = int((dataset["human_burden"] < 0.0).sum())
        _check(rows, "negative_human_burden_cells", negative_burden, 0, 0)

    _write_csv(
        VALIDATION,
        rows,
        ["check", "value", "expected", "absolute_tolerance", "status"],
    )
    artifact_rows = [
        {
            "artifact": str(CUBE.relative_to(ROOT)),
            "file_size_bytes": CUBE.stat().st_size,
            "sha256": sha256_file(CUBE),
            "generation_command": "make preprocess",
            "validation_command": "python scripts/validate_processed.py",
        }
    ]
    _write_csv(
        ARTIFACTS,
        artifact_rows,
        [
            "artifact",
            "file_size_bytes",
            "sha256",
            "generation_command",
            "validation_command",
        ],
    )
    print(f"Validated {len(rows)} processed-data invariants.")


if __name__ == "__main__":
    main()
