"""Generate the Phase 2 handoff from canonical acquisition metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "metadata" / "data_snapshots.csv"
INVENTORY = ROOT / "data" / "metadata" / "data_inventory.csv"
OUTPUT = ROOT / "docs" / "PHASE_2_HANDOFF.md"


def main() -> None:
    ledger = pd.read_csv(LEDGER)
    inventory = pd.read_csv(INVENTORY).set_index("source_key")
    air = inventory.loc["ncep_air_2m_2023"]
    population = inventory.loc["worldpop_population_2020"]
    climate_dimensions = json.loads(str(air["dimensions"]))
    population_dimensions = json.loads(str(population["dimensions"]))
    total_bytes = int(ledger["file_size_bytes"].sum())
    population_total = float(population["sum"])

    text = f"""# Phase 2 handoff: public-data acquisition

## Completed

- Acquired and checksum-verified {len(ledger)} immutable public-source files
  totaling {total_bytes:,} bytes.
- Persisted 2023 NCEP/NCAR Reanalysis 1 temperature, specific humidity,
  pressure, winds, surface radiative fluxes, sea-ice concentration, snow
  water equivalent, and the invariant land mask.
- Persisted the WorldPop 2020 population-count mosaic and Natural Earth 1:110m
  Admin 0 boundaries.
- Validated a common NCEP Gaussian grid of
  {climate_dimensions["lat"]} latitude by {climate_dimensions["lon"]} longitude
  cells with {climate_dimensions["time"]} six-hourly steps from
  {air["time_start"]} through {air["time_end"]}.
- Validated the WorldPop raster at
  {population_dimensions["width"]} by {population_dimensions["height"]} cells.
  Its computed sum is {population_total:,.0f} people; this is a data-integrity
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
"""
    OUTPUT.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
