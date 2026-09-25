# Frozen baseline

## Freeze identity

- Frozen commit: `365f144f27faa54b0abff091b35a7b1b51b4f40c`.
- Branch at freeze: `devin/1790233051-global-heat-allocation`.
- The pre-pass working tree contained only the untracked delivery render
  `submission/nogo_assessment_report.pdf`; it is not a canonical input.
- Any correction to the files below requires a documented defect, a targeted
  patch, rerunning only affected downstream outputs, and updated provenance.

## Verified headline results

- The canonical global table contains 94 scenarios;
  93 have a relocation-positive result.
- Matched-event theoretical spatial value: 777.7645 burden units/GJ.
- Same-location temporal value: 419.3294 burden units/GJ, or 53.9147% of the matched-event spatial value.
- The matched spatial optimum has 422
  exactly co-optimal and 808 within-1%
  sink candidates.
- Finite local-capacity status: 1, 1,000, and 100,000 GJ are
  `feasible`, `feasible`, and
  `feasible`; 1,000,000 GJ is
  `infeasible_under_local_capacity`.
- Structural replication contains 9 prespecified scenarios:
  9 retain positive
  constrained theoretical spatial value,
  9 retain sink
  non-uniqueness, and
  9 retain
  pathological unrestricted sinks.
- Phase G contains 7 ten-minute sensitivity scenarios. Across
  nonzero-demand sensitivities, served demand spans
  94.412%-
  100.000%; residual rejection
  spans 63,501.3-
  75,573.6 MWh-th.
- All 31 finite-dispatch checks pass; the maximum absolute
  timestep thermal-balance error is
  1.137e-13 MWh.

These are model outputs or sensitivity results at their stated evidence level.
They are not practical recommendations, health outcomes, environmental-safety
findings, or evidence of planetary cooling.

## Frozen source evidence

The measured Frontier workbook is frozen after provenance verification:

- source key: `frontier_hpc_facility_data_v4`;
- local path: `data/raw/real_heat_cases/frontier_figshare_v4_20260924T115656Z/frontier_hpc_facility_data_v4.xlsx`;
- file size: 20,164,974 bytes;
- SHA-256: `56a48dd66382896890dfc2e4940ec90f894bb85795ee8e85ea2708dda05796bf`;
- completion: `complete`;
- license: Creative Commons Attribution 4.0 International.

Missing source observations remain unavailable and are not imputed.

## Closed gates

- Structural uncertainty is closed with the documented product, metric, year,
  and resolution limitations.
- Health-claim control is closed and must be maintained: the endpoint is a
  population-weighted thermal-stress burden proxy, not mortality or morbidity.
- Global theoretical analysis, structural replication, measured Frontier
  source evidence, technology comparators, environmental exclusions,
  techno-economic sensitivities, and finite-dispatch sensitivities are frozen.

## Remaining gates

- Exhaustive case-specific evidence inventory and explicit pathway eligibility.
- Global-to-real constraint waterfall without cross-unit arithmetic.
- Evidence-level practical Pareto and mode comparison.
- Manuscript-value traceability and two-scale manuscript rewrite.
- Current Applied Energy fit audit and independent adversarial review.
- Clean rebuild, final claim calibration, and a new GO/WEAK GO/NO-GO decision.

## Analyses not to rerun without a documented defect

- Canonical global one-unit, matched-event, finite-Q, safety-ablation,
  robustness, and physical-diagnostic analyses.
- Phase F structural replication.
- Measured Frontier source preprocessing and descriptive statistics.
- Phase C-E technology, environmental, techno-economic, and operational-
  emissions comparators.
- Phase G constant-demand-bound finite-dispatch sensitivities.

New case evidence may trigger only the affected case-dispatch and downstream
waterfall, Pareto, manuscript, and provenance outputs.

## Canonical files and hashes

| File | SHA-256 |
|---|---|
| `config/model.yml` | `8607e5c5213f42cd35a117af220f6fc2df8914ff502e39aa38f847b0589e36f1` |
| `config/finite_dispatch.yml` | `dd8c346ba42e23350154c3aed26bfe1b5b258cf2eacee604caef9faafac40c9a` |
| `data/metadata/data_snapshots.csv` | `a2e360ed0375ce192b0611de0553c9e17072afd596988072deb472353a7c8743` |
| `data/metadata/technology_parameters.csv` | `82e13d226cd64c909573a8ca50d500ca28e299a3787e9999396c51e621b259fa` |
| `data/metadata/techno_economic_parameters.csv` | `b0d071805bbf1e62431f30dee6c1b220a27df2c8498671c70b7647f1f5057c64` |
| `data/metadata/environmental_parameters.csv` | `78151ca861f5f8640e7463c0a4f808f7a2de274f838220ddb139ce70fd66de4e` |
| `data/raw/real_heat_cases/frontier_figshare_v4_20260924T115656Z/frontier_hpc_facility_data_v4.xlsx` | `56a48dd66382896890dfc2e4940ec90f894bb85795ee8e85ea2708dda05796bf` |
| `results/canonical/one_unit_allocations.csv` | `b6277c4652dd4601e1a8ddd959f38621eef393d3216010f9a1ff87ce18f806cd` |
| `results/canonical/matched_event_allocations.csv` | `1721c3be6e249a678fcf4e5a6d42d1f85118ce7c0cb670ef17f0da5346ff4b78` |
| `results/canonical/finite_q_sensitivity.csv` | `56dcd9ae68e16c8939195e3a1d89274467192685b9aec8a84f86a240bde46c88` |
| `results/tables/structural_replication.csv` | `097ade6b588095040a4e2b256e08267cdb58a4b5449d0ea0fb0b3a61c41e7a99` |
| `results/techno_economic/energy_emissions.csv` | `c07eb0a28410a234da582b8ddaee4be2abfbe14346712883f6a5c4e0922d54f6` |
| `results/techno_economic/economics.csv` | `be2efbc04732130430d2c0f566eef4fdde6a4779afec7c7e828d01411ea6aca5` |
| `results/environmental_constraints/frontier_pathway_assessment.csv` | `6d16d05384f982f606e67e3fa4442dd704100de39640d5339ea83d2f7727aabb` |
| `results/dispatch/finite_dispatch_summary.csv` | `8ae7bd21686b5cbfa9dea1f04c5bdf19624999a721e99b3e89e23fdabd208ebf` |
| `results/dispatch/finite_dispatch_timeseries.csv.gz` | `726f29bd6c81eec06eece31fe3111534628ca2abb61ee46173b05329cc037406` |
| `results/diagnostics/global_analysis_validation.csv` | `2feaa356dc49914f35414c79440b2e9705892424bab5f95cbe64bc3ce160f899` |
| `results/diagnostics/finite_dispatch_validation.csv` | `25d522b9a983f7e279fca200c259bd2377cf09e3338f9101939e794736c4a14b` |
| `provenance/NUMERICAL_PROVENANCE.csv` | `1315cb76383f9fcc2d8fc1178c5537a5894687d99907daf6a83cb2bd7d1e90b6` |
| `submission/manuscript_applied_energy_inline.docx` | `ccdba8d5137ecfcb12325c3ef9788481a33d5d4ac793ce4f658ddf4d7d6e3541` |
| `submission/nogo_assessment_report.docx` | `2c25043d9ec82c41f0fb8963b5feb67a0f8c4ed6eaf3350493acd9b8eda70c91` |
