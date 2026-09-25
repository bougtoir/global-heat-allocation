"""Physical control-volume calculations."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]
EARTH_RADIUS_M = 6_371_008.8


def latitude_bounds(latitude_degrees: ArrayLike) -> FloatArray:
    """Construct pole-bounded latitude edges from cell centers."""
    latitude = np.asarray(latitude_degrees, dtype=np.float64)
    if latitude.ndim != 1 or latitude.size < 2:
        raise ValueError("Latitude centers must be a one-dimensional vector.")
    if not np.all(np.diff(latitude) < 0.0):
        raise ValueError("Latitude centers must be strictly descending.")
    bounds = np.empty(latitude.size + 1, dtype=np.float64)
    bounds[0] = 90.0
    bounds[-1] = -90.0
    bounds[1:-1] = 0.5 * (latitude[:-1] + latitude[1:])
    return bounds


def grid_cell_area_m2(
    latitude_degrees: ArrayLike,
    longitude_degrees: ArrayLike,
) -> FloatArray:
    """Return spherical cell areas for a global latitude-longitude grid."""
    latitude = np.asarray(latitude_degrees, dtype=np.float64)
    longitude = np.asarray(longitude_degrees, dtype=np.float64)
    if longitude.ndim != 1 or longitude.size < 2:
        raise ValueError("Longitude centers must be a one-dimensional vector.")
    spacing = np.diff(np.sort(longitude))
    if not np.allclose(spacing, spacing[0]):
        raise ValueError("Longitude centers must be uniformly spaced.")
    latitude_edges = np.deg2rad(latitude_bounds(latitude))
    longitude_width = np.deg2rad(float(spacing[0]))
    latitude_factor = np.abs(np.sin(latitude_edges[:-1]) - np.sin(latitude_edges[1:]))
    row_area = EARTH_RADIUS_M**2 * longitude_width * latitude_factor
    return np.repeat(row_area[:, np.newaxis], longitude.size, axis=1)


def atmospheric_heat_capacity_j_per_k(
    area_m2: ArrayLike,
    mixing_height_m: float,
    air_density_kg_m3: float,
    air_heat_capacity_j_kg_k: float,
) -> FloatArray:
    """Return sensible heat capacity for the configured atmospheric layer."""
    area = np.asarray(area_m2, dtype=np.float64)
    return area * mixing_height_m * air_density_kg_m3 * air_heat_capacity_j_kg_k


def temperature_change_k(
    energy_gj: ArrayLike,
    heat_capacity_j_per_k: ArrayLike,
) -> FloatArray:
    """Convert a heat increment in GJ to control-volume temperature change."""
    energy = np.asarray(energy_gj, dtype=np.float64)
    heat_capacity = np.asarray(heat_capacity_j_per_k, dtype=np.float64)
    return energy * 1.0e9 / heat_capacity


def great_circle_distance_km(
    source_latitude: ArrayLike,
    source_longitude: ArrayLike,
    sink_latitude: ArrayLike,
    sink_longitude: ArrayLike,
) -> FloatArray:
    """Return vectorized great-circle distance using the haversine formula."""
    source_lat = np.deg2rad(np.asarray(source_latitude, dtype=np.float64))
    source_lon = np.deg2rad(np.asarray(source_longitude, dtype=np.float64))
    sink_lat = np.deg2rad(np.asarray(sink_latitude, dtype=np.float64))
    sink_lon = np.deg2rad(np.asarray(sink_longitude, dtype=np.float64))
    delta_latitude = sink_lat - source_lat
    delta_longitude = sink_lon - source_lon
    haversine = (
        np.sin(delta_latitude / 2.0) ** 2
        + np.cos(source_lat) * np.cos(sink_lat) * np.sin(delta_longitude / 2.0) ** 2
    )
    bounded_haversine = np.clip(haversine, 0.0, 1.0)
    return 2.0 * EARTH_RADIUS_M / 1000.0 * np.arcsin(np.sqrt(bounded_haversine))
