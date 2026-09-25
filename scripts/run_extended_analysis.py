"""Run mask ablations, finite-Q checks, and seasonal/day-night summaries."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.spatial import cKDTree

from global_heat_allocation.config import load_config
from global_heat_allocation.global_analysis import (
    exact_spatial_search,
    unit_sphere_coordinates,
)
from global_heat_allocation.optimization import SpatialAllocation
from global_heat_allocation.physics import EARTH_RADIUS_M, great_circle_distance_km

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
CANONICAL = ROOT / "results" / "canonical"


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


def _global_best(
    source: np.ndarray,
    sink: np.ndarray,
    source_eligible: np.ndarray,
    sink_eligible: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    tree: cKDTree,
    unit_coordinates: np.ndarray,
    maximum_distance_km: float,
    penalty: float,
) -> tuple[SpatialAllocation, int]:
    time_upper_bound = np.where(source_eligible, source, -np.inf).max(axis=1)
    ordered_times = np.argsort(time_upper_bound, kind="stable")[::-1]
    best: SpatialAllocation | None = None
    best_time = -1
    for time_index in ordered_times:
        upper_bound = float(time_upper_bound[time_index])
        if best is not None and upper_bound <= best.net_benefit:
            break
        try:
            result = exact_spatial_search(
                source[time_index],
                sink[time_index],
                source_eligible[time_index],
                sink_eligible[time_index],
                latitude,
                longitude,
                tree,
                unit_coordinates,
                maximum_distance_km,
                (penalty,),
            )
        except ValueError:
            continue
        candidate = result.allocations[penalty]
        if best is None or candidate.net_benefit > best.net_benefit:
            best = candidate
            best_time = int(time_index)
    if best is None:
        raise ValueError("No feasible global allocation.")
    return best, best_time


def _safety_ablations(
    marginal: np.ndarray,
    source_eligible: np.ndarray,
    land: np.ndarray,
    cryosphere: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    times: pd.DatetimeIndex,
    tree: cKDTree,
    unit_coordinates: np.ndarray,
) -> None:
    all_cells = np.ones_like(source_eligible, dtype=bool)
    land_dynamic = np.broadcast_to(
        land[np.newaxis, :] >= 0.5,
        source_eligible.shape,
    )
    scenarios = [
        ("unrestricted_global", all_cells, 20_100.0),
        ("distance_only", all_cells, 5_000.0),
        ("plus_cryosphere_exclusion", ~cryosphere, 5_000.0),
        ("plus_ocean_exclusion", land_dynamic, 5_000.0),
        (
            "plus_ocean_and_cryosphere_exclusion",
            land_dynamic & ~cryosphere,
            5_000.0,
        ),
    ]
    rows: list[dict[str, object]] = []
    for scenario, sink_mask, maximum_distance in scenarios:
        allocation, time_index = _global_best(
            marginal,
            marginal,
            source_eligible,
            sink_mask,
            latitude,
            longitude,
            tree,
            unit_coordinates,
            maximum_distance,
            0.0,
        )
        sink_index = allocation.sink_index
        rows.append(
            {
                "scenario": scenario,
                "source_time": times[time_index].isoformat(),
                "source_latitude": latitude[allocation.source_index],
                "source_longitude": longitude[allocation.source_index],
                "sink_latitude": latitude[sink_index],
                "sink_longitude": longitude[sink_index],
                "sink_is_ocean": land[sink_index] < 0.5,
                "sink_is_cryosphere": cryosphere[time_index, sink_index],
                "distance_km": allocation.distance_km,
                "source_marginal_benefit": allocation.source_benefit,
                "sink_marginal_burden": allocation.sink_burden,
                "net_benefit": allocation.net_benefit,
            }
        )
    _write_rows(CANONICAL / "safety_ablation.csv", rows)


def _finite_q_sensitivity(
    signed_stress: np.ndarray,
    population: np.ndarray,
    heat_capacity: np.ndarray,
    land: np.ndarray,
    cryosphere: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    times: pd.DatetimeIndex,
    tree: cKDTree,
    unit_coordinates: np.ndarray,
    local_load_cap_gj: float,
    maximum_delta_temperature_k: float,
) -> None:
    capacity_gj = np.minimum(
        local_load_cap_gj,
        heat_capacity * maximum_delta_temperature_k / 1.0e9,
    )
    rows: list[dict[str, object]] = []
    for energy_gj in (1.0, 1_000.0, 100_000.0, 1_000_000.0):
        delta_temperature = energy_gj * 1.0e9 / heat_capacity
        delta = delta_temperature[np.newaxis, :]
        source_benefit = population[np.newaxis, :] * np.where(
            signed_stress <= 0.0,
            0.0,
            np.where(
                signed_stress > delta,
                2.0 * signed_stress * delta - delta**2,
                signed_stress**2,
            ),
        )
        sink_burden = population[np.newaxis, :] * np.where(
            signed_stress >= 0.0,
            2.0 * signed_stress * delta + delta**2,
            np.maximum(
                signed_stress + delta,
                0.0,
            )
            ** 2,
        )
        source_mask = (
            (land[np.newaxis, :] >= 0.5)
            & (population[np.newaxis, :] > 0.0)
            & (source_benefit > 0.0)
            & (capacity_gj[np.newaxis, :] >= energy_gj)
        )
        sink_mask = (
            (land[np.newaxis, :] >= 0.5)
            & ~cryosphere
            & (capacity_gj[np.newaxis, :] >= energy_gj)
        )
        penalty_per_gj_km = 1.0e-5 * energy_gj
        if not np.any(source_mask) or not np.any(sink_mask):
            rows.append(
                {
                    "energy_gj": energy_gj,
                    "status": "infeasible_under_local_capacity",
                    "source_time": "",
                    "source_latitude": "",
                    "source_longitude": "",
                    "sink_latitude": "",
                    "sink_longitude": "",
                    "distance_km": "",
                    "source_temperature_change_k": "",
                    "sink_temperature_change_k": "",
                    "source_benefit_total": "",
                    "sink_burden_total": "",
                    "transport_penalty_total": "",
                    "net_benefit_total": "",
                    "net_benefit_per_gj": "",
                }
            )
            continue
        allocation, time_index = _global_best(
            source_benefit,
            sink_burden,
            source_mask,
            sink_mask,
            latitude,
            longitude,
            tree,
            unit_coordinates,
            5_000.0,
            penalty_per_gj_km,
        )
        rows.append(
            {
                "energy_gj": energy_gj,
                "status": "feasible",
                "source_time": times[time_index].isoformat(),
                "source_latitude": latitude[allocation.source_index],
                "source_longitude": longitude[allocation.source_index],
                "sink_latitude": latitude[allocation.sink_index],
                "sink_longitude": longitude[allocation.sink_index],
                "distance_km": allocation.distance_km,
                "source_temperature_change_k": delta_temperature[
                    allocation.source_index
                ],
                "sink_temperature_change_k": delta_temperature[allocation.sink_index],
                "source_benefit_total": allocation.source_benefit,
                "sink_burden_total": allocation.sink_burden,
                "transport_penalty_total": allocation.transport_penalty,
                "net_benefit_total": allocation.net_benefit,
                "net_benefit_per_gj": allocation.net_benefit / energy_gj,
            }
        )
    _write_rows(CANONICAL / "finite_q_sensitivity.csv", rows)


def _seasonal_day_night_summary(
    marginal: np.ndarray,
    human_burden: np.ndarray,
    source_eligible: np.ndarray,
    times: pd.DatetimeIndex,
    longitude_axis: np.ndarray,
    longitude_cells: int,
) -> None:
    season_by_month = {
        12: "DJF",
        1: "DJF",
        2: "DJF",
        3: "MAM",
        4: "MAM",
        5: "MAM",
        6: "JJA",
        7: "JJA",
        8: "JJA",
        9: "SON",
        10: "SON",
        11: "SON",
    }
    grouped_values: dict[tuple[str, str], list[np.ndarray]] = {}
    grouped_burden: dict[tuple[str, str], float] = {}
    local_offset = longitude_axis / 15.0
    for time_index, timestamp in enumerate(times):
        local_hour = (timestamp.hour + local_offset) % 24.0
        period_by_longitude = np.where(
            (local_hour >= 6.0) & (local_hour < 18.0),
            "day",
            "night",
        )
        period = np.tile(period_by_longitude, marginal.shape[1] // longitude_cells)
        season = season_by_month[timestamp.month]
        for label in ("day", "night"):
            selection = source_eligible[time_index] & (period == label)
            if np.any(selection):
                grouped_values.setdefault((season, label), []).append(
                    marginal[time_index, selection]
                )
            burden_selection = period == label
            grouped_burden[(season, label)] = grouped_burden.get(
                (season, label),
                0.0,
            ) + float(human_burden[time_index, burden_selection].sum())
    rows: list[dict[str, object]] = []
    for key, chunks in sorted(grouped_values.items()):
        values = np.concatenate(chunks)
        rows.append(
            {
                "season": key[0],
                "local_period": key[1],
                "eligible_cell_times": values.size,
                "marginal_burden_median": np.median(values),
                "marginal_burden_p95": np.quantile(values, 0.95),
                "marginal_burden_p99": np.quantile(values, 0.99),
                "marginal_burden_max": np.max(values),
                "total_human_burden": grouped_burden[key],
            }
        )
    _write_rows(CANONICAL / "seasonal_day_night_summary.csv", rows)


def _matched_event_comparison(
    marginal: np.ndarray,
    source_eligible: np.ndarray,
    sink_eligible: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    times: pd.DatetimeIndex,
    tree: cKDTree,
    unit_coordinates: np.ndarray,
    maximum_distance_km: float,
    maximum_lag_steps: int,
) -> None:
    source_index_flat = int(np.argmax(np.where(source_eligible, marginal, -np.inf)))
    source_time_index, source_location_index = np.unravel_index(
        source_index_flat,
        marginal.shape,
    )
    source_value = float(marginal[source_time_index, source_location_index])
    fixed_source = np.zeros(marginal.shape[1], dtype=np.float64)
    fixed_source[source_location_index] = source_value
    fixed_source_mask = np.zeros(marginal.shape[1], dtype=bool)
    fixed_source_mask[source_location_index] = True
    rows: list[dict[str, object]] = []
    best_joint: dict[str, object] | None = None
    for lag in range(0, maximum_lag_steps + 1):
        sink_time_index = source_time_index + lag
        if sink_time_index >= marginal.shape[0]:
            continue
        result = exact_spatial_search(
            fixed_source,
            marginal[sink_time_index],
            fixed_source_mask,
            sink_eligible[sink_time_index],
            latitude,
            longitude,
            tree,
            unit_coordinates,
            maximum_distance_km,
            (0.0,),
            exclude_same_location=lag == 0,
        ).allocations[0.0]
        candidate = {
            "analysis": "joint",
            "source_time": times[source_time_index].isoformat(),
            "sink_time": times[sink_time_index].isoformat(),
            "lag_steps": lag,
            "source_latitude": latitude[source_location_index],
            "source_longitude": longitude[source_location_index],
            "sink_latitude": latitude[result.sink_index],
            "sink_longitude": longitude[result.sink_index],
            "distance_km": result.distance_km,
            "source_marginal_benefit": source_value,
            "sink_marginal_burden": result.sink_burden,
            "net_benefit": result.net_benefit,
            "fraction_of_matched_spatial": np.nan,
            "cooptimal_candidate_count": np.nan,
            "near_optimal_candidate_count": np.nan,
        }
        if best_joint is None or float(candidate["net_benefit"]) > float(
            best_joint["net_benefit"]
        ):
            best_joint = candidate
        if lag == 0:
            spatial = candidate | {"analysis": "spatial"}
            angular_radius = min(
                maximum_distance_km * 1000.0 / EARTH_RADIUS_M,
                np.pi,
            )
            candidates = np.asarray(
                tree.query_ball_point(
                    unit_coordinates[source_location_index],
                    2.0 * np.sin(angular_radius / 2.0),
                ),
                dtype=np.int64,
            )
            candidates = candidates[
                sink_eligible[sink_time_index, candidates]
                & (candidates != source_location_index)
            ]
            distances = great_circle_distance_km(
                latitude[source_location_index],
                longitude[source_location_index],
                latitude[candidates],
                longitude[candidates],
            )
            candidates = candidates[distances <= maximum_distance_km + 1.0e-9]
            objective = source_value - marginal[sink_time_index, candidates]
            optimum = float(np.max(objective))
            spatial["cooptimal_candidate_count"] = int(
                np.count_nonzero(
                    np.isclose(objective, optimum, rtol=1.0e-12, atol=1.0e-9)
                )
            )
            spatial["near_optimal_candidate_count"] = int(
                np.count_nonzero(objective >= optimum - 0.01 * abs(optimum))
            )
            rows.append(spatial)
    temporal_candidates = []
    for lag in range(1, maximum_lag_steps + 1):
        sink_time_index = source_time_index + lag
        if (
            sink_time_index < marginal.shape[0]
            and sink_eligible[sink_time_index, source_location_index]
        ):
            temporal_candidates.append(
                (
                    source_value - marginal[sink_time_index, source_location_index],
                    lag,
                    sink_time_index,
                )
            )
    if not temporal_candidates or best_joint is None:
        raise ValueError("No matched temporal or joint allocation.")
    temporal_value, temporal_lag, temporal_time = max(temporal_candidates)
    rows.append(
        {
            "analysis": "temporal",
            "source_time": times[source_time_index].isoformat(),
            "sink_time": times[temporal_time].isoformat(),
            "lag_steps": temporal_lag,
            "source_latitude": latitude[source_location_index],
            "source_longitude": longitude[source_location_index],
            "sink_latitude": latitude[source_location_index],
            "sink_longitude": longitude[source_location_index],
            "distance_km": 0.0,
            "source_marginal_benefit": source_value,
            "sink_marginal_burden": marginal[temporal_time, source_location_index],
            "net_benefit": temporal_value,
            "fraction_of_matched_spatial": (
                temporal_value / float(rows[0]["net_benefit"])
            ),
            "cooptimal_candidate_count": int(
                np.count_nonzero(
                    np.isclose(
                        [candidate[0] for candidate in temporal_candidates],
                        temporal_value,
                        rtol=1.0e-12,
                        atol=1.0e-9,
                    )
                )
            ),
            "near_optimal_candidate_count": int(
                np.count_nonzero(
                    np.asarray([candidate[0] for candidate in temporal_candidates])
                    >= temporal_value - 0.01 * abs(temporal_value)
                )
            ),
        }
    )
    best_joint["fraction_of_matched_spatial"] = float(
        best_joint["net_benefit"]
    ) / float(rows[0]["net_benefit"])
    rows.append(best_joint)
    rows[0]["fraction_of_matched_spatial"] = 1.0
    _write_rows(CANONICAL / "matched_event_allocations.csv", rows)


def main() -> None:
    config = load_config(ROOT / "config" / "model.yml")
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
        shape = (len(times), -1)
        marginal = (
            dataset["marginal_human_burden_per_gj"]
            .values.reshape(shape)
            .astype(np.float64)
        )
        human_burden = dataset["human_burden"].values.reshape(shape).astype(np.float64)
        source_eligible = dataset["source_eligible"].values.reshape(shape).astype(bool)
        cryosphere = dataset["cryosphere_mask"].values.reshape(shape).astype(bool)
        sink_eligible = (
            dataset["primary_sink_eligible"].values.reshape(shape).astype(bool)
        )
        signed_stress = dataset["humidex"].values.reshape(shape).astype(
            np.float64
        ) - float(config["stress"]["reference_temperature_c"])
        population = dataset["population"].values.ravel().astype(np.float64)
        land = dataset["land_fraction"].values.ravel().astype(np.float64)
        heat_capacity = (
            dataset["atmospheric_heat_capacity_j_per_k"]
            .values.ravel()
            .astype(np.float64)
        )

    unit_coordinates = unit_sphere_coordinates(latitude, longitude)
    tree = cKDTree(unit_coordinates)
    _safety_ablations(
        marginal,
        source_eligible,
        land,
        cryosphere,
        latitude,
        longitude,
        times,
        tree,
        unit_coordinates,
    )
    _finite_q_sensitivity(
        signed_stress,
        population,
        heat_capacity,
        land,
        cryosphere,
        latitude,
        longitude,
        times,
        tree,
        unit_coordinates,
        float(config["optimization"]["local_load_cap_gj"]),
        float(config["safety"]["maximum_local_delta_temperature_k"]),
    )
    _seasonal_day_night_summary(
        marginal,
        human_burden,
        source_eligible,
        times,
        longitude_axis,
        longitude_axis.size,
    )
    _matched_event_comparison(
        marginal,
        source_eligible,
        sink_eligible,
        latitude,
        longitude,
        times,
        tree,
        unit_coordinates,
        float(config["optimization"]["maximum_candidate_distance_km"]),
        max(
            int(hours) // int(config["grid"]["global_time_step_hours"])
            for hours in config["optimization"]["storage_windows_hours"]
        ),
    )
    print("Wrote safety, finite-Q, seasonal/day-night, and matched-event analyses.")


if __name__ == "__main__":
    main()
