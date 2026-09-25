# JCP scope and novelty audit

## Journal target

- Target journal: Journal of Cleaner Production.
- Article type selected: Original article, because the work tests a quantitative
  framework and reports reproducible results rather than providing a commissioned
  review or a product note.
- Working title: "There Is No Free Heat Sink: Detecting Environmental Burden
  Shifting in Thermal-Energy Optimization".
- Fit statement: the manuscript addresses cleaner production by testing whether
  thermal-management optimization prevents waste or merely relocates thermal
  burden outside the objective boundary.

## Current JCP requirements snapshot

The stored author-guideline snapshot is
`data/raw/journal_guidance/jcp_20260925T075412Z/devin_web_jcp_guidance_fetch.txt`.
It records that JCP is an international, transdisciplinary cleaner-production,
environmental, and sustainability journal; original articles are 6000-8000 words;
unsolicited review articles are not considered; technical notes are approximately
3000 words; all contributions may contain at most 50 references; and review is
single anonymized. Required submission assets include a title page, abstract,
keywords, highlights, graphical abstract, mathematical formulae, tables,
figures/artwork, supplementary material when used, research-data statement,
article structure, references, declarations, funding, competing interests, and
generative-AI disclosure where applicable.

The stored Elsevier AI-policy snapshot is
`data/raw/journal_guidance/jcp_20260925T075412Z/elsevier_ai_policy.html`.
The final JCP manuscript must disclose substantive AI-assisted manuscript
preparation and must not use AI to fabricate research results or figures.

## Compliance decisions

| Requirement | Decision for this manuscript |
|---|---|
| Article type | Original article. |
| Word count | Target 6000-8000 words for the clean manuscript. |
| References | Use 48 verified main references, below the 50-reference limit. |
| Abstract and keywords | Required; rewrite around no-free-sink/problem-shifting contribution. |
| Highlights | Required; produce a separate short highlights file. |
| Graphical abstract | Produce a professional schematic because the guide lists it as an asset. |
| Figures and tables | Keep primary figures focused on framework, global bound, constraints, temporal contrast, waterfall, and conditional modes; move diagnostics to the supplement. |
| Data and code | Point to the reproducible repository and include data-availability statements; unresolved repository DOI remains AUTHOR ACTION. |
| Declarations | Funding, competing interests, author affiliations, approval status, and repository DOI remain AUTHOR ACTION unless provided by the author. |
| AI disclosure | Include a disclosure of substantive Devin/AI assistance in manuscript preparation. |

## Novelty audit

The JCP literature already contains burden-shifting work for embodied-carbon tools,
energy-system optimization, and data-centre cooling trade-offs. Industrial ecology,
LCA, cleaner production, circular economy, absolute sustainability assessment,
thermal pollution, radiative cooling, waste-heat recovery, high-temperature heat
pumps, and data-centre heat reuse are all active literatures. The manuscript must
therefore not claim to introduce burden shifting, LCA, or waste-heat recovery.

The defendable novelty is narrower: a conservation-aware and evidence-gated
thermal-allocation framework that starts with a global human thermal-burden
screening bound and then demonstrates how apparent local relief collapses into a
problem-shifting audit when the receiving environment and practical pathway are
not evidenced. The frozen cascade is: human_burden_objective, transport_locality, cryosphere_constraint, ocean_constraint, ocean_and_cryosphere_constraint, same_location_temporal_alternative, locality_and_capacity, real_pathway_evidence_eligibility, supported_endpoint.

This novelty remains plausible for JCP because:

- the global model explicitly conserves heat rather than treating removal as
  disappearance;
- the unconstrained objective selects a nominally burden-free receiving class,
  while sparse_land, open_ocean, cryosphere, atmosphere_radiative_concept fail as practical free sinks;
- the practical Frontier/ORNL pathway uses measured source heat and official
  receiving-demand bounds but stops at conditional modes rather than inventing
  missing demand, routing, capture, auxiliary-power, cost, or lifecycle data;
- the final evidence gate identifies 0 supported practical
  endpoints and 6 conditional modes, making transparent that a
  zero-supported-mode result can itself be the cleaner-production finding.

## Required manuscript positioning

The manuscript should lead with environmental problem shifting, not with an
engineering recommendation. It should state that removing heat from one location
does not remove the environmental burden unless the entire receiving pathway is
validated. The conclusion should emphasize optimizing and validating the full
receiving pathway, not merely removing heat from the source environment.

## Desk-rejection risks to control

1. Overclaiming novelty: avoid saying burden shifting is new.
2. Weak cleaner-production relevance: foreground prevention of displaced thermal
   burden and evidence gates.
3. Absence of LCA: state that the framework detects missing lifecycle evidence and
   does not fabricate case-specific LCA.
4. Toy-model concern: describe the global result as a screening bound and connect
   it to the real measured source only through transparent evidence gates.
5. Zero supported practical endpoint: present it as a reproducible negative
   finding, not a failed engineering design.
6. Rhetorical space/free-sink language: keep radiative and atmospheric concepts
   conditional and avoid claiming disposal to space is validated.
