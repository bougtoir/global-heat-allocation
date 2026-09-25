# Phase 3 handoff: formal model and canonical cube

## Canonical artifact

- Artifact: `data/processed/analysis_cube_2023.nc`
- Size: 507.7 MiB
- SHA-256: `c0593448a6f9009eccf523caa96c451b07dc4c38bd65abdb3ce2db63d7a7c6fc`
- Dimensions: 1460 time steps × 94 latitudes × 192 longitudes
- Aggregated population diagnostic: 7,969,633,182
- Maximum one-GJ cell temperature perturbation: 0.00000696 K

The derived cube is intentionally not committed because it is reproducibly
generated from the immutable raw snapshots with `make preprocess`. Its
checksum and validation record are tracked.

## Validation status

All 11 processed-data invariants passed. These cover dimensions,
population conservation, global surface area, humidity bounds, the configured
local perturbation limit, source and sink mask logic, and burden
non-negativity.

All 7 deterministic synthetic-Earth checks passed. The spatial,
temporal, and joint solvers recovered planted source and sink optima, and the
one-GJ transfer conserved energy.

The Stull wet-bulb proxy is missing outside its stated validation domain rather
than extrapolated. Humidex remains the primary burden metric.

## Next phase

Run global one-unit spatial, temporal, and joint analyses; retain negative and
pathological optima; then add transport, storage, capacity, and environmental
constraints progressively.
