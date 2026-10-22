"""
Page 7: Route Drill-Down & Order-to-Ship Timeline Visualizer.
Provides granular lane-level inspection for warehouse managers and operations leaders (FR-12, AD-07, AD-08, AD-11):
  - Route selector (Factory -> Destination) defaulting to canonical bottleneck lane
  - Distinct Order Lines (N) vs Line Items distinction
  - KPI summary metrics: Order Lines, Line Items, Revenue, Manufacturing COGS, Margin, Lead Times, Delay Rate
  - Interactive Plotly order-to-ship timeline scatter chart with threshold reference line
  - Strictly labeled "Order-to-Ship Lead Time" (never "Transit Time")
  - Canadian route tables with factory-to-province centroid Haversine distances
  - Per-order line detail table with auditable columns and audited CSV export via create_export_csv
  - Non-causal operational screening disclosures and AD-11 freight/COGS disclaimers
"""

from typing import Any, Dict, List, Optional, Tuple
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
    MIN_SAMPLE_SIZE,
)
from src.exports import create_export_csv
from src.route_analysis import (
    assign_route_hierarchy,
)


st.set_page_config(
    page_title="Route Drill-Down | Nassau Route Intelligence",
    page_icon="🔍",
    layout="wide",
)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: build route key options
# ──────────────────────────────────────────────────────────────────────────────

