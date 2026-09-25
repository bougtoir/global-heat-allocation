"""Finite-timestep thermal dispatch with explicit storage and rejection."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DispatchParameters:
    timestep_hours: float
    heat_pump_cop: float
    heat_pump_capacity_mw: float
    source_capture_efficiency: float = 1.0
    storage_capacity_mwh: float = 0.0
    storage_charge_power_mw: float = 0.0
    storage_discharge_power_mw: float = 0.0
    storage_roundtrip_efficiency: float = 1.0
    storage_standing_loss_fraction_per_day: float = 0.0
    storage_auxiliary_fraction: float = 0.0
    initial_storage_mwh: float = 0.0


@dataclass(frozen=True)
class DispatchResult:
    timeseries: pd.DataFrame
    summary: dict[str, float | int]


def _validate_parameters(parameters: DispatchParameters) -> None:
    if parameters.timestep_hours <= 0:
        raise ValueError("Timestep must be positive.")
    if parameters.heat_pump_cop <= 1:
        raise ValueError("Heat-pump COP must exceed one.")
    if parameters.heat_pump_capacity_mw < 0:
        raise ValueError("Heat-pump capacity cannot be negative.")
    if not 0 < parameters.source_capture_efficiency <= 1:
        raise ValueError("Source capture efficiency must be in (0, 1].")
    for name, value in {
        "storage_capacity_mwh": parameters.storage_capacity_mwh,
        "storage_charge_power_mw": parameters.storage_charge_power_mw,
        "storage_discharge_power_mw": parameters.storage_discharge_power_mw,
        "initial_storage_mwh": parameters.initial_storage_mwh,
    }.items():
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
    if parameters.initial_storage_mwh > parameters.storage_capacity_mwh:
        raise ValueError("Initial storage cannot exceed storage capacity.")
    if not 0 < parameters.storage_roundtrip_efficiency <= 1:
        raise ValueError("Storage round-trip efficiency must be in (0, 1].")
    if not 0 <= parameters.storage_standing_loss_fraction_per_day < 1:
        raise ValueError("Daily standing loss must be in [0, 1).")
    if parameters.storage_auxiliary_fraction < 0:
        raise ValueError("Storage auxiliary fraction cannot be negative.")


def _validate_series(
    source_heat_mw: np.ndarray,
    demand_mw: np.ndarray,
) -> None:
    if source_heat_mw.ndim != 1 or demand_mw.ndim != 1:
        raise ValueError("Source and demand must be one-dimensional.")
    if len(source_heat_mw) != len(demand_mw):
        raise ValueError("Source and demand must have equal length.")
    if not np.isfinite(source_heat_mw).all() or not np.isfinite(demand_mw).all():
        raise ValueError("Source and demand must be finite.")
    if (source_heat_mw < 0).any() or (demand_mw < 0).any():
        raise ValueError("Source and demand cannot be negative.")


def dispatch_heat(
    *,
    source_heat_mw: np.ndarray,
    demand_mw: np.ndarray,
    parameters: DispatchParameters,
) -> DispatchResult:
    """Dispatch direct heat and storage without imputing unavailable source heat."""
    _validate_parameters(parameters)
    source = np.asarray(source_heat_mw, dtype=float)
    demand = np.asarray(demand_mw, dtype=float)
    _validate_series(source, demand)

    columns = {
        name: np.zeros(len(source), dtype=float)
        for name in [
            "source_heat_available_mwh",
            "source_heat_captured_mwh",
            "source_heat_used_mwh",
            "residual_source_rejection_mwh",
            "heat_pump_output_mwh",
            "heat_pump_electricity_mwh",
            "demand_mwh",
            "direct_heat_delivered_mwh",
            "storage_heat_delivered_mwh",
            "useful_heat_delivered_mwh",
            "unmet_demand_mwh",
            "storage_charge_input_mwh",
            "storage_charge_loss_mwh",
            "storage_discharge_loss_mwh",
            "storage_standing_loss_mwh",
            "storage_auxiliary_electricity_mwh",
            "storage_state_mwh",
            "thermal_balance_error_mwh",
            "source_balance_error_mwh",
            "demand_balance_error_mwh",
        ]
    }
    timestep = parameters.timestep_hours
    source_fraction_of_output = 1 - 1 / parameters.heat_pump_cop
    charge_efficiency = parameters.storage_roundtrip_efficiency**0.5
    discharge_efficiency = parameters.storage_roundtrip_efficiency**0.5
    standing_retention = (1 - parameters.storage_standing_loss_fraction_per_day) ** (
        timestep / 24
    )
    storage_state = parameters.initial_storage_mwh

    for index, (source_power, demand_power) in enumerate(
        zip(source, demand, strict=True)
    ):
        source_available = source_power * timestep
        source_captured = source_available * parameters.source_capture_efficiency
        demand_energy = demand_power * timestep
        storage_before_loss = storage_state
        storage_state *= standing_retention
        standing_loss = storage_before_loss - storage_state

        maximum_heat_pump_output = min(
            parameters.heat_pump_capacity_mw * timestep,
            source_captured / source_fraction_of_output,
        )
        direct_delivery = min(demand_energy, maximum_heat_pump_output)
        remaining_demand = demand_energy - direct_delivery
        storage_delivery = min(
            remaining_demand,
            parameters.storage_discharge_power_mw * timestep,
            storage_state * discharge_efficiency,
        )
        storage_withdrawal = storage_delivery / discharge_efficiency
        discharge_loss = storage_withdrawal - storage_delivery
        storage_state = max(storage_state - storage_withdrawal, 0.0)

        remaining_heat_pump_output = maximum_heat_pump_output - direct_delivery
        charge_input = min(
            remaining_heat_pump_output,
            parameters.storage_charge_power_mw * timestep,
            (
                max(parameters.storage_capacity_mwh - storage_state, 0.0)
                / charge_efficiency
            ),
        )
        charge_stored = charge_input * charge_efficiency
        charge_loss = charge_input - charge_stored
        storage_state = min(
            storage_state + charge_stored,
            parameters.storage_capacity_mwh,
        )

        heat_pump_output = direct_delivery + charge_input
        heat_pump_electricity = heat_pump_output / parameters.heat_pump_cop
        source_used = heat_pump_output - heat_pump_electricity
        residual_rejection = max(source_available - source_used, 0.0)
        useful_delivery = direct_delivery + storage_delivery
        unmet_demand = max(demand_energy - useful_delivery, 0.0)
        storage_auxiliary = storage_delivery * parameters.storage_auxiliary_fraction
        thermal_error = (
            storage_before_loss
            + source_used
            + heat_pump_electricity
            - standing_loss
            - direct_delivery
            - storage_delivery
            - charge_loss
            - discharge_loss
            - storage_state
        )

        values = {
            "source_heat_available_mwh": source_available,
            "source_heat_captured_mwh": source_captured,
            "source_heat_used_mwh": source_used,
            "residual_source_rejection_mwh": residual_rejection,
            "heat_pump_output_mwh": heat_pump_output,
            "heat_pump_electricity_mwh": heat_pump_electricity,
            "demand_mwh": demand_energy,
            "direct_heat_delivered_mwh": direct_delivery,
            "storage_heat_delivered_mwh": storage_delivery,
            "useful_heat_delivered_mwh": useful_delivery,
            "unmet_demand_mwh": unmet_demand,
            "storage_charge_input_mwh": charge_input,
            "storage_charge_loss_mwh": charge_loss,
            "storage_discharge_loss_mwh": discharge_loss,
            "storage_standing_loss_mwh": standing_loss,
            "storage_auxiliary_electricity_mwh": storage_auxiliary,
            "storage_state_mwh": storage_state,
            "thermal_balance_error_mwh": thermal_error,
            "source_balance_error_mwh": (
                source_available - source_used - residual_rejection
            ),
            "demand_balance_error_mwh": (
                demand_energy - useful_delivery - unmet_demand
            ),
        }
        for name, value in values.items():
            columns[name][index] = value

    timeseries = pd.DataFrame(columns)
    total_demand = float(timeseries["demand_mwh"].sum())
    total_delivery = float(timeseries["useful_heat_delivered_mwh"].sum())
    summary: dict[str, float | int] = {
        "interval_count": len(timeseries),
        "source_heat_available_mwh": float(
            timeseries["source_heat_available_mwh"].sum()
        ),
        "source_heat_used_mwh": float(timeseries["source_heat_used_mwh"].sum()),
        "residual_source_rejection_mwh": float(
            timeseries["residual_source_rejection_mwh"].sum()
        ),
        "heat_pump_output_mwh": float(timeseries["heat_pump_output_mwh"].sum()),
        "heat_pump_electricity_mwh": float(
            timeseries["heat_pump_electricity_mwh"].sum()
        ),
        "demand_mwh": total_demand,
        "direct_heat_delivered_mwh": float(
            timeseries["direct_heat_delivered_mwh"].sum()
        ),
        "storage_heat_delivered_mwh": float(
            timeseries["storage_heat_delivered_mwh"].sum()
        ),
        "useful_heat_delivered_mwh": total_delivery,
        "unmet_demand_mwh": float(timeseries["unmet_demand_mwh"].sum()),
        "demand_served_fraction": (
            total_delivery / total_demand if total_demand > 0 else 0.0
        ),
        "storage_charge_input_mwh": float(timeseries["storage_charge_input_mwh"].sum()),
        "storage_charge_loss_mwh": float(timeseries["storage_charge_loss_mwh"].sum()),
        "storage_discharge_loss_mwh": float(
            timeseries["storage_discharge_loss_mwh"].sum()
        ),
        "storage_standing_loss_mwh": float(
            timeseries["storage_standing_loss_mwh"].sum()
        ),
        "storage_auxiliary_electricity_mwh": float(
            timeseries["storage_auxiliary_electricity_mwh"].sum()
        ),
        "initial_storage_mwh": parameters.initial_storage_mwh,
        "final_storage_mwh": float(timeseries["storage_state_mwh"].iloc[-1])
        if len(timeseries)
        else parameters.initial_storage_mwh,
        "maximum_storage_mwh": float(timeseries["storage_state_mwh"].max())
        if len(timeseries)
        else parameters.initial_storage_mwh,
        "intervals_with_unmet_demand": int(
            timeseries["unmet_demand_mwh"].gt(1e-12).sum()
        ),
        "intervals_with_residual_rejection": int(
            timeseries["residual_source_rejection_mwh"].gt(1e-12).sum()
        ),
        "maximum_absolute_thermal_balance_error_mwh": float(
            timeseries["thermal_balance_error_mwh"].abs().max()
        )
        if len(timeseries)
        else 0.0,
        "annual_thermal_balance_error_mwh": float(
            timeseries["thermal_balance_error_mwh"].sum()
        ),
    }
    return DispatchResult(timeseries=timeseries, summary=summary)
