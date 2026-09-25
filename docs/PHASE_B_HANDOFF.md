# Phase B Handoff: Auditable Real Heat Cases

## Status

Phase B is complete. The project remains **NO-GO** for submission. This phase
closes case discovery and selection; it does not close the calibrated
technology, finite dispatch, economic, emissions, environmental, structural
replication, or reproducibility gates.

## Selection outcome

- **Primary case:** Frontier HPC waste heat with the documented local ORNL
  5600--5700--5800 building/steam demand pathway.
- **Contrasting validation case:** Sønderborg district heating, used to validate
  demand, network-temperature, storage, and dispatch behavior on an independent
  measured profile.

Eleven candidates were compared against eight prespecified criteria. The
comparison and decision limitations are in
`data/metadata/real_heat_case_candidates.csv`; the narrative decision record is
`docs/REAL_HEAT_CASE_SELECTION.md`.

## Preserved evidence

### Frontier

- Figshare article 24391240, version 4, DOI
  `10.6084/m9.figshare.24391240.v4`.
- Workbook file 47812750:
  SHA-256
  `56a48dd66382896890dfc2e4940ec90f894bb85795ee8e85ea2708dda05796bf`.
- Figshare metadata:
  SHA-256
  `f974b03cd9e90eb502a8463a16fadfbe94f37a93f49269cee046bcf830612dce`.
- ORNL report ORNL/TM-2023/3218:
  SHA-256
  `b702a806648405498784ac42bab4ad4d98fc98e032eeca8427833ce31f287ebf`.
- *Scientific Data* article:
  SHA-256
  `5ac224f0d926c0eefcea628e1816b673f549b1cdeb40dc96d328b05aa211fbac`.

The workbook contains 49,869 records and 18 fields, with nominal 10-minute
source-side measurements during 2023. Required waste-heat, coolant-grade, and
power fields passed validation. Timestamp gaps and missing return-temperature
measurements are source-data characteristics and require an explicit Phase G
policy.

### Sønderborg

- Zenodo record 7972964, DOI `10.5281/zenodo.7972964`.
- Raw workbook archive:
  SHA-256
  `3d1ab3749dcbb14ccdae33456cbbe631aa858a2371a4753b49202a581b8aaf56`.
- Metadata response:
  SHA-256
  `6bb239e919cb47b4c05940c97db0eadfdc43e82307cc4ddc0b5b4d156e1cde85`.
- Processed 2016--2019 CSV SHA-256 values:
  `ebe944632c1b7e80346747b6192ae1827efd68c1768f544fe81f0976f2dd6acf`,
  `d1dcb5e20070967cabfe29bee027ae28beb14a0924e1c14c511bc065c3f12e4d`,
  `e4e9cdb7d541591c93d713c41c476cf5fbea1e4c40c299b6fa81631da39c8799`,
  and
  `749ee3990569fee906b8c6d6344ccc5b250fd47b43dcc361bdfa4a91e563ccc2`.

The CSVs contain 15-minute heat load and feed/return temperatures for seven
plants. The 2016 file has 35,136 rows; each 2017--2019 file has 35,040 rows.
Autumn daylight-saving timestamps repeat in local clock time and were
unambiguously converted with Europe/Copenhagen rules during validation. Some
reported heat-load fields are negative; raw values were not modified.

## Reproducibility changes

- Registered ten new public sources in `config/data_sources.yml`.
- Recorded complete acquisition provenance and checksums in
  `data/metadata/data_snapshots.csv`.
- Added `openpyxl==3.1.5` for deterministic workbook access.
- Extended `scripts/validate_data.py` for generic ZIP, JSON, PDF, Frontier XLSX,
  and Sønderborg CSV validation.
- Regenerated `data/metadata/data_inventory.csv`.
- Added tests for generic ZIP validation and daylight-saving disambiguation.

Validation completed with:

- 24 public-data files verified against the ledger;
- all 24 complete sources inventoried;
- one explicitly incomplete optional journal-guide challenge record skipped;
- 24 tests passed;
- Ruff lint and format checks passed;
- `git diff --check` passed.

## Binding limitations carried forward

1. The receiving ORNL complex has a documented 1--2 MW heat-demand range and
   annual engineering scenarios, but no public measured hourly demand trace.
2. Frontier timestamp gaps and missing return-temperature cells must not be
   silently interpolated.
3. Sønderborg is a validation case, not a substitute Frontier demand trace and
   not a waste-heat-rejection counterfactual.
4. Technology, cost, emissions, and operational parameters are not yet frozen.
5. Selection provides no evidence that practical benefit survives the global
   theoretical constraint waterfall.

## Next executable phase

Phase C will create `technology_parameters.csv` and
`technology_parameter_sources.csv`. It will compare:

- conventional rejection;
- same-location temporal storage or later reuse;
- local/nearby heat-pump reuse;
- engineering-plausible local transport;
- combined storage and local transport where justified.

Every parameter will be sourced, transparently derived, or labeled as a
prespecified sensitivity. An unsupported pathway will be excluded rather than
made favorable with an invented parameter.
