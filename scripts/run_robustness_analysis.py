"""Run thermal-metric and burden-parameter hotspot robustness analyses."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Point

from global_heat_allocation.metrics import (
    relative_humidity_percent,
    wet_bulb_stull,
)

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
COUNTRIES = (
    ROOT / "data" / "raw" / "natural_earth" / "5.1.2" / "ne_110m_admin_0_countries.zip"
)
OUTPUT = ROOT / "results" / "canonical" / "source_hotspot_robustness.csv"


def _country_name(
    countries: gpd.GeoDataFrame,
    latitude: float,
    longitude: float,
) -> str:
    wrapped_longitude = ((longitude + 180.0) % 360.0) - 180.0
    point = Point(wrapped_longitude, latitude)
    matches = countries[countries.geometry.covers(point)]
    if matches.empty:
        return "Unassigned land"
    return str(matches.iloc[0]["ADMIN"])


def _scenario(
    metric_name: str,
    metric: np.ndarray,
    metric_temperature_derivative: np.ndarray,
    threshold: float,
    curvature: float,
    mixing_height_m: float,
    reference_heat_capacity: np.ndarray,
    population: np.ndarray,
    land: np.ndarray,
    times: pd.DatetimeIndex,
    latitude: np.ndarray,
    longitude: np.ndarray,
    countries: gpd.GeoDataFrame,
) -> dict[str, object]:
    stress = np.maximum(metric - threshold, 0.0)
    heat_capacity = reference_heat_capacity * (mixing_height_m / 100.0)
    valid_derivative = np.isfinite(metric_temperature_derivative) & (
        metric_temperature_derivative > 0.0
    )
    marginal = np.where(
        np.isfinite(stress) & (stress > 0.0) & valid_derivative,
        population[np.newaxis, :, :]
        * curvature
        * stress ** (curvature - 1.0)
        * metric_temperature_derivative
        * 1.0e9
        / heat_capacity[np.newaxis, :, :],
        0.0,
    )
    eligible = (
        (land[np.newaxis, :, :] >= 0.5)
        & (population[np.newaxis, :, :] > 0.0)
        & (stress > 0.0)
        & valid_derivative
    )
    marginal[~eligible] = -np.inf
    flat_index = int(np.argmax(marginal))
    time_index, latitude_index, longitude_index = np.unravel_index(
        flat_index,
        marginal.shape,
    )
    value = float(marginal[time_index, latitude_index, longitude_index])
    if not np.isfinite(value):
        raise ValueError(
            f"No eligible source for {metric_name}, threshold={threshold}."
        )
    source_latitude = float(latitude[latitude_index])
    source_longitude = float(longitude[longitude_index])
    return {
        "metric": metric_name,
        "threshold": threshold,
        "curvature": curvature,
        "mixing_height_m": mixing_height_m,
        "source_time": times[time_index].isoformat(),
        "source_latitude": source_latitude,
        "source_longitude": source_longitude,
        "source_country": _country_name(
            countries,
            source_latitude,
            source_longitude,
        ),
        "source_population": population[latitude_index, longitude_index],
        "source_metric": metric[time_index, latitude_index, longitude_index],
        "source_stress_excess": stress[
            time_index,
            latitude_index,
            longitude_index,
        ],
        "maximum_marginal_burden_per_gj": value,
    }


def main() -> None:
    countries = gpd.read_file(f"zip://{COUNTRIES}")[["ADMIN", "geometry"]]
    with xr.open_dataset(CUBE) as dataset:
        times = pd.DatetimeIndex(dataset["time"].values)
        latitude = dataset["lat"].values.astype(np.float64)
        longitude = dataset["lon"].values.astype(np.float64)
        population = dataset["population"].values.astype(np.float64)
        land = dataset["land_fraction"].values.astype(np.float64)
        heat_capacity = dataset["atmospheric_heat_capacity_j_per_k"].values.astype(
            np.float64
        )
        metrics = {
            "humidex": dataset["humidex"].values.astype(np.float64),
            "air_temperature": dataset["air_temperature_c"].values.astype(np.float64),
            "wet_bulb_proxy": dataset["wet_bulb_temperature_c"].values.astype(
                np.float64
            ),
        }
        temperature = dataset["air_temperature_c"].values.astype(np.float64)
        humidity = dataset["specific_humidity"].values.astype(np.float64)
        pressure = dataset["surface_pressure"].values.astype(np.float64)
    perturbation_c = 0.01
    wet_bulb_derivative = (
        wet_bulb_stull(
            temperature + perturbation_c,
            relative_humidity_percent(
                temperature + perturbation_c,
                humidity,
                pressure,
            ),
        )
        - wet_bulb_stull(
            temperature - perturbation_c,
            relative_humidity_percent(
                temperature - perturbation_c,
                humidity,
                pressure,
            ),
        )
    ) / (2.0 * perturbation_c)
    derivatives = {
        "humidex": np.ones_like(temperature),
        "air_temperature": np.ones_like(temperature),
        "wet_bulb_proxy": wet_bulb_derivative,
    }

    rows: list[dict[str, object]] = []
    for threshold in (22.0, 26.0, 30.0):
        for curvature in (1.0, 2.0, 3.0):
            for mixing_height in (50.0, 100.0, 200.0):
                rows.append(
                    _scenario(
                        "humidex",
                        metrics["humidex"],
                        derivatives["humidex"],
                        threshold,
                        curvature,
                        mixing_height,
                        heat_capacity,
                        population,
                        land,
                        times,
                        latitude,
                        longitude,
                        countries,
                    )
                )
    for metric_name, thresholds in {
        "air_temperature": (24.0, 26.0, 28.0),
        "wet_bulb_proxy": (22.0, 24.0, 26.0),
    }.items():
        for threshold in thresholds:
            rows.append(
                _scenario(
                    metric_name,
                    metrics[metric_name],
                    derivatives[metric_name],
                    threshold,
                    2.0,
                    100.0,
                    heat_capacity,
                    population,
                    land,
                    times,
                    latitude,
                    longitude,
                    countries,
                )
            )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
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
    os.replace(temporary, OUTPUT)
    print(f"Wrote {len(rows)} hotspot robustness scenarios.")


if __name__ == "__main__":
    main()
