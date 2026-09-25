"""Energy, cost, and operational-emissions accounting for heat pathways."""

from __future__ import annotations

from dataclasses import dataclass

MMBTU_PER_MWH = 3.412141633


@dataclass(frozen=True)
class EnergyBalance:
    useful_heat_delivered_mwh: float
    heat_pump_output_mwh: float
    source_heat_withdrawn_mwh: float
    source_heat_recovered_mwh: float
    heat_pump_electricity_mwh: float
    storage_auxiliary_electricity_mwh: float
    transport_pumping_electricity_mwh: float
    total_electricity_mwh: float
    source_side_loss_mwh: float
    storage_loss_mwh: float
    transport_loss_mwh: float
    residual_rejected_heat_captured_stream_mwh: float
    thermal_balance_error_mwh: float


@dataclass(frozen=True)
class BaselineBalance:
    useful_heat_delivered_mwh: float
    boiler_heat_output_mwh: float
    natural_gas_input_mwh_hhv: float
    steam_delivery_loss_mwh: float


def heat_recovery_balance(
    *,
    useful_heat_delivered_mwh: float,
    cop: float,
    source_capture_efficiency: float = 1.0,
    storage_roundtrip_efficiency: float = 1.0,
    storage_standing_loss_fraction: float = 0.0,
    storage_auxiliary_fraction: float = 0.0,
    transport_loss_fraction: float = 0.0,
    transport_pumping_fraction: float = 0.0,
) -> EnergyBalance:
    """Return a normalized useful-heat balance without double-counting auxiliaries."""
    if useful_heat_delivered_mwh <= 0:
        raise ValueError("Useful heat delivered must be positive.")
    if cop <= 1:
        raise ValueError("Heat-pump COP must exceed one.")
    if not 0 < source_capture_efficiency <= 1:
        raise ValueError("Source capture efficiency must be in (0, 1].")
    if not 0 < storage_roundtrip_efficiency <= 1:
        raise ValueError("Storage round-trip efficiency must be in (0, 1].")
    for name, value in {
        "storage_standing_loss_fraction": storage_standing_loss_fraction,
        "storage_auxiliary_fraction": storage_auxiliary_fraction,
        "transport_loss_fraction": transport_loss_fraction,
        "transport_pumping_fraction": transport_pumping_fraction,
    }.items():
        if not 0 <= value < 1:
            raise ValueError(f"{name} must be in [0, 1).")

    transport_input = useful_heat_delivered_mwh / (1 - transport_loss_fraction)
    storage_retention = storage_roundtrip_efficiency * (
        1 - storage_standing_loss_fraction
    )
    heat_pump_output = transport_input / storage_retention
    heat_pump_electricity = heat_pump_output / cop
    source_heat_recovered = heat_pump_output - heat_pump_electricity
    source_heat_withdrawn = source_heat_recovered / source_capture_efficiency
    source_side_loss = source_heat_withdrawn - source_heat_recovered
    storage_loss = heat_pump_output - transport_input
    transport_loss = transport_input - useful_heat_delivered_mwh
    storage_auxiliary = storage_auxiliary_fraction * transport_input
    transport_pumping = transport_pumping_fraction * transport_input
    total_electricity = heat_pump_electricity + storage_auxiliary + transport_pumping
    thermal_balance_error = (
        source_heat_withdrawn
        + heat_pump_electricity
        - source_side_loss
        - storage_loss
        - transport_loss
        - useful_heat_delivered_mwh
    )
    return EnergyBalance(
        useful_heat_delivered_mwh=useful_heat_delivered_mwh,
        heat_pump_output_mwh=heat_pump_output,
        source_heat_withdrawn_mwh=source_heat_withdrawn,
        source_heat_recovered_mwh=source_heat_recovered,
        heat_pump_electricity_mwh=heat_pump_electricity,
        storage_auxiliary_electricity_mwh=storage_auxiliary,
        transport_pumping_electricity_mwh=transport_pumping,
        total_electricity_mwh=total_electricity,
        source_side_loss_mwh=source_side_loss,
        storage_loss_mwh=storage_loss,
        transport_loss_mwh=transport_loss,
        residual_rejected_heat_captured_stream_mwh=0.0,
        thermal_balance_error_mwh=thermal_balance_error,
    )


def conventional_steam_balance(
    *,
    useful_heat_delivered_mwh: float,
    boiler_efficiency: float,
    delivery_loss_fraction: float,
) -> BaselineBalance:
    """Return fuel input for conventional natural-gas steam delivery."""
    if useful_heat_delivered_mwh <= 0:
        raise ValueError("Useful heat delivered must be positive.")
    if not 0 < boiler_efficiency <= 1:
        raise ValueError("Boiler efficiency must be in (0, 1].")
    if not 0 <= delivery_loss_fraction < 1:
        raise ValueError("Delivery loss must be in [0, 1).")
    boiler_output = useful_heat_delivered_mwh / (1 - delivery_loss_fraction)
    return BaselineBalance(
        useful_heat_delivered_mwh=useful_heat_delivered_mwh,
        boiler_heat_output_mwh=boiler_output,
        natural_gas_input_mwh_hhv=boiler_output / boiler_efficiency,
        steam_delivery_loss_mwh=boiler_output - useful_heat_delivered_mwh,
    )


def uniform_present_value_factor(discount_rate: float, years: int) -> float:
    """Present-value factor for a constant end-of-year annual flow."""
    if years <= 0:
        raise ValueError("Years must be positive.")
    if discount_rate < 0:
        raise ValueError("Discount rate cannot be negative.")
    if discount_rate == 0:
        return float(years)
    return (1 - (1 + discount_rate) ** (-years)) / discount_rate


def replacement_present_value(
    *,
    initial_cost: float,
    component_lifetime_years: int,
    study_period_years: int,
    discount_rate: float,
) -> float:
    """Present value of like-for-like replacements, excluding the initial asset."""
    if initial_cost < 0:
        raise ValueError("Initial cost cannot be negative.")
    if component_lifetime_years <= 0 or study_period_years <= 0:
        raise ValueError("Lifetimes and study periods must be positive.")
    if discount_rate < 0:
        raise ValueError("Discount rate cannot be negative.")
    return sum(
        initial_cost / (1 + discount_rate) ** year
        for year in range(
            component_lifetime_years,
            study_period_years,
            component_lifetime_years,
        )
    )


def natural_gas_co2e_kg_per_mmbtu(
    *,
    co2_kg_per_mmbtu: float,
    ch4_g_per_mmbtu: float,
    n2o_g_per_mmbtu: float,
    ch4_gwp: float,
    n2o_gwp: float,
) -> float:
    """Convert fuel-specific combustion factors to kg CO2e per mmBtu."""
    return (
        co2_kg_per_mmbtu
        + ch4_g_per_mmbtu * ch4_gwp / 1000
        + n2o_g_per_mmbtu * n2o_gwp / 1000
    )
