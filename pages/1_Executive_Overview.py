"""
Page 1: Executive Overview & Margin Analysis.
High-level commercial KPIs, order grain distinction (8,549 order lines vs 9,881 line items),
factory and product margin breakdowns, and mandatory AD-11 freight cost disclaimer banners.
"""

import pandas as pd
import streamlit as st

from app import (
    get_active_dataset,
    render_layer_banner,
    render_margin_disclaimer,
    render_sidebar_filters,
)
from src.config import (
    ORDER_LINE_COUNT,
    RECONCILIATION_TARGETS,
)
from src.exports import create_export_csv


st.set_page_config(
    page_title="Executive Overview | Nassau Route Intelligence",
    page_icon="📈",
    layout="wide",
)


def render_page():
    filters = render_sidebar_filters()

    st.title("📈 Executive Overview & Product Margin Analysis")
    st.markdown(
        "Commercial revenue, manufacturing COGS margins, product portfolio mix, "
        "and hierarchical order grain volume across the manufacturing network."
    )
    render_layer_banner(filters["layer"], filters["scenario"])

    df, ref_means = get_active_dataset(filters)

    st.divider()

    # ==========================================================================
    # 1. Commercial Financial KPIs & COGS Margin (AD-11)
    # ==========================================================================
    st.markdown("### 1. Commercial Financial Performance (COGS Basis)")

    total_sales = float(df["Sales"].sum()) if "Sales" in df.columns else 0.0
    total_cost = float(df["Cost"].sum()) if "Cost" in df.columns else 0.0
    total_profit = float(df["Gross Profit"].sum()) if "Gross Profit" in df.columns else 0.0
    margin_pct = (total_profit / total_sales * 100.0) if total_sales > 0 else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Gross Sales (Revenue)", f"${total_sales:,.2f}")
    with kpi2:
        st.metric("Manufacturing COGS", f"${total_cost:,.2f}")
    with kpi3:
        st.metric("Gross Profit", f"${total_profit:,.2f}")
    with kpi4:
        st.metric("Product Gross Margin", f"{margin_pct:.1f}%")

    st.info(
        "⚠️ **Financial Scope & Freight Disclaimer (AD-11):** "
        "Reported Cost reflects manufacturing COGS only; carrier freight transportation costs are not present in dataset. "
        "Sales, COGS, and Gross Profit represent product commercial profitability, not net logistics margins.",
        icon="ℹ️",
    )

    st.divider()

    # ==========================================================================
    # 2. Hierarchical Order Grains: Line Items vs Order Lines (AD-04)
    # ==========================================================================
    st.markdown("### 2. Operational Volume & Hierarchical Order Grains")
    st.caption(
        "Clarifying logistics hierarchy: Line Items (individual SKU rows) vs Order Lines (unique orders dispatched by factory)."
    )

    line_items = len(df)
    order_lines = df["Order ID"].nunique() if "Order ID" in df.columns else line_items
    total_units = int(df["Units"].sum()) if "Units" in df.columns else 0
    avg_units_per_line = (total_units / line_items) if line_items > 0 else 0.0

    vol1, vol2, vol3, vol4 = st.columns(4)
    with vol1:
        st.metric(
            "Line Items (Rows)",
            f"{line_items:,}",
            help="Total SKU rows in current view (9,881 baseline clean rows).",
        )
    with vol2:
        st.metric(
            "Order Lines (Dispatches)",
            f"{order_lines:,}",
            help="Total unique orders dispatched by factory (8,549 baseline order lines).",
        )
    with vol3:
        st.metric("Total Units Dispatched", f"{total_units:,}")
    with vol4:
        st.metric("Mean Units / Line", f"{avg_units_per_line:.1f} units")

    # Grain comparison card
    with st.expander("ℹ️ Logistics Grain Explanation: Order Lines vs Line Items", expanded=False):
        st.markdown(
            f"""
            * **Line Items ({line_items:,} rows in active filter):** The lowest transaction level in the raw dataset, where each row represents a specific product line within an order.
            * **Order Lines ({order_lines:,} unique Order IDs):** The operational fulfillment unit dispatched from a factory.
            * **Ratio:** Multi-item orders average **{line_items / max(1, order_lines):.2f} line items per order line**, with an average of **{avg_units_per_line:.1f} units per line item**.
            * **Multi-Factory Grouping:** In the full clean dataset, 1,702 customer shipments require products from multiple factories, resulting in 8,549 factory order dispatches across 5,067 customer shipments.
            """
        )

    st.divider()

    # ==========================================================================
    # 3. Factory Commercial & Manufacturing Performance Breakdown
    # ==========================================================================
    st.markdown("### 3. Factory Commercial Performance Breakdown")

    if "Factory" in df.columns:
        factory_stats = df.groupby("Factory").agg(
            order_lines=("Order ID", "nunique") if "Order ID" in df.columns else ("Row ID", "count"),
            line_items=("Row ID", "count") if "Row ID" in df.columns else ("Sales", "count"),
            units=("Units", "sum") if "Units" in df.columns else ("Sales", "count"),
            sales=("Sales", "sum"),
            cost=("Cost", "sum"),
            gross_profit=("Gross Profit", "sum"),
        ).reset_index()

        factory_stats["margin_pct"] = (factory_stats["gross_profit"] / factory_stats["sales"] * 100.0).round(1)

        # Format display dataframe
        disp_factory = factory_stats.copy()
        disp_factory = disp_factory.sort_values(by="sales", ascending=False)
        disp_factory["sales"] = disp_factory["sales"].apply(lambda x: f"${x:,.2f}")
        disp_factory["cost"] = disp_factory["cost"].apply(lambda x: f"${x:,.2f}")
        disp_factory["gross_profit"] = disp_factory["gross_profit"].apply(lambda x: f"${x:,.2f}")
        disp_factory["margin_pct"] = disp_factory["margin_pct"].apply(lambda x: f"{x:.1f}%")
        disp_factory["order_lines"] = disp_factory["order_lines"].apply(lambda x: f"{x:,}")
        disp_factory["line_items"] = disp_factory["line_items"].apply(lambda x: f"{x:,}")
        disp_factory["units"] = disp_factory["units"].apply(lambda x: f"{x:,}")

        disp_factory.columns = [
            "Manufacturing Facility",
            "Order Lines",
            "Line Items",
            "Units Sold",
            "Gross Revenue",
            "Manufacturing COGS",
            "Gross Profit",
            "Gross Margin %",
        ]

        st.dataframe(disp_factory, use_container_width=True, hide_index=True)
        csv_bytes_fac = create_export_csv(
            factory_stats,
            metadata={
                "layer": filters["layer"],
                "scenario": filters["scenario"],
                "filters": filters,
            },
        )
        st.download_button(
            label="📥 Download Factory Financials (Audited CSV)",
            data=csv_bytes_fac,
            file_name="nassau_factory_financials.csv",
            mime="text/csv",
        )

    st.divider()

    # ==========================================================================
    # 4. Product Division Mix & Top 10 Products by Revenue
    # ==========================================================================
    st.markdown("### 4. Product Division Mix & Top Commercial Products")

    div_col, top_col = st.columns([1, 1])

    with div_col:
        st.markdown("#### Portfolio Mix by Division")
        if "Division" in df.columns:
            div_stats = df.groupby("Division").agg(
                sales=("Sales", "sum"),
                profit=("Gross Profit", "sum"),
                units=("Units", "sum"),
            ).reset_index()
            div_stats["margin_pct"] = (div_stats["profit"] / div_stats["sales"] * 100.0).round(1)
            div_stats = div_stats.sort_values(by="sales", ascending=False)

            chart_data = div_stats.set_index("Division")[["sales", "profit"]]
            chart_data.columns = ["Revenue ($)", "Gross Profit ($)"]
            st.bar_chart(chart_data)

            for _, r in div_stats.iterrows():
                st.caption(f"**{r['Division']}**: ${r['sales']:,.2f} sales ({r['units']:,} units, {r['margin_pct']:.1f}% margin)")

    with top_col:
        st.markdown("#### Top 10 Products by Sales")
        if "Product Name" in df.columns:
            prod_stats = df.groupby(["Product Name", "Factory"]).agg(
                units=("Units", "sum"),
                sales=("Sales", "sum"),
                gross_profit=("Gross Profit", "sum"),
            ).reset_index()
            prod_stats["margin_pct"] = (prod_stats["gross_profit"] / prod_stats["sales"] * 100.0).round(1)
            top10 = prod_stats.sort_values(by="sales", ascending=False).head(10).copy()

            top10_disp = top10.copy()
            top10_disp["sales"] = top10_disp["sales"].apply(lambda x: f"${x:,.2f}")
            top10_disp["gross_profit"] = top10_disp["gross_profit"].apply(lambda x: f"${x:,.2f}")
            top10_disp["margin_pct"] = top10_disp["margin_pct"].apply(lambda x: f"{x:.1f}%")
            top10_disp["units"] = top10_disp["units"].apply(lambda x: f"{x:,}")

            top10_disp.columns = [
                "Product Description",
                "Assigned Factory",
                "Units",
                "Revenue",
                "Gross Profit",
                "Margin %",
            ]
            st.dataframe(top10_disp, use_container_width=True, hide_index=True)

    # Monthly Revenue Trend
    if "Order Date" in df.columns:
        st.divider()
        st.markdown("### 5. Monthly Commercial Revenue & Margin Trend")
        try:
            temp_df = df.copy()
            temp_df["order_dt"] = pd.to_datetime(temp_df["Order Date"], format="%d-%m-%Y")
            temp_df["year_month"] = temp_df["order_dt"].dt.to_period("M").astype(str)

            monthly = temp_df.groupby("year_month").agg(
                revenue=("Sales", "sum"),
                gross_profit=("Gross Profit", "sum"),
            ).reset_index()
            monthly = monthly.sort_values(by="year_month")

            monthly_chart = monthly.set_index("year_month")[["revenue", "gross_profit"]]
            monthly_chart.columns = ["Gross Revenue ($)", "Gross Profit ($)"]
            st.line_chart(monthly_chart)
            st.caption("Monthly historical billing trend across all distributor dispatches.")
        except Exception:
            pass


if __name__ == "__main__":
    render_page()
