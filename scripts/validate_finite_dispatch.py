"""Validate finite-dispatch conservation, bounds, and evidence status."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv"
TIMESERIES = ROOT / "results" / "dispatch" / "finite_dispatch_timeseries.csv.gz"
OUTPUT = ROOT / "results" / "diagnostics" / "finite_dispatch_validation.csv"
TOLERANCE = 1e-9


def main() -> None:
    summary = pd.read_csv(SUMMARY)
    timeseries = pd.read_csv(TIMESERIES)
    checks: list[dict[str, str | float | bool]] = []

    def add(name: str, passed: bool, observed: str | float) -> None:
        checks.append(
            {
                "check": name,
                "passed": bool(passed),
                "observed": observed,
            }
        )

    expected_rows = int(summary["interval_count"].sum())
    add(
        "timeseries_row_count",
        len(timeseries) == expected_rows,
        f"{len(timeseries)} of {expected_rows}",
    )
    for column in [
        "source_heat_available_mwh",
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
    ]:
        minimum = float(timeseries[column].min())
        add(f"nonnegative_{column}", minimum >= -TOLERANCE, minimum)

    for column in [
        "thermal_balance_error_mwh",
        "source_balance_error_mwh",
        "demand_balance_error_mwh",
    ]:
        maximum = float(timeseries[column].abs().max())
        add(f"timestep_{column}", maximum <= TOLERANCE, maximum)

    capacity = timeseries["scenario_id"].map(
        summary.set_index("scenario_id")["storage_capacity_mwh"]
    )
    storage_excess = float((timeseries["storage_state_mwh"] - capacity).max())
    add("storage_capacity_bound", storage_excess <= TOLERANCE, storage_excess)

    timestep = timeseries["scenario_id"].map(
        summary.set_index("scenario_id")["timestep_hours"]
    )
    heat_pump_limit = (
        timeseries["scenario_id"].map(
            summary.set_index("scenario_id")["heat_pump_capacity_mw"]
        )
        * timestep
    )
    charge_limit = (
        timeseries["scenario_id"].map(
            summary.set_index("scenario_id")["storage_charge_power_mw"]
        )
        * timestep
    )
    add(
        "heat_pump_output_power_bound",
        bool(timeseries["heat_pump_output_mwh"].le(heat_pump_limit + TOLERANCE).all()),
        float((timeseries["heat_pump_output_mwh"] - heat_pump_limit).max()),
    )
    add(
        "source_capture_bound",
        bool(
            timeseries["source_heat_used_mwh"]
            .le(timeseries["source_heat_captured_mwh"] + TOLERANCE)
            .all()
        ),
        float(
            (
                timeseries["source_heat_used_mwh"]
                - timeseries["source_heat_captured_mwh"]
            ).max()
        ),
    )
    discharge_limit = (
        timeseries["scenario_id"].map(
            summary.set_index("scenario_id")["storage_discharge_power_mw"]
        )
        * timestep
    )
    add(
        "storage_charge_power_bound",
        bool(timeseries["storage_charge_input_mwh"].le(charge_limit + TOLERANCE).all()),
        float((timeseries["storage_charge_input_mwh"] - charge_limit).max()),
    )
    add(
        "storage_discharge_power_bound",
        bool(
            timeseries["storage_heat_delivered_mwh"]
            .le(discharge_limit + TOLERANCE)
            .all()
        ),
        float((timeseries["storage_heat_delivered_mwh"] - discharge_limit).max()),
    )
    add(
        "demand_delivery_bound",
        bool(
            timeseries["useful_heat_delivered_mwh"]
            .le(timeseries["demand_mwh"] + TOLERANCE)
            .all()
        ),
        float(
            (timeseries["useful_heat_delivered_mwh"] - timeseries["demand_mwh"]).max()
        ),
    )
    add(
        "residual_rejection_visible",
        bool(summary["residual_source_rejection_mwh"].gt(0).all()),
        float(summary["residual_source_rejection_mwh"].min()),
    )
    demand_scenarios = summary["demand_mwh"].gt(0)
    add(
        "demand_saturation_visible",
        bool(summary.loc[demand_scenarios, "unmet_demand_mwh"].gt(0).any()),
        float(summary.loc[demand_scenarios, "unmet_demand_mwh"].max()),
    )
    add(
        "measured_demand_gate_remains_open",
        bool(summary["practical_case_dispatch_claim_permitted"].eq(False).all()),
        "all scenarios sensitivity-only",
    )

    grouped = timeseries.groupby("scenario_id", sort=False)
    reconciled = grouped[
        [
            "source_heat_available_mwh",
            "source_heat_used_mwh",
            "residual_source_rejection_mwh",
            "demand_mwh",
            "useful_heat_delivered_mwh",
            "unmet_demand_mwh",
        ]
    ].sum()
    source_error = (
        reconciled["source_heat_available_mwh"]
        - reconciled["source_heat_used_mwh"]
        - reconciled["residual_source_rejection_mwh"]
    ).abs()
    demand_error = (
        reconciled["demand_mwh"]
        - reconciled["useful_heat_delivered_mwh"]
        - reconciled["unmet_demand_mwh"]
    ).abs()
    add(
        "annual_source_reconciliation",
        bool(source_error.le(TOLERANCE).all()),
        float(source_error.max()),
    )
    add(
        "annual_demand_reconciliation",
        bool(demand_error.le(TOLERANCE).all()),
        float(demand_error.max()),
    )

    validation = pd.DataFrame(checks)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    validation.to_csv(OUTPUT, index=False)
    failed = validation.loc[~validation["passed"], "check"].tolist()
    if failed:
        raise ValueError(f"Finite-dispatch validation failed: {failed}")
    print(f"Validated {len(validation)} finite-dispatch checks.")


if __name__ == "__main__":
    main()
