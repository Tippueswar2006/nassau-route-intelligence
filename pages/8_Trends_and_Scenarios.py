"""
Page 8: Scenario Trends & RES Weight Sensitivity Lab.
Provides executive-level seasonality trends, multi-scenario comparisons, and
an isolated Route Efficiency Score (RES) sensitivity laboratory (FR-17, FR-19, AD-02, AD-07, AD-11):
  - Monthly order volume seasonality charts from valid historical Original dates
  - Monthly mean lead-time trends across Synthetic scenarios (Baseline vs Stress vs Distance Sensitive)
  - Strictly labeled "Order-to-Ship Lead Time" (never "Transit Time")
  - Isolated RES weight sensitivity sandbox (50/50, 70/30, 90/10, 100/0) with rank delta & stability tracking
  - Audited CSV exports preserving provenance headers via create_export_csv
  - Non-causal operational screening disclosures and AD-11 freight/COGS disclaimers
"""

import warnings
from typing import Any, Dict, List, Optional, Tuple
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
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
)
from src.exports import create_export_csv
from src.load_data import load_prepared_artifacts
from src.metrics import calculate_route_efficiency_scores
from src.route_analysis import (
    aggregate_routes,
    filter_eligible_routes,
)


st.set_page_config(
    page_title="Trends & Scenarios | Nassau Route Intelligence",
    page_icon="📈",
    layout="wide",
)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: Monthly volume trend aggregation (Original Dates)
# ──────────────────────────────────────────────────────────────────────────────

