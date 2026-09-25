# Data-source audit

## Baseline selection

The no-credential baseline uses the public NCEP/NCAR Reanalysis 1 Gaussian
surface grid for 2023. Temperature, specific humidity, pressure, 10 m winds,
radiative fluxes, sea-ice fraction, snow water equivalent, and the invariant
land mask therefore share one native grid. This choice prioritizes a
reproducible global proof of concept. Its coarse resolution and known
reanalysis limitations preclude claims of neighbourhood-scale intervention
performance.

WorldPop's unconstrained 2020 population-count mosaic supplies the primary
exposure weights. Natural Earth Admin 0 boundaries are used only for map
context and aggregation checks.

## Access and licensing

- NOAA PSL exposes the selected NCEP/NCAR files through anonymous HTTPS and
  requests acknowledgement in publications using the data.
- WorldPop describes the 2020 global mosaic as a 30 arc-second WGS84
  population-count raster and distributes it under CC BY 4.0.
- Natural Earth distributes its raster and vector data in the public domain.

Every downloaded file is retained below `data/raw`, and
`data/metadata/data_snapshots.csv` records the source URL, product version,
UTC acquisition time, retrieval conditions, file size, SHA-256 digest,
license terms, and completion state. The acquisition script refuses to
overwrite an existing raw file.

## Audited but deferred sources

ERA5-Land is reserved for higher-resolution sensitivity analysis because CDS
account acceptance and API credentials are not available to the anonymous
baseline. CERES EBAF Edition 4.2 is also deferred pending authenticated
Earthdata acquisition. CERES may provide observational radiative context, but
observed outgoing longwave radiation will not be interpreted as the causal
derivative of radiative loss with respect to relocated surface heat.

## Known limitations

The baseline climate year and population year differ. Results must therefore
be described as a controlled allocation experiment using fixed 2020 exposure
weights and 2023 meteorology, not as a contemporaneous census. Population
absence is not an environmental-safety criterion; cryosphere, ocean,
ecosystem, and physical constraints are modeled separately.
