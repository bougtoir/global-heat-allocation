import numpy as np
import pytest

from global_heat_allocation import optimization
from global_heat_allocation.optimization import (
    select_joint_allocation,
    select_spatial_allocation,
    select_temporal_allocation,
)


def test_spatial_solver_selects_high_benefit_low_burden_pair() -> None:
    allocation = select_spatial_allocation(
        source_benefit=np.array([5.0, 10.0, 2.0]),
        sink_burden=np.array([4.0, 8.0, 1.0]),
        distance_km=np.array(
            [
                [0.0, 100.0, 200.0],
                [100.0, 0.0, 50.0],
                [200.0, 50.0, 0.0],
            ]
        ),
        source_eligible=np.ones(3, dtype=bool),
        sink_eligible=np.ones(3, dtype=bool),
        maximum_distance_km=500.0,
        transport_cost_per_gj_km=0.01,
    )
    assert allocation.source_index == 1
    assert allocation.sink_index == 2
    assert allocation.net_benefit == 8.5


def test_spatial_solver_retains_negative_best_feasible_value() -> None:
    allocation = select_spatial_allocation(
        source_benefit=np.array([1.0, 0.0]),
        sink_burden=np.array([4.0, 5.0]),
        distance_km=np.array([[0.0, 1.0], [1.0, 0.0]]),
        source_eligible=np.array([True, False]),
        sink_eligible=np.array([True, True]),
        maximum_distance_km=2.0,
        transport_cost_per_gj_km=0.0,
    )
    assert allocation.net_benefit == -4.0


def test_temporal_solver_releases_at_lowest_later_burden() -> None:
    allocation = select_temporal_allocation(
        source_benefit=np.array([[1.0], [10.0], [2.0], [1.0]]),
        sink_burden=np.array([[5.0], [8.0], [4.0], [1.0]]),
        source_eligible=np.ones((4, 1), dtype=bool),
        sink_eligible=np.ones((4, 1), dtype=bool),
        maximum_lag_steps=2,
        storage_cost_per_gj_step=0.5,
    )
    assert allocation.source_time_index == 1
    assert allocation.sink_time_index == 3
    assert allocation.net_benefit == 8.0


def test_temporal_solver_uses_distinct_source_and_sink_eligibility() -> None:
    allocation = select_temporal_allocation(
        source_benefit=np.array([[10.0], [0.0]]),
        sink_burden=np.array([[10.0], [1.0]]),
        source_eligible=np.array([[True], [False]]),
        sink_eligible=np.array([[False], [True]]),
        maximum_lag_steps=1,
        storage_cost_per_gj_step=0.0,
    )
    assert allocation.source_time_index == 0
    assert allocation.sink_time_index == 1
    assert allocation.net_benefit == 9.0


def test_joint_solver_combines_spatial_and_temporal_advantage() -> None:
    source = np.array([[1.0, 1.0], [10.0, 1.0], [1.0, 1.0]])
    sink = np.array([[5.0, 5.0], [5.0, 4.0], [5.0, 0.0]])
    allocation = select_joint_allocation(
        source_benefit=source,
        sink_burden=sink,
        distance_km=np.array([[0.0, 100.0], [100.0, 0.0]]),
        source_eligible=np.ones_like(source, dtype=bool),
        sink_eligible=np.ones_like(sink, dtype=bool),
        maximum_distance_km=200.0,
        maximum_lag_steps=1,
        transport_cost_per_gj_km=0.01,
        storage_cost_per_gj_step=0.5,
    )
    assert allocation.source_location_index == 0
    assert allocation.sink_location_index == 1
    assert allocation.source_time_index == 1
    assert allocation.sink_time_index == 2
    assert allocation.net_benefit == 8.5


def test_dense_solver_rejects_global_scale_pair_matrix(monkeypatch) -> None:
    monkeypatch.setattr(optimization, "MAX_DENSE_PAIR_ELEMENTS", 4)
    with pytest.raises(ValueError, match="memory-bounded global search"):
        select_spatial_allocation(
            source_benefit=np.ones(3),
            sink_burden=np.ones(3),
            distance_km=np.zeros((3, 3)),
            source_eligible=np.ones(3, dtype=bool),
            sink_eligible=np.ones(3, dtype=bool),
            maximum_distance_km=1.0,
            transport_cost_per_gj_km=0.0,
        )