def aggregate_monthly_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates distinct order lines, line items, units, and sales by calendar month
    from valid historical order dates (FR-17).
    """
    if df.empty or "Order Date" not in df.columns:
        return pd.DataFrame()

    work_df = df.copy()
    work_df["order_dt"] = pd.to_datetime(work_df["Order Date"], format="%d-%m-%Y", errors="coerce")
    if work_df["order_dt"].isna().all():
        work_df["order_dt"] = pd.to_datetime(work_df["Order Date"], format="%Y-%m-%d", errors="coerce")
    if work_df["order_dt"].isna().all():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            work_df["order_dt"] = pd.to_datetime(work_df["Order Date"], errors="coerce", dayfirst=True)

    valid_df = work_df.dropna(subset=["order_dt"]).copy()
    if valid_df.empty:
        return pd.DataFrame()

    valid_df["year_month"] = valid_df["order_dt"].dt.to_period("M").astype(str)

    monthly_stats = valid_df.groupby("year_month").agg(
        order_line_count=("Order ID", "nunique") if "Order ID" in valid_df.columns else ("Row ID", "count"),
        line_item_count=("Row ID", "count") if "Row ID" in valid_df.columns else ("Order ID", "count"),
        total_units=("Units", "sum") if "Units" in valid_df.columns else ("Order ID", "count"),
        total_sales=("Sales", "sum") if "Sales" in valid_df.columns else ("Order ID", "count"),
    ).reset_index()

    monthly_stats = monthly_stats.sort_values(by="year_month").reset_index(drop=True)
    monthly_stats["formatted_month"] = pd.to_datetime(monthly_stats["year_month"]).dt.strftime("%b %Y")
    return monthly_stats


def build_monthly_volume_figure(monthly_df: pd.DataFrame) -> Optional[go.Figure]:
    """Constructs a Plotly bar chart showing monthly order line volume seasonality."""
    if monthly_df.empty:
        return None

    fig = px.bar(
        monthly_df,
        x="formatted_month",
        y="order_line_count",
        labels={
            "formatted_month": "Calendar Month",
            "order_line_count": "Distinct Customer Orders (N)",
        },
        title="Monthly Order Volume Seasonality (Original Valid Order Dates, 2024–2025)",
        color_discrete_sequence=["#1f77b4"],
    )

    customdata = np.stack(
        (
            monthly_df["formatted_month"],
            monthly_df["order_line_count"],
            monthly_df["line_item_count"],
            monthly_df["total_units"],
            monthly_df["total_sales"],
        ),
        axis=-1,
    )

    fig.update_traces(
        marker=dict(line=dict(width=1, color="rgb(40,40,40)")),
        customdata=customdata,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br><br>"
            + "<b>Distinct Orders:</b> %{customdata[1]:,} orders<br>"
            + "<b>Product Line Items:</b> %{customdata[2]:,} items<br>"
            + "<b>Total Units:</b> %{customdata[3]:,} units<br>"
            + "<b>Gross Sales:</b> $%{customdata[4]:,.2f}<br>"
            + "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=420,
        margin=dict(l=40, r=40, t=60, b=60),
        xaxis=dict(tickangle=-45),
        yaxis=dict(zeroline=False),
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# Helper: Multi-scenario monthly lead-time trends (Synthetic)
# ──────────────────────────────────────────────────────────────────────────────

def aggregate_scenario_lead_times(
    artifacts: Dict[str, pd.DataFrame],
    filters: Dict[str, Any],
) -> pd.DataFrame:
    """
    Computes monthly mean Order-to-Ship Lead Times across Baseline, Stress Test,
    and Distance Sensitive synthetic scenarios matching active filters.
    """
    scenarios = [
        ("baseline", "Baseline (Calibrated)", "#1f77b4"),
        ("stress_test", "Stress Test (Texas Shock)", "#d62728"),
        ("distance_sensitive", "Distance Sensitive", "#ff7f0e"),
    ]

    records = []

    delay_thresh = filters.get("delay_threshold", DEFAULT_DELAY_THRESHOLD)

    for scen_key, scen_label, color in scenarios:
        if scen_key not in artifacts:
            continue
        scen_df = artifacts[scen_key].copy()

        # Apply sidebar filters to ensure apples-to-apples comparison
        if filters.get("factories"):
            scen_df = scen_df[scen_df["Factory"].isin(filters["factories"])]
        if filters.get("regions"):
            scen_df = scen_df[scen_df["Region"].isin(filters["regions"])]
        if filters.get("states"):
            scen_df = scen_df[scen_df["State/Province"].isin(filters["states"])]
        if filters.get("ship_modes"):
            scen_df = scen_df[scen_df["Ship Mode"].isin(filters["ship_modes"])]

        if scen_df.empty or "lead_time_days" not in scen_df.columns:
            continue

        scen_df["order_dt"] = pd.to_datetime(scen_df["Order Date"], format="%d-%m-%Y", errors="coerce")
        if scen_df["order_dt"].isna().all():
            scen_df["order_dt"] = pd.to_datetime(scen_df["Order Date"], errors="coerce", dayfirst=True)

        scen_df = scen_df.dropna(subset=["order_dt", "lead_time_days"])
        if scen_df.empty:
            continue

        scen_df["year_month"] = scen_df["order_dt"].dt.to_period("M").astype(str)

        monthly_grp = scen_df.groupby("year_month").agg(
            mean_lead_time=("lead_time_days", "mean"),
            median_lead_time=("lead_time_days", "median"),
            delayed_count=("lead_time_days", lambda x: int((x > delay_thresh).sum())),
            order_count=("Order ID", "nunique") if "Order ID" in scen_df.columns else ("lead_time_days", "count"),
        ).reset_index()

        for _, r in monthly_grp.iterrows():
            records.append({
                "year_month": r["year_month"],
                "formatted_month": pd.to_datetime(r["year_month"]).strftime("%b %Y"),
                "scenario_key": scen_key,
                "scenario_label": scen_label,
                "color": color,
                "mean_lead_time": np.round(r["mean_lead_time"], 2),
                "median_lead_time": np.round(r["median_lead_time"], 2),
                "delayed_count": int(r["delayed_count"]),
                "delay_rate_pct": np.round((r["delayed_count"] / r["order_count"] * 100.0) if r["order_count"] > 0 else 0.0, 1),
                "order_count": int(r["order_count"]),
            })

    return pd.DataFrame(records)


def build_scenario_trend_figure(trend_df: pd.DataFrame, delay_threshold: float) -> Optional[go.Figure]:
    """Constructs an interactive multi-line chart comparing scenario lead-time trajectories."""
    if trend_df.empty:
        return None

    fig = go.Figure()

    scen_order = [
        ("baseline", "Baseline (Calibrated)", "#1f77b4", "solid"),
        ("stress_test", "Stress Test (Texas Shock)", "#d62728", "dash"),
        ("distance_sensitive", "Distance Sensitive", "#ff7f0e", "dot"),
    ]

    for key, label, color, dash in scen_order:
        sub_df = trend_df[trend_df["scenario_key"] == key].sort_values(by="year_month")
        if sub_df.empty:
            continue

        customdata = np.stack(
            (
                sub_df["formatted_month"],
                sub_df["scenario_label"],
                sub_df["mean_lead_time"],
                sub_df["median_lead_time"],
                sub_df["delay_rate_pct"],
                sub_df["order_count"],
            ),
            axis=-1,
        )

        fig.add_trace(go.Scatter(
            x=sub_df["formatted_month"],
            y=sub_df["mean_lead_time"],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2.5, dash=dash),
            marker=dict(size=7, color=color),
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                + "Month: %{customdata[0]}<br><br>"
                + "<b>Mean Order-to-Ship Lead Time:</b> %{customdata[2]:.2f} days<br>"
                + "<b>Median Lead Time:</b> %{customdata[3]:.2f} days<br>"
                + f"<b>Delay Rate (>{delay_threshold:.1f}d):</b> %{{customdata[4]:.1f}}%<br>"
                + "<b>Monthly Orders:</b> %{customdata[5]:,} orders<br>"
                + "<extra></extra>"
            ),
        ))

    # Add delay threshold reference line
    fig.add_hline(
        y=delay_threshold,
        line_dash="dash",
        line_color="#7f7f7f",
        line_width=1.5,
        annotation_text=f"Delay Threshold: {delay_threshold:.1f}d",
        annotation_position="top right",
    )

    fig.update_layout(
        title="Monthly Mean Order-to-Ship Lead Time by Synthetic Scenario",
        xaxis_title="Calendar Month",
        yaxis_title="Order-to-Ship Lead Time (Days)",
        height=450,
        margin=dict(l=40, r=40, t=60, b=60),
        xaxis=dict(tickangle=-45),
        yaxis=dict(zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# Helper: RES Weight Sensitivity Engine (Isolated Sandbox)
# ──────────────────────────────────────────────────────────────────────────────

def compute_res_weight_sensitivity(
    df: pd.DataFrame,
    sens_w_speed: float,
    sens_w_var: float,
    delay_threshold: float = DEFAULT_DELAY_THRESHOLD,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes side-by-side Route Efficiency Scores (RES) under Baseline weights (0.70/0.30)
    and custom Sensitivity weights for eligible comparison routes (N >= 30).
    Evaluates rank shifts and calculates Spearman rank correlation rho.
    """
    if df.empty or "Factory" not in df.columns:
        return pd.DataFrame(), {
            "spearman_rho": 1.0,
            "top10_retention_pct": 100.0,
            "mean_abs_rank_delta": 0.0,
            "max_rank_gain": 0,
            "max_rank_drop": 0,
            "route_count": 0,
        }

    # 1. Aggregate routes
    raw_agg = aggregate_routes(
        df,
        level="state",
        min_sample=min_sample,
        threshold_days=delay_threshold,
        rollup_small_factories=True,
    )

    eligible_df, _ = filter_eligible_routes(raw_agg, min_sample=min_sample)
    if eligible_df.empty:
        return pd.DataFrame(), {
            "spearman_rho": 1.0,
            "top10_retention_pct": 100.0,
            "mean_abs_rank_delta": 0.0,
            "max_rank_gain": 0,
            "max_rank_drop": 0,
            "route_count": 0,
        }

    # 2. Compute Baseline RES (70/30)
    base_scored = calculate_route_efficiency_scores(
        eligible_df,
        basis="mode_adjusted",
        w_speed=DEFAULT_RES_WEIGHT_SPEED,
        w_var=DEFAULT_RES_WEIGHT_VARIABILITY,
    )
    base_scored["baseline_res"] = base_scored["res_score"]
    base_scored["baseline_rank"] = base_scored["baseline_res"].rank(ascending=False, method="min").astype(int)

    # 3. Compute Sensitivity RES (sens_w_speed / sens_w_var)
    sens_scored = calculate_route_efficiency_scores(
        eligible_df,
        basis="mode_adjusted",
        w_speed=sens_w_speed,
        w_var=sens_w_var,
    )
    sens_scored["sensitivity_res"] = sens_scored["res_score"]
    sens_scored["sensitivity_rank"] = sens_scored["sensitivity_res"].rank(ascending=False, method="min").astype(int)

    # 4. Merge comparison columns
    comparison = pd.DataFrame({
        "route_key": base_scored["route_key"],
        "sample_size": base_scored["sample_size"],
        "mean_lead_time": base_scored["mean_lead_time"],
        "std_lead_time": base_scored["std_lead_time"],
        "baseline_res": base_scored["baseline_res"],
        "baseline_rank": base_scored["baseline_rank"],
        "sensitivity_res": sens_scored["sensitivity_res"],
        "sensitivity_rank": sens_scored["sensitivity_rank"],
    })

    # Rank Delta: Positive = climbed in ranking, Negative = dropped
    comparison["rank_delta"] = comparison["baseline_rank"] - comparison["sensitivity_rank"]

    # 5. Stability Metrics: Spearman rank correlation is Pearson correlation on rank variables
    if len(comparison) > 1 and comparison["baseline_rank"].std() > 0 and comparison["sensitivity_rank"].std() > 0:
        spearman_rho = float(comparison["baseline_rank"].corr(comparison["sensitivity_rank"]))
        if np.isnan(spearman_rho):
            spearman_rho = 1.0
    else:
        spearman_rho = 1.0

    top10_base = set(comparison.sort_values(by="baseline_rank").head(10)["route_key"])
    top10_sens = set(comparison.sort_values(by="sensitivity_rank").head(10)["route_key"])
    retention_count = len(top10_base.intersection(top10_sens))
    top10_retention_pct = (retention_count / min(10, len(comparison)) * 100.0) if len(comparison) > 0 else 100.0

    metrics = {
        "spearman_rho": np.round(spearman_rho, 4),
        "top10_retention_pct": np.round(top10_retention_pct, 1),
        "mean_abs_rank_delta": np.round(comparison["rank_delta"].abs().mean(), 2),
        "max_rank_gain": int(comparison["rank_delta"].max()) if not comparison.empty else 0,
        "max_rank_drop": int(comparison["rank_delta"].min()) if not comparison.empty else 0,
        "route_count": len(comparison),
    }

    return comparison, metrics


