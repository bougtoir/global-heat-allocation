# Real Heat Case Selection

## Purpose

This phase selects an auditable real thermal-energy case for the applied
engineering scale of the study. Selection was performed before technology,
dispatch, economic, emissions, or environmental outcomes were calculated. A
candidate was not favored because it was expected to produce a positive result.

The machine-readable comparison is
`data/metadata/real_heat_case_candidates.csv`.

## Prespecified selection rubric

Each candidate was scored from 0 to 2 against the eight criteria fixed in the
continuation protocol:

1. **Open and auditable data**: 0 means no independently accessible evidence;
   1 means public documentation or an incompletely licensed dataset; 2 means a
   downloadable, citable dataset under explicit open terms.
2. **Reconstructable heat quantity**: 0 means no quantitative heat basis; 1
   means capacity, annual energy, or an indirect estimate; 2 means measured heat
   power or sufficient measured flows and temperatures.
3. **Temperature grade**: 0 means absent; 1 means a broad or indirect grade; 2
   means measured or clearly documented source and/or delivery temperatures.
4. **Temporal profile**: 0 means annual or design-point evidence only; 1 means
   representative or partial temporal evidence; 2 means a continuous measured
   profile at hourly or finer resolution.
5. **Plausible storage or reuse technology**: 0 means no defensible pathway; 1
   means a generic pathway requiring major case-specific assumptions; 2 means a
   documented applicable technology or operating system.
6. **Resolvable climate context**: 0 means location or timing cannot be
   resolved; 1 means only coarse context; 2 means a known site and period that
   can be joined to public meteorology.
7. **Engineering literature**: 0 means no relevant engineering evidence; 1
   means generic literature only; 2 means case-specific or closely analogous
   engineering evidence.
8. **No indispensable proprietary dependency**: 0 means a proprietary input is
   essential; 1 means a material gap may require a bounded scenario; 2 means
   the intended analysis can be completed from public evidence.

The sum is a data-readiness diagnostic, not a welfare score. Ties are resolved
by direct fit to the study question and by whether source, technology, and
receiving pathway can be linked without inventing parameters.

## Search coverage

Eleven candidates were compared across data centers and large cooling systems,
wastewater heat, industrial surplus heat, power-plant cooling, district
heating, refrigeration/cold-chain rejection, metro/rail heat, and geothermal
district heating. The search retained negative findings: several well-known
operating systems publish capacities and annual production but not auditable
time-resolved source and demand data.

Examples retained but not selected include NREL ESIF, the Meta/Fjernvarme Fyn
data-center system, Katri Vala and Kalundborg wastewater heat pumps, Bunhill 2
metro heat recovery, MultiPACK supermarket refrigeration, United States
thermoelectric cooling-water records, and the Danish industrial surplus-heat
subset. Their limitations are explicit in the candidate table rather than
converted into arbitrary penalties in later modeling.

## Primary case: Frontier HPC waste heat and nearby ORNL heat demand

The primary case is the Frontier high-performance-computing facility at Oak
Ridge National Laboratory, Tennessee, United States.

### Public evidence

- Figshare article 24391240, version 4, DOI
  `10.6084/m9.figshare.24391240.v4`, provides a CC BY 4.0 workbook for calendar
  year 2023.
- The workbook reports nominal 10-minute observations of coolant supply and
  return temperatures, coolant flows, three subloop waste-heat estimates,
  overall waste heat, compute power, facility accessory power, total power, and
  power usage effectiveness.
- The accompanying *Scientific Data* article documents the measurements,
  coolant properties, and calculation of waste heat.
- ORNL report ORNL/TM-2023/3218 evaluates recovery of approximately
  30--38 degrees C waste heat with water-water mid-temperature heat pumps
  delivering 85 degrees C hot water.
- The report identifies a nearby receiving pathway: the
  5600--5700--5800 complex uses approximately 1--2 MW of 125 degrees C steam to
  produce 80--90 degrees C hot water for water and space heating.
- The report supplies case-specific technology and scenario evidence, including
  commercial heat-pump capacity, reported COP ranges, annual energy,
  operational-cost and emissions results, capital cost, and payback. Those
  reported outcomes will be treated as external comparators, not copied as
  results of the present model.

### Why this case was selected

Frontier directly matches the paper's applied question: a measured, currently
rejected, low-grade heat stream can be paired with a documented local demand
and a commercially described temperature-lift technology. Quantity,
temperature grade, timing, source location, baseline rejection, technology,
and a nearby reuse pathway are all auditable. The local pathway avoids treating
long-distance low-grade heat transport as practical.

Selection does not presume that storage, heat-pump operation, cost, emissions,
or thermal-burden outcomes will be favorable. Those quantities remain to be
calculated under the gate criteria.

### Binding limitation

No measured time-resolved heat-demand series for the receiving ORNL complex was
identified. The public report provides a demand range and annual engineering
results, not an hourly demand trace. Phase C must determine whether a
conservative, source-bounded demand scenario can be justified. Phase G must
keep results conditional on that demand representation. If a defensible demand
profile and sensitivity envelope cannot be built, the real-demand and finite
dispatch gates remain open and the submission decision remains NO-GO.

## Contrasting validation case: Sønderborg district heating

The contrasting case is the Sønderborg district-heating dataset, Zenodo record
7972964, DOI `10.5281/zenodo.7972964`, licensed CC BY 4.0.

The record provides 15-minute heat load and feed/return temperatures for seven
plants during 2016--2019. Both the source workbooks and the published
year-specific CSV files were preserved. The four CSV files contain complete
calendar-year timestamp grids, including the 2016 leap year. Local timestamps
repeat the 02:00 hour at the autumn daylight-saving transition, and some plant
heat-load fields include negative reported values. Validation disambiguates
timestamps with the Europe/Copenhagen time zone but does not alter the raw
measurements. Any cleaning or interpretation of negative values must be
prespecified and reported in the dispatch phase.

Sønderborg will be used to test whether dispatch, storage-state, demand
matching, and temperature-handling code behaves credibly on an independent
measured district-heating profile. It will not be used to replace missing ORNL
demand measurements, to imply that the Frontier economics transfer to Denmark,
or to characterize a waste-heat-rejection counterfactual.

## Data preservation and reuse

The selected source files, metadata responses, engineering report, dataset
article, raw Sønderborg workbooks, and year-specific Sønderborg CSV files are
stored under `data/raw/real_heat_cases/`. Raw files are intentionally excluded
from Git, while acquisition configuration and the checksum ledger are tracked.
The ledger records URL, version, retrieval time, conditions, local path, size,
SHA-256, license terms, and completion state.

The Frontier dataset and article and the Sønderborg dataset are CC BY 4.0. The
ORNL technical report is publicly distributed by the United States Department
of Energy, but report redistribution rights must be confirmed before any raw
report is included in a public release archive. No raw source is added to the
submission package solely because it is locally available.

## Phase B decision

The primary and contrasting cases are frozen for the next phases:

- **Primary applied case:** Frontier HPC source plus the local ORNL campus
  demand pathway.
- **Contrasting validation case:** Sønderborg district-heating demand and
  network temperatures.

This closes case discovery and selection only. It does not close the
technology, demand, dispatch, cost, emissions, environmental-capacity,
structural-replication, reproducibility, or journal-fit gates. The project
therefore remains **NO-GO** at the end of Phase B.
