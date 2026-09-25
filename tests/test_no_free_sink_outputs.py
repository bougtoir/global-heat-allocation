from __future__ import annotations

import pandas as pd

from scripts import build_no_free_sink_outputs as outputs


def test_burden_shifting_cascade_preserves_unit_separation() -> None:
    cascade = outputs.build_cascade()

    assert cascade["stage_id"].tolist() == [
        "human_burden_objective",
        "transport_locality",
        "cryosphere_constraint",
        "ocean_constraint",
        "ocean_and_cryosphere_constraint",
        "same_location_temporal_alternative",
        "locality_and_capacity",
        "real_pathway_evidence_eligibility",
        "supported_endpoint",
    ]
    assert (
        cascade.loc[cascade["stage_id"].eq("supported_endpoint"), "eligibility"].item()
        == "EXCLUDED"
    )
    assert (
        cascade.loc[
            cascade["stage_id"].eq("real_pathway_evidence_eligibility"),
            "eligibility",
        ].item()
        == "CONDITIONAL"
    )
    assert pd.isna(
        cascade.loc[
            cascade["stage_id"].eq("real_pathway_evidence_eligibility"),
            "screening_value_burden_units_per_gj",
        ].item()
    )


def test_free_sink_failure_matrix_has_required_classes() -> None:
    matrix = outputs.build_failure_matrix()

    assert set(matrix["receiving_class"]) == {
        "populated_land",
        "sparse_land",
        "open_ocean",
        "cryosphere",
        "atmosphere_radiative_concept",
        "engineered_reuse_and_storage",
    }
    assert (
        matrix.loc[
            matrix["receiving_class"].eq("open_ocean"),
            "selected_by_the_unconstrained_objective",
        ].item()
        is True
    )
    assert (
        "residual heat returns"
        in matrix.loc[
            matrix["receiving_class"].eq("engineered_reuse_and_storage"),
            "free_sink_failure_mode",
        ].item()
    )


def test_constraint_cascade_figure_writes_png_and_svg(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(outputs, "FIGURE_OUTPUT", tmp_path)

    outputs.build_constraint_cascade_figure()

    assert (tmp_path / "figure_3_progressive_sink_constraints.png").stat().st_size > 0
    assert (tmp_path / "figure_3_progressive_sink_constraints.svg").stat().st_size > 0
