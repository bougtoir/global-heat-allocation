# Structural uncertainty and global replication

## Purpose

This phase tests whether the model's structural conclusions survive prespecified changes in year, reanalysis, population product, spatial resolution, and thermal metric. It does not seek replication of exact source or sink countries.

## Prespecified design

- Years: 2010, 2015, 2020, and the canonical 2023, selected before running this phase as five-year intervals plus the canonical year.
- Reanalyses: NCEP/NCAR Reanalysis 1 and the anonymously accessible NCEP-DOE Reanalysis 2.
- Population: WorldPop 2020 unconstrained and GHS-POP R2023A 2020 resident-population grids.
- Resolution: the native 94 x 192 Gaussian grid and a conservative 2 x 2 aggregation to 47 x 96.
- Metrics: Humidex, air temperature, and the Stull wet-bulb proxy. Thresholds are model scenarios, not clinical outcome thresholds.

## Structural findings

- Marginal-burden heterogeneity persists: the positive-cell p99/p50 ratio ranges from 59.5 to 179 across the prespecified scenarios.
- Positive constrained theoretical spatial value occurs in 9 of 9 scenarios.
- Sink non-uniqueness occurs in 9 of 9 scenarios using the prespecified one-percent near-optimal tolerance.
- Unrestricted minimum-burden sink sets contain ocean or cryosphere cells in 9 of 9 scenarios, confirming that an unconstrained mathematical sink is not an environmental approval.
- Positive same-location temporal value occurs in 9 of 9 scenarios.
- Where both values are defined, temporal/spatial value ratios range from 0.394 to 1.
- The configured high burden-space transport penalty makes the best matched-event spatial move non-positive in 9 of 9 scenarios. This is a sensitivity result, not a monetary cost estimate.
- Under the Phase E environmental model, new external ambient relocation remains inadmissible in every scenario without site-specific receiving-capacity evidence; therefore theoretical spatial value does not become a practical recommendation.

## Geographic instability

Peak source countries across scenarios: Bangladesh, India. Zero-penalty sink countries: Russia.
Source locations shift by as much as 306 km and selected zero-penalty sinks by as much as 1.61e+03 km relative to the canonical configuration. Exact Bangladesh, Russia, or Bhutan identities are not structurally replicated claims.

## Scenario results

| Scenario | p99/p50 | Spatial value | Near-optimal sinks | Temporal/spatial | High-penalty value | Source | Sink |
|---|---:|---:|---:|---:|---:|---|---|
| ncep1_2010_worldpop_native_humidex | 115 | 787 | 853 | 0.506 | -392 | Bangladesh | Russia |
| ncep1_2015_worldpop_native_humidex | 111 | 763 | 901 | 0.556 | -389 | Bangladesh | Russia |
| ncep1_2020_worldpop_native_humidex | 111 | 766 | 832 | 0.404 | -403 | Bangladesh | Russia |
| ncep1_2023_worldpop_native_humidex | 106 | 778 | 808 | 0.539 | -397 | Bangladesh | Russia |
| ncep1_2023_ghsl_native_humidex | 115 | 787 | 808 | 0.539 | -390 | Bangladesh | Russia |
| ncep1_2023_worldpop_coarse_humidex | 59.5 | 325 | 158 | 0.428 | -1.69e+03 | India | Russia |
| ncep1_2023_worldpop_native_air_temperature | 179 | 504 | 588 | 1 | -599 | Bangladesh | Russia |
| ncep1_2023_worldpop_native_wet_bulb | 129 | 50 | 865 | 0.602 | -915 | Bangladesh | Russia |
| ncep2_2023_worldpop_native_humidex | 93.6 | 649 | 862 | 0.394 | -518 | Bangladesh | Russia |

## Interpretation

The year-only replications move the peak source by up to 0 km. The robust result is the existence of sharp marginal heterogeneity and conditional positive allocation value, not a stable country pair.

## Limitations

- NCEP-DOE Reanalysis 2 is an official alternative reanalysis but shares lineage and the T62 Gaussian grid with Reanalysis 1; this is not an independent modern high-resolution ERA5 replication.
- The alternative-resolution test is aggregation of the same meteorology, not an independently simulated native coarse product.
- WorldPop and GHSL differ in source data and allocation methods; their comparison tests population representation, not population measurement truth.
- The wet-bulb calculation is the Stull proxy and excludes cells outside its valid temperature-humidity domain.
- Burden units are model-index units, not mortality, morbidity, welfare, or currency.
- The burden-space transport penalty cannot be converted to project cost without an unsupported burden-to-money conversion.
- Phase E exclusions prevent unsupported practical sink claims but do not estimate site-specific environmental receiving capacity.

## Reproducibility

Run `python scripts/download_data.py`, `python scripts/validate_data.py`, and `python scripts/run_structural_replication.py` from the project environment. The machine-readable result table is `results/tables/structural_replication.csv`.

The project remains **NO-GO** for submission: structural replication does not close the finite-dispatch or real-case evidence gates.
