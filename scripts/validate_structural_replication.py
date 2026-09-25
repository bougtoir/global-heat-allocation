"""Validate the Phase F structural-replication result table."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "structural_replication.yml"
RESULTS = ROOT / "results" / "tables" / "structural_replication.csv"


def _as_bool(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.lower()
    if not normalized.isin({"true", "false"}).all():
        raise ValueError(f"Invalid Boolean values in {series.name}.")
    return normalized == "true"


def validate(results_path: Path = RESULTS) -> None:
    with CONFIG.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    expected_ids = {str(row["scenario_id"]) for row in config["scenarios"]}
    frame = pd.read_csv(results_path)
    if frame["scenario_id"].duplicated().any():
        raise ValueError("Duplicate structural-replication scenario identifiers.")
    if set(frame["scenario_id"]) != expected_ids:
        raise ValueError("Structural-replication scenarios do not match configuration.")
    required_products = {"NCEP/NCAR Reanalysis 1", "NCEP-DOE Reanalysis 2"}
    if not required_products.issubset(set(frame["climate_product"])):
        raise ValueError("Required climate products are missing.")
    required_populations = {"WorldPop unconstrained", "GHS-POP R2023A"}
    if not required_populations.issubset(set(frame["population_product"])):
        raise ValueError("Required population products are missing.")
    if set(frame["climate_year"]) != {2010, 2015, 2020, 2023}:
        raise ValueError("Prespecified climate years are incomplete.")
    if set(frame["spatial_coarsening_factor"]) != {1, 2}:
        raise ValueError("Native and coarsened spatial resolutions are required.")
    required_metrics = {"humidex", "air_temperature", "wet_bulb_proxy"}
    if set(frame["thermal_metric"]) != required_metrics:
        raise ValueError("Prespecified thermal metrics are incomplete.")

    numeric_columns = [
        "marginal_p50_burden_per_gj",
        "marginal_p95_burden_per_gj",
        "marginal_p99_burden_per_gj",
        "marginal_max_burden_per_gj",
        "marginal_p99_to_p50_ratio",
        "source_marginal_benefit_per_gj",
        "spatial_zero_penalty_net_benefit_per_gj",
        "spatial_high_penalty_net_benefit_per_gj",
        "source_shift_km_from_canonical",
        "zero_penalty_sink_shift_km_from_canonical",
    ]
    values = frame[numeric_columns].to_numpy(dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Structural-replication results contain non-finite values.")
    if (frame["marginal_p99_to_p50_ratio"] < 1.0).any():
        raise ValueError("Marginal p99/p50 ratios must be at least one.")
    if (frame["spatial_near_optimal_sink_count"] < 1).any():
        raise ValueError("Every scenario must retain a feasible spatial sink.")
    if not _as_bool(frame["theoretical_spatial_value_positive"]).any():
        raise ValueError("No scenario retains positive theoretical spatial value.")
    if not _as_bool(frame["unrestricted_pathological_sinks_present"]).any():
        raise ValueError("No scenario identifies pathological unrestricted sinks.")
    if _as_bool(frame["practical_external_ambient_relocation_admissible"]).any():
        raise ValueError("Phase E does not admit external ambient relocation.")
    print(f"Validated {len(frame)} structural replication scenarios.")


if __name__ == "__main__":
    validate()
