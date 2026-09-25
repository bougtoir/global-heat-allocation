import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from global_heat_allocation.dispatch import DispatchParameters, dispatch_heat

ROOT = Path(__file__).resolve().parents[1]


def test_dispatch_conserves_heat_and_exposes_rejection() -> None:
    result = dispatch_heat(
        source_heat_mw=np.array([3.0, 3.0]),
        demand_mw=np.array([1.0, 1.0]),
        parameters=DispatchParameters(
            timestep_hours=1.0,
            heat_pump_cop=3.0,
            heat_pump_capacity_mw=2.0,
        ),
    )

    assert math.isclose(result.summary["useful_heat_delivered_mwh"], 2.0)
    assert result.summary["residual_source_rejection_mwh"] > 0
    assert result.summary["maximum_absolute_thermal_balance_error_mwh"] < 1e-12
    assert np.allclose(result.timeseries["source_balance_error_mwh"], 0.0)
    assert np.allclose(result.timeseries["demand_balance_error_mwh"], 0.0)


def test_dispatch_storage_bridges_source_outage_with_losses() -> None:
    result = dispatch_heat(
        source_heat_mw=np.array([6.0, 0.0]),
        demand_mw=np.array([1.0, 1.0]),
        parameters=DispatchParameters(
            timestep_hours=1.0,
            heat_pump_cop=3.0,
            heat_pump_capacity_mw=3.0,
            storage_capacity_mwh=2.0,
            storage_charge_power_mw=2.0,
            storage_discharge_power_mw=2.0,
            storage_roundtrip_efficiency=0.81,
            storage_standing_loss_fraction_per_day=0.024,
            storage_auxiliary_fraction=0.01,
        ),
    )

    assert result.timeseries.loc[0, "storage_state_mwh"] > 0
    assert result.timeseries.loc[1, "storage_heat_delivered_mwh"] > 0
    assert result.summary["storage_charge_loss_mwh"] > 0
    assert result.summary["storage_discharge_loss_mwh"] > 0
    assert result.summary["storage_standing_loss_mwh"] > 0
    assert result.summary["storage_auxiliary_electricity_mwh"] > 0
    assert result.summary["maximum_absolute_thermal_balance_error_mwh"] < 1e-12


def test_dispatch_enforces_power_and_storage_bounds() -> None:
    result = dispatch_heat(
        source_heat_mw=np.array([100.0, 0.0]),
        demand_mw=np.array([0.0, 100.0]),
        parameters=DispatchParameters(
            timestep_hours=1.0,
            heat_pump_cop=4.0,
            heat_pump_capacity_mw=10.0,
            storage_capacity_mwh=1.0,
            storage_charge_power_mw=0.5,
            storage_discharge_power_mw=0.25,
        ),
    )

    assert math.isclose(
        result.timeseries.loc[0, "storage_charge_input_mwh"],
        0.5,
    )
    assert math.isclose(
        result.timeseries.loc[1, "storage_heat_delivered_mwh"],
        0.25,
    )
    assert result.timeseries["storage_state_mwh"].between(0.0, 1.0).all()
    assert result.timeseries.loc[1, "unmet_demand_mwh"] > 0


def test_dispatch_treats_zero_source_as_unavailable_without_negative_flows() -> None:
    result = dispatch_heat(
        source_heat_mw=np.zeros(3),
        demand_mw=np.ones(3),
        parameters=DispatchParameters(
            timestep_hours=1 / 6,
            heat_pump_cop=3.08,
            heat_pump_capacity_mw=3.0,
        ),
    )

    flow_columns = [
        column
        for column in result.timeseries
        if column.endswith("_mwh") and "error" not in column
    ]
    assert result.timeseries[flow_columns].ge(0).all().all()
    assert math.isclose(result.summary["useful_heat_delivered_mwh"], 0.0)
    assert math.isclose(
        result.summary["unmet_demand_mwh"],
        result.summary["demand_mwh"],
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("timestep_hours", 0.0),
        ("heat_pump_cop", 1.0),
        ("source_capture_efficiency", 0.0),
        ("storage_roundtrip_efficiency", 0.0),
        ("storage_standing_loss_fraction_per_day", 1.0),
    ],
)
def test_dispatch_rejects_invalid_parameters(field: str, value: float) -> None:
    values = {
        "timestep_hours": 1.0,
        "heat_pump_cop": 3.0,
        "heat_pump_capacity_mw": 1.0,
        "source_capture_efficiency": 1.0,
        "storage_roundtrip_efficiency": 1.0,
        "storage_standing_loss_fraction_per_day": 0.0,
    }
    values[field] = value

    with pytest.raises(ValueError):
        dispatch_heat(
            source_heat_mw=np.ones(1),
            demand_mw=np.ones(1),
            parameters=DispatchParameters(**values),
        )


def test_dispatch_rejects_invalid_series() -> None:
    parameters = DispatchParameters(
        timestep_hours=1.0,
        heat_pump_cop=3.0,
        heat_pump_capacity_mw=1.0,
    )

    with pytest.raises(ValueError):
        dispatch_heat(
            source_heat_mw=np.array([1.0]),
            demand_mw=np.array([1.0, 2.0]),
            parameters=parameters,
        )
    with pytest.raises(ValueError):
        dispatch_heat(
            source_heat_mw=np.array([-1.0]),
            demand_mw=np.array([1.0]),
            parameters=parameters,
        )


def test_generated_dispatch_withholds_practical_case_claim() -> None:
    summary = pd.read_csv(ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv")

    assert summary["practical_case_dispatch_claim_permitted"].eq(False).all()
    demand_cases = summary["demand_mwh"].gt(0)
    assert (
        summary.loc[demand_cases, "demand_input_status"]
        .eq("constant_reported_bound_not_measured_trace")
        .all()
    )
    assert summary["residual_source_rejection_mwh"].gt(0).all()
    assert summary["maximum_absolute_thermal_balance_error_mwh"].max() < 1e-9
