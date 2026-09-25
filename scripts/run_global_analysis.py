"""Run exact global one-unit conserved-heat allocation analyses."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from scipy.spatial import cKDTree
from shapely.geometry import Point

from global_heat_allocation.config import load_config
from global_heat_allocation.global_analysis import (
    exact_spatial_search,
    exact_temporal_search,
    unit_sphere_coordinates,
)
from global_heat_allocation.optimization import SpatialAllocation
from global_heat_allocation.physics import great_circle_distance_km

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
COUNTRIES = (
    ROOT / "data" / "raw" / "natural_earth" / "5.1.2" / "ne_110m_admin_0_countries.zip"
)
OUTPUT = ROOT / "results" / "canonical" / "one_unit_allocations.csv"


def _country_name(
    countries: gpd.GeoDataFrame,
    latitude: float,
    longitude: float,
    land_fraction: float,
) -> str:
    if land_fraction < 0.5:
        return "Ocean"
    wrapped_longitude = ((longitude + 180.0) % 360.0) - 180.0
    point = Point(wrapped_longitude, latitude)
    matches = countries[countries.geometry.covers(point)]
    if matches.empty:
        return "Unassigned land"
    return str(matches.iloc[0]["ADMIN"])


def _local_night(timestamp: pd.Timestamp, longitude: float) -> bool:
    utc_hour = timestamp.hour + timestamp.minute / 60.0
    local_hour = (utc_hour + longitude / 15.0) % 24.0
    return local_hour < 6.0 or local_hour >= 18.0


def _flags(
    time_index: int,
    location_index: int,
    timestamp: pd.Timestamp,
    latitude: np.ndarray,
    longitude: np.ndarray,
    population: np.ndarray,
    land: np.ndarray,
    cryosphere: np.ndarray,
) -> str:
    flags: list[str] = []
    if land[location_index] < 0.5:
        flags.append("open_ocean")
    if cryosphere[time_index, location_index]:
        flags.append("cryosphere")
    if abs(latitude[location_index]) >= 60.0:
        flags.append("polar")
    if population[location_index] <= 0.0:
        flags.append("zero_population")
    if _local_night(timestamp, longitude[location_index]):
        flags.append("local_night")
    month = timestamp.month
    if (latitude[location_index] >= 0.0 and month in {12, 1, 2}) or (
        latitude[location_index] < 0.0 and month in {6, 7, 8}
    ):
        flags.append("local_winter")
    return ";".join(flags)


def _allocation_row(
    analysis: str,
    scenario: str,
    allocation: SpatialAllocation,
    source_time_index: int,
    sink_time_index: int,
    transport_coefficient: float,
    storage_coefficient: float,
    storage_penalty: float,
    maximum_distance_km: float,
    maximum_lag_steps: int,
    times: pd.DatetimeIndex,
    latitude: np.ndarray,
    longitude: np.ndarray,
    population: np.ndarray,
    land: np.ndarray,
    cryosphere: np.ndarray,
    countries: gpd.GeoDataFrame,
    evaluated_sources: int | str,
) -> dict[str, object]:
    source_timestamp = times[source_time_index]
    sink_timestamp = times[sink_time_index]
    source_index = allocation.source_index
    sink_index = allocation.sink_index
    return {
        "analysis": analysis,
        "scenario": scenario,
        "transport_penalty_per_gj_km": transport_coefficient,
        "storage_penalty_per_gj_step": storage_coefficient,
        "maximum_distance_km": maximum_distance_km,
        "maximum_lag_steps": maximum_lag_steps,
        "source_time": source_timestamp.isoformat(),
        "sink_time": sink_timestamp.isoformat(),
        "source_latitude": latitude[source_index],
        "source_longitude": longitude[source_index],
        "sink_latitude": latitude[sink_index],
        "sink_longitude": longitude[sink_index],
        "source_country": _country_name(
            countries,
            latitude[source_index],
            longitude[source_index],
            land[source_index],
        ),
        "sink_country": _country_name(
            countries,
            latitude[sink_index],
            longitude[sink_index],
            land[sink_index],
        ),
        "source_population": population[source_index],
        "sink_population": population[sink_index],
        "source_marginal_benefit": allocation.source_benefit,
        "sink_marginal_burden": allocation.sink_burden,
        "distance_km": allocation.distance_km,
        "transport_penalty": allocation.transport_penalty,
        "storage_penalty": storage_penalty,
        "net_benefit": allocation.net_benefit - storage_penalty,
        "relocation_dominates": allocation.net_benefit - storage_penalty > 0.0,
        "source_flags": _flags(
            source_time_index,
            source_index,
            source_timestamp,
            latitude,
            longitude,
            population,
            land,
            cryosphere,
        ),
        "sink_flags": _flags(
            sink_time_index,
            sink_index,
            sink_timestamp,
            latitude,
            longitude,
            population,
            land,
            cryosphere,
        ),
        "evaluated_sources": evaluated_sources,
    }


def _unconstrained_spatial(
    marginal: np.ndarray,
    source_eligible: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
) -> tuple[SpatialAllocation, int]:
    best: SpatialAllocation | None = None
    best_time = -1
    for time_index in range(marginal.shape[0]):
        source_candidates = np.flatnonzero(source_eligible[time_index])
        if source_candidates.size == 0:
            continue
        source_index = int(
            source_candidates[np.argmax(marginal[time_index, source_candidates])]
        )
        sink_values = marginal[time_index].copy()
        sink_values[source_index] = np.inf
        sink_index = int(np.argmin(sink_values))
        candidate = SpatialAllocation(
            source_index=source_index,
            sink_index=sink_index,
            source_benefit=float(marginal[time_index, source_index]),
            sink_burden=float(marginal[time_index, sink_index]),
            distance_km=float(
                great_circle_distance_km(
                    latitude[source_index],
                    longitude[source_index],
                    latitude[sink_index],
                    longitude[sink_index],
                )
            ),
            transport_penalty=0.0,
            net_benefit=float(
                marginal[time_index, source_index] - marginal[time_index, sink_index]
            ),
        )
        if best is None or candidate.net_benefit > best.net_benefit:
            best = candidate
            best_time = time_index
    if best is None:
        raise ValueError("No eligible unconstrained source.")
    return best, best_time


def main() -> None:
    config = load_config(ROOT / "config" / "model.yml")
    optimization = config["optimization"]
    transport_penalties = tuple(
        float(value) for value in optimization["transport_penalty_burden_per_gj_km"]
    )
    storage_penalties = tuple(
        float(value) for value in optimization["storage_penalty_burden_per_gj_step"]
    )
    maximum_distance = float(optimization["maximum_candidate_distance_km"])
    lag_windows = tuple(
        int(hours) // int(config["grid"]["global_time_step_hours"])
        for hours in optimization["storage_windows_hours"]
    )
    countries = gpd.read_file(f"zip://{COUNTRIES}")[["ADMIN", "geometry"]]

    with xr.open_dataset(CUBE) as dataset:
        times = pd.DatetimeIndex(dataset["time"].values)
        latitude_axis = dataset["lat"].values.astype(np.float64)
        longitude_axis = dataset["lon"].values.astype(np.float64)
        latitude_grid, longitude_grid = np.meshgrid(
            latitude_axis,
            longitude_axis,
            indexing="ij",
        )
        latitude = latitude_grid.ravel()
        longitude = longitude_grid.ravel()
        marginal = dataset["marginal_human_burden_per_gj"].values.reshape(
            len(times),
            -1,
        )
        source_eligible = (
            dataset["source_eligible"]
            .values.reshape(
                len(times),
                -1,
            )
            .astype(bool)
        )
        sink_eligible = (
            dataset["primary_sink_eligible"]
            .values.reshape(
                len(times),
                -1,
            )
            .astype(bool)
        )
        cryosphere = (
            dataset["cryosphere_mask"]
            .values.reshape(
                len(times),
                -1,
            )
            .astype(bool)
        )
        population = dataset["population"].values.ravel()
        land = dataset["land_fraction"].values.ravel()

    unit_coordinates = unit_sphere_coordinates(latitude, longitude)
    tree = cKDTree(unit_coordinates)
    rows: list[dict[str, object]] = []

    unconstrained, unconstrained_time = _unconstrained_spatial(
        marginal,
        source_eligible,
        latitude,
        longitude,
    )
    rows.append(
        _allocation_row(
            "spatial",
            "unconstrained_theoretical_upper_bound",
            unconstrained,
            unconstrained_time,
            unconstrained_time,
            0.0,
            0.0,
            0.0,
            float("inf"),
            0,
            times,
            latitude,
            longitude,
            population,
            land,
            cryosphere,
            countries,
            "all source times",
        )
    )

    time_upper_bound = np.where(source_eligible, marginal, -np.inf).max(axis=1)
    ordered_times = np.argsort(time_upper_bound, kind="stable")[::-1]
    spatial_best: dict[float, tuple[SpatialAllocation, int, int]] = {}
    for time_index in ordered_times:
        upper_bound = float(time_upper_bound[time_index])
        if len(spatial_best) == len(transport_penalties) and all(
            upper_bound <= spatial_best[penalty][0].net_benefit
            for penalty in transport_penalties
        ):
            break
        result = exact_spatial_search(
            marginal[time_index],
            marginal[time_index],
            source_eligible[time_index],
            sink_eligible[time_index],
            latitude,
            longitude,
            tree,
            unit_coordinates,
            maximum_distance,
            transport_penalties,
        )
        for penalty, allocation in result.allocations.items():
            if (
                penalty not in spatial_best
                or allocation.net_benefit > spatial_best[penalty][0].net_benefit
            ):
                spatial_best[penalty] = (
                    allocation,
                    int(time_index),
                    result.evaluated_sources,
                )
    for penalty, (allocation, time_index, evaluated) in spatial_best.items():
        rows.append(
            _allocation_row(
                "spatial",
                "primary_land_noncryosphere",
                allocation,
                time_index,
                time_index,
                penalty,
                0.0,
                0.0,
                maximum_distance,
                0,
                times,
                latitude,
                longitude,
                population,
                land,
                cryosphere,
                countries,
                evaluated,
            )
        )

    for maximum_lag in lag_windows:
        temporal = exact_temporal_search(
            marginal,
            marginal,
            source_eligible,
            sink_eligible,
            maximum_lag,
            storage_penalties,
        )
        for penalty, allocation in temporal.items():
            spatial_form = SpatialAllocation(
                source_index=allocation.location_index,
                sink_index=allocation.location_index,
                source_benefit=allocation.source_benefit,
                sink_burden=allocation.sink_burden,
                distance_km=0.0,
                transport_penalty=0.0,
                net_benefit=(allocation.source_benefit - allocation.sink_burden),
            )
            rows.append(
                _allocation_row(
                    "temporal",
                    "primary_same_location_storage",
                    spatial_form,
                    allocation.source_time_index,
                    allocation.sink_time_index,
                    0.0,
                    penalty,
                    allocation.storage_penalty,
                    0.0,
                    maximum_lag,
                    times,
                    latitude,
                    longitude,
                    population,
                    land,
                    cryosphere,
                    countries,
                    "vectorized exact",
                )
            )

    maximum_lag = max(lag_windows)
    joint_best: dict[
        tuple[float, float],
        tuple[SpatialAllocation, int, int, int],
    ] = {}
    time_lag_pairs = [
        (time_index, lag)
        for time_index in range(len(times))
        for lag in range(maximum_lag + 1)
        if time_index + lag < len(times)
    ]
    time_lag_pairs.sort(
        key=lambda pair: time_upper_bound[pair[0]],
        reverse=True,
    )
    for source_time, lag in time_lag_pairs:
        upper_bound = float(time_upper_bound[source_time])
        if len(joint_best) == len(transport_penalties) * len(storage_penalties) and all(
            upper_bound <= record[0].net_benefit - record[3]
            for record in joint_best.values()
        ):
            break
        needed_transport = tuple(
            transport
            for transport in transport_penalties
            if any(
                (transport, storage) not in joint_best
                or upper_bound - storage * lag
                > joint_best[(transport, storage)][0].net_benefit
                - joint_best[(transport, storage)][3]
                for storage in storage_penalties
            )
        )
        if not needed_transport:
            continue
        result = exact_spatial_search(
            marginal[source_time],
            marginal[source_time + lag],
            source_eligible[source_time],
            sink_eligible[source_time + lag],
            latitude,
            longitude,
            tree,
            unit_coordinates,
            maximum_distance,
            needed_transport,
            exclude_same_location=lag == 0,
        )
        for transport, allocation in result.allocations.items():
            for storage in storage_penalties:
                storage_penalty = storage * lag
                key = (transport, storage)
                net_benefit = allocation.net_benefit - storage_penalty
                if (
                    key not in joint_best
                    or net_benefit > joint_best[key][0].net_benefit - joint_best[key][3]
                ):
                    joint_best[key] = (
                        allocation,
                        source_time,
                        source_time + lag,
                        storage_penalty,
                    )
    for (transport, storage), (
        allocation,
        source_time,
        sink_time,
        storage_penalty,
    ) in joint_best.items():
        rows.append(
            _allocation_row(
                "joint",
                "primary_spatiotemporal",
                allocation,
                source_time,
                sink_time,
                transport,
                storage,
                storage_penalty,
                maximum_distance,
                maximum_lag,
                times,
                latitude,
                longitude,
                population,
                land,
                cryosphere,
                countries,
                "branch-and-bound exact",
            )
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(rows[0])
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)
    print(f"Wrote {len(rows)} exact one-unit allocation scenarios.")


if __name__ == "__main__":
    main()
