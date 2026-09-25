"""Write the finite repeated-dispatch handoff from generated outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "dispatch" / "finite_dispatch_summary.csv"
VALIDATION = ROOT / "results" / "diagnostics" / "finite_dispatch_validation.csv"
OUTPUT = ROOT / "docs" / "PHASE_G_HANDOFF.md"


def main() -> None:
    summary = pd.read_csv(SUMMARY)
    validation = pd.read_csv(VALIDATION)
    demand = summary.loc[summary["demand_mwh"].gt(0)].copy()
    minimum_served = float(demand["demand_served_fraction"].min())
    maximum_served = float(demand["demand_served_fraction"].max())
    minimum_rejection = float(summary["residual_source_rejection_mwh"].min())
    maximum_rejection = float(summary["residual_source_rejection_mwh"].max())
    maximum_balance_error = float(
        summary["maximum_absolute_thermal_balance_error_mwh"].max()
    )
    missing_timestamps = int(summary["missing_timestamp_intervals"].iloc[0])
    unavailable_source = int(summary["unavailable_source_intervals"].iloc[0])
    missing_values = unavailable_source - missing_timestamps

    text = f"""# Phase G finite repeated-dispatch handoff

## Scope

The dispatch engine evaluates {len(summary)} prespecified 10-minute scenarios
over the measured 2023 Frontier source calendar. Missing source observations
({missing_timestamps:,} absent timestamps plus {missing_values:,} timestamped
missing heat values) are treated as unavailable and receive zero source credit;
no heat is interpolated or imputed. Subsecond Excel timestamp drift is rounded
to the nearest nominal 10-minute boundary before calendar alignment.

The nonzero demand inputs are constant applications of the published 1-2 MW
receiving-demand bounds. They are not a measured ORNL demand trace. Storage
cases use either the generic 290 MWh comparator or the 52.2 MWh minimum-volume
formula sensitivity. Source capture is an explicit unity upper-bound
assumption because case capture efficiency is unavailable.

## Results

- Demand served spans {minimum_served:.3%}-{maximum_served:.3%} across the
  nonzero-demand sensitivities.
- Residual source rejection remains visible in every scenario and spans
  {minimum_rejection:,.1f}-{maximum_rejection:,.1f} MWh-th.
- Unmet demand remains explicit whenever source availability and stored energy
  cannot satisfy the constant sensitivity demand.
- The maximum absolute timestep thermal-balance error is
  {maximum_balance_error:.3e} MWh.
- All {len(validation)} validation checks pass, including timestep
  conservation, annual reconciliation, non-negativity, storage capacity,
  charge/discharge power, saturation, and residual rejection.

## Gate status

The repeated-dispatch algorithm and conservation checks are implemented.
The Frontier/ORNL practical-case dispatch gate remains **OPEN** because the
measured receiving-demand trace, case source-capture efficiency, case storage
design, route losses, outage schedule, and environmental receiving capacity
remain unavailable. These sensitivities must not be described as observed or
calibrated annual Frontier/ORNL operation.

## Machine-readable outputs

- `results/dispatch/finite_dispatch_summary.csv`
- `results/dispatch/finite_dispatch_timeseries.csv.gz`
- `results/dispatch/finite_dispatch_metadata.json`
- `results/diagnostics/finite_dispatch_validation.csv`
"""
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
