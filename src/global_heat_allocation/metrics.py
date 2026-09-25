"""Thermodynamic and human-burden metrics."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


def vapor_pressure_hpa(
    specific_humidity: ArrayLike,
    pressure_pa: ArrayLike,
) -> FloatArray:
    """Convert specific humidity and pressure to water-vapor pressure."""
    humidity = np.asarray(specific_humidity, dtype=np.float64)
    pressure = np.asarray(pressure_pa, dtype=np.float64)
    epsilon = 0.622
    return humidity * pressure / (epsilon + (1.0 - epsilon) * humidity) / 100.0


def saturation_vapor_pressure_hpa(temperature_c: ArrayLike) -> FloatArray:
    """Return saturation vapor pressure using the Bolton approximation."""
    temperature = np.asarray(temperature_c, dtype=np.float64)
    return 6.112 * np.exp(17.67 * temperature / (temperature + 243.5))


def relative_humidity_percent(
    temperature_c: ArrayLike,
    specific_humidity: ArrayLike,
    pressure_pa: ArrayLike,
) -> FloatArray:
    """Derive bounded relative humidity from temperature, humidity, and pressure."""
    vapor_pressure = vapor_pressure_hpa(specific_humidity, pressure_pa)
    saturation = saturation_vapor_pressure_hpa(temperature_c)
    return np.clip(100.0 * vapor_pressure / saturation, 0.0, 100.0)


def humidex(
    temperature_c: ArrayLike,
    specific_humidity: ArrayLike,
    pressure_pa: ArrayLike,
) -> FloatArray:
    """Calculate Humidex from air temperature and water-vapor pressure."""
    temperature = np.asarray(temperature_c, dtype=np.float64)
    vapor_pressure = vapor_pressure_hpa(specific_humidity, pressure_pa)
    return temperature + (5.0 / 9.0) * (vapor_pressure - 10.0)


def wet_bulb_stull(
    temperature_c: ArrayLike,
    relative_humidity: ArrayLike,
) -> FloatArray:
    """Approximate wet-bulb temperature using Stull's empirical equation."""
    temperature = np.asarray(temperature_c, dtype=np.float64)
    humidity = np.asarray(relative_humidity, dtype=np.float64)
    estimate = (
        temperature * np.arctan(0.151977 * np.sqrt(humidity + 8.313659))
        + np.arctan(temperature + humidity)
        - np.arctan(humidity - 1.676331)
        + 0.00391838 * humidity**1.5 * np.arctan(0.023101 * humidity)
        - 4.686035
    )
    valid = (
        (temperature >= -20.0)
        & (temperature <= 50.0)
        & (humidity >= 5.0)
        & (humidity <= 99.0)
    )
    return np.where(valid, estimate, np.nan)


def stress_excess(
    metric: ArrayLike,
    reference: float,
) -> FloatArray:
    """Return nonnegative thermal-stress excess above a reference."""
    values = np.asarray(metric, dtype=np.float64)
    return np.maximum(values - reference, 0.0)


def human_burden(
    stress: ArrayLike,
    population: ArrayLike,
    curvature: float,
) -> FloatArray:
    """Return population-weighted convex thermal burden."""
    stress_values = np.asarray(stress, dtype=np.float64)
    population_values = np.asarray(population, dtype=np.float64)
    return population_values * stress_values**curvature


def marginal_human_burden_per_gj(
    stress: ArrayLike,
    population: ArrayLike,
    curvature: float,
    heat_capacity_j_per_k: ArrayLike,
) -> FloatArray:
    """Return the marginal burden of adding one GJ to a control volume."""
    stress_values = np.asarray(stress, dtype=np.float64)
    population_values = np.asarray(population, dtype=np.float64)
    heat_capacity = np.asarray(heat_capacity_j_per_k, dtype=np.float64)
    if curvature < 1.0:
        raise ValueError("Curvature must be at least one.")
    return np.where(
        stress_values > 0.0,
        population_values
        * curvature
        * stress_values ** (curvature - 1.0)
        * 1.0e9
        / heat_capacity,
        0.0,
    )
