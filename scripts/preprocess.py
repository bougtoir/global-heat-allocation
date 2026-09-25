"""Build the canonical analysis cube from immutable raw inputs."""

from __future__ import annotations

import os
from pathlib import Path

import netCDF4
import numpy as np

from global_heat_allocation.config import load_config
from global_heat_allocation.metrics import (
    human_burden,
    humidex,
    marginal_human_burden_per_gj,
    relative_humidity_percent,
    stress_excess,
    wet_bulb_stull,
)
from global_heat_allocation.physics import (
    atmospheric_heat_capacity_j_per_k,
    grid_cell_area_m2,
)
from global_heat_allocation.preprocessing import aggregate_population_to_grid

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
INPUTS = {
    "air": RAW / "ncep_reanalysis_1" / "2023" / "air.2m.gauss.2023.nc",
    "shum": RAW / "ncep_reanalysis_1" / "2023" / "shum.2m.gauss.2023.nc",
    "pres": RAW / "ncep_reanalysis_1" / "2023" / "pres.sfc.gauss.2023.nc",
    "uwnd": RAW / "ncep_reanalysis_1" / "2023" / "uwnd.10m.gauss.2023.nc",
    "vwnd": RAW / "ncep_reanalysis_1" / "2023" / "vwnd.10m.gauss.2023.nc",
    "dswrf": RAW / "ncep_reanalysis_1" / "2023" / "dswrf.sfc.gauss.2023.nc",
    "dlwrf": RAW / "ncep_reanalysis_1" / "2023" / "dlwrf.sfc.gauss.2023.nc",
    "uswrf": RAW / "ncep_reanalysis_1" / "2023" / "uswrf.sfc.gauss.2023.nc",
    "ulwrf": RAW / "ncep_reanalysis_1" / "2023" / "ulwrf.sfc.gauss.2023.nc",
    "icec": RAW / "ncep_reanalysis_1" / "2023" / "icec.sfc.gauss.2023.nc",
    "weasd": RAW / "ncep_reanalysis_1" / "2023" / "weasd.sfc.gauss.2023.nc",
    "land": RAW / "ncep_reanalysis_1" / "invariant" / "land.sfc.gauss.nc",
}
POPULATION = RAW / "worldpop" / "2020" / "ppp_2020_1km_Aggregated.tif"


def _copy_coordinate(
    source: netCDF4.Dataset,
    target: netCDF4.Dataset,
    name: str,
) -> None:
    source_variable = source.variables[name]
    target_variable = target.createVariable(name, source_variable.dtype, (name,))
    target_variable.setncatts(source_variable.__dict__)
    target_variable[:] = source_variable[:]


def _create_dynamic_variable(
    dataset: netCDF4.Dataset,
    name: str,
    units: str,
    long_name: str,
    dtype: str = "f4",
) -> netCDF4.Variable:
    latitude_cells = dataset.dimensions["lat"].size
    longitude_cells = dataset.dimensions["lon"].size
    variable = dataset.createVariable(
        name,
        dtype,
        ("time", "lat", "lon"),
        compression="zlib",
        complevel=4,
        chunksizes=(16, latitude_cells, longitude_cells),
    )
    variable.units = units
    variable.long_name = long_name
    return variable


def _read_chunk(
    dataset: netCDF4.Dataset,
    variable: str,
    start: int,
    end: int,
) -> np.ndarray:
    values = dataset.variables[variable][start:end]
    if np.ma.isMaskedArray(values):
        return values.filled(np.nan).astype(np.float64)
    return np.asarray(values, dtype=np.float64)


