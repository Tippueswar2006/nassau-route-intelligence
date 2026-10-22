"""
Page 4: Geographic Analysis & US State Choropleth Heatmap.
Displays interactive US state choropleth heatmap with selectable metrics:
Mean Lead Time, Delay Rate, RES, and Order Volume.
Excludes Canadian destinations from US map geometry (FR-09) and displays
a persistent notification banner documenting retention in company totals.
Hovering over a state reveals factory fulfillment breakdown and sample size.
"""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
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
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
)
from src.exports import create_export_csv
from src.route_analysis import aggregate_state_metrics


st.set_page_config(
    page_title="Geographic Analysis | Nassau Route Intelligence",
    page_icon="🗺️",
    layout="wide",
)


METRIC_OPTIONS = {
    "Mean Lead Time": {
        "col": "mean_lead_time",
        "label": "Mean Lead Time (Days)",
        "unit": "days",
        "colorscale": "YlOrRd",
        "zmin": None,
        "zmax": None,
        "description": "Average order-to-ship lead time in days by destination state.",
        "requires_timing": True,
    },
    "Delay Rate": {
        "col": "delay_rate_pct",
        "label": "Delay Rate (%)",
        "unit": "%",
        "colorscale": "Reds",
        "zmin": 0.0,
        "zmax": 40.0,
        "description": "Percentage of orders exceeding the active analysis delay threshold.",
        "requires_timing": True,
    },
    "RES": {
        "col": "res_score",
        "label": "Route Efficiency Score (0–100)",
        "unit": "pts",
        "colorscale": "RdYlGn",
        "zmin": 40.0,
        "zmax": 90.0,
        "description": "Fixed 70/30 composite score balancing speed and lead-time variability (higher is better).",
        "requires_timing": True,
    },
    "Order Volume": {
        "col": "sample_size",
        "label": "Order Volume (Orders)",
        "unit": "orders",
        "colorscale": "Blues",
        "zmin": None,
        "zmax": None,
        "description": "Total order line count fulfilled to destination state.",
        "requires_timing": False,
    },
}


