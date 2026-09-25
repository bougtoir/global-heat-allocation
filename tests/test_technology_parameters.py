import math

import pandas as pd

from scripts import build_technology_parameters


def test_generated_technology_tables_match_source_workbooks() -> None:
    actual = pd.read_csv(
        build_technology_parameters.METADATA / "technology_parameters.csv",
        dtype=str,
    ).fillna("")
    expected = pd.DataFrame(build_technology_parameters._parameters()).fillna("")

    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        expected.reset_index(drop=True),
        check_dtype=False,
    )


def test_parameter_provenance_and_pathway_references_are_complete() -> None:
    parameters = pd.DataFrame(build_technology_parameters._parameters())
    sources = pd.DataFrame(build_technology_parameters._sources())
    pathways = pd.DataFrame(build_technology_parameters._pathways())
    valid_sources = set(sources["source_id"])
    valid_pathways = set(pathways["pathway_id"])

    assert parameters["parameter_id"].is_unique
    assert sources["source_id"].is_unique
    assert pathways["pathway_id"].is_unique
    for row in parameters.to_dict(orient="records"):
        referenced_pathways = set(str(row["pathways"]).split(";"))
        assert referenced_pathways <= valid_pathways
        referenced_sources = {
            source_id for source_id in str(row["source_ids"]).split(";") if source_id
        }
        assert referenced_sources <= valid_sources
        if row["value_kind"] == "direct_source":
            assert referenced_sources
        elif row["value_kind"] == "derived":
            assert referenced_sources
            assert row["derivation"]
        elif row["value_kind"] == "scenario":
            assert row["derivation"]
        elif row["value_kind"] == "missing_required":
            assert row["value"] == ""
            assert row["case_role"] == "exclusion_gate"
            assert row["limitation"]
        else:
            assert row["value_kind"] == "definition"


def test_transport_and_storage_sensitivities_do_not_become_case_claims() -> None:
    parameters = pd.DataFrame(build_technology_parameters._parameters()).set_index(
        "parameter_id"
    )
    pathways = pd.DataFrame(build_technology_parameters._pathways()).set_index(
        "pathway_id"
    )

    assert pathways.loc["D", "phase_d_use"] == "sensitivity_only"
    assert pathways.loc["E", "phase_d_use"] == "sensitivity_only"
    assert (
        parameters.loc["transport_existing_steam_loss_fraction", "case_role"]
        == "context_only"
    )
    assert (
        parameters.loc["transport_case_loss_function", "value_kind"]
        == "missing_required"
    )
    assert (
        parameters.loc["storage_case_return_temperature_c", "value_kind"]
        == "missing_required"
    )
    assert math.isclose(
        float(parameters.loc["transport_sensitivity_max_distance_km", "value"]),
        1.609344,
    )
    assert math.isclose(
        float(parameters.loc["storage_min_formula_volume_capacity_mwh", "value"]),
        52.2,
    )
