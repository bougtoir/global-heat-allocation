# Phase 2 handoff: public-data acquisition

## Completed

- Acquired and checksum-verified 14 immutable public-source files
  totaling 1,210,190,935 bytes.
- Persisted 2023 NCEP/NCAR Reanalysis 1 temperature, specific humidity,
  pressure, winds, surface radiative fluxes, sea-ice concentration, snow
  water equivalent, and the invariant land mask.
- Persisted the WorldPop 2020 population-count mosaic and Natural Earth 1:110m
  Admin 0 boundaries.
- Validated a common NCEP Gaussian grid of
  94 latitude by 192 longitude
  cells with 1460 six-hourly steps from
  2023-01-01T00:00:00 through 2023-12-31T18:00:00.
- Validated the WorldPop raster at
  43200 by 18720 cells.
  Its computed sum is 7,969,633,182 people; this is a data-integrity
  diagnostic, not a new population estimate.
- Recorded URLs, versions, UTC retrieval times, retrieval conditions, local
  paths, sizes, SHA-256 digests, license terms, and completion states in the
  canonical acquisition ledger.

## Deferred with explicit limitations

- ERA5-Land remains a higher-resolution sensitivity source requiring CDS
  account acceptance and credentials.
- CERES EBAF Edition 4.2 remains an authenticated Earthdata source. It may be
  used for radiative context, not as a causal coefficient for heat disposal.
- The proof-of-concept baseline combines 2023 meteorology with fixed 2020
  population weights and must not be described as a contemporaneous census.

## Next executable phase

Build a canonical analysis cube on the NCEP grid. Derive relative humidity,
Humidex, cell area, population weights, land/ocean and cryosphere masks, and
baseline burden fields while retaining the immutable source files unchanged.
Validate each transformation against units, ranges, conservation identities,
and synthetic edge cases before implementing optimization.
