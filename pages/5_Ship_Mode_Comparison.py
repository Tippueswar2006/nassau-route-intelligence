"""
Page 5: Shipping Mode Distribution & Margin-by-Mode Analysis.
Compares order-to-ship lead-time distributions across individual ship modes
(Same Day, First Class, Second Class, Standard Class) and Expedited vs Standard tiers.
Performs distance band analysis (0–500, 500–1500, 1500–3000, 3000+ km) with N >= 30
sample guardrails, and presents commercial gross margins with non-causal disclaimers (FR-10, AD-11).
"""

from typing import Any, Dict
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
from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DISTANCE_BAND_LABELS,
    MIN_SAMPLE_SIZE,
    SHIPPING_MODES,
)
from src.exports import create_export_csv
from src.route_analysis import (
    aggregate_distance_band_metrics,
    aggregate_ship_mode_metrics,
    assign_distance_bands,
    assign_expedited_group,
)


st.set_page_config(
    page_title="Ship Mode Comparison | Nassau Route Intelligence",
    page_icon="🚚",
    layout="wide",
)

MODE_COLOR_MAP = {
    "Same Day": "#1f77b4",
    "First Class": "#2ca02c",
    "Second Class": "#ff7f0e",
    "Standard Class": "#d62728",
    "Expedited": "#2ca02c",
    "Standard": "#d62728",
}


def build_distribution_figure(
    df: pd.DataFrame,
    group_by: str = "Ship Mode",
) -> go.Figure:
    """
    Constructs a box plot showing order-to-ship lead-time distributions
    with explicit quartile whiskers, dashed mean line, and outlier points.
    """
    cat_order = (
        SHIPPING_MODES
        if group_by == "Ship Mode"
        else ["Expedited", "Standard"]
    )

    fig = px.box(
        df,
        x=group_by,
        y="lead_time_days",
        color=group_by,
        points="outliers",
        color_discrete_map=MODE_COLOR_MAP,
        category_orders={group_by: cat_order},
        labels={
            group_by: "Shipping Mode",
            "lead_time_days": "Order-to-Ship Lead Time (Days)",
        },
        title=f"Order-to-Ship Lead Time Distributions ({group_by})",
    )

    # Show dashed mean indicator line inside each box
    fig.update_traces(boxmean=True)

    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        height=450,
        showlegend=False,
        yaxis=dict(title="Lead Time (Days)", zeroline=True),
        xaxis=dict(title="Shipping Method"),
    )

    return fig


