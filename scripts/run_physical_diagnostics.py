"""Run reduced-order wind and descriptive surface-radiation diagnostics."""

from __future__ import annotations

import csv
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from global_heat_allocation.physics import great_circle_distance_km

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ncep_reanalysis_1" / "2023"
CUBE = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
ALLOCATIONS = ROOT / "results" / "canonical" / "one_unit_allocations.csv"
CANONICAL = ROOT / "results" / "canonical"
DIAGNOSTICS = ROOT / "results" / "diagnostics"
EARTH_RADIUS_M = 6_371_008.8


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _selected_allocation() -> pd.Series:
    rows = pd.read_csv(ALLOCATIONS)
    selection = rows[
        (rows["analysis"] == "spatial")
        & (rows["scenario"] == "primary_land_noncryosphere")
        & np.isclose(rows["transport_penalty_per_gj_km"], 1.0e-5)
    ]
    if len(selection) != 1:
        raise ValueError("Expected one canonical constrained spatial allocation.")
    return selection.iloc[0]


def _nearest_index(values: np.ndarray, target: float) -> int:
    return int(np.abs(values - target).argmin())


def _wind_trajectory(allocation: pd.Series) -> None:
    with (
        xr.open_dataset(RAW / "uwnd.10m.gauss.2023.nc") as eastward_dataset,
        xr.open_dataset(RAW / "vwnd.10m.gauss.2023.nc") as northward_dataset,
        xr.open_dataset(CUBE) as cube,
    ):
        times = pd.DatetimeIndex(eastward_dataset["time"].values)
        latitude_axis = eastward_dataset["lat"].values.astype(np.float64)
        longitude_axis = eastward_dataset["lon"].values.astype(np.float64)
        eastward = eastward_dataset["uwnd"]
        northward = northward_dataset["vwnd"]
        population = cube["population"].values.astype(np.float64)
        land = cube["land_fraction"].values.astype(np.float64)
        cryosphere = cube["cryosphere_mask"]

        start_time = pd.Timestamp(allocation["sink_time"])
        start_index = int(times.get_indexer([start_time])[0])
        if start_index < 0 or start_index + 28 >= len(times):
            raise ValueError(
                "Canonical sink time cannot support a seven-day trajectory."
            )

        latitude = float(allocation["sink_latitude"])
        longitude = float(allocation["sink_longitude"]) % 360.0
        source_latitude = float(allocation["source_latitude"])
        source_longitude = float(allocation["source_longitude"])
        rows: list[dict[str, object]] = []
        diffusion_coefficient_m2_s = 500.0
        step_seconds = 6.0 * 3600.0

        for step in range(29):
            time_index = start_index + step
            latitude_index = _nearest_index(latitude_axis, latitude)
            longitude_index = _nearest_index(longitude_axis, longitude)
            timestamp = times[time_index]
            u_wind = float(
                eastward.isel(
                    time=time_index,
                    lat=latitude_index,
                    lon=longitude_index,
                ).item()
            )
            v_wind = float(
                northward.isel(
                    time=time_index,
                    lat=latitude_index,
                    lon=longitude_index,
                ).item()
            )
            elapsed_seconds = step * step_seconds
            rows.append(
                {
                    "time": timestamp.isoformat(),
                    "elapsed_hours": step * 6,
                    "latitude": latitude,
                    "longitude": longitude,
                    "eastward_wind_m_s": u_wind,
                    "northward_wind_m_s": v_wind,
                    "distance_from_sink_km": float(
                        great_circle_distance_km(
                            float(allocation["sink_latitude"]),
                            float(allocation["sink_longitude"]),
                            latitude,
                            longitude,
                        )
                    ),
                    "distance_from_source_km": float(
                        great_circle_distance_km(
                            source_latitude,
                            source_longitude,
                            latitude,
                            longitude,
                        )
                    ),
                    "gaussian_dispersion_radius_km": math.sqrt(
                        4.0 * diffusion_coefficient_m2_s * elapsed_seconds
                    )
                    / 1_000.0,
                    "nearest_cell_population": population[
                        latitude_index,
                        longitude_index,
                    ],
                    "nearest_cell_land_fraction": land[
                        latitude_index,
                        longitude_index,
                    ],
                    "nearest_cell_cryosphere": bool(
                        cryosphere.isel(
                            time=time_index,
                            lat=latitude_index,
                            lon=longitude_index,
                        ).item()
                    ),
                    "energy_retained_fraction": 1.0,
                }
            )
            if step == 28:
                break
            latitude += math.degrees(v_wind * step_seconds / EARTH_RADIUS_M)
            longitude += math.degrees(
                u_wind
                * step_seconds
                / (EARTH_RADIUS_M * max(math.cos(math.radians(latitude)), 1.0e-6))
            )
            latitude = float(np.clip(latitude, -89.9, 89.9))
            longitude %= 360.0

    _write_rows(DIAGNOSTICS / "wind_trajectory_7d.csv", rows)
    trajectory = pd.DataFrame(rows).set_index("elapsed_hours")
    summary_rows: list[dict[str, object]] = []
    for horizon in (24, 72, 168):
        row = trajectory.loc[horizon]
        summary_rows.append(
            {
                "horizon_hours": horizon,
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "distance_from_sink_km": row["distance_from_sink_km"],
                "distance_from_source_km": row["distance_from_source_km"],
                "gaussian_dispersion_radius_km": row["gaussian_dispersion_radius_km"],
                "nearest_cell_population": row["nearest_cell_population"],
                "nearest_cell_cryosphere": row["nearest_cell_cryosphere"],
                "energy_retained_fraction": row["energy_retained_fraction"],
                "model_scope": (
                    "10m-wind Lagrangian trajectory with assumed Gaussian "
                    "dispersion; not a climate or heat-transport model"
                ),
            }
        )
    _write_rows(CANONICAL / "natural_redistribution_summary.csv", summary_rows)


