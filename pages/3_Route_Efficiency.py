"""
Page 3: Route Efficiency Leaderboard.
Fixed 70/30 RES scoring math (AD-06), sample size threshold guardrails N >= 30 (AD-07),
Top 10 and Bottom 10 leaderboards, mode-adjusted vs raw toggle with rank deltas,
and dedicated low-sample inspection table.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import streamlit as st

from app import (
    get_active_dataset,
    render_layer_banner,
    render_sidebar_filters,
)
from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
)
from src.exports import create_export_csv
from src.metrics import calculate_route_efficiency_scores
from src.route_analysis import (
    aggregate_routes,
    filter_eligible_routes,
    generate_leaderboards,
)


st.set_page_config(
    page_title="Route Efficiency Leaderboard | Nassau Route Intelligence",
    page_icon="🏆",
    layout="wide",
)


def compute_leaderboard_data(
    df: pd.DataFrame,
    min_sample: int = MIN_SAMPLE_SIZE,
    threshold_days: float = DEFAULT_DELAY_THRESHOLD,
    w_speed: float = DEFAULT_RES_WEIGHT_SPEED,
    w_var: float = DEFAULT_RES_WEIGHT_VARIABILITY,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregates routes, filters sample size N >= 30, and computes both mode-adjusted
    and raw scores with rank deltas for side-by-side comparison.
    """
    agg = aggregate_routes(
        df,
        level="state",
        min_sample=min_sample,
        threshold_days=threshold_days,
        rollup_small_factories=True,
        w_speed=w_speed,
        w_var=w_var,
    )

    eligible_df, low_sample_df = filter_eligible_routes(
        agg, min_sample=min_sample, sample_col="sample_size"
    )

    if eligible_df.empty:
        return eligible_df, low_sample_df

    # 1. Mode-adjusted score (default)
    mode_adj_scored = calculate_route_efficiency_scores(
        eligible_df, basis="mode_adjusted", w_speed=w_speed, w_var=w_var
    )
    eligible_df["res_mode_adj"] = mode_adj_scored["res_score"]
    eligible_df["speed_only_score"] = mode_adj_scored["speed_only_score"]

    # 2. Raw lead-time score
    raw_scored = calculate_route_efficiency_scores(
        eligible_df, basis="raw", w_speed=w_speed, w_var=w_var
    )
    eligible_df["res_raw"] = raw_scored["res_score"]

    # 3. Calculate ranks and delta (Rank delta: positive = improved under mode adjustment)
    eligible_df["rank_mode_adj"] = eligible_df["res_mode_adj"].rank(ascending=False, method="min").astype(int)
    eligible_df["rank_raw"] = eligible_df["res_raw"].rank(ascending=False, method="min").astype(int)
    eligible_df["rank_delta"] = eligible_df["rank_raw"] - eligible_df["rank_mode_adj"]

    return eligible_df, low_sample_df