def build_distance_band_figure(
    band_df: pd.DataFrame,
) -> go.Figure:
    """
    Constructs an interactive line/marker figure comparing Mean Lead Time
    across geographic Haversine distance bands for each shipping mode with
    consistent colors and canonical category orders.
    """
    fig = px.line(
        band_df,
        x="distance_band",
        y="mean_lead_time",
        color="Ship Mode",
        markers=True,
        color_discrete_map=MODE_COLOR_MAP,
        category_orders={
            "Ship Mode": SHIPPING_MODES,
            "distance_band": DISTANCE_BAND_LABELS,
        },
        labels={
            "distance_band": "Haversine Distance Band",
            "mean_lead_time": "Mean Lead Time (Days)",
            "Ship Mode": "Shipping Mode",
        },
        title="Mean Lead Time Sensitivity across Haversine Distance Bands",
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        height=450,
        xaxis=dict(title="Distance Band (km)"),
        yaxis=dict(title="Mean Lead Time (Days)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def render_page():
    filters = render_sidebar_filters()

    st.title("🚚 Shipping Mode Distribution & Margin-by-Mode Analysis")
    st.markdown(
        "Empirical lead-time distributions across shipping methods, distance-band sensitivity "
        "curves, and descriptive product commercial margins with non-causal disclosures (FR-10, AD-11)."
    )
    render_layer_banner(filters["layer"], filters["scenario"])

    # Load active filtered dataset
    df, ref_means = get_active_dataset(filters)

    st.divider()

    # ==========================================================================
    # 1. Non-Causal & Freight Disclaimer Banner (FR-10, AD-11)
    # ==========================================================================
    st.info(
        "📊 **Descriptive Association Notice (FR-10 & AD-11):** "
        "Performance variations across shipping modes reflect observed empirical distributions and customer selection patterns, "
        "not proven causal mechanisms ('associated with', never 'caused by'). "
        "Reported Cost represents manufacturing COGS only; carrier freight transportation costs are not present in the dataset. "
        "Gross Profit and Margins represent product commercial profitability, not net logistics profitability. "
        "Cross-border Canadian shipments (194 orders) are included in totals and mode volumes.",
        icon="ℹ️",
    )

    if df.empty:
        st.warning("⚠️ No orders found matching active sidebar filters. Please broaden your selection.")
        return

    has_lead_time = "lead_time_days" in df.columns
    has_distance = "distance_km" in df.columns

    # Aggregate metrics
    mode_stats = aggregate_ship_mode_metrics(
        df,
        threshold_days=filters["delay_threshold"],
        group_col="Ship Mode",
    )
    group_stats = aggregate_ship_mode_metrics(
        df,
        threshold_days=filters["delay_threshold"],
        group_col="ship_mode_group",
    )

    # ==========================================================================
    # 2. Executive KPI Summary Cards by Mode
    # ==========================================================================
    st.markdown("### 1. Mode Performance & Commercial Overview")

    kpi_cols = st.columns(4)
    mode_order = ["Same Day", "First Class", "Second Class", "Standard Class"]

    for idx, mode_name in enumerate(mode_order):
        with kpi_cols[idx]:
            row = mode_stats[mode_stats["Ship Mode"] == mode_name]
            if not row.empty:
                r = row.iloc[0]
                vol = int(r["order_line_count"])
                lines = int(r["line_item_count"])
                margin = float(r["gross_margin_pct"]) if "gross_margin_pct" in r else 0.0

                if has_lead_time:
                    mean_lt = f"{r['mean_lead_time']:.2f}d"
                    delay_pct = f"{r['delay_rate_pct']:.1f}%"
                    sub_str = f"Avg Lead Time: {mean_lt} | Delay: {delay_pct}"
                else:
                    sub_str = "Timing: Calibrated Synthetic Only"

                st.metric(
                    label=f"📦 {mode_name}",
                    value=f"{vol:,} Orders",
                    delta=sub_str,
                    delta_color="off",
                    help=f"{lines:,} line items | Product Gross Margin: {margin:.1f}%",
                )
            else:
                st.metric(label=f"📦 {mode_name}", value="0 Orders")

    st.divider()

    # ==========================================================================
    # 3. Lead-Time Distributions (Box Plot & Stats Table)
    # ==========================================================================
    st.markdown("### 2. Order-to-Ship Lead-Time Distributions")

    if not has_lead_time:
        st.warning(
            "⚠️ Lead-time distribution analysis requires calibrated timing from the **SYNTHETIC** layer (AD-02). "
            "Currently viewing historical records without simulated timing. Select SYNTHETIC layer in sidebar to view lead-time distributions."
        )
    else:
        dist_view = st.radio(
            "Distribution Comparison Mode",
            options=["Individual 4 Shipping Modes", "Standard vs. Expedited Tiers"],
            horizontal=True,
            help="Compare all four individual shipping classes or group Same Day/First/Second Class into Expedited.",
        )
        group_col = "Ship Mode" if dist_view == "Individual 4 Shipping Modes" else "ship_mode_group"
        active_stats = mode_stats if group_col == "Ship Mode" else group_stats

        plot_df = df if group_col == "Ship Mode" else assign_expedited_group(df)
        fig_dist = build_distribution_figure(plot_df, group_by=group_col)
        st.plotly_chart(fig_dist, use_container_width=True)

        st.caption(
            "💡 **Distribution Insights:** Whiskers represent 1.5× IQR; dashed lines show distribution means; "
            "points represent individual outlier orders. Same Day and First Class exhibit tight, low-variance lead times, "
            "whereas Standard Class exhibits substantial dispersion."
        )

        # Statistical Distribution Table
        stat_display_cols = [
            group_col,
            "order_line_count",
            "line_item_count",
            "mean_lead_time",
            "median_lead_time",
            "std_lead_time",
            "p25_lead_time",
            "p75_lead_time",
            "iqr_lead_time",
            "p90_lead_time",
            "delayed_count",
            "delay_rate_pct",
        ]
        rename_stat_dict = {
            group_col: "Shipping Mode",
            "order_line_count": "Order Lines",
            "line_item_count": "Line Items",
            "mean_lead_time": "Mean Lead Time (d)",
            "median_lead_time": "Median Lead Time (d)",
            "std_lead_time": "Std Dev (d)",
            "p25_lead_time": "P25 (d)",
            "p75_lead_time": "P75 (d)",
            "iqr_lead_time": "IQR (d)",
            "p90_lead_time": "P90 (d)",
            "delayed_count": "Delayed Orders",
            "delay_rate_pct": f"Delay Rate % (> {filters['delay_threshold']:.1f}d)",
        }
        valid_stat_cols = [c for c in stat_display_cols if c in active_stats.columns]
        stat_table = active_stats[valid_stat_cols].rename(columns=rename_stat_dict)
        st.dataframe(stat_table, use_container_width=True, hide_index=True)

        # CSV Export for Lead-Time Distributions
        csv_bytes_dist = create_export_csv(
            stat_table,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "delay_threshold": filters["delay_threshold"],
                "analysis": "lead_time_distributions",
                "filters": filters,
            },
        )
        st.download_button(
            label="📥 Download Lead-Time Distribution Statistics (Audited CSV)",
            data=csv_bytes_dist,
            file_name=f"nassau_lead_time_distributions_{filters['scenario']}.csv",
            mime="text/csv",
        )

    st.divider()

    # ==========================================================================
    # 4. Haversine Distance Band Analysis (FR-10)
    # ==========================================================================
    st.markdown("### 3. Haversine Distance Band Sensitivity Analysis")
    st.markdown(
        "Evaluating lead-time response across four discrete geographic distance tiers: "
        "**0–500 km**, **500–1,500 km**, **1,500–3,000 km**, and **3,000+ km**. "
        "Enforces minimum sample guardrail ($N \\ge 30$) to prevent spurious small-cell conclusions."
    )

    if not has_distance:
        st.warning("⚠️ Distance coordinates are not available in the active dataset.")
    elif not has_lead_time:
        st.info("Distance-band lead-time comparisons require calibrated timing from the SYNTHETIC data layer.")
    else:
        band_metrics = aggregate_distance_band_metrics(
            df,
            threshold_days=filters["delay_threshold"],
            min_sample=MIN_SAMPLE_SIZE,
        )

        fig_band = build_distance_band_figure(band_metrics)
        st.plotly_chart(fig_band, use_container_width=True)

        # Distance Band Details Table
        band_display_cols = [
            "Ship Mode",
            "distance_band",
            "order_line_count",
            "line_item_count",
            "sample_status",
            "mean_distance_km",
            "mean_lead_time",
            "median_lead_time",
            "p75_lead_time",
            "p90_lead_time",
            "delay_rate_pct",
            "total_sales",
            "gross_margin_pct",
        ]
        rename_band_dict = {
            "Ship Mode": "Shipping Mode",
            "distance_band": "Distance Band",
            "order_line_count": "Order Lines",
            "line_item_count": "Line Items",
            "sample_status": "Sample Guardrail",
            "mean_distance_km": "Avg Distance (km)",
            "mean_lead_time": "Mean Lead Time (d)",
            "median_lead_time": "Median Lead Time (d)",
            "p75_lead_time": "P75 (d)",
            "p90_lead_time": "P90 (d)",
            "delay_rate_pct": "Delay Rate (%)",
            "total_sales": "Sales ($)",
            "gross_margin_pct": "Gross Margin (%)",
        }
        valid_band_cols = [c for c in band_display_cols if c in band_metrics.columns]
        band_table = band_metrics[valid_band_cols].rename(columns=rename_band_dict)
        st.dataframe(band_table, use_container_width=True, hide_index=True)

        # CSV Export for distance band analysis
        csv_bytes_band = create_export_csv(
            band_table,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "delay_threshold": filters["delay_threshold"],
                "analysis": "distance_band_analysis",
                "filters": filters,
            },
        )
        st.download_button(
            label="📥 Download Distance Band Data (Audited CSV)",
            data=csv_bytes_band,
            file_name=f"nassau_distance_band_analysis_{filters['scenario']}.csv",
            mime="text/csv",
        )

    st.divider()

    # ==========================================================================
    # 5. Commercial Product Margin by Mode (AD-11)
    # ==========================================================================
    st.markdown("### 4. Commercial Product Gross Margin by Shipping Mode")
    st.markdown(
        "Commercial financial breakdown demonstrating sales, manufacturing COGS, and gross profit by mode. "
        "Used to verify commercial product mix across logistics channels without inferring freight rates."
    )

    margin_view = st.radio(
        "Margin Granularity",
        options=["Individual 4 Shipping Modes", "Standard vs. Expedited Tiers"],
        horizontal=True,
        key="margin_granularity_toggle",
    )
    active_margin_stats = mode_stats if margin_view == "Individual 4 Shipping Modes" else group_stats
    margin_group_col = "Ship Mode" if margin_view == "Individual 4 Shipping Modes" else "ship_mode_group"

    margin_display_cols = [
        margin_group_col,
        "order_line_count",
        "line_item_count",
        "total_units",
        "total_sales",
        "total_cogs",
        "total_gross_profit",
        "gross_margin_pct",
    ]
    rename_margin_dict = {
        margin_group_col: "Shipping Mode",
        "order_line_count": "Order Lines",
        "line_item_count": "Line Items",
        "total_units": "Units Sold",
        "total_sales": "Gross Sales ($)",
        "total_cogs": "Manufacturing COGS ($)",
        "total_gross_profit": "Gross Profit ($)",
        "gross_margin_pct": "Gross Margin (%)",
    }
    valid_margin_cols = [c for c in margin_display_cols if c in active_margin_stats.columns]
    margin_table = active_margin_stats[valid_margin_cols].rename(columns=rename_margin_dict)
    st.dataframe(margin_table, use_container_width=True, hide_index=True)

    # Audited CSV Export for margin by mode
    csv_bytes_margin = create_export_csv(
        margin_table,
        metadata={
            "layer": filters["layer"],
            "scenario": filters["scenario"],
            "delay_threshold": filters["delay_threshold"],
            "analysis": "margin_by_mode",
            "filters": filters,
        },
    )
    st.download_button(
        label="📥 Download Margin by Mode Data (Audited CSV)",
        data=csv_bytes_margin,
        file_name=f"nassau_margin_by_mode_{filters['scenario']}.csv",
        mime="text/csv",
    )

    # Mandatory AD-11 disclaimer
    render_margin_disclaimer()


if __name__ == "__main__":
    render_page()
