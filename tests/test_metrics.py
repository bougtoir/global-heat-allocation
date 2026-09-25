import numpy as np

from global_heat_allocation.metrics import (
    human_burden,
    humidex,
    marginal_human_burden_per_gj,
    relative_humidity_percent,
    stress_excess,
    vapor_pressure_hpa,
    wet_bulb_stull,
)


def test_vapor_pressure_and_humidex_are_consistent() -> None:
    temperature = np.array([30.0])
    humidity = np.array([0.015])
    pressure = np.array([101325.0])
    vapor_pressure = vapor_pressure_hpa(humidity, pressure)
    expected_humidex = temperature + (5.0 / 9.0) * (vapor_pressure - 10.0)
    np.testing.assert_allclose(
        humidex(temperature, humidity, pressure),
        expected_humidex,
    )
    relative_humidity = relative_humidity_percent(
        temperature,
        humidity,
        pressure,
    )
    assert 0.0 < relative_humidity[0] < 100.0


def test_wet_bulb_proxy_masks_values_outside_validation_domain() -> None:
    values = wet_bulb_stull(
        np.array([-30.0, 30.0]),
        np.array([50.0, 70.0]),
    )
    assert np.isnan(values[0])
    assert np.isfinite(values[1])


def test_burden_and_marginal_burden_are_zero_below_threshold() -> None:
    stress = stress_excess(np.array([25.0, 30.0]), reference=26.0)
    population = np.array([100.0, 100.0])
    burden = human_burden(stress, population, curvature=2.0)
    marginal = marginal_human_burden_per_gj(
        stress,
        population,
        curvature=2.0,
        heat_capacity_j_per_k=np.array([1.0e12, 1.0e12]),
    )
    np.testing.assert_allclose(burden, np.array([0.0, 1600.0]))
    np.testing.assert_allclose(marginal, np.array([0.0, 0.8]))
