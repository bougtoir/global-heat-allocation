"""Structural replication helpers for global marginal heat allocation."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from global_heat_allocation.physics import great_circle_distance_km

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


def coarsen_sum(values: ArrayLike, factor: int) -> FloatArray:
    """Aggregate the final two dimensions by summation."""
    array = np.asarray(values, dtype=np.float64)
    if factor < 1:
        raise ValueError("Coarsening factor must be positive.")
    if factor == 1:
        return array.copy()
    latitude_count, longitude_count = array.shape[-2:]
    if latitude_count % factor or longitude_count % factor:
        raise ValueError("Grid dimensions must be divisible by the coarsening factor.")
    reshaped = array.reshape(
        *array.shape[:-2],
        latitude_count // factor,
        factor,
        longitude_count // factor,
        factor,
    )
    return reshaped.sum(axis=(-3, -1))


def coarsen_area_weighted(
    values: ArrayLike,
    area_m2: ArrayLike,
    factor: int,
) -> FloatArray:
    """Aggregate the final two dimensions using cell area weights."""
    array = np.asarray(values, dtype=np.float64)
    area = np.asarray(area_m2, dtype=np.float64)
    if array.shape[-2:] != area.shape:
        raise ValueError("Area weights must match the final two value dimensions.")
    numerator = coarsen_sum(array * area, factor)
    denominator = coarsen_sum(area, factor)
    return numerator / denominator


def coarsen_any(values: ArrayLike, factor: int) -> BoolArray:
    """Aggregate a Boolean field conservatively using any-cell membership."""
    array = np.asarray(values, dtype=bool)
    if factor < 1:
        raise ValueError("Coarsening factor must be positive.")
    if factor == 1:
        return array.copy()
    latitude_count, longitude_count = array.shape[-2:]
    if latitude_count % factor or longitude_count % factor:
        raise ValueError("Grid dimensions must be divisible by the coarsening factor.")
    reshaped = array.reshape(
        *array.shape[:-2],
        latitude_count // factor,
        factor,
        longitude_count // factor,
        factor,
    )
    return reshaped.any(axis=(-3, -1))


def coarsen_coordinates(
    latitude: ArrayLike,
    longitude: ArrayLike,
    area_m2: ArrayLike,
    factor: int,
) -> tuple[FloatArray, FloatArray]:
    """Return area-weighted latitude and arithmetic longitude block centers."""
    latitude_values = np.asarray(latitude, dtype=np.float64)
    longitude_values = np.asarray(longitude, dtype=np.float64)
    area = np.asarray(area_m2, dtype=np.float64)
    if area.shape != (latitude_values.size, longitude_values.size):
        raise ValueError("Coordinates and cell areas do not match.")
    if factor == 1:
        return latitude_values.copy(), longitude_values.copy()
    latitude_grid = np.broadcast_to(latitude_values[:, np.newaxis], area.shape)
    coarse_latitude_grid = coarsen_area_weighted(latitude_grid, area, factor)
    coarse_latitude = coarse_latitude_grid.mean(axis=1)
    coarse_longitude = longitude_values.reshape(-1, factor).mean(axis=1)
    return coarse_latitude, coarse_longitude


def summarize_structural_scenario(
    *,
    marginal_burden_per_gj: ArrayLike,
    source_eligible: ArrayLike,
    sink_eligible: ArrayLike,
    population: ArrayLike,
    land_fraction: ArrayLike,
    cryosphere_mask: ArrayLike,
    latitude: ArrayLike,
    longitude: ArrayLike,
    maximum_distance_km: float,
    maximum_temporal_lag_steps: int,
    near_optimal_fraction: float,
    high_transport_penalty_burden_per_gj_km: float,
) -> dict[str, float | int | bool]:
    """Summarize structural properties around the peak marginal source event."""
    marginal = np.asarray(marginal_burden_per_gj, dtype=np.float64)
    source_allowed = np.asarray(source_eligible, dtype=bool)
    sink_allowed = np.asarray(sink_eligible, dtype=bool)
    population_values = np.asarray(population, dtype=np.float64)
    land = np.asarray(land_fraction, dtype=np.float64)
    cryosphere = np.asarray(cryosphere_mask, dtype=bool)
    latitude_values = np.asarray(latitude, dtype=np.float64)
    longitude_values = np.asarray(longitude, dtype=np.float64)

    if marginal.ndim != 3:
        raise ValueError("Marginal burden must have shape (time, latitude, longitude).")
    if (
        source_allowed.shape != marginal.shape
        or sink_allowed.shape != marginal.shape
        or cryosphere.shape != marginal.shape
    ):
        raise ValueError(
            "Dynamic eligibility and mask arrays must match marginal burden."
        )
    if (
        marginal.shape[1:] != population_values.shape
        or land.shape != population_values.shape
    ):
        raise ValueError(
            "Static grids must match the spatial marginal-burden dimensions."
        )
    if marginal.shape[1:] != (latitude_values.size, longitude_values.size):
        raise ValueError("Coordinates do not match marginal-burden dimensions.")
    if maximum_distance_km <= 0.0:
        raise ValueError("Maximum distance must be positive.")
    if maximum_temporal_lag_steps < 1:
        raise ValueError("Maximum temporal lag must be at least one step.")
    if not 0.0 <= near_optimal_fraction < 1.0:
        raise ValueError("Near-optimal fraction must be in [0, 1).")
    if high_transport_penalty_burden_per_gj_km < 0.0:
        raise ValueError("Transport penalty must be nonnegative.")

    eligible_values = marginal[source_allowed & np.isfinite(marginal)]
    positive_values = eligible_values[eligible_values > 0.0]
    if positive_values.size == 0:
        raise ValueError("Scenario has no positive eligible marginal burden.")

    source_objective = np.where(source_allowed, marginal, -np.inf)
    source_flat = int(np.argmax(source_objective))
    source_time, source_latitude_index, source_longitude_index = np.unravel_index(
        source_flat,
        marginal.shape,
    )
    source_spatial_index = np.ravel_multi_index(
        (source_latitude_index, source_longitude_index),
        marginal.shape[1:],
    )
    source_benefit = float(marginal[source_time].ravel()[source_spatial_index])

    latitude_grid, longitude_grid = np.meshgrid(
        latitude_values,
        longitude_values,
        indexing="ij",
    )
    distance = great_circle_distance_km(
        latitude_values[source_latitude_index],
        longitude_values[source_longitude_index],
        latitude_grid,
        longitude_grid,
    ).ravel()
    same_time_marginal = marginal[source_time].ravel()
    same_time_sink_allowed = sink_allowed[source_time].ravel().copy()
    same_time_sink_allowed[source_spatial_index] = False
    distance_allowed = distance <= maximum_distance_km
    feasible = (
        same_time_sink_allowed & distance_allowed & np.isfinite(same_time_marginal)
    )
    if not feasible.any():
        raise ValueError("Scenario has no feasible constrained spatial sink.")

    zero_penalty_objective = source_benefit - same_time_marginal
    zero_penalty_objective[~feasible] = -np.inf
    zero_sink_index = int(np.argmax(zero_penalty_objective))
    zero_penalty_net = float(zero_penalty_objective[zero_sink_index])
    near_tolerance = max(abs(zero_penalty_net) * near_optimal_fraction, 1.0e-12)
    near_optimal = feasible & (
        zero_penalty_objective >= zero_penalty_net - near_tolerance
    )

    high_penalty_objective = (
        source_benefit
        - same_time_marginal
        - high_transport_penalty_burden_per_gj_km * distance
    )
    high_penalty_objective[~feasible] = -np.inf
    high_sink_index = int(np.argmax(high_penalty_objective))
    high_penalty_net = float(high_penalty_objective[high_sink_index])

    unrestricted = np.isfinite(same_time_marginal)
    unrestricted[source_spatial_index] = False
    unrestricted_minimum = float(np.min(same_time_marginal[unrestricted]))
    unrestricted_tolerance = max(abs(unrestricted_minimum) * 1.0e-9, 1.0e-12)
    unrestricted_minima = unrestricted & (
        same_time_marginal <= unrestricted_minimum + unrestricted_tolerance
    )
    pathology = (land.ravel() < 0.5) | cryosphere[source_time].ravel()
    pathological_minima = unrestricted_minima & pathology

    final_time = min(
        marginal.shape[0],
        source_time + maximum_temporal_lag_steps + 1,
    )
    temporal_indices = np.arange(source_time + 1, final_time)
    if temporal_indices.size:
        temporal_sink_allowed = sink_allowed[
            temporal_indices,
            source_latitude_index,
            source_longitude_index,
        ]
        temporal_sink_burden = marginal[
            temporal_indices,
            source_latitude_index,
            source_longitude_index,
        ]
        temporal_objective = np.where(
            temporal_sink_allowed & np.isfinite(temporal_sink_burden),
            source_benefit - temporal_sink_burden,
            -np.inf,
        )
    else:
        temporal_objective = np.array([], dtype=np.float64)
    if temporal_objective.size and np.isfinite(temporal_objective).any():
        temporal_offset = int(np.argmax(temporal_objective))
        temporal_sink_time = int(temporal_indices[temporal_offset])
        temporal_net = float(temporal_objective[temporal_offset])
    else:
        temporal_sink_time = -1
        temporal_net = float("nan")

    zero_sink_latitude_index, zero_sink_longitude_index = np.unravel_index(
        zero_sink_index,
        marginal.shape[1:],
    )
    high_sink_latitude_index, high_sink_longitude_index = np.unravel_index(
        high_sink_index,
        marginal.shape[1:],
    )
    temporal_to_spatial = (
        temporal_net / zero_penalty_net
        if np.isfinite(temporal_net) and zero_penalty_net > 0.0
        else float("nan")
    )
    return {
        "positive_marginal_observation_count": int(positive_values.size),
        "marginal_p50_burden_per_gj": float(np.quantile(positive_values, 0.50)),
        "marginal_p95_burden_per_gj": float(np.quantile(positive_values, 0.95)),
        "marginal_p99_burden_per_gj": float(np.quantile(positive_values, 0.99)),
        "marginal_max_burden_per_gj": float(positive_values.max()),
        "marginal_p99_to_p50_ratio": float(
            np.quantile(positive_values, 0.99) / np.quantile(positive_values, 0.50)
        ),
        "source_time_index": int(source_time),
        "source_latitude_index": int(source_latitude_index),
        "source_longitude_index": int(source_longitude_index),
        "source_latitude": float(latitude_values[source_latitude_index]),
        "source_longitude": float(longitude_values[source_longitude_index]),
        "source_population": float(
            population_values[source_latitude_index, source_longitude_index]
        ),
        "source_marginal_benefit_per_gj": source_benefit,
        "unrestricted_minimum_sink_burden_per_gj": unrestricted_minimum,
        "unrestricted_minimum_sink_count": int(unrestricted_minima.sum()),
        "unrestricted_pathological_minimum_sink_count": int(pathological_minima.sum()),
        "unrestricted_pathological_minimum_sink_fraction": float(
            pathological_minima.sum() / unrestricted_minima.sum()
        ),
        "spatial_zero_penalty_sink_latitude": float(
            latitude_values[zero_sink_latitude_index]
        ),
        "spatial_zero_penalty_sink_longitude": float(
            longitude_values[zero_sink_longitude_index]
        ),
        "spatial_zero_penalty_distance_km": float(distance[zero_sink_index]),
        "spatial_zero_penalty_net_benefit_per_gj": zero_penalty_net,
        "spatial_near_optimal_sink_count": int(near_optimal.sum()),
        "spatial_high_penalty_sink_latitude": float(
            latitude_values[high_sink_latitude_index]
        ),
        "spatial_high_penalty_sink_longitude": float(
            longitude_values[high_sink_longitude_index]
        ),
        "spatial_high_penalty_distance_km": float(distance[high_sink_index]),
        "spatial_high_penalty_net_benefit_per_gj": high_penalty_net,
        "spatial_value_collapses_at_high_penalty": bool(high_penalty_net <= 0.0),
        "temporal_sink_time_index": temporal_sink_time,
        "temporal_net_benefit_per_gj": temporal_net,
        "temporal_to_spatial_value_ratio": temporal_to_spatial,
        "theoretical_spatial_value_positive": bool(zero_penalty_net > 0.0),
        "sink_nonunique_within_tolerance": bool(near_optimal.sum() > 1),
        "unrestricted_pathological_sinks_present": bool(pathological_minima.any()),
    }
