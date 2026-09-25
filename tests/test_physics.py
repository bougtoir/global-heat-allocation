import numpy as np

from global_heat_allocation.physics import (
    EARTH_RADIUS_M,
    atmospheric_heat_capacity_j_per_k,
    great_circle_distance_km,
    grid_cell_area_m2,
    temperature_change_k,
)


def test_global_cell_areas_sum_to_spherical_surface() -> None:
    latitude = np.array([67.5, 22.5, -22.5, -67.5])
    longitude = np.arange(0.0, 360.0, 45.0)
    area = grid_cell_area_m2(latitude, longitude)
    np.testing.assert_allclose(
        area.sum(),
        4.0 * np.pi * EARTH_RADIUS_M**2,
        rtol=1.0e-12,
    )


def test_energy_temperature_conversion_is_reversible() -> None:
    area = np.array([1.0e6])
    capacity = atmospheric_heat_capacity_j_per_k(
        area,
        mixing_height_m=100.0,
        air_density_kg_m3=1.2,
        air_heat_capacity_j_kg_k=1000.0,
    )
    change = temperature_change_k(np.array([12.0]), capacity)
    np.testing.assert_allclose(change, np.array([0.1]))


def test_quarter_circumference_distance() -> None:
    distance = great_circle_distance_km(0.0, 0.0, 0.0, 90.0)
    np.testing.assert_allclose(
        distance,
        np.pi * EARTH_RADIUS_M / 2000.0,
        rtol=1.0e-12,
    )


def test_antipodal_distance_is_finite() -> None:
    distance = great_circle_distance_km(90.0, 0.0, -90.0, 180.0)
    assert np.isfinite(distance)
    np.testing.assert_allclose(
        distance,
        np.pi * EARTH_RADIUS_M / 1000.0,
        rtol=1.0e-12,
    )
