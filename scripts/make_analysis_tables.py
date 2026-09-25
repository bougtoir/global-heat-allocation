"""Generate publication tables from canonical configuration and results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from global_heat_allocation.config import load_config

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "results" / "canonical"
OUTPUT = ROOT / "results" / "tables"


def _write(frame: pd.DataFrame, name: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT / name, index=False, lineterminator="\n")


def main() -> None:
    config = load_config(ROOT / "config" / "model.yml")
    snapshots = pd.read_csv(ROOT / "data" / "metadata" / "data_snapshots.csv")
    datasets = (
        snapshots[
            snapshots["role"].isin(
                [
                    "near_surface_air_temperature",
                    "near_surface_specific_humidity",
                    "surface_pressure",
                    "eastward_wind_10m",
                    "northward_wind_10m",
                    "land_fraction",
                    "sea_ice_fraction",
                    "snow_water_equivalent",
                    "population_count",
                    "country_boundaries",
                    "downward_longwave_flux",
                    "downward_shortwave_flux",
                    "upward_longwave_flux",
                    "upward_shortwave_flux",
                ]
            )
        ][
            [
                "provider",
                "product",
                "version",
                "role",
                "license_terms",
                "completion",
            ]
        ]
        .drop_duplicates()
        .sort_values(["product", "role"])
    )
    _write(datasets, "table_1_datasets.csv")

    assumptions = [
        (
            "Canonical transferred energy",
            config["energy"]["perturbation_gj"],
            "GJ",
        ),
        (
            "Atmospheric mixing height",
            config["energy"]["atmospheric_mixing_height_m"],
            "m",
        ),
        (
            "Air density",
            config["energy"]["air_density_kg_m3"],
            "kg m-3",
        ),
        (
            "Air heat capacity",
            config["energy"]["air_heat_capacity_j_kg_k"],
            "J kg-1 K-1",
        ),
        (
            "Humidex reference",
            config["stress"]["reference_temperature_c"],
            "degrees C equivalent",
        ),
        ("Burden curvature", config["stress"]["curvature"], "dimensionless"),
        (
            "Maximum transfer distance",
            config["optimization"]["maximum_candidate_distance_km"],
            "km",
        ),
        (
            "Local heat-load cap",
            config["optimization"]["local_load_cap_gj"],
            "GJ",
        ),
        (
            "Maximum local temperature perturbation",
            config["safety"]["maximum_local_delta_temperature_k"],
            "K",
        ),
    ]
    _write(
        pd.DataFrame(assumptions, columns=["assumption", "value", "unit"]),
        "table_2_model_assumptions.csv",
    )

    seasonal = pd.read_csv(CANONICAL / "seasonal_day_night_summary.csv")
    _write(seasonal, "table_3_marginal_burden_summary.csv")

    allocations = pd.read_csv(CANONICAL / "one_unit_allocations.csv")
    coordinate_countries: dict[tuple[float, float], str] = {}
    for prefix in ("source", "sink"):
        for row in allocations.itertuples(index=False):
            coordinate_countries[
                (
                    round(float(getattr(row, f"{prefix}_latitude")), 5),
                    round(float(getattr(row, f"{prefix}_longitude")), 5),
                )
            ] = str(getattr(row, f"{prefix}_country"))
    selected = pd.read_csv(CANONICAL / "matched_event_allocations.csv")
    for prefix in ("source", "sink"):
        selected[f"{prefix}_country"] = [
            coordinate_countries.get(
                (round(float(latitude), 5), round(float(longitude), 5)),
                "Unassigned",
            )
            for latitude, longitude in zip(
                selected[f"{prefix}_latitude"],
                selected[f"{prefix}_longitude"],
                strict=True,
            )
        ]
    _write(
        selected[
            [
                "analysis",
                "source_time",
                "sink_time",
                "lag_steps",
                "source_country",
                "sink_country",
                "distance_km",
                "source_marginal_benefit",
                "sink_marginal_burden",
                "net_benefit",
                "fraction_of_matched_spatial",
                "cooptimal_candidate_count",
                "near_optimal_candidate_count",
            ]
        ],
        "table_4_allocation_comparison.csv",
    )

    safety = pd.read_csv(CANONICAL / "safety_ablation.csv")
    finite_q = pd.read_csv(CANONICAL / "finite_q_sensitivity.csv")
    safety_rows = safety.assign(result_type="safety_ablation")
    finite_rows = finite_q.assign(result_type="finite_q_capacity")
    _write(
        pd.concat([safety_rows, finite_rows], ignore_index=True, sort=False),
        "table_5_safety_and_capacity.csv",
    )

    robustness = pd.read_csv(CANONICAL / "source_hotspot_robustness.csv")
    robustness_summary = (
        robustness.groupby(["metric", "source_country"])
        .agg(
            scenarios=("threshold", "count"),
            minimum_source_marginal=("maximum_marginal_burden_per_gj", "min"),
            maximum_source_marginal=("maximum_marginal_burden_per_gj", "max"),
        )
        .reset_index()
    )
    _write(robustness_summary, "table_6_robustness_summary.csv")
    print("Wrote six publication tables.")


if __name__ == "__main__":
    main()
