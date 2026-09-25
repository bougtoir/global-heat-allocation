# Global-to-real constraint waterfall

Burden-space and physical-energy quantities are separated because the
population-weighted thermal-stress burden has no defensible conversion to MWh,
money, mortality, or environmental capacity.

## Burden-space screening waterfall

| Stage | Bound | Value (burden units/GJ) | Eligibility |
|---:|---|---:|---|
| 1 | Global theoretical spatial screening bound | 777.7645 | THEORETICAL_ONLY |
| 2 | Same-location temporal screening bound | 419.3294 | THEORETICAL_ONLY |
| 3-9 | Environmental, locality, pathway, technology, storage/demand, dispatch, and practical endpoint | not quantifiable | `EXCLUDED` |

The canonical temporal bound is
53.9147%
of the matched-event spatial screening bound. No later practical stage is
assigned a burden-space number because doing so would require an unsupported
unit bridge.

## Physical-energy conditional branches

All rows below are demand-bound sensitivities, not observed/calibrated annual
operation.

| Scenario | Source heat used (MWh-th) | Useful heat delivered (MWh-th) | Residual rejection (MWh-th) | Demand served |
|---|---:|---:|---:|---:|
| `direct_lower_demand_bound` | 5,590.9 | 8,278.8 | 69,982.7 | 94.507% |
| `direct_upper_demand_bound` | 11,170.5 | 16,541.0 | 64,403.0 | 94.412% |
| `minimum_formula_storage_lower_demand` | 5,968.8 | 8,747.8 | 69,604.8 | 99.860% |
| `minimum_formula_storage_upper_demand` | 11,670.2 | 17,188.5 | 63,903.4 | 98.108% |
| `generic_storage_lower_demand` | 6,227.4 | 8,760.0 | 69,346.2 | 100.000% |
| `generic_storage_upper_demand` | 12,072.2 | 17,420.1 | 63,501.3 | 99.430% |

The observed source input is
75,573.6 MWh-th over valid
2023 intervals. The useful-delivery column can exceed source heat used because
the heat pump adds electricity; it is not a source-energy subtraction.

## Supported endpoint

No practical annual Frontier-to-ORNL delivery endpoint is currently
`SUPPORTED`. The finite-dispatch branches remain `CONDITIONAL` because the
receiving-demand trace, route/hydraulics, source capture, balance-of-plant
electricity, and complete installed-cost evidence are unresolved. External
ambient and receiving-water disposal pathways remain `EXCLUDED`.

The machine-readable stage ledger is
`results/tables/global_to_real_constraint_waterfall.csv`.
