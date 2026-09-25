"""Run prespecified structural replications of the global screening model."""

from __future__ import annotations

import os
from contextlib import ExitStack
from pathlib import Path

import geopandas as gpd
import netCDF4
import numpy as np
import pandas as pd
import yaml
from shapely.geometry import Point

from global_heat_allocation.config import load_config
from global_heat_allocation.metrics import (
    humidex,
    marginal_human_burden_per_gj,
    relative_humidity_percent,
    stress_excess,
    wet_bulb_stull,
)
from global_heat_allocation.physics import (
    atmospheric_heat_capacity_j_per_k,
    great_circle_distance_km,
    grid_cell_area_m2,
)
from global_heat_allocation.preprocessing import aggregate_population_to_grid
from global_heat_allocation.structural_replication import (
    coarsen_any,
    coarsen_area_weighted,
    coarsen_coordinates,
    coarsen_sum,
    summarize_structural_scenario,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "structural_replication.yml"
MODEL_CONFIG_PATH = ROOT / "config" / "model.yml"
COUNTRIES = (
    ROOT / "data" / "raw" / "natural_earth" / "5.1.2" / "ne_110m_admin_0_countries.zip"
)
OUTPUT = ROOT / "results" / "tables" / "structural_replication.csv"
DOCUMENT = ROOT / "docs" / "STRUCTURAL_UNCERTAINTY.md"


def _read_config() -> dict[str, object]:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("Structural-replication configuration must be a mapping.")
    return loaded


def _filled(values: np.ndarray) -> np.ndarray:
    if np.ma.isMaskedArray(values):
        return values.filled(np.nan).astype(np.float64)
    return np.asarray(values, dtype=np.float64)


def _climate_paths(dataset: dict[str, object]) -> dict[str, Path]:
    year = int(dataset["year"])
    base = ROOT / str(dataset["base_directory"])
    return {
        "air": base / f"air.2m.gauss.{year}.nc",
        "shum": base / f"shum.2m.gauss.{year}.nc",
        "pres": base / f"pres.sfc.gauss.{year}.nc",
        "icec": base / f"icec.sfc.gauss.{year}.nc",
        "weasd": base / f"weasd.sfc.gauss.{year}.nc",
        "land": ROOT / str(dataset["land_path"]),
    }


def _read_grid(dataset: dict[str, object]) -> tuple[np.ndarray, np.ndarray]:
    air_path = _climate_paths(dataset)["air"]
    with netCDF4.Dataset(air_path) as source:
        return (
            _filled(source.variables["lat"][:]),
            _filled(source.variables["lon"][:]),
        )


def _read_climate(
    dataset: dict[str, object],
) -> tuple[
    np.ndarray,
    np.ndarray,
    list[str],
    dict[str, np.ndarray],
]:
    paths = _climate_paths(dataset)
    with ExitStack() as stack:
        inputs = {
            name: stack.enter_context(netCDF4.Dataset(path))
            for name, path in paths.items()
        }
        reference = inputs["air"]
        latitude = _filled(reference.variables["lat"][:])
        longitude = _filled(reference.variables["lon"][:])
        raw_time = _filled(reference.variables["time"][:])
        time_variable = reference.variables["time"]
        calendar = str(time_variable.__dict__.get("calendar", "standard"))
        decoded_time = netCDF4.num2date(
            raw_time,
            units=str(time_variable.units),
            calendar=calendar,
            only_use_cftime_datetimes=False,
        )
        time_iso = [value.isoformat() for value in decoded_time]

        arrays: dict[str, np.ndarray] = {}
        for name, variable_name in {
            "air": "air",
            "shum": "shum",
            "pres": "pres",
            "icec": "icec",
            "weasd": "weasd",
        }.items():
            source = inputs[name]
            np.testing.assert_allclose(source.variables["lat"][:], latitude)
            np.testing.assert_allclose(source.variables["lon"][:], longitude)
            np.testing.assert_allclose(source.variables["time"][:], raw_time)
            values = _filled(source.variables[variable_name][:])
            if values.ndim == 4 and values.shape[1] == 1:
                values = values[:, 0, :, :]
            if values.ndim != 3:
                raise ValueError(f"Unexpected dimensions for {paths[name]}.")
            arrays[name] = values
        land_source = inputs["land"]
        np.testing.assert_allclose(land_source.variables["lat"][:], latitude)
        np.testing.assert_allclose(land_source.variables["lon"][:], longitude)
        land_values = _filled(land_source.variables["land"][:])
        arrays["land"] = land_values[0] if land_values.ndim == 3 else land_values
    return latitude, longitude, time_iso, arrays


def _population_raster_path(dataset: dict[str, object]) -> str:
    if "raster_path" in dataset:
        return str(ROOT / str(dataset["raster_path"]))
    archive = ROOT / str(dataset["archive_path"])
    member = str(dataset["archive_member"])
    return f"/vsizip/{archive}/{member}"


def _metric_and_derivative(
    metric_name: str,
    air_temperature_c: np.ndarray,
    specific_humidity: np.ndarray,
    pressure_pa: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if metric_name == "humidex":
        return (
            humidex(air_temperature_c, specific_humidity, pressure_pa),
            np.ones_like(air_temperature_c),
        )
    if metric_name == "air_temperature":
        return air_temperature_c, np.ones_like(air_temperature_c)
    if metric_name != "wet_bulb_proxy":
        raise ValueError(f"Unsupported thermal metric: {metric_name}")
    relative_humidity = relative_humidity_percent(
        air_temperature_c,
        specific_humidity,
        pressure_pa,
    )
    metric = wet_bulb_stull(air_temperature_c, relative_humidity)
    perturbation_c = 0.01
    derivative = (
        wet_bulb_stull(
            air_temperature_c + perturbation_c,
            relative_humidity_percent(
                air_temperature_c + perturbation_c,
                specific_humidity,
                pressure_pa,
            ),
        )
        - wet_bulb_stull(
            air_temperature_c - perturbation_c,
            relative_humidity_percent(
                air_temperature_c - perturbation_c,
                specific_humidity,
                pressure_pa,
            ),
        )
    ) / (2.0 * perturbation_c)
    return metric, derivative


def _country_name(
    countries: gpd.GeoDataFrame,
    latitude: float,
    longitude: float,
) -> str:
    wrapped_longitude = ((longitude + 180.0) % 360.0) - 180.0
    matches = countries[countries.geometry.covers(Point(wrapped_longitude, latitude))]
    if matches.empty:
        return "Unassigned"
    return str(matches.iloc[0]["ADMIN"])


def _scenario_row(
    *,
    scenario: dict[str, object],
    climate: dict[str, object],
    population_dataset: dict[str, object],
    latitude: np.ndarray,
    longitude: np.ndarray,
    time_iso: list[str],
    arrays: dict[str, np.ndarray],
    population: np.ndarray,
    model_config: dict[str, object],
    analysis_config: dict[str, object],
    countries: gpd.GeoDataFrame,
) -> dict[str, object]:
    factor = int(scenario["spatial_coarsening_factor"])
    fine_area = grid_cell_area_m2(latitude, longitude)
    fine_cryosphere = (arrays["icec"] >= 0.15) | (arrays["weasd"] >= 1.0)

    if factor == 1:
        scenario_latitude = latitude
        scenario_longitude = longitude
        area = fine_area
        air_temperature_c = arrays["air"] - 273.15
        specific_humidity = arrays["shum"]
        pressure_pa = arrays["pres"]
        land_fraction = arrays["land"]
        cryosphere = fine_cryosphere
        scenario_population = population
    else:
        scenario_latitude, scenario_longitude = coarsen_coordinates(
            latitude,
            longitude,
            fine_area,
            factor,
        )
        area = coarsen_sum(fine_area, factor)
        air_temperature_c = (
            coarsen_area_weighted(arrays["air"], fine_area, factor) - 273.15
        )
        specific_humidity = coarsen_area_weighted(
            arrays["shum"],
            fine_area,
            factor,
        )
        pressure_pa = coarsen_area_weighted(arrays["pres"], fine_area, factor)
        land_fraction = coarsen_area_weighted(
            arrays["land"],
            fine_area,
            factor,
        )
        cryosphere = coarsen_any(fine_cryosphere, factor)
        scenario_population = coarsen_sum(population, factor)

    metric, derivative = _metric_and_derivative(
        str(scenario["metric"]),
        air_temperature_c,
        specific_humidity,
        pressure_pa,
    )
    threshold = float(scenario["threshold"])
    stress = stress_excess(metric, threshold)
    energy_config = model_config["energy"]
    stress_config = model_config["stress"]
    if not isinstance(energy_config, dict) or not isinstance(stress_config, dict):
        raise ValueError("Model energy and stress configuration must be mappings.")
    heat_capacity = atmospheric_heat_capacity_j_per_k(
        area,
        mixing_height_m=float(energy_config["atmospheric_mixing_height_m"]),
        air_density_kg_m3=float(energy_config["air_density_kg_m3"]),
        air_heat_capacity_j_kg_k=float(energy_config["air_heat_capacity_j_kg_k"]),
    )
    valid_metric = np.isfinite(metric) & np.isfinite(derivative) & (derivative > 0.0)
    land_dynamic = land_fraction[np.newaxis, :, :]
    population_dynamic = scenario_population[np.newaxis, :, :]
    source_eligible = (
        (land_dynamic >= 0.5)
        & (population_dynamic > 0.0)
        & (stress > 0.0)
        & valid_metric
    )
    sink_eligible = (land_dynamic >= 0.5) & ~cryosphere & valid_metric
    marginal = (
        marginal_human_burden_per_gj(
            stress,
            population_dynamic,
            float(stress_config["curvature"]),
            heat_capacity[np.newaxis, :, :],
        )
        * derivative
    )
    marginal[~valid_metric] = np.nan

    summary = summarize_structural_scenario(
        marginal_burden_per_gj=marginal,
        source_eligible=source_eligible,
        sink_eligible=sink_eligible,
        population=scenario_population,
        land_fraction=land_fraction,
        cryosphere_mask=cryosphere,
        latitude=scenario_latitude,
        longitude=scenario_longitude,
        maximum_distance_km=float(analysis_config["maximum_distance_km"]),
        maximum_temporal_lag_steps=int(analysis_config["maximum_temporal_lag_steps"]),
        near_optimal_fraction=float(analysis_config["near_optimal_fraction"]),
        high_transport_penalty_burden_per_gj_km=float(
            analysis_config["high_transport_penalty_burden_per_gj_km"]
        ),
    )
    source_time_index = int(summary["source_time_index"])
    temporal_sink_time_index = int(summary["temporal_sink_time_index"])
    source_latitude = float(summary["source_latitude"])
    source_longitude = float(summary["source_longitude"])
    zero_sink_latitude = float(summary["spatial_zero_penalty_sink_latitude"])
    zero_sink_longitude = float(summary["spatial_zero_penalty_sink_longitude"])
    high_sink_latitude = float(summary["spatial_high_penalty_sink_latitude"])
    high_sink_longitude = float(summary["spatial_high_penalty_sink_longitude"])
    return {
        "scenario_id": str(scenario["scenario_id"]),
        "climate_product": str(climate["product"]),
        "climate_year": int(climate["year"]),
        "population_product": str(population_dataset["product"]),
        "population_year": int(population_dataset["year"]),
        "spatial_coarsening_factor": factor,
        "grid_latitude_count": int(scenario_latitude.size),
        "grid_longitude_count": int(scenario_longitude.size),
        "time_step_hours": 6,
        "time_step_count": int(marginal.shape[0]),
        "thermal_metric": str(scenario["metric"]),
        "metric_threshold": threshold,
        "population_total": float(scenario_population.sum()),
        "source_time": time_iso[source_time_index],
        "temporal_sink_time": (
            time_iso[temporal_sink_time_index] if temporal_sink_time_index >= 0 else ""
        ),
        "source_country": _country_name(
            countries,
            source_latitude,
            source_longitude,
        ),
        "spatial_zero_penalty_sink_country": _country_name(
            countries,
            zero_sink_latitude,
            zero_sink_longitude,
        ),
        "spatial_high_penalty_sink_country": _country_name(
            countries,
            high_sink_latitude,
            high_sink_longitude,
        ),
        "high_transport_penalty_burden_per_gj_km": float(
            analysis_config["high_transport_penalty_burden_per_gj_km"]
        ),
        "practical_external_ambient_relocation_admissible": False,
        "practical_constraint_interpretation": (
            "Phase E excludes new external ambient relocation without "
            "site-specific receiving-capacity evidence."
        ),
        **summary,
    }


def _add_geographic_shifts(rows: list[dict[str, object]]) -> None:
    canonical = next(
        row
        for row in rows
        if row["scenario_id"] == "ncep1_2023_worldpop_native_humidex"
    )
    for row in rows:
        row["source_shift_km_from_canonical"] = float(
            great_circle_distance_km(
                float(canonical["source_latitude"]),
                float(canonical["source_longitude"]),
                float(row["source_latitude"]),
                float(row["source_longitude"]),
            )
        )
        row["zero_penalty_sink_shift_km_from_canonical"] = float(
            great_circle_distance_km(
                float(canonical["spatial_zero_penalty_sink_latitude"]),
                float(canonical["spatial_zero_penalty_sink_longitude"]),
                float(row["spatial_zero_penalty_sink_latitude"]),
                float(row["spatial_zero_penalty_sink_longitude"]),
            )
        )


def _format_number(value: float) -> str:
    return f"{value:,.3g}"


def _write_document(rows: list[dict[str, object]]) -> None:
    frame = pd.DataFrame(rows)
    year_rows = frame[
        (frame["climate_product"] == "NCEP/NCAR Reanalysis 1")
        & (frame["population_product"] == "WorldPop unconstrained")
        & (frame["spatial_coarsening_factor"] == 1)
        & (frame["thermal_metric"] == "humidex")
    ]
    positive_spatial = int(frame["theoretical_spatial_value_positive"].sum())
    nonunique = int(frame["sink_nonunique_within_tolerance"].sum())
    pathological = int(frame["unrestricted_pathological_sinks_present"].sum())
    temporal_positive = int((frame["temporal_net_benefit_per_gj"] > 0.0).sum())
    penalty_collapse = int(frame["spatial_value_collapses_at_high_penalty"].sum())
    finite_temporal_ratios = (
        frame["temporal_to_spatial_value_ratio"]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .dropna()
    )
    source_countries = sorted(set(frame["source_country"]))
    sink_countries = sorted(set(frame["spatial_zero_penalty_sink_country"]))
    maximum_source_shift = float(frame["source_shift_km_from_canonical"].max())
    maximum_sink_shift = float(frame["zero_penalty_sink_shift_km_from_canonical"].max())

    lines = [
        "# Structural uncertainty and global replication",
        "",
        "## Purpose",
        "",
        (
            "This phase tests whether the model's structural conclusions survive "
            "prespecified changes in year, reanalysis, population product, spatial "
            "resolution, and thermal metric. It does not seek replication of exact "
            "source or sink countries."
        ),
        "",
        "## Prespecified design",
        "",
        (
            "- Years: 2010, 2015, 2020, and the canonical 2023, selected before "
            "running this phase as five-year intervals plus the canonical year."
        ),
        (
            "- Reanalyses: NCEP/NCAR Reanalysis 1 and the anonymously accessible "
            "NCEP-DOE Reanalysis 2."
        ),
        (
            "- Population: WorldPop 2020 unconstrained and GHS-POP R2023A 2020 "
            "resident-population grids."
        ),
        (
            "- Resolution: the native 94 x 192 Gaussian grid and a conservative "
            "2 x 2 aggregation to 47 x 96."
        ),
        (
            "- Metrics: Humidex, air temperature, and the Stull wet-bulb proxy. "
            "Thresholds are model scenarios, not clinical outcome thresholds."
        ),
        "",
        "## Structural findings",
        "",
        (
            f"- Marginal-burden heterogeneity persists: the positive-cell "
            f"p99/p50 ratio ranges from "
            f"{_format_number(float(frame['marginal_p99_to_p50_ratio'].min()))} "
            f"to {_format_number(float(frame['marginal_p99_to_p50_ratio'].max()))} "
            "across the prespecified scenarios."
        ),
        (
            f"- Positive constrained theoretical spatial value occurs in "
            f"{positive_spatial} of {len(frame)} scenarios."
        ),
        (
            f"- Sink non-uniqueness occurs in {nonunique} of {len(frame)} "
            "scenarios using the prespecified one-percent near-optimal tolerance."
        ),
        (
            f"- Unrestricted minimum-burden sink sets contain ocean or cryosphere "
            f"cells in {pathological} of {len(frame)} scenarios, confirming that "
            "an unconstrained mathematical sink is not an environmental approval."
        ),
        (
            f"- Positive same-location temporal value occurs in {temporal_positive} "
            f"of {len(frame)} scenarios."
        ),
        (
            (
                "- Where both values are defined, temporal/spatial value ratios "
                f"range from {_format_number(float(finite_temporal_ratios.min()))} "
                f"to {_format_number(float(finite_temporal_ratios.max()))}."
            )
            if not finite_temporal_ratios.empty
            else "- No finite temporal/spatial value ratio was available."
        ),
        (
            f"- The configured high burden-space transport penalty makes the best "
            f"matched-event spatial move non-positive in {penalty_collapse} of "
            f"{len(frame)} scenarios. This is a sensitivity result, not a monetary "
            "cost estimate."
        ),
        (
            "- Under the Phase E environmental model, new external ambient "
            "relocation remains inadmissible in every scenario without "
            "site-specific receiving-capacity evidence; therefore theoretical "
            "spatial value does not become a practical recommendation."
        ),
        "",
        "## Geographic instability",
        "",
        (
            f"Peak source countries across scenarios: {', '.join(source_countries)}. "
            f"Zero-penalty sink countries: {', '.join(sink_countries)}."
        ),
        (
            f"Source locations shift by as much as "
            f"{_format_number(maximum_source_shift)} "
            f"km and selected zero-penalty sinks by as much as "
            f"{_format_number(maximum_sink_shift)} "
            "km relative to the canonical configuration. Exact Bangladesh, Russia, "
            "or Bhutan identities are not structurally replicated claims."
        ),
        "",
        "## Scenario results",
        "",
        (
            "| Scenario | p99/p50 | Spatial value | Near-optimal sinks | "
            "Temporal/spatial | High-penalty value | Source | Sink |"
        ),
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["scenario_id"]),
                    _format_number(float(row["marginal_p99_to_p50_ratio"])),
                    _format_number(
                        float(row["spatial_zero_penalty_net_benefit_per_gj"])
                    ),
                    str(row["spatial_near_optimal_sink_count"]),
                    _format_number(float(row["temporal_to_spatial_value_ratio"])),
                    _format_number(
                        float(row["spatial_high_penalty_net_benefit_per_gj"])
                    ),
                    str(row["source_country"]),
                    str(row["spatial_zero_penalty_sink_country"]),
                ]
            )
            + " |"
        )
    year_source_shift = float(year_rows["source_shift_km_from_canonical"].max())
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                f"The year-only replications move the peak source by up to "
                f"{_format_number(year_source_shift)} km. The robust result is the "
                "existence of sharp marginal heterogeneity and conditional positive "
                "allocation value, not a stable country pair."
            ),
            "",
            "## Limitations",
            "",
            (
                "- NCEP-DOE Reanalysis 2 is an official alternative reanalysis but "
                "shares lineage and the T62 Gaussian grid with Reanalysis 1; this is "
                "not an independent modern high-resolution ERA5 replication."
            ),
            (
                "- The alternative-resolution test is aggregation of the same "
                "meteorology, not an independently simulated native coarse product."
            ),
            (
                "- WorldPop and GHSL differ in source data and allocation methods; "
                "their comparison tests population representation, not population "
                "measurement truth."
            ),
            (
                "- The wet-bulb calculation is the Stull proxy and excludes cells "
                "outside its valid temperature-humidity domain."
            ),
            (
                "- Burden units are model-index units, not mortality, morbidity, "
                "welfare, or currency."
            ),
            (
                "- The burden-space transport penalty cannot be converted to project "
                "cost without an unsupported burden-to-money conversion."
            ),
            (
                "- Phase E exclusions prevent unsupported practical sink claims but "
                "do not estimate site-specific environmental receiving capacity."
            ),
            "",
            "## Reproducibility",
            "",
            (
                "Run `python scripts/download_data.py`, "
                "`python scripts/validate_data.py`, and "
                "`python scripts/run_structural_replication.py` from the project "
                "environment. The machine-readable result table is "
                "`results/tables/structural_replication.csv`."
            ),
            "",
            "The project remains **NO-GO** for submission: structural replication "
            "does not close the finite-dispatch or real-case evidence gates.",
            "",
        ]
    )
    DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
    temporary = DOCUMENT.with_name(f".{DOCUMENT.name}.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, DOCUMENT)


def main() -> None:
    structural_config = _read_config()
    model_config = load_config(MODEL_CONFIG_PATH)
    climates = structural_config["climate_datasets"]
    populations = structural_config["population_datasets"]
    scenarios = structural_config["scenarios"]
    analysis_config = structural_config["analysis"]
    if (
        not isinstance(climates, dict)
        or not isinstance(populations, dict)
        or not isinstance(scenarios, list)
        or not isinstance(analysis_config, dict)
    ):
        raise ValueError("Invalid structural-replication configuration.")

    countries = gpd.read_file(f"zip://{COUNTRIES}")[["ADMIN", "geometry"]]
    canonical_climate = climates["ncep1_2023"]
    if not isinstance(canonical_climate, dict):
        raise ValueError("Canonical climate configuration must be a mapping.")
    reference_latitude, reference_longitude = _read_grid(canonical_climate)
    population_cache: dict[str, np.ndarray] = {}
    for population_key, population_value in populations.items():
        if not isinstance(population_value, dict):
            raise ValueError("Population configuration must be a mapping.")
        population_cache[str(population_key)] = aggregate_population_to_grid(
            _population_raster_path(population_value),
            reference_latitude,
            reference_longitude,
        )

    scenarios_by_climate: dict[str, list[dict[str, object]]] = {}
    for scenario_value in scenarios:
        if not isinstance(scenario_value, dict):
            raise ValueError("Each structural scenario must be a mapping.")
        climate_key = str(scenario_value["climate_dataset"])
        scenarios_by_climate.setdefault(climate_key, []).append(scenario_value)

    rows: list[dict[str, object]] = []
    for climate_key, climate_scenarios in scenarios_by_climate.items():
        climate_value = climates[climate_key]
        if not isinstance(climate_value, dict):
            raise ValueError("Climate configuration must be a mapping.")
        latitude, longitude, time_iso, arrays = _read_climate(climate_value)
        np.testing.assert_allclose(latitude, reference_latitude)
        np.testing.assert_allclose(longitude, reference_longitude)
        for scenario in climate_scenarios:
            population_key = str(scenario["population_dataset"])
            population_value = populations[population_key]
            if not isinstance(population_value, dict):
                raise ValueError("Population configuration must be a mapping.")
            row = _scenario_row(
                scenario=scenario,
                climate=climate_value,
                population_dataset=population_value,
                latitude=latitude,
                longitude=longitude,
                time_iso=time_iso,
                arrays=arrays,
                population=population_cache[population_key],
                model_config=model_config,
                analysis_config=analysis_config,
                countries=countries,
            )
            rows.append(row)
            print(f"Completed {scenario['scenario_id']}.")

    _add_geographic_shifts(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    pd.DataFrame(rows).to_csv(temporary, index=False, lineterminator="\n")
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, OUTPUT)
    _write_document(rows)
    print(f"Wrote {len(rows)} structural replication scenarios.")


if __name__ == "__main__":
    main()
