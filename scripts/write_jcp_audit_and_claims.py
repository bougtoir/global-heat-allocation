"""Write JCP scope, novelty, reference, and claim-evidence audits."""
# ruff: noqa: E501

from __future__ import annotations

import csv
import os
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "references.yml"
REFERENCE_VERIFICATION = ROOT / "provenance" / "reference_verification.csv"
REFERENCE_REGISTRY = ROOT / "provenance" / "jcp_references_verified.csv"
CLAIM_MATRIX = ROOT / "provenance" / "claim_evidence_matrix.csv"
SCOPE_AUDIT = ROOT / "docs" / "JCP_SCOPE_NOVELTY_AUDIT.md"
CLAIM_ARCHITECTURE = ROOT / "docs" / "JCP_CLAIM_ARCHITECTURE.md"
MANUSCRIPT_VALUES = ROOT / "provenance" / "manuscript_values.csv"
CASCADE = ROOT / "results" / "tables" / "burden_shifting_cascade.csv"
FAILURE_MATRIX = ROOT / "results" / "tables" / "free_sink_failure_matrix.csv"
PARETO = ROOT / "results" / "techno_economic" / "practical_pareto_modes.csv"

JCP_INCLUDED_REFERENCE_KEYS = [
    "glavic2007sustainability",
    "shi2016cleanerproduction",
    "chertow2007symbiosis",
    "hellweg2014lca",
    "finnveden2009lca",
    "laurent2012carbonfootprint",
    "ryberg2018absolute",
    "moncaster2019burdenshifting",
    "gonzalezgaray2019burdenshifting",
    "li2026datacenterburden",
    "zink2017rebound",
    "korhonen2018circular",
    "steffen2015boundaries",
    "mohai2009justice",
    "forman2016wasteheat",
    "papapetrou2018wasteheat",
    "brueckner2015wasteheat",
    "ebrahimi2014datacenter",
    "wahlroos2018datacenter",
    "ebrahimi2019datacenterwhr",
    "zhang2024datacentermismatch",
    "fang2018industrycity",
    "yang2021exergoenvironmental",
    "arpagaus2018heatpumps",
    "guelpa2019storage",
    "lund2014district",
    "li2022allocation",
    "raptis2016thermalpollution",
    "madden2013thermaleffluent",
    "cheng2017oceanheat",
    "serreze2011arctic",
    "flanner2009anthropogenic",
    "chen2004anthropogenic",
    "sherwood2010adaptability",
    "raymond2020heat",
    "mora2017deadlyheat",
    "buzan2015heatstress",
    "liljegren2008wbgt",
    "stull2011wetbulb",
    "kalnay1996ncep",
    "tatem2017worldpop",
    "peyre2019transport",
    "loeb2018ceres",
    "raman2014radiative",
    "zhai2017radiative",
    "frontier2024dataset",
    "frontier2024figshare",
    "ornl2024wasteheatreport",
]

EXCLUDED_REFERENCE_KEYS = {
    "hersbach2020era5": "ERA5 is not the primary climate baseline in the frozen JCP manuscript.",
    "dinapoli2021era5heat": "Heat-stress citation is redundant with direct Humidex and wet-bulb sources.",
    "john2022oceanmover": "Ocean-heat relocation concept is too remote from the final no-free-sink argument.",
    "parno2019seaice": "Cryosphere engineering concept is not needed after categorical exclusion.",
    "vissio2020wasserstein": "Optimal-transport literature is represented by Peyre and Cuturi.",
}


