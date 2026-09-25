from pathlib import Path

import pandas as pd

from scripts import write_pathway_eligibility

ROOT = Path(__file__).resolve().parents[1]


def test_pathway_eligibility_evidence_gate_inputs() -> None:
    evidence = pd.read_csv(ROOT / "provenance" / "case_specific_evidence.csv").fillna(
        ""
    )

    for evidence_id, expected in write_pathway_eligibility.REQUIRED_EVIDENCE.items():
        assert write_pathway_eligibility._status(evidence, evidence_id) == expected


def test_pathway_eligibility_documents_required_exclusions() -> None:
    document = (ROOT / "docs" / "PATHWAY_ELIGIBILITY.md").read_text(encoding="utf-8")

    required_phrases = [
        (
            "Observed or calibrated annual Frontier-to-ORNL useful-heat "
            "delivery | `EXCLUDED`"
        ),
        "Calibrated Frontier hot-water thermal-network transport | `EXCLUDED`",
        "New external receiving-water residual-heat discharge | `EXCLUDED`",
        "Case-specific lifecycle CO2e | `EXCLUDED`",
        "Frontier-specific LCOH, NPC, or payback | `EXCLUDED`",
        "Generic comparator analyses may remain only when labeled",
    ]
    for phrase in required_phrases:
        assert phrase in document
