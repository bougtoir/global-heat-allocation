"""Run finite repeated-dispatch sensitivities on the measured Frontier source."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from global_heat_allocation.dispatch import DispatchParameters, dispatch_heat

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "finite_dispatch.yml"
PARAMETERS = ROOT / "data" / "metadata" / "technology_parameters.csv"
WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "real_heat_cases"
    / "frontier_figshare_v4_20260924T115656Z"
    / "frontier_hpc_facility_data_v4.xlsx"
)
OUTPUT = ROOT / "results" / "dispatch"
SUMMARY = OUTPUT / "finite_dispatch_summary.csv"
TIMESERIES = OUTPUT / "finite_dispatch_timeseries.csv.gz"
METADATA = OUTPUT / "finite_dispatch_metadata.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parameter_values() -> dict[str, float]:
    table = pd.read_csv(PARAMETERS, dtype=str, keep_default_na=False)
    return {
        str(row["parameter_id"]): float(row["value"])
        for row in table.to_dict(orient="records")
        if row["value"]
    }


def _source_profile(config: dict[str, object]) -> pd.DataFrame:
    year = int(config["calendar_year"])
    timestep_minutes = int(config["timestep_minutes"])
    raw = pd.read_excel(WORKBOOK, sheet_name="Frontier2023")
    timestamps = pd.to_datetime(
        raw["Date/Time"],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    ).dt.round(f"{timestep_minutes}min")
    source = pd.to_numeric(raw[str(config["source_column"])], errors="coerce")
    observed = pd.DataFrame(
        {
            "timestamp": timestamps,
            "source_heat_mw": source,
            "timestamp_observation_available": timestamps.notna(),
        }
    ).dropna(subset=["timestamp"])
    if observed["timestamp"].duplicated().any():
        raise ValueError("Frontier source timestamps must be unique.")
    calendar = pd.date_range(
        f"{year}-01-01 00:00:00",
        f"{year}-12-31 23:59:59",
        freq=f"{timestep_minutes}min",
    )
    profile = observed.set_index("timestamp").reindex(calendar)
    profile.index.name = "timestamp"
    profile["timestamp_observation_available"] = profile[
        "timestamp_observation_available"
    ].eq(True)
    profile["source_observation_available"] = profile["source_heat_mw"].notna()
    profile["source_heat_mw"] = profile["source_heat_mw"].fillna(0.0)
    if (profile["source_heat_mw"] < 0).any():
        raise ValueError("Frontier source heat cannot be negative.")
    return profile.reset_index()


def _demand_mw(basis: str, values: dict[str, float]) -> float:
    if basis == "zero_demand":
        return 0.0
    if basis == "reported_lower_bound":
        return values["demand_heat_min_mw"]
    if basis == "reported_upper_bound":
        return values["demand_heat_max_mw"]
    raise ValueError(f"Unknown demand basis: {basis}")


def _storage_parameters(
    basis: str,
    values: dict[str, float],
) -> dict[str, float]:
    if basis == "none":
        return {
            "storage_capacity_mwh": 0.0,
            "storage_charge_power_mw": 0.0,
            "storage_discharge_power_mw": 0.0,
            "storage_roundtrip_efficiency": 1.0,
            "storage_standing_loss_fraction_per_day": 0.0,
            "storage_auxiliary_fraction": 0.0,
        }
    if basis == "minimum_formula":
        capacity = values["storage_min_formula_volume_capacity_mwh"]
    elif basis == "generic_reference":
        capacity = values["storage_generic_capacity_mwh"]
    else:
        raise ValueError(f"Unknown storage basis: {basis}")
    return {
        "storage_capacity_mwh": capacity,
        "storage_charge_power_mw": values["storage_generic_charge_power_mw"],
        "storage_discharge_power_mw": values["storage_generic_discharge_power_mw"],
        "storage_roundtrip_efficiency": values["storage_generic_roundtrip_efficiency"],
        "storage_standing_loss_fraction_per_day": values[
            "storage_generic_standing_loss_per_day"
        ],
        "storage_auxiliary_fraction": values["storage_generic_auxiliary_fraction"],
    }


def main() -> None:
    payload = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    dispatch_config = payload["dispatch"]
    values = _parameter_values()
    source = _source_profile(dispatch_config)
    timestep_hours = float(dispatch_config["timestep_minutes"]) / 60
    heat_pump_cop = values["heat_pump_case_cop"]
    heat_pump_capacity = values["heat_pump_case_total_capacity_mw"]
    source_capture_efficiency = float(
        dispatch_config["source_capture_efficiency_assumption"]
    )
    initial_storage_fraction = float(dispatch_config["initial_storage_fraction"])
    timestamp_intervals = int(source["timestamp_observation_available"].sum())
    observed_intervals = int(source["source_observation_available"].sum())
    summary_rows: list[dict[str, str | float | int | bool]] = []
    timeseries_frames: list[pd.DataFrame] = []

    for scenario in payload["scenarios"]:
        scenario_id = str(scenario["scenario_id"])
        pathway_id = str(scenario["pathway_id"])
        demand_basis = str(scenario["demand_basis"])
        storage_basis = str(scenario["storage_basis"])
        demand_power = _demand_mw(demand_basis, values)
        storage = _storage_parameters(storage_basis, values)
        parameters = DispatchParameters(
            timestep_hours=timestep_hours,
            heat_pump_cop=heat_pump_cop,
            heat_pump_capacity_mw=heat_pump_capacity,
            source_capture_efficiency=source_capture_efficiency,
            initial_storage_mwh=(
                storage["storage_capacity_mwh"] * initial_storage_fraction
            ),
            **storage,
        )
        result = dispatch_heat(
            source_heat_mw=source["source_heat_mw"].to_numpy(dtype=float),
            demand_mw=np.full(len(source), demand_power),
            parameters=parameters,
        )
        detailed = pd.concat(
            [
                source[
                    [
                        "timestamp",
                        "timestamp_observation_available",
                        "source_observation_available",
                        "source_heat_mw",
                    ]
                ].reset_index(drop=True),
                result.timeseries,
            ],
            axis=1,
        )
        detailed.insert(0, "scenario_id", scenario_id)
        detailed.insert(1, "pathway_id", pathway_id)
        detailed.insert(2, "demand_basis", demand_basis)
        detailed.insert(3, "storage_basis", storage_basis)
        detailed.insert(8, "demand_power_mw", demand_power)
        timeseries_frames.append(detailed)
        summary_rows.append(
            {
                "scenario_id": scenario_id,
                "pathway_id": pathway_id,
                "demand_basis": demand_basis,
                "storage_basis": storage_basis,
                "demand_input_status": (
                    "zero_demand_counterfactual"
                    if demand_basis == "zero_demand"
                    else "constant_reported_bound_not_measured_trace"
                ),
                "source_input_status": (
                    "measured_valid_intervals_missing_intervals_unavailable"
                ),
                "practical_case_dispatch_claim_permitted": False,
                "source_capture_efficiency_assumption": (source_capture_efficiency),
                "heat_pump_cop": heat_pump_cop,
                "heat_pump_capacity_mw": heat_pump_capacity,
                "timestep_hours": timestep_hours,
                "demand_power_mw": demand_power,
                "storage_capacity_mwh": storage["storage_capacity_mwh"],
                "storage_charge_power_mw": storage["storage_charge_power_mw"],
                "storage_discharge_power_mw": storage["storage_discharge_power_mw"],
                "storage_roundtrip_efficiency": storage["storage_roundtrip_efficiency"],
                "storage_standing_loss_fraction_per_day": storage[
                    "storage_standing_loss_fraction_per_day"
                ],
                "timestamped_source_intervals": timestamp_intervals,
                "missing_timestamp_intervals": len(source) - timestamp_intervals,
                "observed_source_intervals": observed_intervals,
                "unavailable_source_intervals": len(source) - observed_intervals,
                **result.summary,
            }
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(summary_rows)
    timeseries = pd.concat(timeseries_frames, ignore_index=True)
    summary.to_csv(SUMMARY, index=False)
    timeseries.to_csv(
        TIMESERIES,
        index=False,
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    METADATA.write_text(
        json.dumps(
            {
                "status": "sensitivity_only_missing_measured_receiving_demand",
                "case_dispatch_gate_closed": False,
                "source_missing_policy": dispatch_config["missing_source_policy"],
                "timestamp_normalization": dispatch_config["timestamp_normalization"],
                "source_workbook": str(WORKBOOK.relative_to(ROOT)),
                "source_workbook_sha256": _sha256(WORKBOOK),
                "config": str(CONFIG.relative_to(ROOT)),
                "config_sha256": _sha256(CONFIG),
                "technology_parameters": str(PARAMETERS.relative_to(ROOT)),
                "technology_parameters_sha256": _sha256(PARAMETERS),
                "summary": str(SUMMARY.relative_to(ROOT)),
                "timeseries": str(TIMESERIES.relative_to(ROOT)),
                "scenario_count": len(summary),
                "intervals_per_scenario": len(source),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(summary)} dispatch scenarios and {len(timeseries)} rows.")


if __name__ == "__main__":
    main()
