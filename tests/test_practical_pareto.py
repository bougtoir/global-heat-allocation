from pathlib import Path

import pandas as pd

from scripts import build_practical_pareto

ROOT = Path(__file__).resolve().parents[1]


def test_practical_pareto_uses_only_eligible_pathways() -> None:
    rows = pd.read_csv(build_practical_pareto.OUTPUT)

    assert set(rows["pathway_id"]) == {"B", "C"}
    assert rows["eligibility"].eq("CONDITIONAL").all()
    assert not rows["selected_practical_mode"].any()
    assert rows["pareto_efficient_within_demand_basis"].all()


def test_direct_reuse_is_least_assumption_mode() -> None:
    rows = pd.read_csv(build_practical_pareto.OUTPUT)
    least_assumption = rows.loc[rows["least_assumption_mode_within_demand_basis"]]

    assert set(least_assumption["scenario_id"]) == {
        "direct_lower_demand_bound",
        "direct_upper_demand_bound",
    }
    assert least_assumption["mode_decision"].eq("CONDITIONAL_LEAST_ASSUMPTION").all()


def test_practical_pareto_matches_current_dispatch_and_evidence() -> None:
    dispatch = pd.read_csv(build_practical_pareto.DISPATCH)
    evidence = pd.read_csv(build_practical_pareto.EVIDENCE).fillna("")
    expected = build_practical_pareto._build_rows(dispatch, evidence).reset_index(
        drop=True
    )
    actual = pd.read_csv(build_practical_pareto.OUTPUT).reset_index(drop=True)

    pd.testing.assert_frame_equal(actual, expected, check_like=False)
