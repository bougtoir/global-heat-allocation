"""Write the Phase F structural-replication handoff."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "tables" / "structural_replication.csv"
OUTPUT = ROOT / "docs" / "PHASE_F_HANDOFF.md"


def main() -> None:
    frame = pd.read_csv(RESULTS)
    positive_spatial = int(
        frame["theoretical_spatial_value_positive"]
        .astype(str)
        .str.lower()
        .eq("true")
        .sum()
    )
    nonunique = int(
        frame["sink_nonunique_within_tolerance"]
        .astype(str)
        .str.lower()
        .eq("true")
        .sum()
    )
    pathological = int(
        frame["unrestricted_pathological_sinks_present"]
        .astype(str)
        .str.lower()
        .eq("true")
        .sum()
    )
    temporal_positive = int((frame["temporal_net_benefit_per_gj"] > 0.0).sum())
    penalty_collapse = int(
        frame["spatial_value_collapses_at_high_penalty"]
        .astype(str)
        .str.lower()
        .eq("true")
        .sum()
    )
    source_country_count = int(frame["source_country"].nunique())
    sink_country_count = int(frame["spatial_zero_penalty_sink_country"].nunique())
    geography_statement = (
        "Source-country labels vary across scenarios."
        if source_country_count > 1
        else "The source-country label is unchanged across scenarios."
    )
    geography_statement += (
        " Sink-country labels vary across scenarios."
        if sink_country_count > 1
        else " The sink-country label is unchanged, although selected sink "
        "locations can shift."
    )
    text = f"""# Phase F handoff: structural global replication

## Completed scope

Phase F evaluates {len(frame)} prespecified scenarios spanning climate years
{", ".join(str(value) for value in sorted(frame["climate_year"].unique()))},
NCEP/NCAR Reanalysis 1, NCEP-DOE Reanalysis 2, WorldPop, GHS-POP, native and
coarsened grids, and Humidex, air-temperature, and wet-bulb-proxy metrics.

The tracked outputs are:

- `results/tables/structural_replication.csv`
- `docs/STRUCTURAL_UNCERTAINTY.md`
- `docs/PHASE_F_HANDOFF.md`

## Structural outcomes

- Positive constrained theoretical spatial value: {positive_spatial} of {len(frame)}
  scenarios.
- Sink non-uniqueness within the configured tolerance: {nonunique} of {len(frame)}
  scenarios.
- Ocean or cryosphere cells among unrestricted minimum-burden sinks:
  {pathological} of {len(frame)} scenarios.
- Positive matched-source temporal value: {temporal_positive} of {len(frame)}
  scenarios.
- Non-positive matched-event value at the configured high burden-space transport
  penalty: {penalty_collapse} of {len(frame)} scenarios.

{geography_statement} The replicated claims are structural, not geographic.

## Rebuild and validation

```bash
make structural-replication
make phase-f-handoff
make test
make lint
```

Raw public inputs are persisted under `data/raw/structural_replication` and
hash-linked in `data/metadata/data_snapshots.csv`.

## Remaining gaps

- NCEP-DOE Reanalysis 2 shares lineage and resolution with Reanalysis 1 and is not
  a modern independent high-resolution replication such as ERA5.
- The coarsened grid is derived from the same meteorological fields.
- The burden-space transport penalty is not a monetary project cost.
- Phase E still excludes unsupported new ambient sinks.
- Finite repeated dispatch and the global-to-real constraint waterfall remain
  open.

**NO-GO remains in force.** Structural replication does not close the practical
dispatch, demand, cost, auxiliary-energy, residual-rejection, or environmental
receiving-capacity gates.
"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, OUTPUT)
    print("Wrote Phase F structural-replication handoff.")


if __name__ == "__main__":
    main()