def main() -> None:
    config = load_config(ROOT / "config" / "model.yml")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    temporary.unlink(missing_ok=True)

    inputs = {name: netCDF4.Dataset(path, "r") for name, path in INPUTS.items()}
    try:
        reference = inputs["air"]
        latitude = np.asarray(reference.variables["lat"][:], dtype=np.float64)
        longitude = np.asarray(reference.variables["lon"][:], dtype=np.float64)
        time_steps = reference.dimensions["time"].size
        for name, dataset in inputs.items():
            if name == "land":
                continue
            np.testing.assert_array_equal(dataset.variables["lat"][:], latitude)
            np.testing.assert_array_equal(dataset.variables["lon"][:], longitude)
            np.testing.assert_array_equal(
                dataset.variables["time"][:],
                reference.variables["time"][:],
            )

        area = grid_cell_area_m2(latitude, longitude)
        energy = config["energy"]
        heat_capacity = atmospheric_heat_capacity_j_per_k(
            area,
            mixing_height_m=float(energy["atmospheric_mixing_height_m"]),
            air_density_kg_m3=float(energy["air_density_kg_m3"]),
            air_heat_capacity_j_kg_k=float(energy["air_heat_capacity_j_kg_k"]),
        )
        population = aggregate_population_to_grid(
            POPULATION,
            latitude,
            longitude,
        )
        land = _read_chunk(inputs["land"], "land", 0, 1)[0]
        stress_config = config["stress"]
        reference_temperature = float(stress_config["reference_temperature_c"])
        curvature = float(stress_config["curvature"])

        with netCDF4.Dataset(temporary, "w", format="NETCDF4") as output:
            output.title = "Canonical heat-allocation analysis cube"
            output.source = (
                "NCEP/NCAR Reanalysis 1 (2023) and WorldPop population (2020)"
            )
            output.heat_conservation_scope = (
                "Relocation conserves energy unless a separate radiative-loss "
                "experiment is explicitly identified."
            )
            output.createDimension("time", time_steps)
            output.createDimension("lat", latitude.size)
            output.createDimension("lon", longitude.size)
            _copy_coordinate(reference, output, "time")
            _copy_coordinate(reference, output, "lat")
            _copy_coordinate(reference, output, "lon")

            static_specs = {
                "cell_area_m2": (area, "m2", "Grid-cell surface area"),
                "population": (
                    population,
                    "people",
                    "WorldPop 2020 population count aggregated to grid",
                ),
                "atmospheric_heat_capacity_j_per_k": (
                    heat_capacity,
                    "J K-1",
                    "Configured atmospheric control-volume heat capacity",
                ),
                "land_fraction": (land, "1", "NCEP land-sea mask"),
                "polar_mask": (
                    np.broadcast_to(
                        np.abs(latitude[:, np.newaxis])
                        >= float(config["safety"]["polar_latitude_threshold_degrees"]),
                        area.shape,
                    ),
                    "1",
                    "Latitude-based polar diagnostic mask",
                ),
            }
            for name, (values, units, long_name) in static_specs.items():
                dtype = "i1" if values.dtype == np.bool_ else "f8"
                variable = output.createVariable(
                    name,
                    dtype,
                    ("lat", "lon"),
                    compression="zlib",
                    complevel=4,
                )
                variable.units = units
                variable.long_name = long_name
                variable[:, :] = values

            dynamic_specs = {
                "air_temperature_c": ("degree_Celsius", "2 m air temperature"),
                "specific_humidity": ("kg kg-1", "2 m specific humidity"),
                "surface_pressure": ("Pa", "Surface pressure"),
                "relative_humidity": ("percent", "Derived relative humidity"),
                "humidex": ("1", "Humidex thermal-stress index"),
                "wet_bulb_temperature_c": (
                    "degree_Celsius",
                    "Stull approximate wet-bulb temperature",
                ),
                "wind_speed_10m": ("m s-1", "10 m wind speed"),
                "net_surface_radiation": (
                    "W m-2",
                    "Downward minus upward surface radiative flux",
                ),
                "sea_ice_fraction": ("1", "Sea-ice concentration"),
                "snow_water_equivalent": ("kg m-2", "Snow water equivalent"),
                "stress_excess": ("1", "Humidex excess above reference"),
                "human_burden": (
                    "people index2",
                    "Population-weighted convex Humidex burden",
                ),
                "marginal_human_burden_per_gj": (
                    "people index GJ-1",
                    "Marginal burden of one GJ added to the control volume",
                ),
                "cryosphere_mask": ("1", "Sea-ice or snow safety mask"),
                "primary_sink_eligible": (
                    "1",
                    "Land, non-cryosphere primary sink eligibility",
                ),
                "source_eligible": (
                    "1",
                    "Populated land cell with positive Humidex stress",
                ),
            }
            output_variables = {
                name: _create_dynamic_variable(
                    output,
                    name,
                    units,
                    long_name,
                    dtype=(
                        "i1"
                        if name.endswith("_mask") or name.endswith("_eligible")
                        else "f4"
                    ),
                )
                for name, (units, long_name) in dynamic_specs.items()
            }

            for start in range(0, time_steps, 32):
                end = min(start + 32, time_steps)
                air_c = _read_chunk(inputs["air"], "air", start, end) - 273.15
                specific_humidity = _read_chunk(inputs["shum"], "shum", start, end)
                pressure = _read_chunk(inputs["pres"], "pres", start, end)
                relative_humidity = relative_humidity_percent(
                    air_c,
                    specific_humidity,
                    pressure,
                )
                humidex_values = humidex(air_c, specific_humidity, pressure)
                stress = stress_excess(humidex_values, reference_temperature)
                ice = _read_chunk(inputs["icec"], "icec", start, end)
                snow = _read_chunk(inputs["weasd"], "weasd", start, end)
                cryosphere = (ice >= 0.15) | (snow >= 1.0)
                land_dynamic = land[np.newaxis, :, :]
                population_dynamic = population[np.newaxis, :, :]
                sink_eligible = (land_dynamic >= 0.5) & ~cryosphere
                source_eligible = (
                    (land_dynamic >= 0.5) & (population_dynamic > 0.0) & (stress > 0.0)
                )
                burden = human_burden(stress, population_dynamic, curvature)
                marginal = marginal_human_burden_per_gj(
                    stress,
                    population_dynamic,
                    curvature,
                    heat_capacity[np.newaxis, :, :],
                )
                eastward = _read_chunk(inputs["uwnd"], "uwnd", start, end)
                northward = _read_chunk(inputs["vwnd"], "vwnd", start, end)
                downward_shortwave = _read_chunk(
                    inputs["dswrf"],
                    "dswrf",
                    start,
                    end,
                )
                downward_longwave = _read_chunk(
                    inputs["dlwrf"],
                    "dlwrf",
                    start,
                    end,
                )
                upward_shortwave = _read_chunk(
                    inputs["uswrf"],
                    "uswrf",
                    start,
                    end,
                )
                upward_longwave = _read_chunk(
                    inputs["ulwrf"],
                    "ulwrf",
                    start,
                    end,
                )
                values = {
                    "air_temperature_c": air_c,
                    "specific_humidity": specific_humidity,
                    "surface_pressure": pressure,
                    "relative_humidity": relative_humidity,
                    "humidex": humidex_values,
                    "wet_bulb_temperature_c": wet_bulb_stull(
                        air_c,
                        relative_humidity,
                    ),
                    "wind_speed_10m": np.hypot(eastward, northward),
                    "net_surface_radiation": (
                        downward_shortwave
                        + downward_longwave
                        - upward_shortwave
                        - upward_longwave
                    ),
                    "sea_ice_fraction": ice,
                    "snow_water_equivalent": snow,
                    "stress_excess": stress,
                    "human_burden": burden,
                    "marginal_human_burden_per_gj": marginal,
                    "cryosphere_mask": cryosphere,
                    "primary_sink_eligible": sink_eligible,
                    "source_eligible": source_eligible,
                }
                for name, chunk in values.items():
                    output_variables[name][start:end] = chunk
                print(f"Processed time steps {start}:{end}.")
        os.replace(temporary, OUTPUT)
    finally:
        for dataset in inputs.values():
            dataset.close()


if __name__ == "__main__":
    main()
