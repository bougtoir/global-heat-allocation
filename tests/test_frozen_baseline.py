from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_baseline_matches_canonical_outputs() -> None:
    baseline = (ROOT / "docs" / "FROZEN_BASELINE.md").read_text(encoding="utf-8")
    matched = pd.read_csv(ROOT / "results/canonical/matched_event_allocations.csv")
    dispatch = pd.read_csv(ROOT / "results/dispatch/finite_dispatch_summary.csv")

    spatial = matched.loc[matched["analysis"].eq("spatial")].iloc[0]
    temporal = matched.loc[matched["analysis"].eq("temporal")].iloc[0]

    assert f"{float(spatial['net_benefit']):.4f} burden units/GJ" in baseline
    assert f"{float(temporal['net_benefit']):.4f} burden" in baseline
    assert f"Phase G contains {len(dispatch)} ten-minute sensitivity" in baseline
    assert "not mortality or morbidity" in baseline
    assert "not practical recommendations" in baseline
