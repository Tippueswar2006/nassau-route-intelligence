"""
Standalone Publication Figure Generation Script for Nassau Route Intelligence.
Generates publication-quality, 300 DPI figures using Matplotlib and Seaborn
for academic papers and executive reporting (PRD Section 11 & Story 6.2).
Strictly decoupled from UI libraries (Zero Streamlit imports).
"""

import argparse
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple, Union
import warnings

# Suppress upstream Seaborn/Matplotlib categorical pending deprecations
warnings.filterwarnings("ignore", category=PendingDeprecationWarning, module="seaborn")

# Set headless backend before importing pyplot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import (
    BASELINE_PARQUET,
    DISTANCE_PARQUET,
    STRESS_PARQUET,
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
    ROBUSTNESS_SEEDS,
)
from src.route_analysis import aggregate_routes, filter_eligible_routes
from src.metrics import calculate_route_efficiency_scores
from src.bottleneck_rules import flag_bottlenecks, DEFAULT_TARGET_BOTTLENECK_ROUTES
from src.sensitivity import compute_weight_sensitivity, compute_sample_threshold_sensitivity

DEFAULT_OUTPUT_DIR = BASE_DIR / "docs" / "figures"
DEFAULT_DPI = 300
DEFAULT_FORMATS = ["png", "pdf"]
SYNTHETIC_DISCLOSURE = "SYNTHETIC - NOT ACTUAL PERFORMANCE | Nassau Route Intelligence"


SUPPORTED_FORMATS = {"png", "pdf", "svg", "jpg", "jpeg"}