def build_route_options(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Assigns hierarchy and creates sorted list of route keys available in df.
    Returns (df_with_hierarchy, sorted_route_keys).
    """
    if df.empty:
        return df, []
    if "analysis_route_key" not in df.columns:
        df = assign_route_hierarchy(df)
    routes = sorted(df["analysis_route_key"].dropna().unique().tolist())
    return df, routes


def filter_to_route(df: pd.DataFrame, route_key: str) -> pd.DataFrame:
    """Filters df to rows matching the selected route key."""
    if "analysis_route_key" not in df.columns:
        df = assign_route_hierarchy(df)
    return df[df["analysis_route_key"] == route_key].copy().reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: route summary statistics card
# ──────────────────────────────────────────────────────────────────────────────

def render_route_summary(route_df: pd.DataFrame, delay_threshold: float):
    """
    Renders structured KPI metric rows for the selected route, rigorously distinguishing
    between Order Lines (distinct Order ID count, N) and Line Items (total product rows).
    """
    order_line_count = int(route_df["Order ID"].nunique()) if "Order ID" in route_df.columns else len(route_df)
    line_item_count = len(route_df)
    total_sales = float(route_df["Sales"].sum()) if "Sales" in route_df.columns else 0.0
    total_cogs = float(route_df["Cost"].sum()) if "Cost" in route_df.columns else 0.0
    gross_profit = float(route_df["Gross Profit"].sum()) if "Gross Profit" in route_df.columns else (total_sales - total_cogs)
    gross_margin_pct = (gross_profit / total_sales * 100.0) if total_sales > 0 else 0.0
    distance_km = float(route_df["distance_km"].iloc[0]) if ("distance_km" in route_df.columns and route_df["distance_km"].notna().any()) else 0.0

    has_lead_time = "lead_time_days" in route_df.columns and route_df["lead_time_days"].notna().any()

    # Commercial & Volume KPIs
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    kpi_col1.metric("Order Lines (N)", f"{order_line_count:,}", help="Distinct Customer Orders (shipment grain)")
    kpi_col2.metric("Line Items", f"{line_item_count:,}", help="Total product lines across all orders")
    kpi_col3.metric("Gross Revenue", f"${total_sales:,.2f}")
    kpi_col4.metric("Manufacturing COGS", f"${total_cogs:,.2f}", help="Manufacturing costs only; excludes freight shipping charges (AD-11)")
    kpi_col5.metric("Gross Margin", f"{gross_margin_pct:.1f}%")

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # Operational Lead-Time KPIs
    kpi2_col1, kpi2_col2, kpi2_col3, kpi2_col4, kpi2_col5 = st.columns(5)

    if has_lead_time:
        # Group by Order ID to calculate shipment-level lead times accurately
        order_grouped = route_df.drop_duplicates(subset=["Order ID"]) if "Order ID" in route_df.columns else route_df
        mean_lt = float(order_grouped["lead_time_days"].mean())
        median_lt = float(order_grouped["lead_time_days"].median())
        p90_lt = float(order_grouped["lead_time_days"].quantile(0.90))

        # Strict delay rule: lead_time_days > delay_threshold (AD-07)
        delayed_orders = int((order_grouped["lead_time_days"] > delay_threshold).sum())
        delay_rate_pct = (delayed_orders / len(order_grouped) * 100.0) if len(order_grouped) > 0 else 0.0

        kpi2_col1.metric("Mean Order-to-Ship Lead Time", f"{mean_lt:.2f} d")
        kpi2_col2.metric("Median Order-to-Ship Lead Time", f"{median_lt:.2f} d")
        kpi2_col3.metric("P90 Lead Time", f"{p90_lt:.2f} d")
        kpi2_col4.metric(
            f"Delay Rate (>{delay_threshold:.1f}d)",
            f"{delay_rate_pct:.1f}%",
            delta=f"{delayed_orders} of {order_line_count} orders",
            delta_color="inverse",
            help=f"Strict delay rule: Order-to-Ship Lead Time > {delay_threshold:.1f} days",
        )
        kpi2_col5.metric("Centroid Distance", f"{distance_km:,.1f} km", help="Haversine distance between Factory and Destination Centroid")
    else:
        total_units = int(route_df["Units"].sum()) if "Units" in route_df.columns else 0
        kpi2_col1.metric("Total Units", f"{total_units:,}")
        kpi2_col2.metric("Centroid Distance", f"{distance_km:,.1f} km")
        kpi2_col3.metric("Lead-Time Analysis", "Requires Synthetic Layer")
        kpi2_col4.metric("Delay Rate", "N/A (Historical)")
        kpi2_col5.metric("Timing Status", "Unsimulated")


# ──────────────────────────────────────────────────────────────────────────────
# Helper: order-to-ship timeline chart
# ──────────────────────────────────────────────────────────────────────────────

def build_timeline_figure(
    route_df: pd.DataFrame,
    route_key: str,
    delay_threshold: float,
) -> Optional[go.Figure]:
    """
    Constructs an interactive Plotly timeline scatter chart for the selected route.
    Plots Order Date on x-axis vs Order-to-Ship Lead Time on y-axis with a dashed
    delay threshold line. Strictly labeled 'Order-to-Ship Lead Time', never 'Transit Time'.
    """
    if "lead_time_days" not in route_df.columns:
        return None

    # Deduplicate to distinct customer orders for the shipment timeline
    plot_df = (
        route_df.drop_duplicates(subset=["Order ID"]).copy().reset_index(drop=True)
        if "Order ID" in route_df.columns
        else route_df.copy().reset_index(drop=True)
    )
    plot_df = plot_df.dropna(subset=["lead_time_days"]).reset_index(drop=True)
    if plot_df.empty:
        return None

    # Sort chronologically by Order Date if available
    order_date_col = "Order Date" if "Order Date" in plot_df.columns else None
    if order_date_col:
        plot_df["order_dt"] = pd.to_datetime(plot_df[order_date_col], errors="coerce", dayfirst=True)
        plot_df = plot_df.sort_values(by="order_dt").reset_index(drop=True)
        x_vals = plot_df["order_dt"]
        x_title = "Order Date"
    else:
        plot_df["order_idx"] = range(1, len(plot_df) + 1)
        x_vals = plot_df["order_idx"]
        x_title = "Order Index"

    # Strict delay rule: lead_time_days > delay_threshold
    plot_df["is_delayed"] = plot_df["lead_time_days"] > delay_threshold

    ship_date_col = "Ship_Date_Synthetic" if "Ship_Date_Synthetic" in plot_df.columns else ("Ship Date" if "Ship Date" in plot_df.columns else None)

    def _col_series(col: Optional[str]) -> List[str]:
        if col and col in plot_df.columns:
            return plot_df[col].astype(str).tolist()
        return ["N/A"] * len(plot_df)

    order_ids = _col_series("Order ID")
    cust_ids = _col_series("Customer ID")
    order_dates = _col_series("Order Date")
    ship_dates = _col_series(ship_date_col)
    ship_modes = _col_series("Ship Mode")
    factories = _col_series("Factory")

    status_labels = ["Delayed" if d else "On-Time" for d in plot_df["is_delayed"]]

    customdata_list = list(zip(
        order_ids,
        cust_ids,
        order_dates,
        ship_dates,
        ship_modes,
        factories,
        status_labels,
    ))
    customdata_arr = np.array(customdata_list, dtype=object)

    fig = go.Figure()

    hovertemplate = (
        "<b>Order ID:</b> %{customdata[0]}<br>"
        "<b>Customer ID:</b> %{customdata[1]}<br>"
        "<b>Order Date:</b> %{customdata[2]}<br>"
        "<b>Ship Date:</b> %{customdata[3]}<br>"
        "<b>Ship Mode:</b> %{customdata[4]}<br>"
        "<b>Factory:</b> %{customdata[5]}<br>"
        "<b>Order-to-Ship Lead Time:</b> %{y:.2f} days<br>"
        "<b>Status:</b> %{customdata[6]}"
        "<extra></extra>"
    )

    # 1. On-Time Orders Trace
    on_time_mask = (~plot_df["is_delayed"]).to_numpy()
    if on_time_mask.any():
        fig.add_trace(go.Scatter(
            x=x_vals[on_time_mask],
            y=plot_df.loc[on_time_mask, "lead_time_days"],
            mode="markers",
            name="On-Time Orders",
            marker=dict(size=8, color="#2ca02c", opacity=0.75, line=dict(width=1, color="rgb(30,30,30)")),
            customdata=customdata_arr[on_time_mask],
            hovertemplate=hovertemplate,
        ))

    # 2. Delayed Orders Trace
    delayed_mask = plot_df["is_delayed"].to_numpy()
    if delayed_mask.any():
        fig.add_trace(go.Scatter(
            x=x_vals[delayed_mask],
            y=plot_df.loc[delayed_mask, "lead_time_days"],
            mode="markers",
            name=f"Delayed Orders (>{delay_threshold:.1f}d)",
            marker=dict(size=10, symbol="diamond", color="#d62728", opacity=0.85, line=dict(width=1, color="rgb(30,30,30)")),
            customdata=customdata_arr[delayed_mask],
            hovertemplate=hovertemplate,
        ))

    # 3. Horizontal Delay Threshold Reference Line
    fig.add_hline(
        y=delay_threshold,
        line_dash="dash",
        line_color="#ff7f0e",
        line_width=2,
        annotation_text=f"Delay Threshold: {delay_threshold:.1f}d",
        annotation_position="top right",
        annotation_font=dict(color="#d62728", size=11),
    )

    fig.update_layout(
        title=dict(
            text=f"Order-to-Ship Lead Time Timeline — {route_key}",
            font=dict(size=15, color="#1a1a2e"),
        ),
        xaxis_title=x_title,
        yaxis_title="Order-to-Ship Lead Time (Days)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=430,
        margin=dict(l=60, r=40, t=80, b=60),
        font=dict(family="Inter, sans-serif", size=12),
        hovermode="closest",
    )

    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", zeroline=False)

    return fig


# ──────────────────────────────────────────────────────────────────────────────
# Helper: Canadian routes distance callout & table
# ──────────────────────────────────────────────────────────────────────────────

def render_canadian_route_section(df: pd.DataFrame, route_df: pd.DataFrame, delay_threshold: float = 5.0):
    """
    Renders Canadian centroid distance callout and network table (FR-09, FR-12).
    """
    if route_df.empty:
        return

    is_route_canadian = (
        ("is_canadian" in route_df.columns and bool(route_df["is_canadian"].iloc[0]))
        or ("Country/Region" in route_df.columns and str(route_df["Country/Region"].iloc[0]).strip() == "Canada")
    )

    if is_route_canadian:
        dest_prov = route_df["State/Province"].iloc[0] if "State/Province" in route_df.columns else "Canada"
        factory_name = route_df["Factory"].iloc[0] if "Factory" in route_df.columns else "Factory"
        distance_km = float(route_df["distance_km"].iloc[0]) if "distance_km" in route_df.columns else 0.0

        st.info(
            f"🍁 **Canadian Fulfillment Route Notice (FR-09 / FR-12):**\n\n"
            f"- **Lane:** {factory_name} → {dest_prov}, Canada\n"
            f"- **Factory-to-Province Centroid Haversine Distance:** **{distance_km:,.1f} km**\n"
            f"- **Methodology Notice:** Canadian destinations are excluded from US state choropleth map geometries "
            f"(Page 4) to prevent map distortion, but are 100% retained in all company volume, financial, and route efficiency metrics.",
            icon="ℹ️",
        )

    # Canadian network orders table
    if "Country/Region" in df.columns:
        canada_df = df[df["Country/Region"].astype(str).str.strip() == "Canada"].copy()
        if not canada_df.empty:
            with st.expander(f"🇨🇦 View All Canadian Network Orders ({len(canada_df):,} lines across Canada)", expanded=is_route_canadian):
                st.caption(
                    "Canadian destinations use factory-to-province centroid Haversine distances. "
                    "These routes are excluded from the US State Choropleth (Page 4) but retained in all company totals."
                )
                col_map = {
                    "Order ID": "Order ID",
                    "Factory": "Factory",
                    "State/Province": "Province",
                    "Ship Mode": "Ship Mode",
                    "distance_km": "Distance (km)",
                    "lead_time_days": "Order-to-Ship Lead Time (Days)",
                    "Units": "Units",
                    "Sales": "Sales ($)",
                    "Gross Profit": "Gross Profit ($)",
                }
                present_cols = [c for c in col_map if c in canada_df.columns]
                show_can = canada_df[present_cols].rename(columns=col_map).copy()
                if "Order-to-Ship Lead Time (Days)" in show_can.columns:
                    show_can["Order-to-Ship Lead Time (Days)"] = show_can["Order-to-Ship Lead Time (Days)"].round(2)
                if "Distance (km)" in show_can.columns:
                    show_can["Distance (km)"] = show_can["Distance (km)"].round(1)

                st.dataframe(show_can, use_container_width=True, height=260, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: order line detail table
# ──────────────────────────────────────────────────────────────────────────────

def render_order_line_table(route_df: pd.DataFrame, delay_threshold: float):
    """Renders per-order-line table with key fields."""
    ship_date_col = "Ship_Date_Synthetic" if "Ship_Date_Synthetic" in route_df.columns else "Ship Date"
    col_map = {
        "Order ID": "Order ID",
        "Order Date": "Order Date",
        ship_date_col: "Ship Date (Synthetic)" if "Ship_Date_Synthetic" in route_df.columns else "Ship Date",
        "Ship Mode": "Ship Mode",
        "Factory": "Factory",
        "State/Province": "Destination State/Province",
        "Country/Region": "Country",
        "distance_km": "Distance (km)",
        "lead_time_days": "Order-to-Ship Lead Time (Days)",
        "Product Name": "Product Name",
        "Units": "Units",
        "Sales": "Gross Revenue ($)",
        "Cost": "Manufacturing COGS ($)",
        "Gross Profit": "Gross Profit ($)",
    }

    present_cols = [c for c in col_map if c in route_df.columns]
    show_df = route_df[present_cols].rename(columns=col_map).copy()

    if "Order-to-Ship Lead Time (Days)" in show_df.columns:
        show_df["Order-to-Ship Lead Time (Days)"] = show_df["Order-to-Ship Lead Time (Days)"].round(2)
    if "Distance (km)" in show_df.columns:
        show_df["Distance (km)"] = show_df["Distance (km)"].round(1)

    st.dataframe(show_df, use_container_width=True, height=360, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# Main page
# ──────────────────────────────────────────────────────────────────────────────

def render_page():
    filters = render_sidebar_filters()

    st.title("🔍 Route Drill-Down & Order-to-Ship Timeline")
    st.markdown(
        "Granular lane inspection — select a specific factory-to-destination route to review "
        "individual order timelines, order-to-ship lead times, and Canadian centroid distances (FR-12)."
    )

    render_layer_banner(filters["layer"], filters.get("scenario"))

    st.divider()

    # 1. Mandatory Non-Causal & Operational Screening Disclosure (FR-12, AD-08)
    st.info(
        "🔍 **Operational Screening Disclosure (FR-12 & AD-08):** "
        "Lead times shown on this page represent **Order-to-Ship Lead Time** "
        "(order placement date to shipment dispatch date). This is NOT carrier transit time or customer delivery time. "
        "Delays reflect simulated fulfillment latency, not verified operational failures. "
        "Strict delay threshold is set at **{:.1f} days**.".format(filters["delay_threshold"]),
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

    # 3. Route Selector
    df, route_options = build_route_options(df)
    if not route_options:
        st.warning("No route keys could be constructed from the available data.")
        return

    # Default to canonical bottleneck route if present, else highest volume route
    canonical_route = "Lot's O' Nuts -> Texas"
    default_index = 0
    if canonical_route in route_options:
        default_index = route_options.index(canonical_route)

    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        selected_route = st.selectbox(
            "Select Route Lane (Factory → Destination)",
            options=route_options,
            index=default_index,
            key="drilldown_route_selector",
            help="Select an individual factory-to-state or regional shipping lane.",
        )

    route_df = filter_to_route(df, selected_route)

    with sel_col2:
        order_n = route_df["Order ID"].nunique() if "Order ID" in route_df.columns else len(route_df)
        is_eligible = order_n >= MIN_SAMPLE_SIZE
        sample_badge = "✅ Robust Sample (N >= 30)" if is_eligible else "⚠️ Low Sample (N < 30)"
        st.metric("Lane Order Lines (N)", f"{order_n:,}")
        st.caption(sample_badge)

    if route_df.empty:
        st.warning(f"No order lines found for route: **{selected_route}**")
        return

    # Low sample guardrail warning (AD-07)
    if not is_eligible:
        st.warning(
            f"⚠️ **Low Sample Size Warning (AD-07):** Route **{selected_route}** contains only "
            f"N = {order_n} distinct order lines (below the N >= {MIN_SAMPLE_SIZE} statistical threshold). "
            "Summary lead times and delay rates may exhibit high variance.",
            icon="⚠️",
        )

    # 4. Canadian Route Centroid Distance Callout
    render_canadian_route_section(df, route_df, filters["delay_threshold"])

    # 5. Route Summary KPIs
    st.divider()
    st.subheader(f"📊 Summary Statistics — {selected_route}")
    render_route_summary(route_df, filters["delay_threshold"])

    # 6. Interactive Order-to-Ship Timeline Chart
    st.divider()
    st.subheader("📈 Order-to-Ship Timeline Visualizer")

    has_lead_time = "lead_time_days" in route_df.columns and route_df["lead_time_days"].notna().any()

    if has_lead_time:
        fig = build_timeline_figure(route_df, selected_route, filters["delay_threshold"])
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                f"💡 **Timeline Guide:** Each point represents a distinct customer order shipment. "
                f"Red diamonds indicate delayed orders with Order-to-Ship Lead Time strictly greater than {filters['delay_threshold']:.1f} days. "
                f"Green circles reflect on-time dispatches. Orange dashed line marks the {filters['delay_threshold']:.1f}-day delay threshold."
            )
        else:
            st.info("No valid lead time points available to construct timeline figure.")
    else:
        st.warning(
            "⚠️ Order-to-Ship Lead Time simulation and delay analysis require calibrated timing from the **SYNTHETIC** layer (AD-02). "
            "Currently viewing historical distributor records without simulated fulfillment intervals."
        )

    # 7. Granular Order Line Details Table
    st.divider()
    st.subheader("📋 Granular Order Line Records")
    st.caption(
        "Individual product order line items associated with this lane. "
        "Manufacturing COGS reflects direct material/production cost only (excludes freight carrier fees per AD-11)."
    )
    render_order_line_table(route_df, filters["delay_threshold"])

    # 8. Audited CSV Export Engine
    st.divider()
    st.subheader("📥 Audited Route Export")

    # Pass route_df directly to create_export_csv with complete provenance metadata
    csv_bytes = create_export_csv(
        df=route_df,
        metadata={
            "layer": filters.get("layer", "SYNTHETIC"),
            "scenario": filters.get("scenario", "baseline"),
            "delay_threshold": filters.get("delay_threshold", DEFAULT_DELAY_THRESHOLD),
            "route": selected_route,
            "screening": "route_drill_down",
            "filters": filters,
        },
    )

    safe_route = selected_route.replace(" ", "_").replace("'", "").replace("->", "to")
    st.download_button(
        label=f"📥 Download Audited CSV: {selected_route}",
        data=csv_bytes,
        file_name=f"nassau_route_{safe_route}_{filters.get('scenario', 'baseline')}.csv",
        mime="text/csv",
        key="drilldown_export_btn",
    )
    st.caption("Provenance metadata prepended to export: Data Layer, Active Scenario, Delay Threshold, and Timestamp.")


if __name__ == "__main__":
    render_page()
