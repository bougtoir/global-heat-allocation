"""Dense reference solvers for small synthetic conserved-heat problems."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

MAX_DENSE_PAIR_ELEMENTS = 10_000_000


def _require_dense_pair_limit(source_count: int, sink_count: int) -> None:
    if source_count * sink_count > MAX_DENSE_PAIR_ELEMENTS:
        raise ValueError(
            "Dense reference solver exceeds its pair limit; use the "
            "memory-bounded global search."
        )


@dataclass(frozen=True)
class SpatialAllocation:
    """Best same-time relocation candidate."""

    source_index: int
    sink_index: int
    source_benefit: float
    sink_burden: float
    distance_km: float
    transport_penalty: float
    net_benefit: float


@dataclass(frozen=True)
class TemporalAllocation:
    """Best later-time release candidate at one location."""

    location_index: int
    source_time_index: int
    sink_time_index: int
    source_benefit: float
    sink_burden: float
    storage_penalty: float
    net_benefit: float


@dataclass(frozen=True)
class JointAllocation:
    """Best spatial and later-time relocation candidate."""

    source_location_index: int
    sink_location_index: int
    source_time_index: int
    sink_time_index: int
    source_benefit: float
    sink_burden: float
    distance_km: float
    transport_penalty: float
    storage_penalty: float
    net_benefit: float


def select_spatial_allocation(
    source_benefit: ArrayLike,
    sink_burden: ArrayLike,
    distance_km: ArrayLike,
    source_eligible: ArrayLike,
    sink_eligible: ArrayLike,
    maximum_distance_km: float,
    transport_cost_per_gj_km: float,
) -> SpatialAllocation:
    """Select the best nontrivial same-time source-sink pair."""
    source = np.asarray(source_benefit, dtype=np.float64)
    sink = np.asarray(sink_burden, dtype=np.float64)
    distance = np.asarray(distance_km, dtype=np.float64)
    source_allowed = np.asarray(source_eligible, dtype=bool)
    sink_allowed = np.asarray(sink_eligible, dtype=bool)
    if source.ndim != 1 or sink.ndim != 1:
        raise ValueError("Source benefit and sink burden must be vectors.")
    if source_allowed.shape != source.shape or sink_allowed.shape != sink.shape:
        raise ValueError("Eligibility vectors must match objective vectors.")
    if distance.shape != (source.size, sink.size):
        raise ValueError("Distance matrix does not match source and sink vectors.")
    if maximum_distance_km < 0.0 or transport_cost_per_gj_km < 0.0:
        raise ValueError("Distance and transport limits must be nonnegative.")
    _require_dense_pair_limit(source.size, sink.size)

    feasible = (
        source_allowed[:, np.newaxis]
        & sink_allowed[np.newaxis, :]
        & (distance <= maximum_distance_km)
    )
    if source.size == sink.size:
        feasible &= ~np.eye(source.size, dtype=bool)
    objective = (
        source[:, np.newaxis]
        - sink[np.newaxis, :]
        - transport_cost_per_gj_km * distance
    )
    objective[~feasible] = -np.inf
    if not np.isfinite(objective).any():
        raise ValueError("No feasible spatial relocation pair.")
    source_index, sink_index = np.unravel_index(
        int(np.nanargmax(objective)),
        objective.shape,
    )
    transport_penalty = transport_cost_per_gj_km * distance[source_index, sink_index]
    return SpatialAllocation(
        source_index=int(source_index),
        sink_index=int(sink_index),
        source_benefit=float(source[source_index]),
        sink_burden=float(sink[sink_index]),
        distance_km=float(distance[source_index, sink_index]),
        transport_penalty=float(transport_penalty),
        net_benefit=float(objective[source_index, sink_index]),
    )


def select_temporal_allocation(
    source_benefit: ArrayLike,
    sink_burden: ArrayLike,
    source_eligible: ArrayLike,
    sink_eligible: ArrayLike,
    maximum_lag_steps: int,
    storage_cost_per_gj_step: float,
) -> TemporalAllocation:
    """Select the best later release at the same location."""
    source = np.asarray(source_benefit, dtype=np.float64)
    sink = np.asarray(sink_burden, dtype=np.float64)
    source_allowed = np.asarray(source_eligible, dtype=bool)
    sink_allowed = np.asarray(sink_eligible, dtype=bool)
    if (
        source.shape != sink.shape
        or source.shape != source_allowed.shape
        or sink.shape != sink_allowed.shape
    ):
        raise ValueError("Temporal objective and eligibility arrays must match.")
    if source.ndim != 2:
        raise ValueError("Temporal arrays must have shape (time, location).")
    if maximum_lag_steps < 1:
        raise ValueError("Maximum lag must permit at least one later step.")
    if storage_cost_per_gj_step < 0.0:
        raise ValueError("Storage cost must be nonnegative.")

    best: TemporalAllocation | None = None
    time_steps, locations = source.shape
    for location in range(locations):
        for source_time in range(time_steps - 1):
            if not source_allowed[source_time, location]:
                continue
            final_time = min(time_steps, source_time + maximum_lag_steps + 1)
            for sink_time in range(source_time + 1, final_time):
                if not sink_allowed[sink_time, location]:
                    continue
                lag = sink_time - source_time
                storage_penalty = storage_cost_per_gj_step * lag
                net_benefit = (
                    source[source_time, location]
                    - sink[sink_time, location]
                    - storage_penalty
                )
                candidate = TemporalAllocation(
                    location_index=location,
                    source_time_index=source_time,
                    sink_time_index=sink_time,
                    source_benefit=float(source[source_time, location]),
                    sink_burden=float(sink[sink_time, location]),
                    storage_penalty=float(storage_penalty),
                    net_benefit=float(net_benefit),
                )
                if best is None or candidate.net_benefit > best.net_benefit:
                    best = candidate
    if best is None:
        raise ValueError("No feasible temporal relocation pair.")
    return best


def select_joint_allocation(
    source_benefit: ArrayLike,
    sink_burden: ArrayLike,
    distance_km: ArrayLike,
    source_eligible: ArrayLike,
    sink_eligible: ArrayLike,
    maximum_distance_km: float,
    maximum_lag_steps: int,
    transport_cost_per_gj_km: float,
    storage_cost_per_gj_step: float,
) -> JointAllocation:
    """Select the best same-time or later joint relocation."""
    source = np.asarray(source_benefit, dtype=np.float64)
    sink = np.asarray(sink_burden, dtype=np.float64)
    distance = np.asarray(distance_km, dtype=np.float64)
    source_allowed = np.asarray(source_eligible, dtype=bool)
    sink_allowed = np.asarray(sink_eligible, dtype=bool)
    if source.shape != sink.shape:
        raise ValueError("Source benefit and sink burden must have equal shape.")
    if source.shape != source_allowed.shape or sink.shape != sink_allowed.shape:
        raise ValueError("Eligibility arrays must match the objective arrays.")
    if source.ndim != 2:
        raise ValueError("Joint arrays must have shape (time, location).")
    time_steps, locations = source.shape
    if distance.shape != (locations, locations):
        raise ValueError("Distance matrix does not match location count.")
    if maximum_lag_steps < 0:
        raise ValueError("Maximum lag cannot be negative.")
    if (
        maximum_distance_km < 0.0
        or transport_cost_per_gj_km < 0.0
        or storage_cost_per_gj_step < 0.0
    ):
        raise ValueError("Distance, transport, and storage limits must be nonnegative.")
    _require_dense_pair_limit(locations, locations)

    spatial_feasible = distance <= maximum_distance_km
    best: JointAllocation | None = None
    for source_time in range(time_steps):
        final_time = min(time_steps, source_time + maximum_lag_steps + 1)
        for sink_time in range(source_time, final_time):
            feasible = (
                source_allowed[source_time, :, np.newaxis]
                & sink_allowed[sink_time, np.newaxis, :]
                & spatial_feasible
            )
            if source_time == sink_time:
                feasible &= ~np.eye(locations, dtype=bool)
            storage_penalty = storage_cost_per_gj_step * (sink_time - source_time)
            objective = (
                source[source_time, :, np.newaxis]
                - sink[sink_time, np.newaxis, :]
                - transport_cost_per_gj_km * distance
                - storage_penalty
            )
            objective[~feasible] = -np.inf
            if not np.isfinite(objective).any():
                continue
            source_location, sink_location = np.unravel_index(
                int(np.nanargmax(objective)),
                objective.shape,
            )
            net_benefit = float(objective[source_location, sink_location])
            if best is None or net_benefit > best.net_benefit:
                transport_penalty = (
                    transport_cost_per_gj_km * distance[source_location, sink_location]
                )
                best = JointAllocation(
                    source_location_index=int(source_location),
                    sink_location_index=int(sink_location),
                    source_time_index=source_time,
                    sink_time_index=sink_time,
                    source_benefit=float(source[source_time, source_location]),
                    sink_burden=float(sink[sink_time, sink_location]),
                    distance_km=float(distance[source_location, sink_location]),
                    transport_penalty=float(transport_penalty),
                    storage_penalty=float(storage_penalty),
                    net_benefit=net_benefit,
                )
    if best is None:
        raise ValueError("No feasible joint relocation pair.")
    return best
