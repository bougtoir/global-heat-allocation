# Practical Pareto and mode decision

Only the evidence-eligible local direct-reuse (`C`) and temporal-storage (`B`)
branches are compared. Excluded transport, ambient-disposal, and
receiving-water pathways are not Pareto candidates.

## Objectives

Within each reported demand bound, the Pareto screen:

- maximizes useful heat delivered and demand served;
- minimizes residual source rejection, heat-pump electricity, storage
  capacity, and storage losses.

Case-specific cost and lifecycle CO2e are not objectives because the required
installed-cost and lifecycle inventories are absent.

| Scenario | Pathway | Useful delivery (MWh-th) | Demand served | Residual rejection (MWh-th) | HP electricity (MWh-e) | Storage (MWh-th) | Evidence gaps | Pareto | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `direct_lower_demand_bound` | C | 8,278.8 | 94.507% | 69,982.7 | 2,687.9 | 0.0 | 5 | yes | `CONDITIONAL_LEAST_ASSUMPTION` |
| `minimum_formula_storage_lower_demand` | B | 8,747.8 | 99.860% | 69,604.8 | 2,869.6 | 52.2 | 6 | yes | `CONDITIONAL_SENSITIVITY` |
| `generic_storage_lower_demand` | B | 8,760.0 | 100.000% | 69,346.2 | 2,993.9 | 290.0 | 6 | yes | `CONDITIONAL_SENSITIVITY` |
| `direct_upper_demand_bound` | C | 16,541.0 | 94.412% | 64,403.0 | 5,370.5 | 0.0 | 5 | yes | `CONDITIONAL_LEAST_ASSUMPTION` |
| `minimum_formula_storage_upper_demand` | B | 17,188.5 | 98.108% | 63,903.4 | 5,610.7 | 52.2 | 6 | yes | `CONDITIONAL_SENSITIVITY` |
| `generic_storage_upper_demand` | B | 17,420.1 | 99.430% | 63,501.3 | 5,804.0 | 290.0 | 6 | yes | `CONDITIONAL_SENSITIVITY` |

## Decision

All six demand-bound candidates are Pareto-efficient because additional
delivery trades against electricity, storage capacity, and storage losses.
The direct-reuse branch is the least-assumption conditional mode within each
demand bound because it introduces no case-specific storage design.

No practical mode is selected as `SUPPORTED`. Direct reuse is retained as
`CONDITIONAL_LEAST_ASSUMPTION`; formula-sized and generic storage remain
`CONDITIONAL_SENSITIVITY`. A practical selection requires an auditable
receiving-demand trace, route/hydraulic design, source-capture calibration,
incremental auxiliary electricity, and complete installed-cost evidence.

The machine-readable output is
`results/techno_economic/practical_pareto_modes.csv`.