def render_page():
    filters = render_sidebar_filters()

    st.title("🏆 Route Efficiency Leaderboard (Fixed 70/30 RES)")
    st.markdown(
        "Benchmarking route performance across the distribution network. "
        "Isolates genuine routing efficiency from shipping mode mix while enforcing "
        "sample size guardrails ($N \\ge 30$)."
    )
    render_layer_banner(filters["layer"], filters["scenario"])

    df, ref_means = get_active_dataset(filters)

    st.divider()

    # ==========================================================================
    # 1. Scoring Basis Controls & Fixed Weight Policy (AD-06)
    # ==========================================================================
    ctrl_col1, ctrl_col2 = st.columns([1, 1])

    with ctrl_col1:
        basis_selection = st.radio(
            "Select Lead-Time Scoring Basis",
            options=["Mode-Adjusted RES (Recommended)", "Raw Lead Time RES"],
            index=0,
            horizontal=True,
            help=(
                "Mode-Adjusted RES centers route lead times around ship-mode means before normalising penalties, "
                "preventing Standard Class-heavy routes from being unfairly penalized."
            ),
        )
        use_mode_adj = "Mode-Adjusted" in basis_selection

    with ctrl_col2:
        st.info(
            "📌 **Fixed Weighting Policy (AD-06, Option A):** "
            "70% Speed / 30% Variability weighting is **fixed and invariant** on Pages 1 through 7 for executive consistency. "
            "Interactive sensitivity testing (50/50, 70/30, 90/10) is available on **Page 8: Trends & Scenarios**.",
            icon="ℹ️",
        )

    # Compute leaderboards
    eligible_df, low_sample_df = compute_leaderboard_data(
        df,
        min_sample=MIN_SAMPLE_SIZE,
        threshold_days=filters["delay_threshold"],
        w_speed=DEFAULT_RES_WEIGHT_SPEED,
        w_var=DEFAULT_RES_WEIGHT_VARIABILITY,
    )

    if eligible_df.empty:
        st.warning("No eligible routes found with the active filter selections ($N \\ge 30$). Please adjust filters.")
        return

    # Determine active score and sort column
    score_col = "res_mode_adj" if use_mode_adj else "res_raw"
    eligible_df["active_score"] = eligible_df[score_col]

    top_10, bottom_10 = generate_leaderboards(
        eligible_df, top_n=10, score_col="active_score", min_sample=MIN_SAMPLE_SIZE
    )

    # ==========================================================================
    # 2. Executive Summary Metrics
    # ==========================================================================
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Eligible Routes (N ≥ 30)", f"{len(eligible_df):,}")
    with m2:
        st.metric("Low-Sample Routes (N < 30)", f"{len(low_sample_df):,}")
    with m3:
        st.metric("Delay Threshold", f"{filters['delay_threshold']:.1f} days")
    with m4:
        st.metric("Mean RES Score", f"{eligible_df['active_score'].mean():.1f}")
    with m5:
        st.metric("Top Route Score", f"{eligible_df['active_score'].max():.1f}")

    st.divider()

    # ==========================================================================
    # 3. Leaderboard Presentation Tabs (Top 10 / Bottom 10 / Full Rankings)
    # ==========================================================================
    tab_top, tab_bottom, tab_all = st.tabs([
        "🏆 Top 10 Most Efficient Routes",
        "⚠️ Bottom 10 Least Efficient Routes",
        "📋 Full Eligible Route Rankings",
    ])

    def _format_table(df_subset: pd.DataFrame) -> pd.DataFrame:
        out = df_subset.copy()
        out["res_mode_adj"] = out["res_mode_adj"].apply(lambda x: f"{x:.1f}")
        out["res_raw"] = out["res_raw"].apply(lambda x: f"{x:.1f}")
        out["speed_only_score"] = out["speed_only_score"].apply(lambda x: f"{x:.1f}")
        out["mean_lead_time"] = out["mean_lead_time"].apply(lambda x: f"{x:.2f}d")
        out["std_lead_time"] = out["std_lead_time"].apply(lambda x: f"{x:.2f}d")
        out["delay_rate"] = out["delay_rate"].apply(lambda x: f"{x * 100.0:.1f}%")
        out["rank_delta_fmt"] = out["rank_delta"].apply(
            lambda x: f"+{x}" if x > 0 else (f"{x}" if x < 0 else "0")
        )

        cols = [
            "rank",
            "route_key",
            "sample_size",
            "res_mode_adj",
            "res_raw",
            "rank_delta_fmt",
            "speed_only_score",
            "mean_lead_time",
            "std_lead_time",
            "delay_rate",
        ]
        col_names = [
            "Rank",
            "Route Key",
            "Sample (N)",
            "Mode-Adjusted RES",
            "Raw RES",
            "Rank Delta (Δ)",
            "Speed-Only (100/0)",
            "Mean Lead Time",
            "Variability (Std)",
            f"Delay Rate (>{filters['delay_threshold']:.1f}d)",
        ]
        res_table = out[cols]
        res_table.columns = col_names
        return res_table

    with tab_top:
        st.markdown(f"#### 🏆 Top 10 Routes — Ranked by {basis_selection}")
        st.caption("Highest operational efficiency routes meeting minimum sample size guardrail ($N \\ge 30$).")
        st.dataframe(_format_table(top_10), use_container_width=True, hide_index=True)
        csv_bytes_top = create_export_csv(
            top_10,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "delay_threshold": filters["delay_threshold"],
                "filters": filters,
            },
        )
        st.download_button(
            label="📥 Download Top 10 Routes (Audited CSV)",
            data=csv_bytes_top,
            file_name=f"nassau_top10_routes_{filters['scenario']}.csv",
            mime="text/csv",
        )

    with tab_bottom:
        st.markdown(f"#### ⚠️ Bottom 10 Routes — Ranked by {basis_selection}")
        st.caption("Lowest operational efficiency routes meeting minimum sample size guardrail ($N \\ge 30$).")
        st.dataframe(_format_table(bottom_10), use_container_width=True, hide_index=True)
        csv_bytes_bottom = create_export_csv(
            bottom_10,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "delay_threshold": filters["delay_threshold"],
                "filters": filters,
            },
        )
        st.download_button(
            label="📥 Download Bottom 10 Routes (Audited CSV)",
            data=csv_bytes_bottom,
            file_name=f"nassau_bottom10_routes_{filters['scenario']}.csv",
            mime="text/csv",
        )

    with tab_all:
        st.markdown("#### 📋 Complete Eligible Route Rankings")
        st.caption(f"All {len(eligible_df)} qualifying routes with $N \\ge 30$ order lines.")
        full_sorted = eligible_df.sort_values(by="active_score", ascending=False).reset_index(drop=True)
        full_sorted["rank"] = range(1, len(full_sorted) + 1)
        st.dataframe(_format_table(full_sorted), use_container_width=True, hide_index=True)
        csv_bytes_all = create_export_csv(
            full_sorted,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "delay_threshold": filters["delay_threshold"],
                "filters": filters,
            },
        )
        st.download_button(
            label="📥 Download All Qualifying Routes (Audited CSV)",
            data=csv_bytes_all,
            file_name=f"nassau_qualifying_routes_{filters['scenario']}.csv",
            mime="text/csv",
        )

    st.divider()

    # ==========================================================================
    # 4. Low-Sample Routes / Insufficient Data Table (AD-07)
    # ==========================================================================
    st.markdown("### 4. Insufficient Sample / Low-Volume Routes ($N < 30$)")
    st.markdown(
        "Per **Architecture Decision AD-07**, routes with fewer than 30 order lines are strictly excluded from "
        "Top 10 and Bottom 10 leaderboards to prevent ranking volatility caused by small-sample statistical noise. "
        "These routes are routed to this dedicated inspection table."
    )

    if not low_sample_df.empty:
        disp_low = low_sample_df.copy()
        disp_low = disp_low.sort_values(by="sample_size", ascending=False).reset_index(drop=True)

        disp_cols = ["route_key", "Factory", "sample_size"]
        col_renames = ["Route Key", "Factory Origin", "Sample Size (N)"]

        if "mean_lead_time" in disp_low.columns:
            disp_low["mean_lt_fmt"] = disp_low["mean_lead_time"].apply(lambda x: f"{x:.2f}d" if pd.notna(x) else "N/A")
            disp_cols.append("mean_lt_fmt")
            col_renames.append("Mean Lead Time")

        if "delay_rate" in disp_low.columns:
            disp_low["delay_rate_fmt"] = disp_low["delay_rate"].apply(lambda x: f"{x * 100.0:.1f}%" if pd.notna(x) else "N/A")
            disp_cols.append("delay_rate_fmt")
            col_renames.append(f"Delay Rate (>{filters['delay_threshold']:.1f}d)")

        disp_low["status"] = "⚠️ Low Sample (N < 30)"
        disp_cols.append("status")
        col_renames.append("Guardrail Status")

        final_low = disp_low[disp_cols].copy()
        final_low.columns = col_renames

        with st.expander(f"🔍 Inspect {len(low_sample_df)} Low-Sample Routes", expanded=False):
            st.dataframe(final_low, use_container_width=True, hide_index=True)
    else:
        st.success("All active routes satisfy the $N \\ge 30$ sample threshold.")


if __name__ == "__main__":
    render_page()