# ──────────────────────────────────────────────────────────────────────────────
# Main Page Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def render_page():
    filters = render_sidebar_filters()

    st.title("📈 Trends & Scenarios Lab")
    st.markdown(
        "Executive trends and simulation sandbox — review long-term order volume seasonality from valid "
        "historical dates (FR-17), compare multi-scenario lead-time trajectories, and evaluate Route "
        "Efficiency Score (RES) sensitivity across speed/variability weights in an isolated sandbox (FR-19)."
    )

    render_layer_banner(filters["layer"], filters.get("scenario"))

    st.divider()

    # 1. Mandatory Non-Causal Operational & COGS Disclaimers (FR-17, AD-08, AD-11)
    st.info(
        "🔍 **Operational Screening Disclosure (FR-17 & AD-08):** "
        "Monthly volume trends reflect cleaned historical distributor records. "
        "Lead-time trajectories are synthetic scenario simulations strictly labeled **'Order-to-Ship Lead Time'** "
        "(order placement to ship dispatch). They do NOT represent carrier transit or delivery time.",
        icon="ℹ️",
    )
    render_margin_disclaimer()

    # 2. Load active filtered dataset
    try:
        df, ref_means = get_active_dataset(filters)
    except Exception as exc:
        st.error(f"Failed to load dataset: {exc}")
        return

    if df.empty:
        st.warning("⚠️ No orders found matching active sidebar filters. Please broaden your selection.")
        return

    # 3. Render Three Executive Analysis Tabs
    tab_vol, tab_scen, tab_sens = st.tabs([
        "📅 Monthly Order Volume Seasonality",
        "📊 Scenario Comparison & Lead Times",
        "🧪 RES Weight Sensitivity Lab",
    ])

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 1: Monthly Order Volume Seasonality (Original Dates)
    # ──────────────────────────────────────────────────────────────────────────
    with tab_vol:
        st.markdown("### 1. Monthly Order Volume Trends (Original Layer)")
        st.caption(
            "Distinct customer order volume across calendar months using valid historical order dates (2024–2025). "
            "Cleaned and reconciled from raw distributor records."
        )

        monthly_df = aggregate_monthly_volume(df)

        if monthly_df.empty:
            st.info("No valid order date records available under current filters.")
        else:
            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
            peak_row = monthly_df.loc[monthly_df["order_line_count"].idxmax()]
            low_row = monthly_df.loc[monthly_df["order_line_count"].idxmin()]
            total_orders = monthly_df["order_line_count"].sum()

            kpi_col1.metric("Total Filtered Orders", f"{total_orders:,}")
            kpi_col2.metric("Monthly Order Average", f"{monthly_df['order_line_count'].mean():,.0f} / mo")
            kpi_col3.metric("Peak Volume Month", f"{peak_row['formatted_month']}", delta=f"{peak_row['order_line_count']:,} orders")
            kpi_col4.metric("Lowest Volume Month", f"{low_row['formatted_month']}", delta=f"{low_row['order_line_count']:,} orders", delta_color="off")

            vol_fig = build_monthly_volume_figure(monthly_df)
            if vol_fig is not None:
                st.plotly_chart(vol_fig, use_container_width=True)

            st.markdown("#### Monthly Volume Breakdown")
            display_vol = monthly_df[[
                "formatted_month", "order_line_count", "line_item_count", "total_units", "total_sales"
            ]].rename(columns={
                "formatted_month": "Calendar Month",
                "order_line_count": "Distinct Orders (N)",
                "line_item_count": "Product Line Items",
                "total_units": "Total Units",
                "total_sales": "Gross Revenue ($)",
            })
            st.dataframe(display_vol, use_container_width=True, hide_index=True)

            csv_vol = create_export_csv(
                df=monthly_df,
                metadata={
                    "layer": filters.get("layer", "ORIGINAL"),
                    "scenario": filters.get("scenario", "none"),
                    "delay_threshold": filters.get("delay_threshold", DEFAULT_DELAY_THRESHOLD),
                    "screening": "monthly_volume_trends",
                    "filters": filters,
                },
            )
            st.download_button(
                label="📥 Download Monthly Volume Trends (Audited CSV)",
                data=csv_vol,
                file_name=f"nassau_monthly_volume_trends.csv",
                mime="text/csv",
                key="btn_dl_monthly_vol",
            )

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 2: Scenario Comparison & Lead Times (Synthetic)
    # ──────────────────────────────────────────────────────────────────────────
    with tab_scen:
        st.markdown("### 2. Multi-Scenario Lead-Time Trajectories (Synthetic Layer)")
        st.caption(
            "Comparison of simulated lead times and delay rates across Baseline (Calibrated), "
            "Stress Test (Texas shock), and Distance Sensitive scenarios (FR-17)."
        )

        has_lead_time = "lead_time_days" in df.columns and df["lead_time_days"].notna().any()

        if not has_lead_time:
            st.warning(
                "⚠️ Scenario comparisons and simulated lead-time trajectories require calibrated timing "
                "from the **SYNTHETIC** layer (AD-02). Currently viewing historical records without simulated lead times."
            )
        else:
            try:
                artifacts = load_prepared_artifacts()
            except Exception as e:
                st.error(f"Failed to load scenario artifacts: {e}")
                artifacts = {}

            if artifacts:
                scen_trend_df = aggregate_scenario_lead_times(artifacts, filters)

                if scen_trend_df.empty:
                    st.info("No matching scenario order records found under active filters.")
                else:
                    # Scenario Summary Cards
                    base_df = scen_trend_df[scen_trend_df["scenario_key"] == "baseline"]
                    stress_df = scen_trend_df[scen_trend_df["scenario_key"] == "stress_test"]
                    dist_df = scen_trend_df[scen_trend_df["scenario_key"] == "distance_sensitive"]

                    scen_c1, scen_c2, scen_c3 = st.columns(3)
                    with scen_c1:
                        b_mean = base_df["mean_lead_time"].mean() if not base_df.empty else 0.0
                        b_del = base_df["delay_rate_pct"].mean() if not base_df.empty else 0.0
                        st.metric("Baseline Overall Mean Lead Time", f"{b_mean:.2f} d", delta=f"{b_del:.1f}% delay rate")
                    with scen_c2:
                        s_mean = stress_df["mean_lead_time"].mean() if not stress_df.empty else 0.0
                        s_del = stress_df["delay_rate_pct"].mean() if not stress_df.empty else 0.0
                        st.metric("Stress Test Overall Mean Lead Time", f"{s_mean:.2f} d", delta=f"{s_del:.1f}% delay rate (+{s_del - b_del:.1f}%)", delta_color="inverse")
                    with scen_c3:
                        d_mean = dist_df["mean_lead_time"].mean() if not dist_df.empty else 0.0
                        d_del = dist_df["delay_rate_pct"].mean() if not dist_df.empty else 0.0
                        st.metric("Distance Sensitive Overall Mean", f"{d_mean:.2f} d", delta=f"{d_del:.1f}% delay rate", delta_color="off")

                    active_delay_thresh = filters.get("delay_threshold", DEFAULT_DELAY_THRESHOLD)
                    trend_fig = build_scenario_trend_figure(scen_trend_df, active_delay_thresh)
                    if trend_fig is not None:
                        st.plotly_chart(trend_fig, use_container_width=True)

                    st.markdown("#### Scenario Trajectory Data Table")
                    display_scen = scen_trend_df[[
                        "formatted_month", "scenario_label", "mean_lead_time", "median_lead_time", "delay_rate_pct", "order_count"
                    ]].rename(columns={
                        "formatted_month": "Month",
                        "scenario_label": "Scenario",
                        "mean_lead_time": "Mean Lead Time (d)",
                        "median_lead_time": "Median Lead Time (d)",
                        "delay_rate_pct": f"Delay Rate (>{active_delay_thresh:.1f}d) %",
                        "order_count": "Orders (N)",
                    })
                    st.dataframe(display_scen, use_container_width=True, hide_index=True)

                    csv_scen = create_export_csv(
                        df=scen_trend_df,
                        metadata={
                            "layer": "SYNTHETIC",
                            "scenario": "multi_scenario_comparison",
                            "delay_threshold": active_delay_thresh,
                            "screening": "scenario_lead_time_trends",
                            "filters": filters,
                        },
                    )
                    st.download_button(
                        label="📥 Download Scenario Lead-Time Trends (Audited CSV)",
                        data=csv_scen,
                        file_name=f"nassau_scenario_lead_time_trends.csv",
                        mime="text/csv",
                        key="btn_dl_scen_trends",
                    )

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 3: RES Weight Sensitivity Lab (Isolated Sandbox)
    # ──────────────────────────────────────────────────────────────────────────
    with tab_sens:
        st.markdown("### 3. Isolated RES Weight Sensitivity Laboratory")
        st.caption(
            "Interactive sensitivity testing sandbox — adjust the relative weights between Speed Penalty and "
            "Variability Penalty to evaluate route rank stability and ranking shifts (FR-19, Section 13). "
            "**Isolated Sandbox:** Adjustments made here are confined to Page 8 and do NOT alter global sidebar settings."
        )

        has_lead_time = "lead_time_days" in df.columns and df["lead_time_days"].notna().any()

        if not has_lead_time:
            st.warning(
                "⚠️ RES weight sensitivity modeling requires calibrated lead times from the **SYNTHETIC** layer (AD-02). "
                "Switch to the SYNTHETIC layer in the sidebar to use the sensitivity laboratory."
            )
        else:
            # Initialize session state for sensitivity sandbox if not present
            if "sens_speed_weight" not in st.session_state:
                st.session_state.sens_speed_weight = DEFAULT_RES_WEIGHT_SPEED

            # Preset Configuration Buttons
            st.markdown("##### Quick Weight Presets")
            p_col1, p_col2, p_col3, p_col4 = st.columns(4)
            if p_col1.button("Default Model (70/30)", use_container_width=True, help="Production default: 70% Speed, 30% Variability"):
                st.session_state.sens_speed_weight = 0.70
                st.rerun()
            if p_col2.button("Balanced Model (50/50)", use_container_width=True, help="Equal balance: 50% Speed, 50% Variability"):
                st.session_state.sens_speed_weight = 0.50
                st.rerun()
            if p_col3.button("Speed-Focused (90/10)", use_container_width=True, help="Priority on speed: 90% Speed, 10% Variability"):
                st.session_state.sens_speed_weight = 0.90
                st.rerun()
            if p_col4.button("Speed-Only (100/0)", use_container_width=True, help="Speed-only: 100% Speed, 0% Variability"):
                st.session_state.sens_speed_weight = 1.00
                st.rerun()

            # Interactive Weight Slider
            sens_speed = st.slider(
                "Speed Penalty Weight (w_speed)",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                key="sens_speed_weight",
                help="Weight assigned to normalized Mean Lead Time penalty. Variability weight is locked to (1.0 - w_speed).",
            )
            sens_var = np.round(1.0 - sens_speed, 2)

            st.caption(
                f"Active Sensitivity Weighting: **Speed = {sens_speed * 100:.0f}%** | "
                f"**Variability = {sens_var * 100:.0f}%** (Baseline Reference: 70% / 30%)"
            )

            # Compute sensitivity ranking comparison
            comp_df, stability_metrics = compute_res_weight_sensitivity(
                df=df,
                sens_w_speed=sens_speed,
                sens_w_var=sens_var,
                delay_threshold=filters.get("delay_threshold", DEFAULT_DELAY_THRESHOLD),
                min_sample=MIN_SAMPLE_SIZE,
            )

            if comp_df.empty:
                st.warning("No routes meeting the minimum sample size guardrail (N >= 30) were found under active filters.")
            else:
                st.divider()
                st.markdown("#### Rank Stability & Robustness Indicators")
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)

                rho_val = stability_metrics["spearman_rho"]
                rho_color = "normal" if rho_val >= 0.90 else "inverse"
                s_col1.metric(
                    "Spearman Rank Correlation (ρ)",
                    f"{rho_val:.4f}",
                    delta="High Rank Stability" if rho_val >= 0.90 else "Moderate / High Shift",
                    delta_color=rho_color,
                    help="Correlation between Baseline (70/30) and Sensitivity ranks across eligible routes.",
                )
                s_col2.metric(
                    "Top 10 Retention Rate",
                    f"{stability_metrics['top10_retention_pct']:.0f}%",
                    help="Percentage of Baseline Top 10 routes remaining in Top 10 under sensitivity weights.",
                )
                s_col3.metric(
                    "Mean Absolute Rank Shift",
                    f"{stability_metrics['mean_abs_rank_delta']:.1f} ranks",
                    help="Average number of rank positions shifted across all evaluated routes.",
                )
                s_col4.metric(
                    "Max Rank Gain / Drop",
                    f"+{stability_metrics['max_rank_gain']} / {stability_metrics['max_rank_drop']}",
                    help="Maximum upward and downward rank position shifts under sensitivity weights.",
                )

                st.divider()
                st.markdown("#### Route Ranking Comparison (Baseline 70/30 vs Sensitivity Weights)")
                st.caption(
                    "Rank Delta = Baseline Rank - Sensitivity Rank. "
                    "Green / positive delta indicates improved standing under sensitivity weights; negative indicates drop."
                )

                table_df = comp_df.sort_values(by="sensitivity_rank").copy()
                table_disp = table_df[[
                    "route_key", "sample_size", "mean_lead_time", "std_lead_time",
                    "baseline_res", "baseline_rank", "sensitivity_res", "sensitivity_rank", "rank_delta"
                ]].rename(columns={
                    "route_key": "Route Lane",
                    "sample_size": "Order Volume (N)",
                    "mean_lead_time": "Mean Lead Time (d)",
                    "std_lead_time": "Std Dev (d)",
                    "baseline_res": "Baseline RES (70/30)",
                    "baseline_rank": "Baseline Rank",
                    "sensitivity_res": f"Sensitivity RES ({sens_speed*100:.0f}/{sens_var*100:.0f})",
                    "sensitivity_rank": "Sensitivity Rank",
                    "rank_delta": "Rank Delta (Shift)",
                })

                st.dataframe(table_disp, use_container_width=True, hide_index=True)

                csv_sens = create_export_csv(
                    df=comp_df,
                    metadata={
                        "layer": filters.get("layer", "SYNTHETIC"),
                        "scenario": filters.get("scenario", "baseline"),
                        "delay_threshold": filters.get("delay_threshold", DEFAULT_DELAY_THRESHOLD),
                        "w_speed_sensitivity": sens_speed,
                        "w_var_sensitivity": sens_var,
                        "screening": "res_weight_sensitivity",
                        "filters": filters,
                    },
                )
                st.download_button(
                    label=f"📥 Download Sensitivity Analysis ({sens_speed*100:.0f}/{sens_var*100:.0f} Audited CSV)",
                    data=csv_sens,
                    file_name=f"nassau_res_sensitivity_{int(sens_speed*100)}_{int(sens_var*100)}.csv",
                    mime="text/csv",
                    key="btn_dl_sens_analysis",
                )


if __name__ == "__main__":
    render_page()