def build_choropleth_figure(
    us_state_df: pd.DataFrame,
    metric_name: str,
    metric_cfg: Dict[str, Any],
    delay_threshold: Optional[float] = None,
) -> go.Figure:
    """
    Constructs an interactive Plotly US Choropleth figure with custom hover
    tooltips displaying factory fulfillment breakdown and sample size.
    """
    col = metric_cfg["col"]

    # Filter out states where metric is missing (e.g. low sample or no timing)
    plot_df = us_state_df.dropna(subset=["state_code", col]).copy()

    # Format hover text value based on metric
    def _format_val(val):
        if metric_name == "Mean Lead Time":
            return f"{val:.2f} days"
        elif metric_name == "Delay Rate":
            return f"{val:.1f}%"
        elif metric_name == "RES":
            return f"{val:.1f} pts"
        else:
            return f"{int(val):,} orders"

    plot_df["metric_display"] = plot_df[col].apply(_format_val)

    sample_status_series = (
        plot_df["sample_status"]
        if "sample_status" in plot_df.columns
        else plot_df["sample_size"].apply(lambda n: "Eligible (N >= 30)" if n >= 30 else "⚠️ Low Sample (N < 30)")
    )

    # Customdata packing for hover:
    # 0: State Name
    # 1: Sample Size (Formatted)
    # 2: Metric Display String
    # 3: Top Factory
    # 4: Factory Breakdown HTML
    # 5: Sample Status
    customdata = np.stack(
        (
            plot_df["State/Province"],
            plot_df["sample_size"].apply(lambda x: f"{int(x):,}"),
            plot_df["metric_display"],
            plot_df["top_factory"],
            plot_df["factory_breakdown_html"],
            sample_status_series,
        ),
        axis=-1,
    )

    threshold_subtitle = f" (Threshold: {delay_threshold:.1f}d)" if delay_threshold and metric_name == "Delay Rate" else ""

    hover_template = (
        "<b>%{customdata[0]} (%{location})</b><br>"
        + "Status: <i>%{customdata[5]}</i><br><br>"
        + f"<b>{metric_name}{threshold_subtitle}:</b> %{{customdata[2]}}<br>"
        + "<b>Sample Size:</b> %{customdata[1]} orders<br>"
        + "<b>Primary Factory:</b> %{customdata[3]}<br><br>"
        + "<b>Factory Fulfillment Breakdown:</b><br>"
        + "%{customdata[4]}"
        + "<extra></extra>"
    )

    choropleth_kwargs = dict(
        locations=plot_df["state_code"],
        z=plot_df[col],
        locationmode="USA-states",
        colorscale=metric_cfg["colorscale"],
        colorbar=dict(
            title=dict(
                text=metric_cfg["label"],
                side="right",
            ),
            thickness=18,
            len=0.8,
        ),
        customdata=customdata,
        hovertemplate=hover_template,
        marker_line_color="rgb(220, 220, 220)",
        marker_line_width=1,
    )

    if metric_cfg.get("zmin") is not None:
        choropleth_kwargs["zmin"] = metric_cfg["zmin"]
    if metric_cfg.get("zmax") is not None:
        choropleth_kwargs["zmax"] = metric_cfg["zmax"]

    fig = go.Figure(data=go.Choropleth(**choropleth_kwargs))

    fig.update_layout(
        geo=dict(
            scope="usa",
            projection=dict(type="albers usa"),
            showlakes=True,
            lakecolor="rgb(240, 248, 255)",
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=540,
    )

    return fig


def render_page():
    filters = render_sidebar_filters()

    st.title("🗺️ Geographic Delivery & State Choropleth Analysis")
    st.markdown(
        "Interactive state-level delivery performance heatmap across US destination states. "
        "Examines geographic lead time and delay frequency, provides factory fulfillment "
        "transparency, and documents cross-border Canadian orders (FR-09)."
    )
    render_layer_banner(filters["layer"], filters["scenario"])

    # Load active dataset according to sidebar filters
    df, ref_means = get_active_dataset(filters)

    st.divider()

    # ==========================================================================
    # 1. Canadian Destination Disclosure Banner (FR-09)
    # ==========================================================================
    st.info(
        "🇨🇦 **Canadian Orders Geographic Disclosure (FR-09):** "
        "Canadian destination orders are excluded from the US state choropleth map geometry "
        "to prevent geographic distortion (3-character partial postal codes), but are fully retained "
        "in all company-wide volume, financial totals, and overall performance metrics.",
        icon="ℹ️",
    )

    if df.empty:
        st.warning("⚠️ No orders found matching active sidebar filters. Please broaden your selection.")
        return

    # Aggregate state metrics using pure backend engine
    us_state_df, canada_df = aggregate_state_metrics(
        df,
        threshold_days=filters["delay_threshold"],
        w_speed=DEFAULT_RES_WEIGHT_SPEED,
        w_var=DEFAULT_RES_WEIGHT_VARIABILITY,
        min_sample=MIN_SAMPLE_SIZE,
    )

    # ==========================================================================
    # 2. Executive Geographic Summary Metrics (Grain Consistent)
    # ==========================================================================
    total_order_lines = df["Order ID"].nunique() if "Order ID" in df.columns else len(df)
    total_line_items = len(df)
    us_order_lines = us_state_df["sample_size"].sum() if not us_state_df.empty else 0
    can_order_lines = canada_df["Order ID"].nunique() if ("Order ID" in canada_df.columns and not canada_df.empty) else len(canada_df)
    us_states_active = len(us_state_df) if not us_state_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Filtered Orders",
            f"{total_order_lines:,}",
            help=f"Distinct order lines ({total_line_items:,} line items) across all regions.",
        )
    with col2:
        st.metric(
            "US Map Destination Orders",
            f"{us_order_lines:,}",
            help="Total order lines visualized in the US state choropleth.",
        )
    with col3:
        st.metric(
            "Canadian Excluded Orders",
            f"{can_order_lines:,}",
            help="Canadian orders retained in volume/revenue totals but excluded from US map geometry.",
        )
    with col4:
        st.metric("Active US States Covered", f"{us_states_active} States / DC")

    st.divider()

    # ==========================================================================
    # 3. Metric Selector & Choropleth Heatmap (FR-09)
    # ==========================================================================
    st.markdown("### 1. Interactive US State Choropleth Heatmap")

    has_lead_time = "mean_lead_time" in us_state_df.columns if not us_state_df.empty else False

    metric_ctrl, info_ctrl = st.columns([3, 2])
    with metric_ctrl:
        available_metric_names = list(METRIC_OPTIONS.keys())
        if not has_lead_time:
            # If historical layer without lead times is active, restrict to Order Volume
            available_metric_names = ["Order Volume"]
            st.caption(
                "ℹ️ *Note: Lead time, Delay Rate, and RES metrics require the SYNTHETIC calibrated data layer (AD-02).*"
            )

        selected_metric_name = st.radio(
            "Select Heatmap Metric",
            options=available_metric_names,
            index=0,
            horizontal=True,
            help="Change the active metric rendered across the US state choropleth.",
        )

    metric_cfg = METRIC_OPTIONS[selected_metric_name]

    with info_ctrl:
        st.caption(f"**Metric Definition:** {metric_cfg['description']}")
        if selected_metric_name == "Delay Rate":
            st.caption(f"*Active Analysis Threshold:* **{filters['delay_threshold']:.1f} days** (configurable in sidebar)")
        elif selected_metric_name == "RES":
            st.caption("*Scoring Weights:* **70% Speed / 30% Variability** (fixed on Pages 1–7 per AD-06)")

    if us_state_df.empty:
        st.warning("No US state data available for visualization under the selected filters.")
    else:
        fig = build_choropleth_figure(
            us_state_df,
            metric_name=selected_metric_name,
            metric_cfg=metric_cfg,
            delay_threshold=filters["delay_threshold"],
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "💡 **Map Interaction Tip:** Hover over any US state to reveal sample size, selected metric value, "
            "guardrail eligibility ($N \\ge 30$), and the exact factory fulfillment breakdown."
        )

    st.divider()

    # ==========================================================================
    # 4. State Performance Benchmarking Table
    # ==========================================================================
    st.markdown("### 2. State Performance Details & Fulfillment Breakdown")

    if not us_state_df.empty:
        # Prepare display table safely checking for column presence
        display_cols = ["State/Province", "state_code"]
        if "Region" in us_state_df.columns:
            display_cols.append("Region")

        display_cols += ["sample_size", "sample_status", "top_factory"]

        rename_dict = {
            "State/Province": "Destination State",
            "state_code": "Code",
            "sample_size": "Order Volume",
            "sample_status": "Sample Status",
            "top_factory": "Primary Fulfilling Factory",
        }

        if has_lead_time:
            display_cols += ["mean_lead_time", "median_lead_time", "delay_rate_pct", "res_score"]
            rename_dict.update({
                "mean_lead_time": "Mean Lead Time (d)",
                "median_lead_time": "Median Lead Time (d)",
                "delay_rate_pct": "Delay Rate (%)",
                "res_score": "RES Score",
            })

        # Filter display columns to only those actually present in us_state_df
        valid_display_cols = [c for c in display_cols if c in us_state_df.columns]
        table_df = us_state_df[valid_display_cols].rename(columns=rename_dict)

        # Sort by active metric
        sort_col = rename_dict.get(metric_cfg["col"], "Order Volume")
        if sort_col in table_df.columns:
            ascending = selected_metric_name in ["Mean Lead Time", "Delay Rate"]  # Lower is better for lead time & delays
            table_df = table_df.sort_values(by=sort_col, ascending=ascending).reset_index(drop=True)

        st.dataframe(table_df, use_container_width=True, hide_index=True)

        # Download button for audited CSV containing all available fields
        csv_bytes = create_export_csv(
            table_df,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "delay_threshold": filters["delay_threshold"],
                "metric": selected_metric_name,
                "filters": filters,
            },
        )
        st.download_button(
            label="📥 Download State Performance Data (Audited CSV)",
            data=csv_bytes,
            file_name=f"nassau_state_geographic_analysis_{filters['scenario']}.csv",
            mime="text/csv",
        )

    # ==========================================================================
    # 5. Canadian Retained Orders Summary (FR-09)
    # ==========================================================================
    with st.expander("🇨🇦 Canadian Retained Orders Summary (Excluded from Map Geometry)", expanded=False):
        st.markdown(
            "Per requirement **FR-09**, Canadian destination records are retained in all volume and financial "
            "totals across the dashboard, but excluded from the 2D US state choropleth map geometry."
        )
        if canada_df.empty:
            st.info("No Canadian orders found under the active filter selection.")
        else:
            can_province_col = "State/Province" if "State/Province" in canada_df.columns else "Region"

            can_agg_dict = {
                "orders": ("Order ID", "nunique") if "Order ID" in canada_df.columns else ("Row ID", "count"),
            }
            if "Units" in canada_df.columns:
                can_agg_dict["units"] = ("Units", "sum")
            if "Sales" in canada_df.columns:
                can_agg_dict["sales"] = ("Sales", "sum")
            if "lead_time_days" in canada_df.columns:
                can_agg_dict["mean_lead_time"] = ("lead_time_days", "mean")

            can_summary = canada_df.groupby(can_province_col).agg(**can_agg_dict).reset_index()

            can_rename = {
                can_province_col: "Canadian Province",
                "orders": "Order Volume",
                "units": "Total Units",
                "sales": "Gross Sales ($)",
            }
            if "mean_lead_time" in can_summary.columns:
                can_summary["mean_lead_time"] = np.round(can_summary["mean_lead_time"], 2)
                can_rename["mean_lead_time"] = "Mean Lead Time (d)"

            if "sales" in can_summary.columns:
                can_summary["sales"] = np.round(can_summary["sales"], 2)

            st.dataframe(
                can_summary.rename(columns=can_rename),
                use_container_width=True,
                hide_index=True,
            )

    # ==========================================================================
    # 6. Commercial Margin & Freight Disclaimer (AD-11)
    # ==========================================================================
    render_margin_disclaimer()


if __name__ == "__main__":
    render_page()
