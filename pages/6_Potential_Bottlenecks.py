"""
Page 6: Potential Bottlenecks & Quadrant Screening.
Identifies high-volume, high-delay fulfillment routes across the network using
transparent 75th percentile and median screening rules (FR-11, AD-08).
Enforces N >= 30 sample size guardrails (AD-07) and provides interactive Plotly
scatter visualization with threshold reference lines, inspection tables, and audited CSV exports.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app import (
    get_active_dataset,
    render_layer_banner,
    render_margin_disclaimer,
    render_sidebar_filters,
)
from src.bottleneck_rules import flag_bottlenecks
from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
)
from src.exports import create_export_csv
from src.route_analysis import (
    aggregate_routes,
    aggregate_state_metrics,
    filter_eligible_routes,
)


st.set_page_config(
    page_title="Potential Bottlenecks | Nassau Route Intelligence",
    page_icon="⚠️",
    layout="wide",
)

QUADRANT_COLOR_MAP = {
    "Critical Bottleneck (High Vol, High Delay)": "#d62728",
    "Watchlist (High Vol, Moderate Delay)": "#ff7f0e",
    "Efficient High Volume (High Vol, Low Delay)": "#2ca02c",
    "Secondary Distress (Low Vol, High Delay)": "#9467bd",
    "Normal / Low Volume (Low Vol, Low Delay)": "#7f7f7f",
}

QUADRANT_SYMBOL_MAP = {
    "Critical Bottleneck (High Vol, High Delay)": "diamond",
    "Watchlist (High Vol, Moderate Delay)": "square",
    "Efficient High Volume (High Vol, Low Delay)": "circle",
    "Secondary Distress (Low Vol, High Delay)": "triangle-up",
    "Normal / Low Volume (Low Vol, Low Delay)": "circle",
}

QUADRANT_ORDER = [
    "Critical Bottleneck (High Vol, High Delay)",
    "Watchlist (High Vol, Moderate Delay)",
    "Efficient High Volume (High Vol, Low Delay)",
    "Secondary Distress (Low Vol, High Delay)",
    "Normal / Low Volume (Low Vol, Low Delay)",
]


def build_quadrant_scatter_figure(
    df: pd.DataFrame,
    vol_threshold: float,
    delay_threshold_pct: float,
    med_delay_pct: float,
    level_label: str = "Route",
) -> go.Figure:
    """
    Constructs an interactive Plotly quadrant scatter plot of Volume vs Delay Rate
    with 75th percentile and median reference lines and color-coded quadrant categories.
    """
    plot_df = df.copy()
    if "delay_rate_pct" not in plot_df.columns:
        plot_df["delay_rate_pct"] = np.round(plot_df["delay_rate"] * 100.0, 1)

    key_col = "route_key" if "route_key" in plot_df.columns else "State/Province"

    fig = go.Figure()

    for cat in QUADRANT_ORDER:
        cat_df = plot_df[plot_df["quadrant_category"] == cat]
        if cat_df.empty:
            continue

        mean_lt = cat_df["mean_lead_time"] if "mean_lead_time" in cat_df.columns else pd.Series(0.0, index=cat_df.index)
        res_sc = cat_df["res_score"] if "res_score" in cat_df.columns else pd.Series(0.0, index=cat_df.index)

        cd_df = pd.DataFrame({
            "key": cat_df[key_col],
            "sample_size": cat_df["sample_size"],
            "delay_rate_pct": cat_df["delay_rate_pct"],
            "mean_lt": mean_lt,
            "res_sc": res_sc,
            "category": cat_df["quadrant_category"],
        })
        customdata = cd_df.to_numpy()

        fig.add_trace(
            go.Scatter(
                x=cat_df["sample_size"],
                y=cat_df["delay_rate_pct"],
                mode="markers",
                name=cat,
                marker=dict(
                    size=14 if cat.startswith("Critical") else 10,
                    symbol=QUADRANT_SYMBOL_MAP.get(cat, "circle"),
                    color=QUADRANT_COLOR_MAP.get(cat, "#7f7f7f"),
                    opacity=0.85,
                    line=dict(width=1, color="rgb(40,40,40)"),
                ),
                customdata=customdata,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    + "<b>Category:</b> %{customdata[5]}<br><br>"
                    + f"<b>{level_label} Volume:</b> %{{customdata[1]:,}} orders<br>"
                    + "<b>Delay Rate:</b> %{customdata[2]:.1f}%<br>"
                    + "<b>Mean Lead Time:</b> %{customdata[3]:.2f} days<br>"
                    + "<b>RES Score:</b> %{customdata[4]:.1f}<br>"
                    + "<extra></extra>"
                ),
            )
        )

    # Add 75th percentile and median reference lines
    fig.add_vline(
        x=vol_threshold,
        line_dash="dash",
        line_color="#d62728",
        line_width=1.5,
        annotation_text=f"P75 Vol: {vol_threshold:.0f}",
        annotation_position="top left",
    )
    fig.add_hline(
        y=delay_threshold_pct,
        line_dash="dash",
        line_color="#d62728",
        line_width=1.5,
        annotation_text=f"P75 Delay: {delay_threshold_pct:.1f}%",
        annotation_position="bottom right",
    )
    fig.add_hline(
        y=med_delay_pct,
        line_dash="dot",
        line_color="#ff7f0e",
        line_width=1.5,
        annotation_text=f"Median Delay: {med_delay_pct:.1f}%",
        annotation_position="top right",
    )

    fig.update_layout(
        title=f"Potential Bottleneck Screening Quadrant: {level_label} Volume vs Delay Rate",
        xaxis_title=f"{level_label} Volume (Distinct Order Lines, N >= 30)",
        yaxis_title="Delay Rate (%)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=540,
        xaxis=dict(zeroline=False),
        yaxis=dict(zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def render_page():
    filters = render_sidebar_filters()

    st.title("⚠️ Potential Bottlenecks & Quadrant Screening")
    st.markdown(
        "Screening fulfillment routes into performance quadrants based on 75th percentile "
        "order volume and delay rates (FR-11). Identifies **Critical Bottlenecks** and "
        "**Watchlist** routes with sample size guardrails ($N \\ge 30$) to support prioritization."
    )
    render_layer_banner(filters["layer"], filters["scenario"])

    # Load active filtered dataset
    df, ref_means = get_active_dataset(filters)

    st.divider()

    # ==========================================================================
    # 1. Screening Signal & Operational Disclaimer (FR-11, AD-08)
    # ==========================================================================
    st.info(
        "🔍 **Operational Screening Disclosure (FR-11 & AD-08):** "
        "Bottleneck flags are diagnostic screening signals based on comparative volume and delay frequency, "
        "not definitive proof of facility or carrier failure. "
        "True operational root-cause analysis requires external carrier transit logs and warehouse floor records. "
        "Strict delay threshold is currently set at **{:.1f} days**.".format(filters["delay_threshold"]),
        icon="ℹ️",
    )
    # Render AD-11 margin disclaimer prominently
    render_margin_disclaimer()

    if df.empty:
        st.warning("⚠️ No orders found matching active sidebar filters. Please broaden your selection.")
        return

    has_lead_time = "lead_time_days" in df.columns

    if not has_lead_time:
        st.warning(
            "⚠️ Potential bottleneck screening requires calibrated lead times from the **SYNTHETIC** layer (AD-02). "
            "Currently viewing historical records without simulated timing. Select SYNTHETIC layer in sidebar to screen bottlenecks."
        )
        return

    # ==========================================================================
    # 2. Aggregation Level & Screening Parameter Controls
    # ==========================================================================
    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    with ctrl_col1:
        analysis_level = st.radio(
            "Screening Aggregation Dimension",
            options=["Factory → State Routes (Default)", "Destination States Overall"],
            horizontal=True,
            key="radio_screening_level",
            help="Evaluate bottlenecks at the individual Factory-to-State shipping lane grain, or aggregated across all factories by destination State.",
        )
        is_state_level = "States Overall" in analysis_level

    with ctrl_col2:
        st.caption(
            "📌 **Screening Rules (PRD Section 12):**<br>"
            "• **Critical Bottleneck:** Volume $\\ge P_{75}$ AND Delay Rate $\\ge P_{75}$<br>"
            "• **Watchlist:** Volume $\\ge P_{75}$ AND Delay Rate $>$ Median (not Critical)<br>"
            "• **Sample Guardrail:** Ineligible low-sample lanes ($N < 30$) are excluded.",
            unsafe_allow_html=True,
        )

    # Perform aggregation based on selected level
    if is_state_level:
        raw_agg, _ = aggregate_state_metrics(
            df,
            threshold_days=filters["delay_threshold"],
            w_speed=DEFAULT_RES_WEIGHT_SPEED,
            w_var=DEFAULT_RES_WEIGHT_VARIABILITY,
            min_sample=MIN_SAMPLE_SIZE,
        )
        level_label = "State"
    else:
        raw_agg = aggregate_routes(
            df,
            level="state",
            min_sample=MIN_SAMPLE_SIZE,
            threshold_days=filters["delay_threshold"],
            rollup_small_factories=True,
        )
        level_label = "Route"

    eligible_df, low_sample_df = filter_eligible_routes(
        raw_agg,
        min_sample=MIN_SAMPLE_SIZE,
        sample_col="sample_size",
    )

    if eligible_df.empty:
        st.warning("No routes meeting the minimum sample size guardrail ($N \\ge 30$) were found under active filters.")
        return

    # Screen bottlenecks on eligible comparison population
    flagged_df = flag_bottlenecks(eligible_df)
    flagged_df["delay_rate_pct"] = np.round(flagged_df["delay_rate"] * 100.0, 1)

    p_vol = float(flagged_df["p75_volume_threshold"].iloc[0])
    p_delay = float(flagged_df["p75_delay_threshold"].iloc[0])
    p_delay_pct = p_delay * 100.0
    med_delay = float(flagged_df["median_delay_threshold"].iloc[0])
    med_delay_pct = med_delay * 100.0

    critical_df = flagged_df[flagged_df["is_bottleneck"]].copy().reset_index(drop=True)
    watchlist_df = flagged_df[flagged_df["is_watchlist"]].copy().reset_index(drop=True)

    # ==========================================================================
    # 3. Summary KPI Metrics
    # ==========================================================================
    st.divider()
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric(f"Evaluated {level_label}s ($N \\ge 30$)", f"{len(eligible_df):,}")
    with kpi2:
        crit_pct = (len(critical_df) / len(eligible_df) * 100.0) if len(eligible_df) > 0 else 0.0
        st.metric("🚨 Critical Bottlenecks", f"{len(critical_df)}", delta=f"{crit_pct:.1f}% of network", delta_color="inverse")
    with kpi3:
        watch_pct = (len(watchlist_df) / len(eligible_df) * 100.0) if len(eligible_df) > 0 else 0.0
        st.metric("⚠️ Watchlist Lanes", f"{len(watchlist_df)}", delta=f"{watch_pct:.1f}% of network", delta_color="off")
    with kpi4:
        st.metric(f"P75 Volume Threshold", f"{p_vol:,.0f} orders")
    with kpi5:
        st.metric("P75 Delay Rate", f"{p_delay_pct:.1f}%", help=f"Median network delay rate: {med_delay_pct:.1f}%")

    st.divider()

    # ==========================================================================
    # 4. Interactive Plotly Quadrant Scatter Visualizer
    # ==========================================================================
    st.markdown(f"### 1. Interactive Quadrant Scatter Visualizer ({level_label} Level)")

    fig = build_quadrant_scatter_figure(
        flagged_df,
        vol_threshold=p_vol,
        delay_threshold_pct=p_delay_pct,
        med_delay_pct=med_delay_pct,
        level_label=level_label,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "💡 **Quadrant Guide:** Red points in the upper-right quadrant represent **Critical Bottlenecks** (high volume and high delay rates). "
        "Orange points represent the **Watchlist** (high volume with above-median delays). "
        "Green points reflect high-volume, highly efficient operations."
    )

    st.divider()

    # ==========================================================================
    # 5. Bottleneck Tables & Export Engines
    # ==========================================================================
    st.markdown("### 2. Bottleneck Inspection & Prioritization Tables")

    tab_crit, tab_watch, tab_all, tab_low = st.tabs([
        f"🚨 Critical Bottlenecks ({len(critical_df)})",
        f"⚠️ Watchlist ({len(watchlist_df)})",
        f"📋 All Evaluated {level_label}s ({len(eligible_df)})",
        f"🔍 Low-Sample Inspection ({len(low_sample_df)})",
    ])

    key_name = "route_key" if "route_key" in flagged_df.columns else "State/Province"
    display_cols = [
        key_name,
        "sample_size",
        "delay_rate_pct",
        "mean_lead_time",
        "median_lead_time",
        "res_score",
        "quadrant_category",
    ]
    rename_dict = {
        key_name: f"{level_label} Lane",
        "sample_size": "Order Volume (N)",
        "delay_rate_pct": "Delay Rate (%)",
        "mean_lead_time": "Mean Lead Time (d)",
        "median_lead_time": "Median Lead Time (d)",
        "res_score": "RES Score",
        "quadrant_category": "Quadrant Classification",
    }
    valid_cols = [c for c in display_cols if c in flagged_df.columns]

    with tab_crit:
        st.markdown("**Critical Bottlenecks (Upper-Right Quadrant: $\\text{Volume} \\ge P_{75}$ & $\\text{Delay} \\ge P_{75}$)**")
        if critical_df.empty:
            st.success("🎉 No routes currently qualify as Critical Bottlenecks under active filters!")
        else:
            crit_table = critical_df[valid_cols].sort_values(by="sample_size", ascending=False).rename(columns=rename_dict)
            st.dataframe(crit_table, use_container_width=True, hide_index=True)

            csv_crit = create_export_csv(
                critical_df,
                metadata={
                    "layer": filters["layer"],
                    "scenario": filters["scenario"],
                    "delay_threshold": filters["delay_threshold"],
                    "screening": f"{level_label.lower()}_critical_bottlenecks",
                    "filters": filters,
                },
            )
            st.download_button(
                label=f"📥 Download Critical Bottlenecks ({level_label} Level Audited CSV)",
                data=csv_crit,
                file_name=f"nassau_{level_label.lower()}_critical_bottlenecks_{filters['scenario']}.csv",
                mime="text/csv",
                key="dl_crit_csv",
            )

    with tab_watch:
        st.markdown("**Watchlist Lanes (High Volume $\\ge P_{75}$ & Delay Rate $>$ Median)**")
        if watchlist_df.empty:
            st.info("No routes currently meet Watchlist screening criteria.")
        else:
            watch_table = watchlist_df[valid_cols].sort_values(by="delay_rate_pct", ascending=False).rename(columns=rename_dict)
            st.dataframe(watch_table, use_container_width=True, hide_index=True)

            csv_watch = create_export_csv(
                watchlist_df,
                metadata={
                    "layer": filters["layer"],
                    "scenario": filters["scenario"],
                    "delay_threshold": filters["delay_threshold"],
                    "screening": f"{level_label.lower()}_watchlist_routes",
                    "filters": filters,
                },
            )
            st.download_button(
                label=f"📥 Download Watchlist {level_label}s (Audited CSV)",
                data=csv_watch,
                file_name=f"nassau_{level_label.lower()}_watchlist_{filters['scenario']}.csv",
                mime="text/csv",
                key="dl_watch_csv",
            )

    with tab_all:
        st.markdown(f"**All Evaluated {level_label}s ($N \\ge 30$)**")
        all_table = flagged_df[valid_cols].sort_values(by="sample_size", ascending=False).rename(columns=rename_dict)
        st.dataframe(all_table, use_container_width=True, hide_index=True)

        csv_all = create_export_csv(
            flagged_df,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "delay_threshold": filters["delay_threshold"],
                "screening": f"{level_label.lower()}_all_evaluated",
                "filters": filters,
            },
        )
        st.download_button(
            label=f"📥 Download All {level_label}s (Audited CSV)",
            data=csv_all,
            file_name=f"nassau_{level_label.lower()}_all_evaluated_{filters['scenario']}.csv",
            mime="text/csv",
            key="dl_all_csv",
        )

    with tab_low:
        st.markdown(f"**Insufficient Sample Size {level_label}s ($N < 30$ Guardrail)**")
        if low_sample_df.empty:
            st.success(f"All {level_label.lower()}s meet the $N \\ge 30$ sample size threshold!")
        else:
            low_disp = low_sample_df.copy()
            if "delay_rate" in low_disp.columns:
                low_disp["delay_rate_pct"] = np.round(low_disp["delay_rate"] * 100.0, 1)
            low_cols = [c for c in [key_name, "sample_size", "delay_rate_pct", "mean_lead_time"] if c in low_disp.columns]
            low_table = low_disp[low_cols].sort_values(by="sample_size", ascending=False).rename(columns=rename_dict)
            st.dataframe(low_table, use_container_width=True, hide_index=True)

            csv_low = create_export_csv(
                low_sample_df,
                metadata={
                    "layer": filters["layer"],
                    "scenario": filters["scenario"],
                    "delay_threshold": filters["delay_threshold"],
                    "screening": f"{level_label.lower()}_low_sample_ineligible",
                    "filters": filters,
                },
            )
            st.download_button(
                label=f"📥 Download Low-Sample {level_label}s (Audited CSV)",
                data=csv_low,
                file_name=f"nassau_{level_label.lower()}_low_sample_{filters['scenario']}.csv",
                mime="text/csv",
                key="dl_low_csv",
            )

    # Mandatory AD-11 disclaimer
    render_margin_disclaimer()


if __name__ == "__main__":
    render_page()
