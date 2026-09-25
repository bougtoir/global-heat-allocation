import math

import pytest

from global_heat_allocation.environmental_constraints import (
    allowable_surface_water_temperature_rise_c,
    scaled_tank_storage_capacity_mwh,
)


def test_scaled_tank_storage_capacity_matches_reference() -> None:
    capacity = scaled_tank_storage_capacity_mwh(
        reference_capacity_mwh=290,
        reference_volume_m3=5000,
        reference_delta_temperature_k=55,
        volume_m3=5000,
        delta_temperature_k=55,
    )

    assert math.isclose(capacity, 290)


def test_scaled_tank_storage_capacity_scales_volume_and_temperature() -> None:
    capacity = scaled_tank_storage_capacity_mwh(
        reference_capacity_mwh=290,
        reference_volume_m3=5000,
        reference_delta_temperature_k=55,
        volume_m3=10000,
        delta_temperature_k=27.5,
    )

    assert math.isclose(capacity, 290)


@pytest.mark.parametrize(
    "field",
    [
        "reference_capacity_mwh",
        "reference_volume_m3",
        "reference_delta_temperature_k",
        "volume_m3",
        "delta_temperature_k",
    ],
)
def test_scaled_tank_storage_capacity_rejects_nonpositive_inputs(field: str) -> None:
    arguments = {
        "reference_capacity_mwh": 290,
        "reference_volume_m3": 5000,
        "reference_delta_temperature_k": 55,
        "volume_m3": 900,
        "delta_temperature_k": 40,
    }
    arguments[field] = 0

    with pytest.raises(ValueError):
        scaled_tank_storage_capacity_mwh(**arguments)


def test_surface_water_temperature_envelope_respects_absolute_limit() -> None:
    assert math.isclose(
        allowable_surface_water_temperature_rise_c(
            upstream_temperature_c=29,
            maximum_temperature_change_c=3,
            maximum_water_temperature_c=30.5,
        ),
        1.5,
    )
    assert math.isclose(
        allowable_surface_water_temperature_rise_c(
            upstream_temperature_c=25,
            maximum_temperature_change_c=3,
            maximum_water_temperature_c=30.5,
        ),
        3,
    )
    assert math.isclose(
        allowable_surface_water_temperature_rise_c(
            upstream_temperature_c=31,
            maximum_temperature_change_c=3,
            maximum_water_temperature_c=30.5,
        ),
        0,
    )
