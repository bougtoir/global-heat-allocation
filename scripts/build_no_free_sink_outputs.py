"""Derive the no-free-sink cascade and failure matrix from frozen results."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams["svg.hashsalt"] = "global-heat-allocation"
SAFETY_ABLATION = ROOT / "results" / "canonical" / "safety_ablation.csv"
MATCHED_EVENTS = ROOT / "results" / "canonical" / "matched_event_allocations.csv"
FINITE_Q = ROOT / "results" / "canonical" / "finite_q_sensitivity.csv"
RECEIVING_CLASSES = (
    ROOT / "results" / "environmental_constraints" / "receiving_class_constraints.csv"
)
PATHWAY_ASSESSMENT = (
    ROOT / "results" / "environmental_constraints" / "frontier_pathway_assessment.csv"
)
PRACTICAL_MODES = ROOT / "results" / "techno_economic" / "practical_pareto_modes.csv"
WATERFALL = ROOT / "results" / "tables" / "global_to_real_constraint_waterfall.csv"
CASCADE_OUTPUT = ROOT / "results" / "tables" / "burden_shifting_cascade.csv"
MATRIX_OUTPUT = ROOT / "results" / "tables" / "free_sink_failure_matrix.csv"
FIGURE_OUTPUT = ROOT / "results" / "figures"
SCHEMATIC_STEM = "figure_1_no_free_heat_sink_framework"
CASCADE_STEM = "figure_3_progressive_sink_constraints"

ABLATION_STAGES = [
    (
        "human_burden_objective",
        "unrestricted_global",
        "Human-burden objective only",
        "none",
        "The objective rewards release where few people are exposed.",
    ),
    (
        "transport_locality",
        "distance_only",
        "Transport-distance limit",
        "maximum candidate distance",
        "Distance limits shorten the relocation, not the receiving-environment risk.",
    ),
    (
        "cryosphere_constraint",
        "plus_cryosphere_exclusion",
        "Cryosphere exclusion",
        "cryosphere cells excluded",
        "Snow and sea-ice cells are removed as receiving candidates.",
    ),
    (
        "ocean_constraint",
        "plus_ocean_exclusion",
        "Ocean exclusion",
        "ocean cells excluded",
        "Open-water cells are removed as receiving candidates.",
    ),
    (
        "ocean_and_cryosphere_constraint",
        "plus_ocean_and_cryosphere_exclusion",
        "Ocean and cryosphere exclusion",
        "ocean and cryosphere cells excluded",
        "The canonical constrained screening configuration.",
    ),
]

ATMOSPHERE_ROW = {
    "receiving_class": "atmosphere_radiative_concept",
    "screening_role": "not_represented_as_a_disposal_term",
    "practical_default": "excluded",
    "free_sink_failure_mode": (
        "The slab formulation conserves heat in the receiving air column; "
        "no radiative disposal term removes it from the Earth system."
    ),
    "required_evidence": (
        "Device-level emitter performance, sky conditions, deployment area, "
        "and an audited system-level heat balance."
    ),
    "evidence_status": "MODEL_DEFINITION_AND_LITERATURE_CONDITIONED",
    "source_artifact": "src/global_heat_allocation/physics.py",
}


def _write_csv_atomic(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    frame.to_csv(temporary, index=False, lineterminator="\n")
    with temporary.open("rb+") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _ablation_row(ablation: pd.DataFrame, scenario: str) -> pd.Series:
    matches = ablation.loc[ablation["scenario"].eq(scenario)]
    if len(matches) != 1:
        raise ValueError(f"Expected one safety-ablation row for {scenario}")
    return matches.iloc[0]


def _receiving_class(row: pd.Series) -> str:
    if bool(row["sink_is_cryosphere"]):
        return "cryosphere"
    if bool(row["sink_is_ocean"]):
        return "open_ocean"
    return "land"


def _matched_value(matched: pd.DataFrame, analysis: str, column: str) -> float:
    matches = matched.loc[matched["analysis"].eq(analysis), column]
    if len(matches) != 1:
        raise ValueError(f"Expected one matched-event row for {analysis}")
    return float(matches.iloc[0])


def build_cascade() -> pd.DataFrame:
    ablation = pd.read_csv(SAFETY_ABLATION)
    matched = pd.read_csv(MATCHED_EVENTS)
    finite_q = pd.read_csv(FINITE_Q)
    modes = pd.read_csv(PRACTICAL_MODES)
    waterfall = pd.read_csv(WATERFALL)

    unrestricted = float(_ablation_row(ablation, "unrestricted_global")["net_benefit"])
    rows: list[dict[str, object]] = []
    for order, (stage_id, scenario, label, constraint, note) in enumerate(
        ABLATION_STAGES, start=1
    ):
        row = _ablation_row(ablation, scenario)
        value = float(row["net_benefit"])
        rows.append(
            {
                "stage_order": order,
                "stage_id": stage_id,
                "stage_label": label,
                "constraint_applied": constraint,
                "receiving_class": _receiving_class(row),
                "sink_latitude": float(row["sink_latitude"]),
                "sink_longitude": float(row["sink_longitude"]),
                "screening_value_burden_units_per_gj": value,
                "value_retained_fraction": value / unrestricted,
                "objective_detects_the_shift": not np.isclose(value, unrestricted),
                "evidence_status": "MODEL_OUTPUT",
                "eligibility": "THEORETICAL_ONLY",
                "interpretation": note,
            }
        )

    temporal_value = _matched_value(matched, "temporal", "net_benefit")
    rows.append(
        {
            "stage_order": len(rows) + 1,
            "stage_id": "same_location_temporal_alternative",
            "stage_label": "Same-location temporal release",
            "constraint_applied": "no spatial relocation; release delayed in place",
            "receiving_class": "source_location_atmosphere",
            "sink_latitude": _matched_value(matched, "temporal", "sink_latitude"),
            "sink_longitude": _matched_value(matched, "temporal", "sink_longitude"),
            "screening_value_burden_units_per_gj": temporal_value,
            "value_retained_fraction": _matched_value(
                matched, "temporal", "fraction_of_matched_spatial"
            ),
            "objective_detects_the_shift": True,
            "evidence_status": "MODEL_OUTPUT",
            "eligibility": "THEORETICAL_ONLY",
            "interpretation": (
                "Delaying release in place keeps the receiving environment "
                "unchanged and is the only screening option that does not "
                "move the burden to another location."
            ),
        }
    )

    infeasible = finite_q.loc[finite_q["status"].ne("feasible"), "energy_gj"]
    feasible = finite_q.loc[finite_q["status"].eq("feasible"), "energy_gj"]
    rows.append(
        {
            "stage_order": len(rows) + 1,
            "stage_id": "locality_and_capacity",
            "stage_label": "Finite local receiving capacity",
            "constraint_applied": "local heat-load cap on the receiving cell",
            "receiving_class": "land",
            "sink_latitude": np.nan,
            "sink_longitude": np.nan,
            "screening_value_burden_units_per_gj": np.nan,
            "value_retained_fraction": np.nan,
            "objective_detects_the_shift": True,
            "evidence_status": "MODEL_OUTPUT",
            "eligibility": "THEORETICAL_ONLY",
            "interpretation": (
                f"Feasible up to {feasible.max():.0f} GJ per event; "
                f"infeasible at {infeasible.min():.0f} GJ under the local cap."
            ),
        }
    )

    conditional = modes.loc[modes["eligibility"].eq("CONDITIONAL")]
    supported = modes.loc[modes["eligibility"].eq("SUPPORTED")]
    rows.append(
        {
            "stage_order": len(rows) + 1,
            "stage_id": "real_pathway_evidence_eligibility",
            "stage_label": "Real pathway and evidence eligibility",
            "constraint_applied": "case-specific public evidence requirements",
            "receiving_class": "engineered_reuse_and_storage",
            "sink_latitude": np.nan,
            "sink_longitude": np.nan,
            "screening_value_burden_units_per_gj": np.nan,
            "value_retained_fraction": np.nan,
            "objective_detects_the_shift": True,
            "evidence_status": "EVIDENCE_GATE",
            "eligibility": "CONDITIONAL",
            "interpretation": (
                f"{len(conditional)} closed-loop reuse or storage modes remain "
                "conditional; each carries unresolved case-specific evidence gaps."
            ),
        }
    )

    endpoint = waterfall.loc[
        waterfall["stage_id"].eq("practical_supported_endpoint"), "eligibility"
    ].unique()
    if list(endpoint) != ["EXCLUDED"]:
        raise ValueError(f"Unexpected supported-endpoint eligibility: {endpoint}")
    rows.append(
        {
            "stage_order": len(rows) + 1,
            "stage_id": "supported_endpoint",
            "stage_label": "Supported practical endpoint",
            "constraint_applied": "all gates applied",
            "receiving_class": "none_supported",
            "sink_latitude": np.nan,
            "sink_longitude": np.nan,
            "screening_value_burden_units_per_gj": np.nan,
            "value_retained_fraction": np.nan,
            "objective_detects_the_shift": True,
            "evidence_status": "EVIDENCE_GATE",
            "eligibility": "EXCLUDED",
            "interpretation": (
                f"{len(supported)} pathways are evidence-supported as delivered "
                "heat endpoints under the current public evidence."
            ),
        }
    )
    return pd.DataFrame(rows)


def build_failure_matrix() -> pd.DataFrame:
    classes = pd.read_csv(RECEIVING_CLASSES)
    pathways = pd.read_csv(PATHWAY_ASSESSMENT)
    ablation = pd.read_csv(SAFETY_ABLATION)

    unrestricted = _ablation_row(ablation, "unrestricted_global")
    selected_without_constraints = {
        "open_ocean": bool(unrestricted["sink_is_ocean"]),
        "cryosphere": bool(unrestricted["sink_is_cryosphere"]),
    }

    rows: list[dict[str, object]] = []
    receiving_classes = ("populated_land", "sparse_land", "open_ocean", "cryosphere")
    for receiving_class in receiving_classes:
        matches = classes.loc[classes["receiving_class"].eq(receiving_class)]
        if len(matches) != 1:
            raise ValueError(f"Expected one constraint row for {receiving_class}")
        record = matches.iloc[0]
        rows.append(
            {
                "receiving_class": receiving_class,
                "screening_role": record["global_screening_role"],
                "practical_default": record["practical_default"],
                "selected_by_the_unconstrained_objective": (
                    selected_without_constraints.get(receiving_class, False)
                ),
                "free_sink_failure_mode": record["rationale"],
                "required_evidence": record["required_evidence"],
                "evidence_status": "CONSTRAINT_RULE",
                "source_artifact": (
                    "results/environmental_constraints/receiving_class_constraints.csv"
                ),
            }
        )

    rows.append(
        {
            **ATMOSPHERE_ROW,
            "selected_by_the_unconstrained_objective": False,
        }
    )

    reuse = pathways.loc[pathways["assessment_status"].eq("conditional_open")]
    if reuse.empty:
        raise ValueError("No conditional engineered reuse pathway is available.")
    rows.append(
        {
            "receiving_class": "engineered_reuse_and_storage",
            "screening_role": "real_case_pathway",
            "practical_default": "conditional_closed_loop_only",
            "selected_by_the_unconstrained_objective": False,
            "free_sink_failure_mode": (
                "Closed-loop reuse avoids a new external discharge, but residual "
                "heat returns to the existing rejection system rather than "
                "disappearing."
            ),
            "required_evidence": "; ".join(sorted(set(reuse["binding_constraints"]))),
            "evidence_status": "CONDITIONAL_PATHWAY",
            "source_artifact": (
                "results/environmental_constraints/frontier_pathway_assessment.csv"
            ),
        }
    )
    columns = [
        "receiving_class",
        "screening_role",
        "practical_default",
        "selected_by_the_unconstrained_objective",
        "free_sink_failure_mode",
        "required_evidence",
        "evidence_status",
        "source_artifact",
    ]
    return pd.DataFrame(rows)[columns]


def _save_figure(figure: plt.Figure, stem: str) -> None:
    FIGURE_OUTPUT.mkdir(parents=True, exist_ok=True)
    png_path = FIGURE_OUTPUT / f"{stem}.png"
    svg_path = FIGURE_OUTPUT / f"{stem}.svg"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(svg_path, bbox_inches="tight", metadata={"Date": None})
    figure.savefig(
        FIGURE_OUTPUT / f"{stem}.pdf",
        bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(figure)


def build_problem_shifting_schematic() -> None:
    matrix = build_failure_matrix()
    conditional_text = "6 conditional modes\n0 supported endpoints"
    sink_classes = "\n".join(
        "- " + item.replace("_", " ")
        for item in matrix.loc[
            matrix["practical_default"].str.contains("excluded"),
            "receiving_class",
        ].tolist()
    )

    figure, axis = plt.subplots(figsize=(12.0, 6.0))
    axis.set_axis_off()
    boxes = [
        (
            0.05,
            0.67,
            0.18,
            0.18,
            "Heat source",
            "1 GJ global perturbation\nor measured Frontier source",
            "#e6f0ff",
        ),
        (
            0.29,
            0.67,
            0.20,
            0.18,
            "Optimizer",
            "Minimize local\nhuman thermal burden",
            "#f3e8ff",
        ),
        (
            0.55,
            0.67,
            0.22,
            0.18,
            "Apparent sink",
            "Sparse population,\nocean, land, atmosphere",
            "#fff4db",
        ),
        (
            0.80,
            0.67,
            0.17,
            0.18,
            "No free sink",
            "Receiving pathway\nmust be validated",
            "#ffe2e2",
        ),
        (
            0.08,
            0.25,
            0.25,
            0.20,
            "Failure classes",
            sink_classes,
            "#fff7ed",
        ),
        (
            0.40,
            0.25,
            0.25,
            0.20,
            "Evidence gates",
            "Demand trace\nRoute/capture/auxiliary\nCost/LCA/ecology",
            "#ecfdf5",
        ),
        (
            0.72,
            0.25,
            0.23,
            0.20,
            "Supported endpoint",
            conditional_text,
            "#eef2ff",
        ),
    ]
    for x_value, y_value, width, height, title, body, fill in boxes:
        axis.add_patch(
            plt.Rectangle(
                (x_value, y_value),
                width,
                height,
                facecolor=fill,
                edgecolor="#374151",
                linewidth=1.1,
            )
        )
        axis.text(
            x_value + width / 2,
            y_value + height - 0.045,
            title,
            ha="center",
            va="top",
            fontsize=11,
            fontweight="bold",
        )
        axis.text(
            x_value + width / 2,
            y_value + height / 2 - (0.035 if body.count("\n") >= 3 else 0.025),
            body,
            ha="center",
            va="center",
            fontsize=8.2 if body.count("\n") >= 3 else 8.8,
        )

    arrow_pairs = [
        ((0.23, 0.76), (0.29, 0.76)),
        ((0.49, 0.76), (0.55, 0.76)),
        ((0.77, 0.76), (0.80, 0.76)),
        ((0.89, 0.67), (0.85, 0.45)),
        ((0.33, 0.35), (0.40, 0.35)),
        ((0.65, 0.35), (0.72, 0.35)),
    ]
    for start, end in arrow_pairs:
        axis.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=16,
                linewidth=1.2,
                color="#374151",
            )
        )
    axis.text(
        0.50,
        0.08,
        "Removing heat from one place does not remove its environmental consequences.",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
    )
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    _save_figure(figure, SCHEMATIC_STEM)


def build_constraint_cascade_figure() -> None:
    cascade = build_cascade()
    labels = {
        "human_burden_objective": "Human-burden\nobjective",
        "transport_locality": "Distance\nlimit",
        "cryosphere_constraint": "Exclude\ncryosphere",
        "ocean_constraint": "Exclude\nocean",
        "ocean_and_cryosphere_constraint": "Canonical\nglobal mask",
        "same_location_temporal_alternative": "Temporal\nalternative",
        "locality_and_capacity": "Finite local\ncapacity",
        "real_pathway_evidence_eligibility": "Real-pathway\nevidence",
        "supported_endpoint": "Supported\nendpoint",
    }
    colors = {
        "THEORETICAL_ONLY": "#dbeafe",
        "CONDITIONAL": "#fef3c7",
        "EXCLUDED": "#fee2e2",
    }
    figure, axis = plt.subplots(figsize=(13.2, 5.8))
    axis.set_axis_off()
    x_positions = np.linspace(0.05, 0.95, len(cascade))
    for index, row in cascade.reset_index(drop=True).iterrows():
        x_value = x_positions[index]
        eligibility = str(row["eligibility"])
        axis.add_patch(
            plt.Rectangle(
                (x_value - 0.047, 0.54),
                0.094,
                0.20,
                facecolor=colors[eligibility],
                edgecolor="#374151",
                linewidth=1.1,
            )
        )
        axis.text(
            x_value,
            0.665,
            str(index + 1),
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )
        axis.text(
            x_value,
            0.605,
            labels[str(row["stage_id"])],
            ha="center",
            va="center",
            fontsize=8.3,
        )
        value = row["screening_value_burden_units_per_gj"]
        if pd.notna(value):
            detail = f"{float(value):.1f}\nburden units/GJ"
        elif row["stage_id"] == "locality_and_capacity":
            detail = "≤100,000 GJ feasible\n1,000,000 GJ\ninfeasible"
        elif row["stage_id"] == "real_pathway_evidence_eligibility":
            detail = "6 conditional\nmodes"
        else:
            detail = "0 supported\nmodes"
        axis.text(
            x_value,
            0.44,
            detail,
            ha="center",
            va="top",
            fontsize=7.0,
        )
        if index < len(cascade) - 1:
            axis.add_patch(
                FancyArrowPatch(
                    (x_value + 0.048, 0.64),
                    (x_positions[index + 1] - 0.048, 0.64),
                    arrowstyle="-|>",
                    mutation_scale=13,
                    linewidth=1.0,
                    color="#4b5563",
                )
            )
    axis.text(
        0.05,
        0.89,
        "Burden-space screening",
        transform=axis.transAxes,
        fontsize=11,
        fontweight="bold",
        color="#1d4ed8",
    )
    axis.plot(
        [0.05, x_positions[6] - 0.055],
        [0.85, 0.85],
        transform=axis.transAxes,
        color="#1d4ed8",
        linewidth=2,
    )
    axis.text(
        x_positions[7] - 0.05,
        0.89,
        "Physical-energy evidence gates",
        transform=axis.transAxes,
        fontsize=11,
        fontweight="bold",
        color="#92400e",
    )
    axis.plot(
        [x_positions[7] - 0.05, 0.95],
        [0.85, 0.85],
        transform=axis.transAxes,
        color="#92400e",
        linewidth=2,
    )
    axis.text(
        0.5,
        0.12,
        (
            "Later evidence stages are categorical and are not converted into "
            "burden units, MWh-th, USD, or CO2e."
        ),
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
    )
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    _save_figure(figure, CASCADE_STEM)


def main() -> None:
    _write_csv_atomic(CASCADE_OUTPUT, build_cascade())
    _write_csv_atomic(MATRIX_OUTPUT, build_failure_matrix())
    build_problem_shifting_schematic()
    build_constraint_cascade_figure()
    print(f"Wrote {CASCADE_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {MATRIX_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {(FIGURE_OUTPUT / f'{SCHEMATIC_STEM}.png').relative_to(ROOT)}")
    print(f"Wrote {(FIGURE_OUTPUT / f'{CASCADE_STEM}.png').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
