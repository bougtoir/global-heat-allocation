# Phase G finite repeated-dispatch handoff

## Scope

The dispatch engine evaluates 7 prespecified 10-minute scenarios
over the measured 2023 Frontier source calendar. Missing source observations
(2,691 absent timestamps plus 0 timestamped
missing heat values) are treated as unavailable and receive zero source credit;
no heat is interpolated or imputed. Subsecond Excel timestamp drift is rounded
to the nearest nominal 10-minute boundary before calendar alignment.

The nonzero demand inputs are constant applications of the published 1-2 MW
receiving-demand bounds. They are not a measured ORNL demand trace. Storage
cases use either the generic 290 MWh comparator or the 52.2 MWh minimum-volume
formula sensitivity. Source capture is an explicit unity upper-bound
assumption because case capture efficiency is unavailable.

## Results

- Demand served spans 94.412%-100.000% across the
  nonzero-demand sensitivities.
- Residual source rejection remains visible in every scenario and spans
  63,501.3-75,573.6 MWh-th.
- Unmet demand remains explicit whenever source availability and stored energy
  cannot satisfy the constant sensitivity demand.
- The maximum absolute timestep thermal-balance error is
  1.137e-13 MWh.
- All 31 validation checks pass, including timestep
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
