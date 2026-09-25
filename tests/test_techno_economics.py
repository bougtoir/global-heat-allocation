import math

import pytest

from global_heat_allocation.techno_economics import (
    MMBTU_PER_MWH,
    conventional_steam_balance,
    heat_recovery_balance,
    natural_gas_co2e_kg_per_mmbtu,
    replacement_present_value,
    uniform_present_value_factor,
)


def test_heat_recovery_balance_counts_cop_electricity_once() -> None:
    balance = heat_recovery_balance(
        useful_heat_delivered_mwh=1.0,
        cop=4.0,
    )

    assert math.isclose(balance.heat_pump_output_mwh, 1.0)
    assert math.isclose(balance.heat_pump_electricity_mwh, 0.25)
    assert math.isclose(balance.source_heat_withdrawn_mwh, 0.75)
    assert math.isclose(balance.source_heat_recovered_mwh, 0.75)
    assert math.isclose(balance.source_side_loss_mwh, 0.0)
    assert math.isclose(balance.total_electricity_mwh, 0.25)
    assert math.isclose(balance.thermal_balance_error_mwh, 0.0, abs_tol=1e-12)


def test_heat_recovery_balance_preserves_losses_and_auxiliaries() -> None:
    balance = heat_recovery_balance(
        useful_heat_delivered_mwh=1.0,
        cop=3.0,
        source_capture_efficiency=0.9,
        storage_roundtrip_efficiency=0.98,
        storage_standing_loss_fraction=0.01,
        storage_auxiliary_fraction=0.004,
        transport_loss_fraction=0.1,
        transport_pumping_fraction=0.02,
    )

    assert balance.source_side_loss_mwh > 0
    assert balance.storage_loss_mwh > 0
    assert balance.transport_loss_mwh > 0
    assert math.isclose(
        balance.total_electricity_mwh,
        balance.heat_pump_electricity_mwh
        + balance.storage_auxiliary_electricity_mwh
        + balance.transport_pumping_electricity_mwh,
    )
    assert math.isclose(balance.thermal_balance_error_mwh, 0.0, abs_tol=1e-12)


def test_conventional_steam_balance_accounts_for_boiler_and_delivery_losses() -> None:
    balance = conventional_steam_balance(
        useful_heat_delivered_mwh=1.0,
        boiler_efficiency=0.82,
        delivery_loss_fraction=0.08,
    )

    assert math.isclose(balance.boiler_heat_output_mwh, 1 / 0.92)
    assert math.isclose(balance.natural_gas_input_mwh_hhv, 1 / 0.92 / 0.82)
    assert math.isclose(balance.steam_delivery_loss_mwh, 1 / 0.92 - 1)


def test_discounting_and_replacement_are_explicit() -> None:
    assert math.isclose(
        uniform_present_value_factor(0.03, 3),
        sum(1 / 1.03**year for year in range(1, 4)),
    )
    assert math.isclose(
        replacement_present_value(
            initial_cost=100.0,
            component_lifetime_years=10,
            study_period_years=25,
            discount_rate=0.05,
        ),
        100 / 1.05**10 + 100 / 1.05**20,
    )


def test_natural_gas_co2e_includes_non_co2_gases() -> None:
    factor = natural_gas_co2e_kg_per_mmbtu(
        co2_kg_per_mmbtu=53.06,
        ch4_g_per_mmbtu=1.0,
        n2o_g_per_mmbtu=0.1,
        ch4_gwp=28.0,
        n2o_gwp=265.0,
    )

    assert math.isclose(factor, 53.1145)
    assert factor * MMBTU_PER_MWH > 53.06 * MMBTU_PER_MWH


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cop", 1.0),
        ("source_capture_efficiency", 0.0),
        ("storage_roundtrip_efficiency", 0.0),
        ("transport_loss_fraction", 1.0),
    ],
)
def test_heat_recovery_balance_rejects_invalid_inputs(
    field: str,
    value: float,
) -> None:
    arguments = {
        "useful_heat_delivered_mwh": 1.0,
        "cop": 3.0,
        "source_capture_efficiency": 1.0,
        "storage_roundtrip_efficiency": 1.0,
        "transport_loss_fraction": 0.0,
    }
    arguments[field] = value

    with pytest.raises(ValueError):
        heat_recovery_balance(**arguments)
