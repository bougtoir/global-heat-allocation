# Phase 0 handoff: repository and reproducibility

## Completed

- Established the project structure, package metadata, MIT code license,
  citation metadata, model/data configuration, provenance ledgers, and
  reproducibility commands.
- Fixed the target journal to *Applied Energy* and recorded the governing
  scientific guardrails.
- Added initial configuration tests that verify the canonical energy unit and
  target-journal override.

## Decisions

- Python 3.10 is the minimum supported interpreter because it is available on
  the current reproducibility VM.
- The initial global empirical model will use a computationally tractable
  2.5-degree, 6-hourly public reanalysis product. Resolution and study-period
  dependence will be treated as limitations and tested where feasible.
- Raw public data will be preserved locally with checksums and acquisition
  metadata. Large source files will not be committed to the monorepo.
- Numerical results will flow from canonical generated tables into every
  manuscript and figure artifact.

## Validation

Phase 0 is complete when the editable package installs, Ruff passes, and the
configuration tests pass in a clean project virtual environment.

## Next executable task

Verify primary literature, data licenses, and current official *Applied Energy*
scope and author instructions; then freeze the formal model specification
before empirical analysis.
