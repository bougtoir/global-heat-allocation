import numpy as np

from global_heat_allocation.structural_replication import (
    coarsen_any,
    coarsen_area_weighted,
    coarsen_coordinates,
    coarsen_sum,
    summarize_structural_scenario,
)


def test_coarsening_helpers_preserve_extensive_totals() -> None:
    values = np.arange(16, dtype=np.float64).reshape(4, 4)
    area = np.ones((4, 4), dtype=np.float64)
    latitude = np.array([60.0, 20.0, -20.0, -60.0])
    longitude = np.array([0.0, 90.0, 180.0, 270.0])

    summed = coarsen_sum(values, 2)
    weighted = coarsen_area_weighted(values, area, 2)
    mask = coarsen_any(values > 10.0, 2)
    coarse_latitude, coarse_longitude = coarsen_coordinates(
        latitude,
        longitude,
        area,
        2,
    )

    assert summed.sum() == values.sum()
    np.testing.assert_allclose(weighted, [[2.5, 4.5], [10.5, 12.5]])
    np.testing.assert_array_equal(mask, [[False, False], [True, True]])
    np.testing.assert_allclose(coarse_latitude, [40.0, -40.0])
    np.testing.assert_allclose(coarse_longitude, [45.0, 225.0])


def test_structural_summary_detects_value_nonuniqueness_and_pathology() -> None:
    marginal = np.array(
        [
            [[10.0, 1.0, 0.0], [1.0, 2.0, 0.0]],
            [[4.0, 1.0, 0.0], [1.0, 2.0, 0.0]],
            [[8.0, 1.0, 0.0], [1.0, 2.0, 0.0]],
            [[9.0, 1.0, 0.0], [1.0, 2.0, 0.0]],
        ]
    )
    source_eligible = np.zeros_like(marginal, dtype=bool)
    source_eligible[0, 0, 0] = True
    land = np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 0.0]])
    cryosphere = np.zeros_like(marginal, dtype=bool)
    cryosphere[:, 0, 2] = True
    sink_eligible = (
        (land[np.newaxis, :, :] >= 0.5)
        & ~cryosphere
        & np.ones_like(marginal, dtype=bool)
    )

    summary = summarize_structural_scenario(
        marginal_burden_per_gj=marginal,
        source_eligible=source_eligible,
        sink_eligible=sink_eligible,
        population=np.ones((2, 3)),
        land_fraction=land,
        cryosphere_mask=cryosphere,
        latitude=np.array([10.0, -10.0]),
        longitude=np.array([0.0, 120.0, 240.0]),
        maximum_distance_km=20_000.0,
        maximum_temporal_lag_steps=3,
        near_optimal_fraction=0.01,
        high_transport_penalty_burden_per_gj_km=5.0,
    )

    assert summary["theoretical_spatial_value_positive"]
    assert summary["spatial_zero_penalty_net_benefit_per_gj"] == 9.0
    assert summary["spatial_near_optimal_sink_count"] == 2
    assert summary["sink_nonunique_within_tolerance"]
    assert summary["unrestricted_pathological_minimum_sink_count"] == 2
    assert summary["unrestricted_pathological_sinks_present"]
    assert summary["temporal_net_benefit_per_gj"] == 6.0
    assert summary["temporal_to_spatial_value_ratio"] == 2.0 / 3.0
    assert summary["spatial_value_collapses_at_high_penalty"]
