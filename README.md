# There Is No Free Heat Sink

This repository develops a reproducible, conservation-aware and evidence-gated
framework for detecting environmental burden shifting in thermal-energy
optimization. It connects a deliberately reduced-order global human-burden
screen to an auditable measured waste-heat pathway while keeping environmental
eligibility separate from the optimization objective.

The project separates four questions:

1. Where is the marginal burden of added heat highest or lowest?
2. What conditional bound follows from same-time relocation in the prescribed
   atmospheric slab?
3. How much can short-duration local storage achieve without long-distance
   transport?
4. How do transport, storage, capacity, cryosphere, and ocean exclusions
   change the representative optimum?

Heat relocation is not planetary cooling. Every optimization conserves energy
within its stated control volume unless a separately identified radiative-loss
experiment is being evaluated.

## Status

The final package is a **WEAK GO for editorial submission to the Journal of
Cleaner Production after author-controlled metadata are completed**. Six
practical modes remain conditional and zero practical endpoints are
evidence-supported under the prespecified standard.

## Reproduction

The repository currently contains the verified global analysis, auditable real
heat-case selection, practical-technology calibration, techno-economic and
operational-emissions sensitivity, and environmental receiving-capacity
constraints, and Phase F structural global replication. Reproduce the tracked
state with:

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev,manuscript]"
make all
```

From a clean checkout, run `make install && make all`, then `make jcp-qc`. The
top-level workflow acquires or checksum-verifies raw snapshots, preprocesses and
validates the analysis cube, regenerates the analyses, runs tests and lint, and
writes the numerical provenance ledger. The JCP target rebuilds and validates
the final manuscript package from the frozen analysis outputs.

Restore the large, intentionally untracked raw inputs with `make download`.
Existing ledger records require a byte-identical remote file; changed upstream
content is rejected rather than silently substituted.

## Main commands

```bash
make references        # acquire a new immutable Crossref snapshot
make verify-references # verify committed reference files and checksums
make download          # acquire versioned public inputs (about 2.5 GB)
make verify-data       # verify local public inputs and checksums
make validate-data     # inspect formats, ranges, grids, and archive integrity
make technology-parameters # rebuild Phase C pathways and technology parameters
make techno-economic   # rebuild Phase D energy, economics, and emissions
make environmental-constraints # rebuild Phase E capacity and exclusion tables
make phase-e-handoff   # rebuild the Phase E model and handoff documents
make structural-replication # rebuild Phase F year/product/grid/metric tests
make phase-f-handoff   # rebuild the Phase F uncertainty and handoff documents
make preprocess          # build the canonical analysis cube
make validate-processed  # verify conservation and processed-data invariants
make synthetic-validation # recover planted synthetic optima
make phase-3-handoff      # regenerate the formal-model handoff
make analyze              # run exact global one-unit allocation scenarios
make extended-analysis     # run mask, finite-Q, and seasonal summaries
make physical-diagnostics  # run wind and surface-radiation diagnostics
make robustness           # test metrics, thresholds, curvature, and depth
make figures              # generate canonical PNG and SVG analysis figures
make tables               # generate publication tables from canonical results
make results-handoff      # summarize canonical results for manuscript drafting
make submission           # rebuild the retained legacy Applied Energy package
make jcp-qc               # build and validate the current JCP package
make validate-analysis    # verify global result identities and feasibility
make provenance           # hash-link generated artifacts to inputs and code
make test                # run implemented tests
make lint                # check implemented Python code
make all                 # reproduce and verify the full submission package
```

Large public-source snapshots remain intentionally untracked by Git. Preserve
`data/raw` with the project workspace or another authorized persistent store;
the tracked acquisition ledger makes every local file independently
verifiable.

## Repository layout

- `config/`: versioned model and scenario configuration.
- `data/raw/`: immutable source snapshots.
- `data/metadata/`: acquisition and integrity ledgers.
- `data/processed/`: canonical analysis inputs.
- `src/global_heat_allocation/`: acquisition, modeling, and reporting code.
- `results/`: generated canonical outputs, figures, maps, and diagnostics.
- `manuscript/`: generated manuscript sources and submission documents.
- `docs/`: model specification, audits, reviews, and phase handoffs.
- `provenance/`: numerical and reference provenance.
- `submission/`: generated journal submission package.

## Scientific guardrails

- No observational or empirical value is fabricated.
- Synthetic data are always labeled as synthetic.
- No analysis result is manually hard-coded into a manuscript or figure.
- Observed outgoing longwave radiation is not treated as a causal estimate of
  disposal efficiency.
- Population absence is not treated as evidence of environmental safety.
- Null, negative, and pathological optimization results are retained.

## License

Code is released under the MIT License. Third-party data retain their original
licenses and terms; see `data/metadata/data_snapshots.csv`.
