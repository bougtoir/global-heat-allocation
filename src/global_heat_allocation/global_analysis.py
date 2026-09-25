"""Exact, memory-bounded searches over the global analysis cube."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.spatial import cKDTree

from global_heat_allocation.optimization import SpatialAllocation, TemporalAllocation
from global_heat_allocation.physics import EARTH_RADIUS_M, great_circle_distance_km

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class SpatialSearchResult:
    """Best allocations and branch-and-bound search diagnostics."""

    allocations: dict[float, SpatialAllocation]
    evaluated_sources: int


def unit_sphere_coordinates(
    latitude_degrees: ArrayLike,
    longitude_degrees: ArrayLike,
) -> FloatArray:
    """Convert geographic coordinates to three-dimensional unit vectors."""
    latitude = np.deg2rad(np.asarray(latitude_degrees, dtype=np.float64))
    longitude = np.deg2rad(np.asarray(longitude_degrees, dtype=np.float64))
    cosine_latitude = np.cos(latitude)
    return np.column_stack(
        (
            cosine_latitude * np.cos(longitude),
            cosine_latitude * np.sin(longitude),
            np.sin(latitude),
        )
    )


def exact_spatial_search(
    source_benefit: ArrayLike,
    sink_burden: ArrayLike,
    source_eligible: ArrayLike,
    sink_eligible: ArrayLike,
    latitude_degrees: ArrayLike,
    longitude_degrees: ArrayLike,
    tree: cKDTree,
    unit_coordinates: FloatArray,
    maximum_distance_km: float,
    transport_penalties: tuple[float, ...],
    exclude_same_location: bool = True,
) -> SpatialSearchResult:
    """Find exact best pairs without materializing a global distance matrix."""
    source = np.asarray(source_benefit, dtype=np.float64)
    sink = np.asarray(sink_burden, dtype=np.float64)
    source_allowed = np.asarray(source_eligible, dtype=bool)
    sink_allowed = np.asarray(sink_eligible, dtype=bool)
    latitude = np.asarray(latitude_degrees, dtype=np.float64)
    longitude = np.asarray(longitude_degrees, dtype=np.float64)
    if not (
        source.shape
        == sink.shape
        == source_allowed.shape
        == sink_allowed.shape
        == latitude.shape
        == longitude.shape
    ):
        raise ValueError("Spatial search vectors must have identical shapes.")
    if np.any(source < 0.0) or np.any(sink < 0.0):
        raise ValueError("Branch bounds require nonnegative burdens.")
    if maximum_distance_km < 0.0 or any(
        penalty < 0.0 for penalty in transport_penalties
    ):
        raise ValueError("Distance and transport penalties must be nonnegative.")

    angular_radius = min(maximum_distance_km * 1000.0 / EARTH_RADIUS_M, np.pi)
    chord_radius = 2.0 * np.sin(angular_radius / 2.0)
    ordered_sources = np.flatnonzero(source_allowed)
    ordered_sources = ordered_sources[
        np.argsort(source[ordered_sources], kind="stable")[::-1]
    ]
    best: dict[float, SpatialAllocation] = {}
    evaluated_sources = 0
    for source_index in ordered_sources:
        source_value = float(source[source_index])
        if len(best) == len(transport_penalties) and all(
            source_value <= best[penalty].net_benefit for penalty in transport_penalties
        ):
            break
        candidates = np.asarray(
            tree.query_ball_point(
                unit_coordinates[source_index],
                chord_radius,
            ),
            dtype=np.int64,
        )
        candidates = candidates[sink_allowed[candidates]]
        if exclude_same_location:
            candidates = candidates[candidates != source_index]
        if candidates.size == 0:
            continue
        evaluated_sources += 1
        distance = great_circle_distance_km(
            latitude[source_index],
            longitude[source_index],
            latitude[candidates],
            longitude[candidates],
        )
        within_limit = distance <= maximum_distance_km + 1.0e-9
        candidates = candidates[within_limit]
        distance = distance[within_limit]
        if candidates.size == 0:
            continue
        for penalty in transport_penalties:
            if penalty in best and source_value <= best[penalty].net_benefit:
                continue
            objective = source_value - sink[candidates] - penalty * distance
            position = int(np.argmax(objective))
            sink_index = int(candidates[position])
            candidate = SpatialAllocation(
                source_index=int(source_index),
                sink_index=sink_index,
                source_benefit=source_value,
                sink_burden=float(sink[sink_index]),
                distance_km=float(distance[position]),
                transport_penalty=float(penalty * distance[position]),
                net_benefit=float(objective[position]),
            )
            if penalty not in best or candidate.net_benefit > best[penalty].net_benefit:
                best[penalty] = candidate
    if len(best) != len(transport_penalties):
        raise ValueError("No feasible pair for one or more transport scenarios.")
    return SpatialSearchResult(best, evaluated_sources)


def exact_temporal_search(
    source_benefit: ArrayLike,
    sink_burden: ArrayLike,
    source_eligible: ArrayLike,
    sink_eligible: ArrayLike,
    maximum_lag_steps: int,
    storage_penalties: tuple[float, ...],
) -> dict[float, TemporalAllocation]:
    """Find exact same-location, later-time optima by vectorized lag scans."""
    source = np.asarray(source_benefit, dtype=np.float64)
    sink = np.asarray(sink_burden, dtype=np.float64)
    source_allowed = np.asarray(source_eligible, dtype=bool)
    sink_allowed = np.asarray(sink_eligible, dtype=bool)
    if not (source.shape == sink.shape == source_allowed.shape == sink_allowed.shape):
        raise ValueError("Temporal arrays must have identical shapes.")
    if source.ndim != 2:
        raise ValueError("Temporal arrays must have shape (time, location).")
    if maximum_lag_steps < 1 or any(penalty < 0.0 for penalty in storage_penalties):
        raise ValueError("Lag and storage penalties must be nonnegative.")

    best: dict[float, TemporalAllocation] = {}
    for lag in range(1, maximum_lag_steps + 1):
        feasible = source_allowed[:-lag] & sink_allowed[lag:]
        for penalty in storage_penalties:
            objective = source[:-lag] - sink[lag:] - penalty * lag
            objective = np.where(feasible, objective, -np.inf)
            flat_index = int(np.argmax(objective))
            value = float(objective.ravel()[flat_index])
            if not np.isfinite(value):
                continue
            source_time, location = np.unravel_index(
                flat_index,
                objective.shape,
            )
            candidate = TemporalAllocation(
                location_index=int(location),
                source_time_index=int(source_time),
                sink_time_index=int(source_time + lag),
                source_benefit=float(source[source_time, location]),
                sink_burden=float(sink[source_time + lag, location]),
                storage_penalty=float(penalty * lag),
                net_benefit=value,
            )
            if penalty not in best or candidate.net_benefit > best[penalty].net_benefit:
                best[penalty] = candidate
    if len(best) != len(storage_penalties):
        raise ValueError("No feasible pair for one or more storage scenarios.")
    return best