def _apply_figure_theme() -> None:
    """Applies clean academic styling and typography."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams.update({
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 13,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def _save_figure(
    fig: plt.Figure,
    base_name: str,
    output_dir: Path,
    dpi: int = DEFAULT_DPI,
    formats: Optional[List[str]] = None,
) -> List[Path]:
    """Saves figure in all requested formats at specified DPI."""
    if formats is None:
        formats = DEFAULT_FORMATS

    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for fmt in formats:
        clean_fmt = fmt.strip().lower().replace(".", "")
        if clean_fmt not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported figure format '{clean_fmt}'. Supported: {sorted(list(SUPPORTED_FORMATS))}")
        dest_path = output_dir / f"{base_name}.{clean_fmt}"
        fig.savefig(dest_path, dpi=dpi, bbox_inches="tight")
        saved_paths.append(dest_path)

    return saved_paths


# ──────────────────────────────────────────────────────────────────────────────
# Figure 1: Lead-Time Distributions Across Scenarios
# ──────────────────────────────────────────────────────────────────────────────

def generate_fig1_lead_time_distributions(
    baseline_df: pd.DataFrame,
    distance_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dpi: int = DEFAULT_DPI,
    formats: Optional[List[str]] = None,
) -> Tuple[plt.Figure, List[Path]]:
    """
    Generates Figure 1: KDE density curves and boxplots comparing lead-time
    distributions across Baseline, Distance-Sensitive, and Stress-Test scenarios.
    Highlights the Texas shock disruption delay tail.
    """
    _apply_figure_theme()
    if baseline_df.empty or distance_df.empty or stress_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No shipment scenario data available", ha="center", va="center")
        saved_files = _save_figure(fig, "fig1_lead_time_distributions", output_dir, dpi, formats)
        return fig, saved_files

    fig, (ax_kde, ax_box) = plt.subplots(1, 2, figsize=(12, 5))

    scenarios = [
        ("Baseline (Calibrated)", baseline_df, "#1f77b4", "-"),
        ("Distance-Sensitive", distance_df, "#ff7f0e", "--"),
        ("Stress-Test (Texas Shock)", stress_df, "#d62728", "-"),
    ]

    # Subplot 1: KDE Density
    for label, df, color, linestyle in scenarios:
        sns.kdeplot(
            data=df["lead_time_days"],
            ax=ax_kde,
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=2.0,
            fill=True,
            alpha=0.15,
        )

    ax_kde.axvline(
        DEFAULT_DELAY_THRESHOLD,
        color="#7f7f7f",
        linestyle=":",
        linewidth=1.8,
        label=f"Delay Threshold ({DEFAULT_DELAY_THRESHOLD:0.1f} Days)",
    )
    ax_kde.set_title("A: Order-to-Ship Lead Time Density (KDE)", fontweight="bold")
    ax_kde.set_xlabel("Order-to-Ship Lead Time (Days)")
    ax_kde.set_ylabel("Probability Density")
    ax_kde.set_xlim(0, 16)
    ax_kde.legend(loc="upper right", frameon=True)

    # Subplot 2: Boxplots
    plot_data = pd.DataFrame({
        "Baseline": baseline_df["lead_time_days"],
        "Distance-Sensitive": distance_df["lead_time_days"],
        "Stress-Test": stress_df["lead_time_days"],
    })
    palette = ["#1f77b4", "#ff7f0e", "#d62728"]
    sns.boxplot(
        data=plot_data,
        ax=ax_box,
        palette=palette,
        width=0.45,
        showmeans=True,
        meanprops={"marker": "D", "markeredgecolor": "black", "markerfacecolor": "yellow"},
    )
    ax_box.axhline(
        DEFAULT_DELAY_THRESHOLD,
        color="#7f7f7f",
        linestyle=":",
        linewidth=1.8,
    )
    ax_box.set_title("B: Scenario Dispersion & Outlier Range", fontweight="bold")
    ax_box.set_xlabel("Operational Scenario")
    ax_box.set_ylabel("Order-to-Ship Lead Time (Days)")
    ax_box.set_ylim(0, 16)

    # Supertitle and layer badge
    plt.suptitle("Figure 1: Shipment Lead-Time Distributions Across Operational Scenarios", fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.5, -0.02, SYNTHETIC_DISCLOSURE, ha="center", fontsize=8, color="#555555", style="italic")

    saved_files = _save_figure(fig, "fig1_lead_time_distributions", output_dir, dpi, formats)
    return fig, saved_files


# ──────────────────────────────────────────────────────────────────────────────
# Figure 2: RES Screening Quadrant Scatter
# ──────────────────────────────────────────────────────────────────────────────

def generate_fig2_res_quadrant_scatter(
    baseline_agg_df: pd.DataFrame,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dpi: int = DEFAULT_DPI,
    formats: Optional[List[str]] = None,
) -> Tuple[plt.Figure, List[Path]]:
    """
    Generates Figure 2: Route Efficiency Score (RES) screening quadrant scatter plot
    (Speed Penalty vs. Variability Penalty) with route volume point sizing and
    callout annotations for critical bottleneck routes.
    """
    _apply_figure_theme()
    if baseline_agg_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No route data available", ha="center", va="center")
        saved_files = _save_figure(fig, "fig2_res_quadrant_scatter", output_dir, dpi, formats)
        return fig, saved_files

    eligible_df, _ = filter_eligible_routes(baseline_agg_df, min_sample=MIN_SAMPLE_SIZE)
    scored_df = calculate_route_efficiency_scores(eligible_df, basis="mode_adjusted")
    flagged_df = flag_bottlenecks(scored_df)

    fig, ax = plt.subplots(figsize=(9, 7))

    # Color map by quadrant
    color_map = {
        "Critical Bottleneck (High Vol, High Delay)": "#d62728",      # Red
        "Watchlist (High Vol, Moderate Delay)": "#ff7f0e",            # Orange
        "Efficient High Volume (High Vol, Low Delay)": "#2ca02c",     # Green
        "Secondary Distress (Low Vol, High Delay)": "#9467bd",        # Purple
        "Normal / Low Volume (Low Vol, Low Delay)": "#1f77b4",        # Blue
    }

    # Points sized by sample size (N)
    size_col = "sample_size" if "sample_size" in flagged_df.columns else ("order_line_count" if "order_line_count" in flagged_df.columns else None)

    for cat, color in color_map.items():
        sub = flagged_df[flagged_df["quadrant_category"] == cat]
        if not sub.empty:
            sub_sizes = np.clip(sub[size_col] * 0.8, 40, 260) if size_col else 80.0
            ax.scatter(
                sub["speed_penalty"],
                sub["variability_penalty"],
                s=sub_sizes,
                c=color,
                label=cat,
                alpha=0.75,
                edgecolors="black",
                linewidth=0.8,
            )

    # Quadrant dividing lines
    x_mid = 50.0
    y_mid = 50.0
    ax.axvline(x_mid, color="#888888", linestyle="--", linewidth=1.2)
    ax.axhline(y_mid, color="#888888", linestyle="--", linewidth=1.2)

    # Quadrant background labels
    ax.text(80, 85, "Q1: Critical Bottlenecks\n(Slow & Volatile)", fontsize=9, color="#d62728", ha="center", alpha=0.8, fontweight="bold")
    ax.text(20, 85, "Q2: High Variability\n(Fast but Inconsistent)", fontsize=9, color="#555555", ha="center", alpha=0.7)
    ax.text(20, 15, "Q3: High Efficiency\n(Fast & Predictable)", fontsize=9, color="#2ca02c", ha="center", alpha=0.8, fontweight="bold")
    ax.text(80, 15, "Q4: Low Speed\n(Slow but Predictable)", fontsize=9, color="#555555", ha="center", alpha=0.7)

    # Annotations for key routes
    key_routes = [
        ("Lot's O' Nuts -> Texas", (15, 10)),
        ("Wicked Choccy's -> Texas", (15, -15)),
        ("Hicksville -> New York", (-25, -20)),
    ]
    for r_key, offset in key_routes:
        match = flagged_df[flagged_df["route_key"] == r_key]
        if not match.empty:
            row = match.iloc[0]
            ax.annotate(
                f"{r_key}\n(N={int(row['sample_size'])}, RES={row['res_score']:.1f})",
                xy=(row["speed_penalty"], row["variability_penalty"]),
                xytext=offset,
                textcoords="offset points",
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
                fontsize=8.5,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="black", alpha=0.85),
            )

    ax.set_title("Figure 2: Route Efficiency Score (RES) Screening Quadrant", fontweight="bold", pad=15)
    ax.set_xlabel(r"Speed Penalty Component ($P_{speed} \in [0, 100]$) — Higher is Slower")
    ax.set_ylabel(r"Variability Penalty Component ($P_{var} \in [0, 100]$) — Higher is More Volatile")
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True, title="Quadrant Category")

    fig.text(0.5, -0.02, SYNTHETIC_DISCLOSURE, ha="center", fontsize=8, color="#555555", style="italic")

    saved_files = _save_figure(fig, "fig2_res_quadrant_scatter", output_dir, dpi, formats)
    return fig, saved_files


# ──────────────────────────────────────────────────────────────────────────────
# Figure 3: Scenario Comparison (Lead Time & Delay Rate)
# ──────────────────────────────────────────────────────────────────────────────

def generate_fig3_scenario_comparison_bars(
    baseline_df: pd.DataFrame,
    distance_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dpi: int = DEFAULT_DPI,
    formats: Optional[List[str]] = None,
) -> Tuple[plt.Figure, List[Path]]:
    """
    Generates Figure 3: Side-by-side grouped bar charts comparing Mean Lead Time
    and Delay Rate (%) across scenarios for the Entire Network vs. Target Texas Routes.
    """
    _apply_figure_theme()
    if baseline_df.empty or distance_df.empty or stress_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No scenario data available", ha="center", va="center")
        saved_files = _save_figure(fig, "fig3_scenario_comparison_bars", output_dir, dpi, formats)
        return fig, saved_files

    fig, (ax_lt, ax_dr) = plt.subplots(1, 2, figsize=(12, 5))

    scenarios = [
        ("Baseline", baseline_df),
        ("Distance-Sens.", distance_df),
        ("Stress-Test", stress_df),
    ]

    records = []
    for sc_name, df in scenarios:
        # 1. Entire Network
        net_mean_lt = df["lead_time_days"].mean()
        net_delay_rate = (df["lead_time_days"] > DEFAULT_DELAY_THRESHOLD).mean() * 100.0

        # 2. Texas Target Destination
        dest_col = "State/Province" if "State/Province" in df.columns else ("analysis_destination" if "analysis_destination" in df.columns else None)
        tx_sub = df[df[dest_col] == "Texas"] if (dest_col is not None and not df.empty) else pd.DataFrame()
        tx_mean_lt = tx_sub["lead_time_days"].mean() if not tx_sub.empty else 0.0
        tx_delay_rate = ((tx_sub["lead_time_days"] > DEFAULT_DELAY_THRESHOLD).mean() * 100.0) if not tx_sub.empty else 0.0

        records.append({
            "Scenario": sc_name,
            "Network Mean Lead Time": net_mean_lt,
            "Texas Mean Lead Time": tx_mean_lt,
            "Network Delay Rate": net_delay_rate,
            "Texas Delay Rate": tx_delay_rate,
        })

    comp_df = pd.DataFrame(records)

    x = np.arange(len(comp_df))
    width = 0.35

    # Panel A: Mean Lead Time
    rects1 = ax_lt.bar(x - width/2, comp_df["Network Mean Lead Time"], width, label="Entire Network", color="#1f77b4", edgecolor="black")
    rects2 = ax_lt.bar(x + width/2, comp_df["Texas Mean Lead Time"], width, label="Texas Destination", color="#d62728", edgecolor="black")
    ax_lt.axhline(DEFAULT_DELAY_THRESHOLD, color="#7f7f7f", linestyle=":", linewidth=1.5, label=f"Delay Threshold ({DEFAULT_DELAY_THRESHOLD:0.1f}d)")

    ax_lt.set_title("A: Order-to-Ship Mean Lead Time (Days)", fontweight="bold")
    ax_lt.set_ylabel("Lead Time (Days)")
    ax_lt.set_xticks(x)
    ax_lt.set_xticklabels(comp_df["Scenario"])
    ax_lt.set_ylim(0, 8)
    ax_lt.legend(loc="upper left")

    # Add bar values
    for rect in rects1:
        h = rect.get_height()
        ax_lt.annotate(f"{h:.2f}d", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                       textcoords="offset points", ha="center", va="bottom", fontsize=8)
    for rect in rects2:
        h = rect.get_height()
        ax_lt.annotate(f"{h:.2f}d", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                       textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

    # Panel B: Delay Rate (%)
    rects3 = ax_dr.bar(x - width/2, comp_df["Network Delay Rate"], width, label="Entire Network", color="#1f77b4", edgecolor="black")
    rects4 = ax_dr.bar(x + width/2, comp_df["Texas Delay Rate"], width, label="Texas Destination", color="#d62728", edgecolor="black")

    ax_dr.set_title("B: Delayed Orders Rate (% > 6 Days)", fontweight="bold")
    ax_dr.set_ylabel("Delayed Orders (%)")
    ax_dr.set_xticks(x)
    ax_dr.set_xticklabels(comp_df["Scenario"])
    ax_dr.set_ylim(0, 65)
    ax_dr.legend(loc="upper left")

    for rect in rects3:
        h = rect.get_height()
        ax_dr.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                       textcoords="offset points", ha="center", va="bottom", fontsize=8)
    for rect in rects4:
        h = rect.get_height()
        ax_dr.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                       textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.suptitle("Figure 3: Operational Scenario Comparison — Network vs. Disrupted Texas Routes", fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.5, -0.02, SYNTHETIC_DISCLOSURE, ha="center", fontsize=8, color="#555555", style="italic")

    saved_files = _save_figure(fig, "fig3_scenario_comparison_bars", output_dir, dpi, formats)
    return fig, saved_files


# ──────────────────────────────────────────────────────────────────────────────
# Figure 4: Weight Sensitivity & Sample Size Trade-offs
# ──────────────────────────────────────────────────────────────────────────────

def generate_fig4_weight_sensitivity_and_thresholds(
    baseline_agg_df: pd.DataFrame,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dpi: int = DEFAULT_DPI,
    formats: Optional[List[str]] = None,
) -> Tuple[plt.Figure, List[Path]]:
    """
    Generates Figure 4: Dual-panel visualization showing RES rank correlations
    (Spearman rho) across weight profiles and the sample size threshold trade-off curve.
    """
    _apply_figure_theme()
    if baseline_agg_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No route data available", ha="center", va="center")
        saved_files = _save_figure(fig, "fig4_weight_sensitivity_and_thresholds", output_dir, dpi, formats)
        return fig, saved_files

    eligible_df, _ = filter_eligible_routes(baseline_agg_df, min_sample=MIN_SAMPLE_SIZE)

    # 1. Weight Sensitivity
    weights_list = [
        (0.70, 0.30),
        (0.50, 0.50),
        (0.90, 0.10),
        (1.00, 0.00),
        (0.00, 1.00),
    ]
    _, summary = compute_weight_sensitivity(eligible_df, weights_list=weights_list)
    p_metrics = summary["profile_metrics"]

    profiles = [
        ("70/30 (Base)", p_metrics["70_30"]["spearman_rho"], "#1f77b4"),
        ("90/10 (Speed)", p_metrics["90_10"]["spearman_rho"], "#2ca02c"),
        ("50/50 (Balanced)", p_metrics["50_50"]["spearman_rho"], "#ff7f0e"),
        ("100/0 (Speed-Only)", p_metrics["100_0"]["spearman_rho"], "#8c564b"),
        ("0/100 (Var-Only)", p_metrics["0_100"]["spearman_rho"], "#9467bd"),
    ]

    # 2. Sample Size Threshold Trade-offs
    thresh_df = compute_sample_threshold_sensitivity(baseline_agg_df)

    fig, (ax_weights, ax_thresh) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A: Weight Sensitivity Bars
    names = [p[0] for p in profiles]
    rhos = [p[1] for p in profiles]
    colors = [p[2] for p in profiles]

    bars = ax_weights.bar(names, rhos, color=colors, width=0.55, edgecolor="black")
    ax_weights.axhline(0.85, color="#d62728", linestyle="--", linewidth=1.5, label="High Stability Benchmark (ρ ≥ 0.85)")
    ax_weights.set_title("A: RES Rank Correlation (Spearman ρ vs. 70/30)", fontweight="bold")
    ax_weights.set_ylabel("Spearman Rank Correlation (ρ)")
    ax_weights.set_ylim(0, 1.15)
    ax_weights.set_xticks(range(len(names)))
    ax_weights.set_xticklabels(names, rotation=20, ha="right")
    ax_weights.legend(loc="upper right")

    for bar, rho in zip(bars, rhos):
        ax_weights.annotate(
            f"ρ = {rho:.3f}",
            xy=(bar.get_x() + bar.get_width() / 2, rho),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )

    # Panel B: Dual-Axis Sample Threshold Curve
    ax_routes = ax_thresh
    ax_orders = ax_thresh.twinx()

    x_vals = thresh_df["min_sample_threshold"]
    line1 = ax_routes.plot(
        x_vals,
        thresh_df["eligible_route_count"],
        marker="o",
        color="#1f77b4",
        linewidth=2.2,
        label="Eligible Routes",
    )
    line2 = ax_orders.plot(
        x_vals,
        thresh_df["order_coverage_pct"],
        marker="s",
        color="#2ca02c",
        linewidth=2.2,
        linestyle="--",
        label="Volume Coverage (%)",
    )

    # Selected N = 30 marker
    ax_routes.axvline(30, color="#d62728", linestyle=":", linewidth=1.8, label="Selected Guardrail (N = 30)")

    ax_routes.set_title("B: Sample Size Guardrail Trade-off (N ≥ Threshold)", fontweight="bold")
    ax_routes.set_xlabel("Minimum Order-Line Sample Size Threshold (N)")
    ax_routes.set_ylabel("Number of Eligible Routes", color="#1f77b4")
    ax_orders.set_ylabel("Network Volume Coverage (%)", color="#2ca02c")
    ax_routes.set_xticks(x_vals)
    ax_orders.set_ylim(0, 105)

    # Combined legend
    lines = line1 + line2 + [ax_routes.lines[-1]]
    labels = [l.get_label() for l in lines]
    ax_routes.legend(lines, labels, loc="lower left")

    plt.suptitle("Figure 4: Scoring Weight Sensitivity and Sample Size Guardrail Trade-offs", fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.5, -0.02, SYNTHETIC_DISCLOSURE, ha="center", fontsize=8, color="#555555", style="italic")

    saved_files = _save_figure(fig, "fig4_weight_sensitivity_and_thresholds", output_dir, dpi, formats)
    return fig, saved_files


# ──────────────────────────────────────────────────────────────────────────────
# Master Generation & CLI Interface
# ──────────────────────────────────────────────────────────────────────────────

def generate_all_figures(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dpi: int = DEFAULT_DPI,
    formats: Optional[List[str]] = None,
) -> Dict[str, List[Path]]:
    """
    Loads all synthetic Parquet datasets and generates the full set of 4
    publication figures into the target directory.
    """
    if formats is None:
        formats = DEFAULT_FORMATS

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check input files
    for p_path in [BASELINE_PARQUET, DISTANCE_PARQUET, STRESS_PARQUET]:
        if not p_path.exists():
            raise FileNotFoundError(f"Required synthetic artifact not found: {p_path}")

    # Load synthetic scenario datasets
    print("Loading synthetic scenario artifacts...")
    baseline_df = pd.read_parquet(BASELINE_PARQUET)
    distance_df = pd.read_parquet(DISTANCE_PARQUET)
    stress_df = pd.read_parquet(STRESS_PARQUET)

    # Route aggregates
    print("Computing route aggregates for baseline scenario...")
    baseline_agg_df = aggregate_routes(baseline_df, level="state", rollup_small_factories=False)

    generated: Dict[str, List[Path]] = {}

    try:
        print(f"Generating Figure 1: Lead-time distributions (DPI={dpi}, Formats={formats})...")
        fig1, paths1 = generate_fig1_lead_time_distributions(baseline_df, distance_df, stress_df, output_dir, dpi, formats)
        plt.close(fig1)
        generated["fig1"] = paths1

        print(f"Generating Figure 2: RES screening quadrant scatter...")
        fig2, paths2 = generate_fig2_res_quadrant_scatter(baseline_agg_df, output_dir, dpi, formats)
        plt.close(fig2)
        generated["fig2"] = paths2

        print(f"Generating Figure 3: Scenario comparison bars...")
        fig3, paths3 = generate_fig3_scenario_comparison_bars(baseline_df, distance_df, stress_df, output_dir, dpi, formats)
        plt.close(fig3)
        generated["fig3"] = paths3

        print(f"Generating Figure 4: Weight sensitivity & sample threshold trade-offs...")
        fig4, paths4 = generate_fig4_weight_sensitivity_and_thresholds(baseline_agg_df, output_dir, dpi, formats)
        plt.close(fig4)
        generated["fig4"] = paths4

        print(f"Successfully generated all {len(generated)} figures into {output_dir}")
        return generated
    finally:
        plt.close("all")


def main() -> int:
    """CLI Entrypoint."""
    parser = argparse.ArgumentParser(
        description="Generates publication-quality 300 DPI figures for Nassau Route Intelligence academic paper."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save generated figures (default: docs/figures)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help="Figure DPI resolution (default: 300)",
    )
    parser.add_argument(
        "--formats",
        type=str,
        default="png,pdf",
        help="Comma-separated file formats to save (default: png,pdf)",
    )

    args = parser.parse_args()
    formats_list = [f.strip() for f in args.formats.split(",") if f.strip()]

    try:
        results = generate_all_figures(
            output_dir=args.output_dir,
            dpi=args.dpi,
            formats=formats_list,
        )
        total_files = sum(len(paths) for paths in results.values())
        print(f"\nDone: {len(results)} figures ({total_files} files) successfully exported to {args.output_dir}")
        return 0
    except Exception as e:
        print(f"\nERROR generating publication figures: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