def _write_text_atomic(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    with temporary.open("rb+") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_csv_atomic(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty CSV: {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _latest_reference_rows() -> dict[str, dict[str, str]]:
    verification = pd.read_csv(REFERENCE_VERIFICATION).fillna("")
    snapshot = sorted(verification["snapshot_id"].unique())[-1]
    latest = verification.loc[verification["snapshot_id"].eq(snapshot)]
    return {
        str(row["citation_key"]): {
            "snapshot_id": str(row["snapshot_id"]),
            "title": str(row["title"]),
            "doi_or_url": str(row["doi_or_url"]),
            "verified_utc": str(row["verified_utc"]),
            "claim_supported": str(row["claim_supported"]),
            "verification_notes": str(row["verification_notes"]),
        }
        for _, row in latest.iterrows()
    }


def _reference_config() -> dict[str, dict[str, str]]:
    with CONFIG.open(encoding="utf-8") as handle:
        records = yaml.safe_load(handle)["references"]
    return {str(record["key"]): record for record in records}


def build_reference_registry() -> list[dict[str, object]]:
    latest = _latest_reference_rows()
    config = _reference_config()
    rows: list[dict[str, object]] = []
    order = 1
    for key in JCP_INCLUDED_REFERENCE_KEYS:
        if key not in latest:
            raise ValueError(f"Missing verified metadata for {key}")
        rows.append(
            {
                "jcp_reference_order": order,
                "citation_key": key,
                "doi": config[key]["doi"],
                "registry": config[key].get("registry", "crossref"),
                "title": latest[key]["title"],
                "doi_or_url": latest[key]["doi_or_url"],
                "verified_utc": latest[key]["verified_utc"],
                "claim_supported": latest[key]["claim_supported"],
                "jcp_use": "include",
                "verification_notes": latest[key]["verification_notes"],
            }
        )
        order += 1
    for key, reason in EXCLUDED_REFERENCE_KEYS.items():
        if key not in latest:
            raise ValueError(f"Missing verified metadata for {key}")
        rows.append(
            {
                "jcp_reference_order": "",
                "citation_key": key,
                "doi": config[key]["doi"],
                "registry": config[key].get("registry", "crossref"),
                "title": latest[key]["title"],
                "doi_or_url": latest[key]["doi_or_url"],
                "verified_utc": latest[key]["verified_utc"],
                "claim_supported": latest[key]["claim_supported"],
                "jcp_use": "exclude_from_main_reference_list",
                "verification_notes": reason,
            }
        )
    included = [row for row in rows if row["jcp_use"] == "include"]
    if len(included) > 50:
        raise ValueError(f"JCP reference limit exceeded: {len(included)}")
    return rows


def _value(values: pd.DataFrame, value_id: str, column: str = "display_value") -> str:
    matches = values.loc[values["value_id"].eq(value_id), column]
    if len(matches) != 1:
        raise ValueError(f"Expected one manuscript value for {value_id}")
    return str(matches.iloc[0])


def build_claim_matrix() -> list[dict[str, object]]:
    values = pd.read_csv(MANUSCRIPT_VALUES).fillna("")
    cascade = pd.read_csv(CASCADE).fillna("")
    failure_matrix = pd.read_csv(FAILURE_MATRIX).fillna("")
    pareto = pd.read_csv(PARETO).fillna("")
    conditional_modes = int(pareto["eligibility"].eq("CONDITIONAL").sum())
    supported_modes = int(pareto["eligibility"].eq("SUPPORTED").sum())
    ocean_selected = bool(
        failure_matrix.loc[
            failure_matrix["receiving_class"].eq("open_ocean"),
            "selected_by_the_unconstrained_objective",
        ].item()
    )
    endpoint_status = str(
        cascade.loc[cascade["stage_id"].eq("supported_endpoint"), "eligibility"].item()
    )
    rows = [
        {
            "claim_id": "L1_global_screening_bound",
            "claim_level": "Level 1 directly supported",
            "claim_text": (
                "The frozen global model identifies positive one-unit relocation "
                "screening value in 93 of 94 canonical scenarios."
            ),
            "support_artifacts": (
                "provenance/manuscript_values.csv;"
                "results/canonical/one_unit_allocations.csv"
            ),
            "evidence_status": "MODEL_OUTPUT",
            "allowed_use": "Report as a theoretical screening result.",
            "prohibited_overstatement": "Do not call it practical heat delivery.",
        },
        {
            "claim_id": "L1_spatial_temporal_values",
            "claim_level": "Level 1 directly supported",
            "claim_text": (
                "The matched-event spatial screening value is "
                f"{_value(values, 'matched_spatial_value')} burden units/GJ; "
                "the same-location temporal value is "
                f"{_value(values, 'matched_temporal_value')} burden units/GJ."
            ),
            "support_artifacts": (
                "provenance/manuscript_values.csv;"
                "results/canonical/matched_event_allocations.csv"
            ),
            "evidence_status": "MODEL_OUTPUT",
            "allowed_use": "Compare frozen burden-space bounds.",
            "prohibited_overstatement": "Do not monetize or health-convert burden units.",
        },
        {
            "claim_id": "L1_free_sink_pathology",
            "claim_level": "Level 1 directly supported",
            "claim_text": (
                "The unconstrained human-burden objective selects an open-ocean "
                f"mathematical sink: {ocean_selected}."
            ),
            "support_artifacts": (
                "results/canonical/safety_ablation.csv;"
                "results/tables/free_sink_failure_matrix.csv"
            ),
            "evidence_status": "MODEL_OUTPUT",
            "allowed_use": "Use as the no-free-sink diagnostic.",
            "prohibited_overstatement": "Do not describe the ocean as a safe sink.",
        },
        {
            "claim_id": "L1_measured_source",
            "claim_level": "Level 1 directly supported",
            "claim_text": (
                "The measured Frontier source contains "
                f"{_value(values, 'frontier_valid_intervals')} valid intervals "
                "and "
                f"{_value(values, 'frontier_observed_heat')} MWh-th."
            ),
            "support_artifacts": (
                "provenance/manuscript_values.csv;"
                "data/raw/real_heat_cases/frontier_figshare_v4_20260924T115656Z/"
            ),
            "evidence_status": "FOUND_MEASURED",
            "allowed_use": "Use as measured source availability.",
            "prohibited_overstatement": "Do not impute missing source timestamps.",
        },
        {
            "claim_id": "L1_zero_supported_endpoint",
            "claim_level": "Level 1 directly supported",
            "claim_text": (
                f"{supported_modes} practical modes are evidence-supported; "
                f"{conditional_modes} modes remain conditional; final endpoint status "
                f"is {endpoint_status}."
            ),
            "support_artifacts": (
                "results/techno_economic/practical_pareto_modes.csv;"
                "results/tables/global_to_real_constraint_waterfall.csv"
            ),
            "evidence_status": "EVIDENCE_GATE",
            "allowed_use": "Report zero supported delivered-heat endpoint.",
            "prohibited_overstatement": (
                "Do not recommend a Frontier-to-ORNL project as deployable."
            ),
        },
        {
            "claim_id": "L2_burden_shifting_framework",
            "claim_level": "Level 2 interpretive but defensible",
            "claim_text": (
                "Optimizing local thermal burden can shift environmental burden "
                "when the receiving environment is treated as free."
            ),
            "support_artifacts": (
                "results/tables/burden_shifting_cascade.csv;"
                "results/tables/free_sink_failure_matrix.csv;"
                "provenance/jcp_references_verified.csv"
            ),
            "evidence_status": "MODEL_OUTPUT_PLUS_LITERATURE",
            "allowed_use": "Use as the JCP contribution framing.",
            "prohibited_overstatement": "Do not claim all heat reuse is burden shifting.",
        },
        {
            "claim_id": "L2_jcp_novelty",
            "claim_level": "Level 2 interpretive but defensible",
            "claim_text": (
                "The contribution is a conservation-aware, evidence-gated "
                "thermal-allocation framework for detecting problem shifting."
            ),
            "support_artifacts": (
                "docs/JCP_SCOPE_NOVELTY_AUDIT.md;provenance/jcp_references_verified.csv"
            ),
            "evidence_status": "LITERATURE_POSITIONING",
            "allowed_use": "Use as novelty claim if scoped to detection and gating.",
            "prohibited_overstatement": "Do not claim first study of burden shifting.",
        },
        {
            "claim_id": "L3_prohibited_safe_sink",
            "claim_level": "Level 3 unsupported/prohibited",
            "claim_text": "A specific receiving sink is environmentally safe.",
            "support_artifacts": "none",
            "evidence_status": "UNSUPPORTED",
            "allowed_use": "Exclude.",
            "prohibited_overstatement": "Any recommendation of ocean, cryosphere, land, or ambient discharge as safe.",
        },
        {
            "claim_id": "L3_prohibited_deployable_relocation",
            "claim_level": "Level 3 unsupported/prohibited",
            "claim_text": "The study demonstrates deployable global heat relocation.",
            "support_artifacts": "none",
            "evidence_status": "UNSUPPORTED",
            "allowed_use": "Exclude.",
            "prohibited_overstatement": "Do not state or imply operational global heat relocation.",
        },
        {
            "claim_id": "L3_prohibited_cost_or_lca",
            "claim_level": "Level 3 unsupported/prohibited",
            "claim_text": "Case-specific LCOH, NPC, payback, or lifecycle CO2e is known.",
            "support_artifacts": "provenance/case_specific_evidence.csv",
            "evidence_status": "NOT_FOUND_OR_BOUND_ONLY",
            "allowed_use": "Only identify as an evidence gap.",
            "prohibited_overstatement": "Do not fabricate cost or embodied-emissions values.",
        },
        {
            "claim_id": "L3_prohibited_health_or_cooling",
            "claim_level": "Level 3 unsupported/prohibited",
            "claim_text": (
                "The burden proxy is mortality, morbidity, welfare, or planetary "
                "cooling."
            ),
            "support_artifacts": "docs/JCP_ANALYSIS_FREEZE.md;README.md",
            "evidence_status": "PROHIBITED_BY_DESIGN",
            "allowed_use": "State the limitation explicitly.",
            "prohibited_overstatement": "Do not convert thermal-stress burden to health outcomes.",
        },
    ]
    return rows


def build_scope_audit() -> str:
    reference_rows = build_reference_registry()
    included_count = sum(row["jcp_use"] == "include" for row in reference_rows)
    cascade = pd.read_csv(CASCADE).fillna("")
    failure_matrix = pd.read_csv(FAILURE_MATRIX).fillna("")
    pareto = pd.read_csv(PARETO).fillna("")
    conditional_modes = int(pareto["eligibility"].eq("CONDITIONAL").sum())
    supported_modes = int(pareto["eligibility"].eq("SUPPORTED").sum())
    unsupported_classes = ", ".join(
        failure_matrix.loc[
            failure_matrix["practical_default"].str.contains("excluded"),
            "receiving_class",
        ].tolist()
    )
    cascade_ids = ", ".join(cascade["stage_id"].tolist())
    return f"""# JCP scope and novelty audit

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
| References | Use {included_count} verified main references, below the 50-reference limit. |
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
not evidenced. The frozen cascade is: {cascade_ids}.

This novelty remains plausible for JCP because:

- the global model explicitly conserves heat rather than treating removal as
  disappearance;
- the unconstrained objective selects a nominally burden-free receiving class,
  while {unsupported_classes} fail as practical free sinks;
- the practical Frontier/ORNL pathway uses measured source heat and official
  receiving-demand bounds but stops at conditional modes rather than inventing
  missing demand, routing, capture, auxiliary-power, cost, or lifecycle data;
- the final evidence gate identifies {supported_modes} supported practical
  endpoints and {conditional_modes} conditional modes, making transparent that a
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
"""


def build_claim_architecture() -> str:
    claim_rows = build_claim_matrix()
    level_1 = [
        row for row in claim_rows if str(row["claim_level"]).startswith("Level 1")
    ]
    level_2 = [
        row for row in claim_rows if str(row["claim_level"]).startswith("Level 2")
    ]
    level_3 = [
        row for row in claim_rows if str(row["claim_level"]).startswith("Level 3")
    ]

    def table(rows: list[dict[str, object]]) -> str:
        lines = [
            "| Claim ID | Claim | Evidence status | Allowed use |",
            "|---|---|---|---|",
        ]
        for row in rows:
            lines.append(
                "| {claim_id} | {claim_text} | {evidence_status} | {allowed_use} |".format(
                    claim_id=row["claim_id"],
                    claim_text=row["claim_text"],
                    evidence_status=row["evidence_status"],
                    allowed_use=row["allowed_use"],
                )
            )
        return "\n".join(lines)

    prohibited = "\n".join(
        f"- {row['claim_text']} — {row['prohibited_overstatement']}" for row in level_3
    )
    return f"""# JCP claim architecture

This architecture governs the JCP rewrite. Claims are separated into directly
supported results, interpretive but defensible framing, and unsupported claims that
must be excluded.

## Level 1: directly supported

{table(level_1)}

## Level 2: interpretive but defensible

{table(level_2)}

These claims require cautious wording. The contribution is detection and evidence
gating of environmental burden shifting in thermal-energy optimization, not proof
that any specific sink is safe or that a practical project is ready to deploy.

## Level 3: unsupported or prohibited

{table(level_3)}

The following claims are prohibited in the manuscript, cover letter, graphical
abstract, highlights, and final handoff:

{prohibited}

Additional prohibited overstatements:

- a specific environmentally safe sink;
- deployable global relocation;
- calibrated Frontier/ORNL annual operation;
- case-specific LCOH, NPC, or payback;
- case-specific lifecycle CO2e;
- health benefit;
- planetary cooling;
- space as a validated practical sink;
- comprehensive ecosystem-damage quantification.

## Permitted central claim

The permitted central claim is: a conservation-aware, evidence-gated framework can
detect when optimization of local thermal burden merely relocates environmental
burden to an unevidenced receiving pathway.
"""


def main() -> None:
    _write_csv_atomic(REFERENCE_REGISTRY, build_reference_registry())
    _write_csv_atomic(CLAIM_MATRIX, build_claim_matrix())
    _write_text_atomic(SCOPE_AUDIT, build_scope_audit())
    _write_text_atomic(CLAIM_ARCHITECTURE, build_claim_architecture())
    print(f"Wrote {SCOPE_AUDIT.relative_to(ROOT)}")
    print(f"Wrote {CLAIM_ARCHITECTURE.relative_to(ROOT)}")
    print(f"Wrote {REFERENCE_REGISTRY.relative_to(ROOT)}")
    print(f"Wrote {CLAIM_MATRIX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
