import numpy as np

from global_heat_allocation.preprocessing import (
    latitude_bin_indices,
    longitude_bin_indices,
)


def test_longitude_bins_wrap_across_dateline() -> None:
    target = np.arange(0.0, 360.0, 90.0)
    source = np.array([-179.0, -1.0, 1.0, 179.0, 359.0])
    np.testing.assert_array_equal(
        longitude_bin_indices(source, target),
        np.array([2, 0, 0, 2, 0]),
    )


def test_latitude_bins_include_polar_caps() -> None:
    target = np.array([67.5, 22.5, -22.5, -67.5])
    source = np.array([90.0, 45.0, 0.0, -45.0, -90.0])
    np.testing.assert_array_equal(
        latitude_bin_indices(source, target),
        np.array([0, 1, 2, 3, 3]),
    )