def _surface_radiation_diagnostic(allocation: pd.Series) -> None:
    with xr.open_dataset(RAW / "ulwrf.sfc.gauss.2023.nc") as dataset:
        upward_longwave = dataset["ulwrf"]
        annual_mean = upward_longwave.mean("time").values.astype(np.float64)
        time = pd.Timestamp(allocation["sink_time"])
        event = upward_longwave.sel(time=time)
        latitude_axis = dataset["lat"].values.astype(np.float64)
        longitude_axis = dataset["lon"].values.astype(np.float64)
        rows: list[dict[str, object]] = []
        for role in ("source", "sink"):
            latitude = float(allocation[f"{role}_latitude"])
            longitude = float(allocation[f"{role}_longitude"]) % 360.0
            latitude_index = _nearest_index(latitude_axis, latitude)
            longitude_index = _nearest_index(longitude_axis, longitude)
            rows.append(
                {
                    "location_role": role,
                    "latitude": latitude_axis[latitude_index],
                    "longitude": longitude_axis[longitude_index],
                    "event_surface_upward_longwave_w_m2": float(
                        event.isel(
                            lat=latitude_index,
                            lon=longitude_index,
                        ).item()
                    ),
                    "annual_mean_surface_upward_longwave_w_m2": annual_mean[
                        latitude_index,
                        longitude_index,
                    ],
                    "global_annual_mean_percentile": float(
                        100.0
                        * np.mean(
                            annual_mean <= annual_mean[latitude_index, longitude_index]
                        )
                    ),
                    "interpretation": (
                        "descriptive surface flux only; not TOA radiative "
                        "escape or a causal response to added heat"
                    ),
                }
            )
    _write_rows(DIAGNOSTICS / "surface_radiation_context.csv", rows)


def main() -> None:
    allocation = _selected_allocation()
    _wind_trajectory(allocation)
    _surface_radiation_diagnostic(allocation)
    print("Wrote reduced-order wind and surface-radiation diagnostics.")


if __name__ == "__main__":
    main()
