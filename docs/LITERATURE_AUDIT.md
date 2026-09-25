# Literature audit

## Audit method

The audit used targeted searches of publisher pages and DOI records, followed
by Crossref metadata retrieval for the curated set in `config/references.yml`.
The raw Crossref responses are preserved locally with checksums. Search-result
snippets were not treated as evidence. The claims below are intentionally no
broader than the verified works support.

## Global heat and climate response

Flanner (2009) established that anthropogenic heat flux is globally small in
mean radiative-forcing terms but spatially concentrated, with modeled regional
atmospheric effects in high-flux cells. Chen et al. (2004) likewise modeled
regional climate-pattern responses to anthropogenic heat. Earlier experiments
also examined highly localized waste-heat release, demonstrating that
concentrated sinks cannot be assumed harmless merely because they are remote.

**Implication:** redistribution must be modeled as a source-and-sink
perturbation with local capacity and environmental constraints. It cannot be
described as planetary cooling.

## Human thermal stress

ERA5-HEAT demonstrates that global gridded UTCI and mean radiant temperature
can be derived consistently from reanalysis. Buzan et al. showed that
heat-stress metrics have materially different formulations and behavior.
Liljegren et al. provided a physics-based WBGT formulation from standard
meteorological inputs. Raymond et al. documented the relevance of compound
heat and humidity extremes, while Mora et al. demonstrated the global
importance of population exposure to dangerous heat.

**Implication:** the primary endpoint should be labeled thermal-stress exposure
burden, not mortality. Multiple stress metrics and perturbation sizes require
sensitivity analysis.

## Thermal-energy transport and storage

Li et al. formulated spatial allocation of district-heating/cooling resources
using transportation theory and linear programming. Guelpa and Verda reviewed
short- and long-duration thermal storage within district energy systems. Lund
et al. placed low-temperature networks, distributed sources, and storage
within fourth-generation district heating.

**Implication:** there is established precedent for constrained spatial and
temporal thermal-resource allocation at network scale. The present framework
must clearly distinguish that literature from a global theoretical upper
bound and avoid implying that low-grade heat can be moved intercontinentally
with present technology.

## Conserved-allocation methods in Earth-system applications

Computational optimal transport supplies scalable regularized methods for
mass-conserving allocation. Earth-science applications have used Wasserstein
methods to compare climate-model fields, track sea-ice motion, and analyze
oceanographic distributions.

**Implication:** optimal transport provides relevant mathematical context, but
the implemented canonical calculation is a one-unit marginal source-sink pair
search, not a finite-mass transport plan. The manuscript must use the narrower
description unless a genuine transport-plan optimization is implemented.

## Radiative escape

CERES EBAF provides balanced observed radiation products. Raman et al.
demonstrated sub-ambient daytime radiative cooling using an engineered
spectrally selective device.

**Implication:** an observed OLR climatology is not the derivative of OLR with
respect to an imposed surface heat increment. Radiative escape must remain a
separate exploratory analysis unless a defensible response model is available.

## Evidence gaps retained

- No verified source establishes safe large-scale disposal of heat in oceans,
  deserts, polar regions, or sparsely populated land.
- No globally transferable causal mortality function is adopted.
- No source makes intercontinental low-grade-heat transport currently
  practical.
- The available literature does not by itself validate a single effective heat
  capacity for atmosphere, land, and ocean.

These gaps become explicit model constraints or limitations, not parameters
filled with invented values.
