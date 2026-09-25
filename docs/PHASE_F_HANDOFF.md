# Phase F handoff: structural global replication

## Completed scope

Phase F evaluates 9 prespecified scenarios spanning climate years
2010, 2015, 2020, 2023,
NCEP/NCAR Reanalysis 1, NCEP-DOE Reanalysis 2, WorldPop, GHS-POP, native and
coarsened grids, and Humidex, air-temperature, and wet-bulb-proxy metrics.

The tracked outputs are:

- `results/tables/structural_replication.csv`
- `docs/STRUCTURAL_UNCERTAINTY.md`
- `docs/PHASE_F_HANDOFF.md`

## Structural outcomes

- Positive constrained theoretical spatial value: 9 of 9
  scenarios.
- Sink non-uniqueness within the configured tolerance: 9 of 9
  scenarios.
- Ocean or cryosphere cells among unrestricted minimum-burden sinks:
  9 of 9 scenarios.
- Positive matched-source temporal value: 9 of 9
  scenarios.
- Non-positive matched-event value at the configured high burden-space transport
  penalty: 9 of 9 scenarios.

Source-country labels vary across scenarios. The sink-country label is unchanged, although selected sink locations can shift. The replicated claims are structural, not geographic.

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
