"""Physical screening helpers for environmental heat-receiving constraints."""

from __future__ import annotations


def scaled_tank_storage_capacity_mwh(
    *,
    reference_capacity_mwh: float,
    reference_volume_m3: float,
    reference_delta_temperature_k: float,
    volume_m3: float,
    delta_temperature_k: float,
) -> float:
    """Scale sensible tank capacity at unchanged medium and availability."""
    for name, value in {
        "reference_capacity_mwh": reference_capacity_mwh,
        "reference_volume_m3": reference_volume_m3,
        "reference_delta_temperature_k": reference_delta_temperature_k,
        "volume_m3": volume_m3,
        "delta_temperature_k": delta_temperature_k,
    }.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive.")
    return (
        reference_capacity_mwh
        * volume_m3
        / reference_volume_m3
        * delta_temperature_k
        / reference_delta_temperature_k
    )


def allowable_surface_water_temperature_rise_c(
    *,
    upstream_temperature_c: float,
    maximum_temperature_change_c: float,
    maximum_water_temperature_c: float,
) -> float:
    """Return the remaining regulatory temperature-rise envelope."""
    if maximum_temperature_change_c < 0:
        raise ValueError("Maximum temperature change cannot be negative.")
    return max(
        0.0,
        min(
            maximum_temperature_change_c,
            maximum_water_temperature_c - upstream_temperature_c,
        ),
    )
