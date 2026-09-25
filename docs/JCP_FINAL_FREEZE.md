# JCP final finishing freeze

## Identity and scope

- Final-finishing work starts from commit
  `7563b4394a3a5d411410f05bb74fd620021ea6e8`.
- The analytically frozen baseline remains commit
  `c81a2469859b069d99291d413b757d971f49ce90`, with the last
  analytical-content commit `aa2a0a98`.
- The existing freeze conditions in `docs/JCP_ANALYSIS_FREEZE.md` remain
  controlling. Final finishing may change text, document layout, derived
  JCP-specific summaries, and submission assets. It may not rerun or alter
  primary analysis except to correct a demonstrated reproducible defect.
- No defect requiring the primary analysis to reopen was identified during
  this inventory.

## Verified frozen analytical state

| Component | Verified state |
|---|---|
| Global canonical screening | 94 scenarios; 93 relocation-positive |
| Matched spatial and temporal screening | 777.7645 and 419.3294 burden units/GJ; temporal fraction 53.9147% |
| Finite local capacity | 1, 1,000, and 100,000 GJ feasible; 1,000,000 GJ infeasible |
| Structural replication | 9 prespecified scenarios |
| Measured Frontier source | 49,869 valid ten-minute intervals; 75,573.59055081538 MWh-th |
| Finite dispatch | 7 sensitivity scenarios; 31 validation checks passing |
| Practical endpoint | 6 conditional modes; 0 supported modes |
| Manuscript value registry | 76 registered values plus header |
| Verified JCP reference registry | 48 included references within 53 verified candidate records |
| Claim-evidence matrix | 11 claims plus header |

## Frozen and derived artifact hashes

| Artifact | SHA-256 |
|---|---|
| `provenance/manuscript_values.csv` | `80e5d7683bb6d9ba6fe2555280f6da0132baba870712eef7bcc2e080fbc66627` |
| `provenance/claim_evidence_matrix.csv` | `02864ca84a989e62f9bb45dec1daf804752ebcc4e0e2c2bc3bb15c4c39bcca99` |
| `results/tables/structural_replication.csv` | `097ade6b588095040a4e2b256e08267cdb58a4b5449d0ea0fb0b3a61c41e7a99` |
| `results/tables/global_to_real_constraint_waterfall.csv` | `d5d9cc8e299bc928065866c1e0fca2cbbf09d7d4c82df1e294caeb0bad890cb8` |
| `results/techno_economic/practical_pareto_modes.csv` | `a525d3903c66bc15b90052c8a83b971369c7f8d887e82444ad66728e07a43796` |
| `results/tables/burden_shifting_cascade.csv` | `d135e3251e60ec28eda8bd02c96d20c719aca81fe3cb5c371d173b5132abf2f2` |
| `results/tables/free_sink_failure_matrix.csv` | `42a3b7d10eafa7b5a4bd30cb6439d5d3158f6662195ae1820f32021fa582ac0a` |

The JCP-specific cascade and failure matrix are deterministic summaries of the
frozen outputs and evidence state; they are not new primary analyses.

## Validation at final-finishing entry

- `make jcp-qc` regenerated the JCP outputs and passed.
- Reference verification found 109 files across four immutable snapshots.
- Ruff check passed; Ruff confirmed 78 files already formatted.
- The repository-supported test command, `make test`, passed 86 tests.
- The submission ZIP passed `unzip -t`.
- Entry ZIP SHA-256:
  `312bbfcbb685bb0f975a8bbd07450c2a3f3c362f51054b0a57c0983f16fa20cb`.
- The working tree was clean before final-finishing edits.

## Reopening rule

Any analytical reopening must first record the affected equation, mapping,
unit conversion, source value, or artifact mismatch; preserve the prior
artifact and hash; apply the smallest correction; rerun only affected
downstream outputs; and update provenance. Editorial preference, compression,
or a desire for a stronger result is not a valid reason to reopen analysis.
