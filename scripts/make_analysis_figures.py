"""Generate canonical analysis figures from current result artifacts."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

mpl.rcParams["svg.hashsalt"] = "global-heat-allocation"

ROOT = Path(__file__).resolve().parents[1]
CUBE = ROOT / "data" / "processed" / "analysis_cube_2023.nc"
ALLOCATIONS = ROOT / "results" / "canonical" / "one_unit_allocations.csv"
ROBUSTNESS = ROOT / "results" / "canonical" / "source_hotspot_robustness.csv"
SAFETY = ROOT / "results" / "canonical" / "safety_ablation.csv"
SEASONAL = ROOT / "results" / "canonical" / "seasonal_day_night_summary.csv"
FINITE_Q = ROOT / "results" / "canonical" / "finite_q_sensitivity.csv"
REDISTRIBUTION = ROOT / "results" / "canonical" / "natural_redistribution_summary.csv"
TRAJECTORY = ROOT / "results" / "diagnostics" / "wind_trajectory_7d.csv"
MATCHED = ROOT / "results" / "canonical" / "matched_event_allocations.csv"
DISPATCH = ROOT / "results" / "dispatch" / "finite_dispatch_timeseries.csv.gz"
PARETO = ROOT / "results" / "techno_economic" / "practical_pareto_modes.csv"
WATERFALL = ROOT / "results" / "tables" / "global_to_real_constraint_waterfall.csv"
MANUSCRIPT_VALUES = ROOT / "provenance" / "manuscript_values.csv"
COUNTRIES = (
    ROOT / "data" / "raw" / "natural_earth" / "5.1.2" / "ne_110m_admin_0_countries.zip"
)
OUTPUT = ROOT / "results" / "figures"


def _save(figure: plt.Figure, stem: str) -> None:
    svg_path = OUTPUT / f"{stem}.svg"
    figure.savefig(OUTPUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    figure.savefig(svg_path, bbox_inches="tight", metadata={"Date": None})
    figure.savefig(
        OUTPUT / f"{stem}.pdf",
        bbox_inches="tight",
        metadata={"CreationDate": None, "ModDate": None},
    )
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n"
    )
    plt.close(figure)


def _plot_framework() -> None:
    figure, axis = plt.subplots(figsize=(11.0, 4.8))
    axis.set_axis_off()
    global_boxes = [
        (0.08, "Climate +\npopulation"),
        (0.27, "Marginal\nburden"),
        (0.46, "Conserved\nallocation"),
    ]
    case_boxes = [
        (0.08, "Measured\nsource heat"),
        (0.27, "Demand +\ntechnology bounds"),
        (0.46, "Finite\ndispatch"),
    ]
    for x_position, label in global_boxes:
        axis.text(
            x_position,
            0.72,
            label,
            ha="center",
            va="center",
            transform=axis.transAxes,
            fontsize=11,
            bbox={
                "boxstyle": "round,pad=0.5",
                "facecolor": "#e6f2f8",
                "edgecolor": "#0072b2",
            },
        )
    for x_position, label in case_boxes:
        axis.text(
            x_position,
            0.28,
            label,
            ha="center",
            va="center",
            transform=axis.transAxes,
            fontsize=11,
            bbox={
                "boxstyle": "round,pad=0.5",
                "facecolor": "#e8f5ee",
                "edgecolor": "#009e73",
            },
        )
    for boxes, y_position in ((global_boxes, 0.72), (case_boxes, 0.28)):
        for left, right in zip(boxes[:-1], boxes[1:], strict=True):
            axis.annotate(
                "",
                xy=(right[0] - 0.07, y_position),
                xytext=(left[0] + 0.07, y_position),
                xycoords=axis.transAxes,
                arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#444444"},
            )
    axis.annotate(
        "",
        xy=(0.58, 0.50),
        xytext=(0.48, 0.50),
        xycoords=axis.transAxes,
        arrowprops={"arrowstyle": "->", "lw": 2.2, "color": "#555555"},
    )
    axis.text(
        0.52,
        0.56,
        "No unit bridge",
        ha="center",
        transform=axis.transAxes,
        fontsize=10,
        color="#555555",
    )
    axis.text(
        0.74,
        0.50,
        "Evidence-gated\nconstraint waterfall",
        ha="center",
        va="center",
        transform=axis.transAxes,
        fontsize=13,
        bbox={
            "boxstyle": "round,pad=0.6",
            "facecolor": "#f3f0f7",
            "edgecolor": "#cc79a7",
        },
    )
    axis.annotate(
        "",
        xy=(0.91, 0.50),
        xytext=(0.84, 0.50),
        xycoords=axis.transAxes,
        arrowprops={"arrowstyle": "->", "lw": 2.2, "color": "#555555"},
    )
    axis.text(
        0.94,
        0.50,
        "Supported\npractical\nmodes",
        ha="center",
        va="center",
        transform=axis.transAxes,
        fontsize=11,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": "#f8dddd",
            "edgecolor": "#d55e00",
        },
    )
    axis.text(
        0.94,
        0.23,
        "Current result: 0",
        ha="center",
        transform=axis.transAxes,
        fontsize=11,
        weight="bold",
        color="#d55e00",
    )
    axis.text(
        0.27,
        0.93,
        "Global burden-space screening",
        ha="center",
        transform=axis.transAxes,
        fontsize=12,
        weight="bold",
        color="#0072b2",
    )
    axis.text(
        0.27,
        0.04,
        "Real physical-energy case",
        ha="center",
        transform=axis.transAxes,
        fontsize=12,
        weight="bold",
        color="#009e73",
    )
    axis.set_title(
        "Two-scale heat-allocation and evidence framework",
        fontsize=16,
        pad=10,
    )
    figure.tight_layout()
    _save(figure, "figure_1_framework")


def _plot_peak_map(countries: gpd.GeoDataFrame) -> None:
    with xr.open_dataset(CUBE) as dataset:
        peak = dataset["marginal_human_burden_per_gj"].max("time").values
        latitude = dataset["lat"].values
        longitude = dataset["lon"].values
    wrapped = ((longitude + 180.0) % 360.0) - 180.0
    order = np.argsort(wrapped)
    figure, axis = plt.subplots(figsize=(10.5, 4.8))
    image = axis.pcolormesh(
        wrapped[order],
        latitude,
        np.log10(peak[:, order] + 1.0),
        shading="auto",
        cmap="viridis",
    )
    countries.boundary.plot(ax=axis, color="white", linewidth=0.35, alpha=0.8)
    axis.set(
        xlim=(-180.0, 180.0),
        ylim=(-90.0, 90.0),
        xlabel="Longitude",
        ylabel="Latitude",
        title="Annual peak marginal heat burden",
    )
    colorbar = figure.colorbar(image, ax=axis, pad=0.02)
    colorbar.set_label("log10(maximum marginal burden per GJ + 1)")
    figure.tight_layout()
    _save(figure, "supplementary_figure_s4_peak_marginal_burden_map")


def _plot_seasonal_day_night(seasonal: pd.DataFrame) -> None:
    seasons = ["DJF", "MAM", "JJA", "SON"]
    day = seasonal.set_index(["season", "local_period"]).loc[
        [(season, "day") for season in seasons]
    ]
    night = seasonal.set_index(["season", "local_period"]).loc[
        [(season, "night") for season in seasons]
    ]
    positions = np.arange(len(seasons))
    width = 0.36
    figure, axis = plt.subplots(figsize=(7.5, 4.5))
    axis.bar(
        positions - width / 2,
        day["marginal_burden_p95"],
        width,
        label="Local day",
        color="#e69f00",
    )
    axis.bar(
        positions + width / 2,
        night["marginal_burden_p95"],
        width,
        label="Local night",
        color="#0072b2",
    )
    axis.set_xticks(positions, seasons)
    axis.set(
        ylabel="95th percentile marginal burden per GJ",
        xlabel="Meteorological season",
        title="Upper-tail heat burden persists by day and night",
    )
    axis.legend(frameon=False)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    _save(figure, "supplementary_figure_s5_seasonal_day_night")


def _plot_primary_transfer(
    countries: gpd.GeoDataFrame,
    allocations: pd.DataFrame,
) -> None:
    selected = allocations[
        (allocations["analysis"] == "spatial")
        & (allocations["scenario"] == "primary_land_noncryosphere")
        & np.isclose(
            allocations["transport_penalty_per_gj_km"],
            1.0e-5,
        )
    ].iloc[0]
    source_longitude = ((selected["source_longitude"] + 180.0) % 360.0) - 180.0
    sink_longitude = ((selected["sink_longitude"] + 180.0) % 360.0) - 180.0
    figure, axis = plt.subplots(figsize=(7.5, 4.8))
    countries.boundary.plot(ax=axis, color="#666666", linewidth=0.55)
    axis.annotate(
        "",
        xy=(sink_longitude, selected["sink_latitude"]),
        xytext=(source_longitude, selected["source_latitude"]),
        arrowprops={"arrowstyle": "->", "color": "#d55e00", "lw": 2.0},
    )
    axis.scatter(
        [source_longitude],
        [selected["source_latitude"]],
        c="#cc79a7",
        edgecolor="black",
        s=75,
        label=f"Source: {selected['source_country']}",
        zorder=3,
    )
    axis.scatter(
        [sink_longitude],
        [selected["sink_latitude"]],
        c="#0072b2",
        edgecolor="black",
        s=75,
        label=f"Sink: {selected['sink_country']}",
        zorder=3,
    )
    axis.set(
        xlim=(75.0, 105.0),
        ylim=(15.0, 38.0),
        xlabel="Longitude",
        ylabel="Latitude",
        title="A small transport penalty selects a nearby land sink",
    )
    axis.legend(frameon=True, loc="lower left")
    figure.tight_layout()
    _save(figure, "figure_2_primary_spatial_transfer")


def _plot_mode_comparison(matched: pd.DataFrame) -> None:
    selected = matched.set_index("analysis").loc[["spatial", "temporal", "joint"]]
    temporal_lag_hours = int(selected.loc["temporal", "lag_steps"]) * 6
    figure, axis = plt.subplots(figsize=(6.8, 4.5))
    labels = ["Spatial", f"Temporal ({temporal_lag_hours} h)", "Joint"]
    colors = ["#0072b2", "#009e73", "#d55e00"]
    bars = axis.bar(labels, selected["net_benefit"], color=colors)
    axis.bar_label(bars, fmt="%.1f", padding=3)
    axis.set(
        ylabel="Net marginal burden reduction per GJ",
        title="Matched-event comparison at the peak source cell-time",
    )
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    _save(figure, "figure_3_allocation_mode_comparison")


def _plot_safety_ablation(
    countries: gpd.GeoDataFrame,
    safety: pd.DataFrame,
) -> None:
    labels = {
        "unrestricted_global": "Unrestricted",
        "distance_only": "Distance only",
        "plus_cryosphere_exclusion": "+ cryosphere exclusion",
        "plus_ocean_exclusion": "+ ocean exclusion",
        "plus_ocean_and_cryosphere_exclusion": "+ ocean and cryosphere",
    }
    figure, axis = plt.subplots(figsize=(10.0, 4.8))
    countries.boundary.plot(ax=axis, color="#777777", linewidth=0.4)
    axis.scatter(
        safety["source_longitude"],
        safety["source_latitude"],
        c="#cc79a7",
        edgecolor="black",
        marker="*",
        s=130,
        label="Common source",
        zorder=4,
    )
    colors = ["#0072b2" if ocean else "#009e73" for ocean in safety["sink_is_ocean"]]
    plotted = safety.assign(
        wrapped_longitude=lambda frame: ((frame["sink_longitude"] + 180.0) % 360.0)
        - 180.0,
        label=lambda frame: frame["scenario"].map(labels),
        color=colors,
    )
    grouped = plotted.groupby(
        ["wrapped_longitude", "sink_latitude", "sink_is_ocean"],
        sort=False,
    )
    for (longitude, latitude, is_ocean), group in grouped:
        color = "#0072b2" if is_ocean else "#009e73"
        axis.scatter(
            longitude,
            latitude,
            color=color,
            edgecolor="black",
            s=55,
            zorder=4,
        )
        axis.annotate(
            "\n".join(group["label"]),
            (longitude, latitude),
            xytext=(5, 7),
            textcoords="offset points",
            fontsize=8,
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.8,
            },
        )
    axis.set(
        xlim=(-180.0, 180.0),
        ylim=(-60.0, 80.0),
        xlabel="Longitude",
        ylabel="Latitude",
        title="Exclusion masks change representative sink geography",
    )
    axis.scatter([], [], color="#0072b2", label="Ocean sink")
    axis.scatter([], [], color="#009e73", label="Land sink")
    axis.legend(frameon=True, loc="lower left", ncol=3)
    figure.tight_layout()
    _save(figure, "supplementary_figure_s6_safety_ablation")


def _plot_joint_sensitivity(allocations: pd.DataFrame) -> None:
    joint = allocations[allocations["analysis"] == "joint"]
    table = joint.pivot(
        index="storage_penalty_per_gj_step",
        columns="transport_penalty_per_gj_km",
        values="net_benefit",
    ).sort_index(ascending=False)
    baseline = float(
        table.loc[
            table.index.min(),
            table.columns.min(),
        ]
    )
    loss = baseline - table
    mode = joint.copy()
    mode["mode"] = np.where(
        np.isclose(mode["distance_km"], 0.0)
        & (mode["source_time"] != mode["sink_time"]),
        "T",
        np.where(mode["source_time"] == mode["sink_time"], "S", "J"),
    )
    mode_table = mode.pivot(
        index="storage_penalty_per_gj_step",
        columns="transport_penalty_per_gj_km",
        values="mode",
    ).sort_index(ascending=False)
    figure, axis = plt.subplots(figsize=(10.0, 5.5))
    image = axis.imshow(
        loss.values,
        aspect="auto",
        cmap="magma",
        vmin=0.0,
        vmax=float(loss.to_numpy().max()),
    )
    for row in range(table.shape[0]):
        for column in range(table.shape[1]):
            axis.text(
                column,
                row,
                f"{mode_table.iloc[row, column]}\n{loss.iloc[row, column]:.1f}",
                ha="center",
                va="center",
                color="white",
                fontsize=9,
            )
    axis.set_xticks(
        range(table.shape[1]),
        [f"{value:g}" for value in table.columns],
    )
    axis.set_yticks(
        range(table.shape[0]),
        [f"{value:g}" for value in table.index],
    )
    axis.set(
        xlabel="Transport penalty per GJ-km",
        ylabel="Storage penalty per GJ-step",
        title="Decision penalties shift the selected mode (S/T/J)",
    )
    figure.colorbar(
        image,
        ax=axis,
        label="Loss of net marginal burden reduction per GJ",
    )
    figure.tight_layout()
    _save(figure, "supplementary_figure_s7_joint_penalty_sensitivity")


def _plot_robustness(robustness: pd.DataFrame) -> None:
    counts = (
        robustness.groupby(["metric", "source_country"])
        .size()
        .rename("scenarios")
        .reset_index()
    )
    labels = [
        f"{row.metric.replace('_', ' ').title()}\n{row.source_country}"
        for row in counts.itertuples()
    ]
    figure, axis = plt.subplots(figsize=(7.4, 4.2))
    bars = axis.bar(
        labels,
        counts["scenarios"],
        color=["#0072b2", "#009e73", "#cc79a7"],
    )
    axis.bar_label(bars, padding=3)
    axis.set(
        ylabel="Parameter scenarios selecting hotspot",
        title="Bangladesh remains the source hotspot in a limited parameter sweep",
    )
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    _save(figure, "supplementary_figure_s1_source_hotspot_robustness")


def _plot_finite_q(finite_q: pd.DataFrame) -> None:
    feasible = finite_q[finite_q["status"] == "feasible"]
    infeasible = finite_q[finite_q["status"] != "feasible"]
    figure, axis = plt.subplots(figsize=(6.8, 4.4))
    axis.plot(
        feasible["energy_gj"],
        feasible["net_benefit_per_gj"],
        marker="o",
        color="#0072b2",
        linewidth=2.0,
    )
    axis.set_xscale("log")
    if not infeasible.empty:
        axis.axvline(
            float(infeasible["energy_gj"].iloc[0]),
            color="#d55e00",
            linestyle="--",
            label="Infeasible under 0.1-K cell cap",
        )
    axis.set(
        xlabel="Transferred heat (GJ)",
        ylabel="Net burden reduction per GJ",
        title="Finite-transfer results remain near-linear until capacity binds",
    )
    axis.legend(frameon=False)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    _save(figure, "supplementary_figure_s2_finite_q_sensitivity")


def _plot_trajectory(
    countries: gpd.GeoDataFrame,
    trajectory: pd.DataFrame,
    redistribution: pd.DataFrame,
) -> None:
    figure, axis = plt.subplots(figsize=(7.4, 5.0))
    countries.boundary.plot(ax=axis, color="#777777", linewidth=0.5)
    axis.plot(
        trajectory["longitude"],
        trajectory["latitude"],
        color="#d55e00",
        linewidth=2.0,
        label="10-m wind trajectory",
    )
    axis.scatter(
        trajectory["longitude"].iloc[0],
        trajectory["latitude"].iloc[0],
        color="#0072b2",
        edgecolor="black",
        s=65,
        label="Release cell",
        zorder=3,
    )
    axis.scatter(
        redistribution["longitude"],
        redistribution["latitude"],
        color="#009e73",
        edgecolor="black",
        s=45,
        label="24, 72, and 168 h",
        zorder=3,
    )
    axis.set(
        xlim=(82.0, 100.0),
        ylim=(22.0, 40.0),
        xlabel="Longitude",
        ylabel="Latitude",
        title="Reduced-order winds move the released-heat trajectory",
    )
    axis.legend(frameon=True, loc="upper right")
    figure.tight_layout()
    _save(figure, "supplementary_figure_s3_wind_trajectory")


def _plot_case_source_and_demand(
    dispatch: pd.DataFrame,
    manuscript_values: pd.DataFrame,
) -> None:
    source = dispatch.loc[
        dispatch["scenario_id"].eq("zero_demand_rejection_baseline"),
        [
            "timestamp",
            "source_observation_available",
            "source_heat_mw",
        ],
    ].copy()
    source["timestamp"] = pd.to_datetime(source["timestamp"])
    source["month"] = source["timestamp"].dt.month
    monthly = source.groupby("month", observed=True)["source_heat_mw"].agg(
        mean="mean",
        p05=lambda values: values.quantile(0.05),
        p95=lambda values: values.quantile(0.95),
    )
    availability = source.groupby("month", observed=True)[
        "source_observation_available"
    ].mean()
    case_a_average = float(manuscript_values.loc["ornl_case_a_average", "value"])
    case_b_average = float(
        manuscript_values.loc["ornl_case_b_selected_average", "value"]
    )
    case_b_maximum = float(
        manuscript_values.loc["ornl_case_b_selected_maximum", "value"]
    )

    figure, (heat_axis, availability_axis) = plt.subplots(
        2,
        1,
        figsize=(9.0, 6.2),
        sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.0]},
    )
    heat_axis.fill_between(
        monthly.index,
        monthly["p05"],
        monthly["p95"],
        color="#56b4e9",
        alpha=0.3,
        label="Monthly 5th-95th percentile",
    )
    heat_axis.plot(
        monthly.index,
        monthly["mean"],
        color="#0072b2",
        marker="o",
        linewidth=2.0,
        label="Monthly mean Frontier waste heat",
    )
    heat_axis.axhline(
        case_a_average,
        color="#009e73",
        linestyle="-",
        label="ORNL Case A average demand bound",
    )
    heat_axis.axhline(
        case_b_average,
        color="#e69f00",
        linestyle="-",
        label="ORNL Case B average demand bound",
    )
    heat_axis.axhline(
        case_b_maximum,
        color="#d55e00",
        linestyle="--",
        label="ORNL Case B maximum demand bound",
    )
    heat_axis.set(
        ylabel="Thermal power (MW)",
        title="Measured Frontier source and reported ORNL demand bounds",
    )
    heat_axis.legend(loc="upper right", fontsize=8, ncol=2)
    heat_axis.spines[["top", "right"]].set_visible(False)

    availability_axis.bar(
        availability.index,
        availability * 100.0,
        color="#999999",
        width=0.72,
    )
    availability_axis.set(
        xlabel="Month of 2023",
        ylabel="Available\nintervals (%)",
        xticks=range(1, 13),
        ylim=(0.0, 105.0),
    )
    availability_axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    _save(figure, "figure_4_case_source_and_demand")


def _plot_constraint_waterfall(waterfall: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(10.5, 5.6), sharex=True)
    palette = {
        "THEORETICAL_ONLY": "#0072b2",
        "SUPPORTED_INPUT": "#009e73",
        "CONDITIONAL": "#e69f00",
        "EXCLUDED": "#d55e00",
    }
    titles = {
        "burden_space": "Global burden-space branch",
        "physical_energy": "Real physical-energy branch",
    }
    for axis, waterfall_id in zip(
        axes,
        ("burden_space", "physical_energy"),
        strict=True,
    ):
        subset = waterfall.loc[waterfall["waterfall_id"].eq(waterfall_id)].copy()
        colors = [palette.get(value, "#999999") for value in subset["eligibility"]]
        axis.scatter(
            subset["stage_order"],
            np.zeros(len(subset)),
            s=520,
            c=colors,
            edgecolor="white",
            linewidth=1.4,
            zorder=3,
        )
        axis.plot(
            subset["stage_order"],
            np.zeros(len(subset)),
            color="#777777",
            linewidth=2.0,
            zorder=1,
        )
        for row in subset.itertuples(index=False):
            axis.text(
                row.stage_order,
                0.0,
                str(row.stage_order),
                ha="center",
                va="center",
                color="white",
                weight="bold",
                fontsize=9,
                zorder=4,
            )
        axis.set(
            ylim=(-0.5, 0.5),
            yticks=[],
            title=titles[waterfall_id],
        )
        axis.spines[["top", "right", "left", "bottom"]].set_visible(False)
    final_subset = waterfall.loc[
        waterfall["waterfall_id"].eq("physical_energy")
    ].sort_values("stage_order")
    axes[-1].set_xticks(
        final_subset["stage_order"],
        [
            label.replace(" and ", " & ").replace(" ", "\n")
            for label in final_subset["stage_label"]
        ],
        fontsize=8,
    )
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markeredgecolor="white",
            markersize=11,
            label=label.replace("_", " ").title(),
        )
        for label, color in palette.items()
    ]
    figure.legend(handles=handles, loc="lower center", ncol=4, frameon=False)
    figure.suptitle(
        "Constraint attrition prevents a supported practical endpoint",
        fontsize=15,
    )
    figure.tight_layout(rect=(0.0, 0.09, 1.0, 0.95))
    _save(figure, "figure_5_constraint_waterfall")


def _plot_practical_modes(pareto: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(8.2, 5.4))
    colors = {
        "reported_lower_bound": "#0072b2",
        "reported_upper_bound": "#d55e00",
    }
    markers = {
        "none": "o",
        "minimum_formula": "s",
        "generic_reference": "^",
    }
    labels = {
        "none": "Direct reuse",
        "minimum_formula": "Formula-sized storage",
        "generic_reference": "Generic-reference storage",
    }
    for row in pareto.itertuples(index=False):
        axis.scatter(
            row.demand_served_fraction * 100.0,
            row.residual_source_rejection_mwh / 1000.0,
            s=125,
            color=colors[row.demand_basis],
            marker=markers[row.storage_basis],
            edgecolor="black",
            linewidth=0.7,
            zorder=3,
        )
        axis.annotate(
            labels[row.storage_basis],
            (
                row.demand_served_fraction * 100.0,
                row.residual_source_rejection_mwh / 1000.0,
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    axis.set(
        xlabel="Demand served (%)",
        ylabel="Residual source rejection (GWh-th)",
        title="All evaluated practical modes remain conditional",
    )
    axis.spines[["top", "right"]].set_visible(False)
    color_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markeredgecolor="black",
            markersize=9,
            label=label,
        )
        for label, color in (
            ("Reported lower demand bound", colors["reported_lower_bound"]),
            ("Reported upper demand bound", colors["reported_upper_bound"]),
        )
    ]
    axis.legend(handles=color_handles, loc="best", fontsize=9)
    figure.tight_layout()
    _save(figure, "figure_6_practical_modes")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.png", "*.svg"):
        for path in OUTPUT.glob(pattern):
            path.unlink()
    countries = gpd.read_file(f"zip://{COUNTRIES}")[["ADMIN", "geometry"]]
    allocations = pd.read_csv(ALLOCATIONS)
    robustness = pd.read_csv(ROBUSTNESS)
    safety = pd.read_csv(SAFETY)
    seasonal = pd.read_csv(SEASONAL)
    finite_q = pd.read_csv(FINITE_Q)
    redistribution = pd.read_csv(REDISTRIBUTION)
    trajectory = pd.read_csv(TRAJECTORY)
    matched = pd.read_csv(MATCHED)
    dispatch = pd.read_csv(DISPATCH, parse_dates=["timestamp"])
    pareto = pd.read_csv(PARETO)
    waterfall = pd.read_csv(WATERFALL)
    manuscript_values = pd.read_csv(MANUSCRIPT_VALUES).set_index("value_id")
    _plot_framework()
    _plot_peak_map(countries)
    _plot_seasonal_day_night(seasonal)
    _plot_primary_transfer(countries, allocations)
    _plot_mode_comparison(matched)
    _plot_safety_ablation(countries, safety)
    _plot_joint_sensitivity(allocations)
    _plot_case_source_and_demand(dispatch, manuscript_values)
    _plot_constraint_waterfall(waterfall)
    _plot_practical_modes(pareto)
    _plot_robustness(robustness)
    _plot_finite_q(finite_q)
    _plot_trajectory(countries, trajectory, redistribution)
    print("Wrote six main and seven supplementary figures as PNG, SVG, and PDF.")


if __name__ == "__main__":
    main()
