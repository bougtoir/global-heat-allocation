"""Grid alignment and population aggregation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from numpy.typing import ArrayLike, NDArray
from rasterio.windows import Window

from global_heat_allocation.physics import latitude_bounds

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def longitude_bin_indices(
    source_longitude_degrees: ArrayLike,
    target_longitude_degrees: ArrayLike,
) -> IntArray:
    """Map longitudes to nearest cells on a uniform cyclic target grid."""
    source = np.asarray(source_longitude_degrees, dtype=np.float64)
    target = np.asarray(target_longitude_degrees, dtype=np.float64)
    spacing = np.diff(target)
    if not np.allclose(spacing, spacing[0]):
        raise ValueError("Target longitude grid must be uniform.")
    normalized = np.mod(source - target[0], 360.0)
    return (
        np.floor((normalized + spacing[0] / 2.0) / spacing[0]).astype(np.int64)
        % target.size
    )


def latitude_bin_indices(
    source_latitude_degrees: ArrayLike,
    target_latitude_degrees: ArrayLike,
) -> IntArray:
    """Map latitudes to pole-bounded target latitude cells."""
    source = np.asarray(source_latitude_degrees, dtype=np.float64)
    bounds = latitude_bounds(target_latitude_degrees)
    indices = np.searchsorted(-bounds, -source, side="right") - 1
    return np.clip(indices, 0, bounds.size - 2).astype(np.int64)


def aggregate_population_to_grid(
    raster_path: Path | str,
    target_latitude_degrees: ArrayLike,
    target_longitude_degrees: ArrayLike,
    row_chunk_size: int = 256,
) -> FloatArray:
    """Conservatively aggregate a population-count raster to target cells."""
    target_latitude = np.asarray(target_latitude_degrees, dtype=np.float64)
    target_longitude = np.asarray(target_longitude_degrees, dtype=np.float64)
    population = np.zeros(
        (target_latitude.size, target_longitude.size),
        dtype=np.float64,
    )
    with rasterio.open(raster_path) as dataset:
        columns = np.arange(dataset.width, dtype=np.float64)
        source_longitude = dataset.transform.c + (columns + 0.5) * dataset.transform.a
        longitude_indices = longitude_bin_indices(
            source_longitude,
            target_longitude,
        )
        for start in range(0, dataset.height, row_chunk_size):
            height = min(row_chunk_size, dataset.height - start)
            rows = np.arange(start, start + height, dtype=np.float64)
            source_latitude = dataset.transform.f + (rows + 0.5) * dataset.transform.e
            latitude_indices = latitude_bin_indices(
                source_latitude,
                target_latitude,
            )
            values = dataset.read(
                1,
                window=Window(0, start, dataset.width, height),
                masked=True,
            )
            dense = values.filled(0.0).astype(np.float64, copy=False)
            dense[~np.isfinite(dense) | (dense < 0.0)] = 0.0
            for latitude_index in np.unique(latitude_indices):
                row_values = dense[latitude_indices == latitude_index].sum(axis=0)
                population[latitude_index] += np.bincount(
                    longitude_indices,
                    weights=row_values,
                    minlength=target_longitude.size,
                )
    return population
