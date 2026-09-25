import numpy as np
from scipy.spatial import cKDTree

from global_heat_allocation.global_analysis import (
    exact_spatial_search,
    exact_temporal_search,
    unit_sphere_coordinates,
)
from global_heat_allocation.physics import great_circle_distance_km


def test_branch_and_bound_spatial_search_matches_brute_force() -> None:
    latitude = np.array([20.0, 10.0, 0.0, -10.0, -20.0])
    longitude = np.array([0.0, 15.0, 30.0, 45.0, 60.0])
    source = np.array([1.0, 8.0, 3.0, 5.0, 2.0])
    sink = np.array([2.0, 7.0, 1.0, 4.0, 0.5])
    source_allowed = np.array([True, True, True, False, True])
    sink_allowed = np.array([True, False, True, True, True])
    unit = unit_sphere_coordinates(latitude, longitude)
    penalties = (0.0, 0.01)
    result = exact_spatial_search(
        source,
        sink,
        source_allowed,
        sink_allowed,
        latitude,
        longitude,
        cKDTree(unit),
        unit,
        maximum_distance_km=10_000.0,
        transport_penalties=penalties,
    )
    distance = great_circle_distance_km(
        latitude[:, np.newaxis],
        longitude[:, np.newaxis],
        latitude[np.newaxis, :],
        longitude[np.newaxis, :],
    )
    for penalty in penalties:
        objective = source[:, np.newaxis] - sink[np.newaxis, :] - penalty * distance
        feasible = source_allowed[:, np.newaxis] & sink_allowed[np.newaxis, :]
        feasible &= ~np.eye(source.size, dtype=bool)
        feasible &= distance <= 10_000.0
        objective[~feasible] = -np.inf
        assert result.allocations[penalty].net_benefit == np.max(objective)


def test_vectorized_temporal_search_matches_expected_pair() -> None:
    result = exact_temporal_search(
        source_benefit=np.array([[9.0, 1.0], [2.0, 1.0], [1.0, 1.0]]),
        sink_burden=np.array([[8.0, 8.0], [4.0, 4.0], [0.0, 3.0]]),
        source_eligible=np.ones((3, 2), dtype=bool),
        sink_eligible=np.ones((3, 2), dtype=bool),
        maximum_lag_steps=2,
        storage_penalties=(0.0, 1.0),
    )
    assert result[0.0].source_time_index == 0
    assert result[0.0].sink_time_index == 2
    assert result[0.0].location_index == 0
    assert result[0.0].net_benefit == 9.0
    assert result[1.0].net_benefit == 7.0
