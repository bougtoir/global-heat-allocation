# Global analysis results

This file is generated from canonical result tables. Do not edit it manually.

## Canonical search

The exact search produced 94 scenarios; 93 favored relocation over the no-relocation baseline.

The following are independently optimized annual maxima and must not be divided to infer storage retention:

- **Spatial**: Bangladesh to Russia, 4665.7 km, net benefit 777.8 burden units per GJ.
- **Temporal**: Bangladesh to Bangladesh, 0.0 km, net benefit 524.0 burden units per GJ.
- **Joint**: Bangladesh to Russia, 4665.7 km, net benefit 777.8 burden units per GJ.

## Matched-event comparison

- **Spatial**: source (23.81, 90.00) at 2023-06-05T00:00:00; sink (44.76, 135.00) at 2023-06-05T00:00:00; net benefit 777.8 burden units per GJ; 422 co-optimal and 808 within 1% of optimum.
- **Temporal**: source (23.81, 90.00) at 2023-06-05T00:00:00; sink (23.81, 90.00) at 2023-06-05T18:00:00; net benefit 419.3 burden units per GJ; 1 co-optimal and 1 within 1% of optimum.
- **Joint**: source (23.81, 90.00) at 2023-06-05T00:00:00; sink (44.76, 135.00) at 2023-06-05T00:00:00; net benefit 777.8 burden units per GJ.

For this peak source cell-time, the 18-hour same-location candidate yielded 53.9% of the simultaneous spatial bound. This event-matched fraction must not be generalized to a technology without calibration.

The retained no-relocation-dominated set contains 1 scenario(s); these results are not clipped to zero.

## Parameter sweep and exclusion masks

The limited one-year parameter sweep evaluated 33 combinations and selected Bangladesh. It does not test structural uncertainty across years, products, grids, or population surfaces.
Progressive mask ablation retained 5 scenarios. 3 selected representative ocean sinks before or without ocean exclusion; equal objective values make these sink locations non-unique.

## Finite energy and redistribution

Finite-transfer analysis retained 3 feasible energy level(s), from 1 to 100000 GJ.
Infeasible levels under the local temperature cap: 1e+06 GJ.
The reduced-order wind trajectory entered cryosphere-classified cells at horizon(s): 24 h, 72 h.

## Interpretation limits

- The endpoint is population-weighted thermal-stress burden, not mortality.
- Population absence is not evidence of environmental safety.
- The wind trajectory is a reduced-order diagnostic, not a climate model.
- Surface radiation fields are descriptive context; they do not estimate causal radiative escape from added heat.
- Feasibility and engineering practicality are not established.

## Reproduction

```bash
make install
make all
```
