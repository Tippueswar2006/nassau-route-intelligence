"""
Nassau Candy Route Intelligence - Streamlit Multi-Page Application Shell.
Provides cached Parquet artifact loading (@st.cache_data), global sidebar filter state,
AD-02 layer provenance banners, and executive cockpit summary.
Decoupled architecture: pure presentation layer, zero Streamlit imports inside src/.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st

from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
    RAW_DATA_PATH,
    SHIPPING_MODES,
    SMALL_FACTORIES,
)
from src.load_data import (
    get_deployment_mode,
    load_metadata,
    load_prepared_artifacts,
    load_raw_data,
    load_transformation_log,
)
from src.metrics import (
    apply_delay_threshold,
    calculate_mode_adjusted_lead_time,
    compute_mode_reference_means,
)


# ==============================================================================
# 1. Page Configuration & Setup
# ==============================================================================

st.set_page_config(
    page_title="Nassau Route Intelligence",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# 2. Presentation Layer Caching (@st.cache_data)
# ==============================================================================

@st.cache_data(show_spinner=False)
def get_cached_artifacts() -> Dict[str, pd.DataFrame]:
    """
    Cached loader for pre-computed Parquet artifacts.
    Loads once into memory and serves sub-second filtered views.
    """
    return load_prepared_artifacts()


@st.cache_data(show_spinner=False)
def get_cached_metadata() -> Dict[str, Any]:
    """Cached loader for synthetic and build metadata."""
    return load_metadata()


@st.cache_data(show_spinner=False)
def get_cached_transformation_log() -> Dict[str, Any]:
    """Cached loader for data quality transformation log."""
    return load_transformation_log()


@st.cache_data(show_spinner=False)
def get_cached_raw_data() -> Optional[pd.DataFrame]:
    """Cached loader for raw original data (local development only)."""
    if RAW_DATA_PATH.exists():
        try:
            return load_raw_data(RAW_DATA_PATH, verify_hash=True)
        except Exception:
            return None
    return None


# ==============================================================================
# 3. Session State Management
# ==============================================================================

def init_session_state():
    """Initializes global filter state in st.session_state if not already present."""
    defaults = {
        "filter_layer": "SYNTHETIC",
        "filter_scenario": "baseline",
        "filter_factories": [],
        "filter_regions": [],
        "filter_states": [],
        "filter_ship_modes": [],
        "filter_delay_threshold": DEFAULT_DELAY_THRESHOLD,
        "filter_exclude_duplicates": True,
        "filter_res_weight_speed": DEFAULT_RES_WEIGHT_SPEED,
        "filter_res_weight_var": DEFAULT_RES_WEIGHT_VARIABILITY,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ==============================================================================
# 4. Sidebar Controls & Global Filters
# ==============================================================================

def render_sidebar_filters() -> Dict[str, Any]:
    """
    Renders global sidebar filters across all application pages.
    Returns the active filter parameters dictionary.
    """
    init_session_state()
    mode = get_deployment_mode()

    with st.sidebar:
        st.markdown("## 🍬 Nassau Route Intelligence")
        st.caption(f"Deployment Mode: **{mode.upper()}** (Zero-PII Cloud Artifacts)")
        st.divider()

        st.markdown("### 1. Data Layer & Provenance")
        available_layers = ["SYNTHETIC", "DERIVED"]
        if mode == "local":
            available_layers.append("ORIGINAL")

        selected_layer = st.selectbox(
            "Select Data Layer",
            options=available_layers,
            index=available_layers.index(st.session_state.filter_layer) if st.session_state.filter_layer in available_layers else 0,
            help="Strict Three-Tier Layer Separation (AD-02). SYNTHETIC contains calibrated lead times.",
            key="sb_layer",
        )
        st.session_state.filter_layer = selected_layer

        selected_scenario = st.session_state.filter_scenario
        if selected_layer == "SYNTHETIC":
            scenario_options = {
                "baseline": "Baseline (Empirical Sampling)",
                "distance_sensitive": "Distance-Sensitive Model",
                "stress_test": "Stress Test (Injected Delays)",
            }
            scenario_key = st.selectbox(
                "Synthetic Scenario",
                options=list(scenario_options.keys()),
                format_func=lambda x: scenario_options[x],
                index=list(scenario_options.keys()).index(selected_scenario) if selected_scenario in scenario_options else 0,
                help="Multi-scenario synthetic lead-time engine (Seed 42).",
                key="sb_scenario",
            )
            selected_scenario = scenario_key
            st.session_state.filter_scenario = scenario_key

        st.divider()
        st.markdown("### 2. Geographic & Route Filters")

        # Load clean orders to inspect available filter categories
        try:
            artifacts = get_cached_artifacts()
            base_ref = artifacts.get("clean_orders", pd.DataFrame())
        except Exception:
            base_ref = pd.DataFrame()

        factory_list = sorted(base_ref["Factory"].dropna().unique().tolist()) if not base_ref.empty and "Factory" in base_ref.columns else []
        region_list = sorted(base_ref["Region"].dropna().unique().tolist()) if not base_ref.empty and "Region" in base_ref.columns else ["Atlantic", "Gulf", "Interior", "Pacific"]
        state_list = sorted(base_ref["State/Province"].dropna().unique().tolist()) if not base_ref.empty and "State/Province" in base_ref.columns else []

        selected_factories = st.multiselect(
            "Factory Origin",
            options=factory_list,
            default=st.session_state.filter_factories,
            placeholder="All Factories",
            key="sb_factories",
        )
        st.session_state.filter_factories = selected_factories

        selected_regions = st.multiselect(
            "Destination Region",
            options=region_list,
            default=st.session_state.filter_regions,
            placeholder="All Regions",
            key="sb_regions",
        )
        st.session_state.filter_regions = selected_regions

        selected_states = st.multiselect(
            "Destination State/Province",
            options=state_list,
            default=st.session_state.filter_states,
            placeholder="All States (59 distinct)",
            key="sb_states",
        )
        st.session_state.filter_states = selected_states

        st.divider()
        st.markdown("### 3. Shipping & Thresholds")

        selected_modes = st.multiselect(
            "Ship Mode",
            options=SHIPPING_MODES,
            default=st.session_state.filter_ship_modes,
            placeholder="All Ship Modes",
            key="sb_modes",
        )
        st.session_state.filter_ship_modes = selected_modes

        delay_threshold = st.slider(
            "Delay Threshold (Days)",
            min_value=1.0,
            max_value=15.0,
            value=float(st.session_state.filter_delay_threshold),
            step=0.5,
            help="Strict inequality: Lead Time > Threshold is delayed (AD-09). Exactly 5.0d is on-time.",
            key="sb_delay_threshold",
        )
        st.session_state.filter_delay_threshold = delay_threshold

        exclude_duplicates = st.checkbox(
            "Exclude Duplicate Orders",
            value=st.session_state.filter_exclude_duplicates,
            help="Excludes 313 exact duplicate order records reconciling 4 financial metrics (AD-12).",
            key="sb_exclude_dup",
        )
        st.session_state.filter_exclude_duplicates = exclude_duplicates

        st.divider()
        if st.button("🔄 Reset All Filters", use_container_width=True):
            st.session_state.filter_factories = []
            st.session_state.filter_regions = []
            st.session_state.filter_states = []
            st.session_state.filter_ship_modes = []
            st.session_state.filter_delay_threshold = DEFAULT_DELAY_THRESHOLD
            st.session_state.filter_exclude_duplicates = True
            st.rerun()

    return {
        "layer": selected_layer,
        "scenario": selected_scenario,
        "factories": selected_factories,
        "regions": selected_regions,
        "states": selected_states,
        "ship_modes": selected_modes,
        "delay_threshold": delay_threshold,
        "exclude_duplicates": exclude_duplicates,
        "weight_speed": st.session_state.filter_res_weight_speed,
        "weight_var": st.session_state.filter_res_weight_var,
    }


# ==============================================================================
# 5. Data Retrieval & Filtering Pipeline
# ==============================================================================

def get_active_dataset(filters: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Retrieves and filters the active dataset based on selected sidebar criteria.
    Maintains invariant ship-mode reference means pre-computed before filtering.

    Returns:
      (filtered_df, precomputed_mode_reference_means)
    """
    layer = filters["layer"]
    scenario = filters["scenario"]
    artifacts = get_cached_artifacts()

    # Select base dataset
    if layer == "ORIGINAL":
        raw_df = get_cached_raw_data()
        if raw_df is not None:
            from src.validate_data import clean_dataset
            df = clean_dataset(raw_df)
        else:
            df = artifacts["clean_orders"].copy()
        df["data_layer"] = "ORIGINAL"
        ref_means = {}
    elif layer == "DERIVED":
        df = artifacts["clean_orders"].copy()
        df["data_layer"] = "DERIVED"
        ref_means = {}
    else:  # SYNTHETIC
        df = artifacts.get(scenario, artifacts["baseline"]).copy()
        df["data_layer"] = "SYNTHETIC"
        # Pre-compute scenario mode reference means on FULL dataset before user filters (AD-06)
        ref_means = compute_mode_reference_means(df)
        df = calculate_mode_adjusted_lead_time(df, ref_means)

    # 1. Filter duplicates if requested
    if filters["exclude_duplicates"] and "is_duplicate" in df.columns:
        df = df[~df["is_duplicate"]].copy()

    # 2. Filter Factory
    if filters["factories"] and "Factory" in df.columns:
        df = df[df["Factory"].isin(filters["factories"])].copy()

    # 3. Filter Region
    if filters["regions"] and "Region" in df.columns:
        df = df[df["Region"].isin(filters["regions"])].copy()

    # 4. Filter State/Province
    if filters["states"] and "State/Province" in df.columns:
        df = df[df["State/Province"].isin(filters["states"])].copy()

    # 5. Filter Ship Mode
    if filters["ship_modes"] and "Ship Mode" in df.columns:
        df = df[df["Ship Mode"].isin(filters["ship_modes"])].copy()

    # 6. Apply strict delay thresholding
    if "lead_time_days" in df.columns:
        df = apply_delay_threshold(df, threshold_days=filters["delay_threshold"])

    return df, ref_means


# ==============================================================================
# 6. Persistent Header & Layer Provenance Banners
# ==============================================================================

def render_layer_banner(layer: str, scenario: Optional[str] = None):
    """
    Renders persistent header badges in compliance with AD-02 and AD-11:
      - ORIGINAL - SOURCE DATA
      - DERIVED - CALCULATED FROM SOURCE
      - SYNTHETIC - NOT ACTUAL PERFORMANCE
    """
    if layer == "ORIGINAL":
        st.info(
            "🔷 **DATA LAYER: ORIGINAL — SOURCE DATA** | "
            "Direct historical distributor records. Unmodified raw observations (local-only layer).",
            icon="ℹ️",
        )
    elif layer == "DERIVED":
        st.success(
            "🟢 **DATA LAYER: DERIVED — CALCULATED FROM SOURCE** | "
            "Cleaned and mapped historical records. Normalized fields, duplicate reconciliation flags, "
            "and factory-centroid assignments.",
            icon="✅",
        )
    else:  # SYNTHETIC
        scenario_label = {
            "baseline": "Baseline (Empirical Calibration)",
            "distance_sensitive": "Distance-Sensitive Simulation (+0.5d / 1000km)",
            "stress_test": "Stress Test (Simulated Assumptions: +1.0d peak season, +1.0d CA/NY, +1.5d Texas)",
        }.get(scenario, scenario or "Synthetic")

        st.warning(
            f"🔶 **DATA LAYER: SYNTHETIC — NOT ACTUAL PERFORMANCE** | "
            f"Active Scenario: **{scenario_label}**. Lead times are simulated based on empirical distributions and "
            f"distance models. NOT verified carrier delivery stamps.",
            icon="⚠️",
        )


def render_margin_disclaimer():
    """Renders mandatory financial disclaimer per AD-11 (COGS vs Freight)."""
    st.caption(
        "⚠️ *Financial Disclaimer (AD-11): Reported Cost reflects manufacturing COGS only. "
        "Carrier freight expenses are absent from the source dataset.*"
    )


# ==============================================================================
# 7. Application Landing View (app.py Entrypoint)
# ==============================================================================

def main():
    start_time = time.time()
    filters = render_sidebar_filters()

    # Header & Layer Banner
    st.title("🍬 Nassau Candy Route Intelligence")
    st.markdown(
        "Enterprise logistics performance analytics, mode-adjusted route efficiency scoring, "
        "and bottleneck discovery engine."
    )
    render_layer_banner(filters["layer"], filters["scenario"])

    # Load filtered dataset
    df, ref_means = get_active_dataset(filters)

    # Executive Overview KPI Cards
    st.markdown("### 📊 Executive Overview Cockpit")

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    order_lines = len(df)
    orders_count = df["Order ID"].nunique() if "Order ID" in df.columns else order_lines
    total_units = int(df["Units"].sum()) if "Units" in df.columns else 0
    total_sales = float(df["Sales"].sum()) if "Sales" in df.columns else 0.0
    total_profit = float(df["Gross Profit"].sum()) if "Gross Profit" in df.columns else 0.0
    margin_pct = (total_profit / total_sales * 100.0) if total_sales > 0 else 0.0

    with kpi1:
        st.metric("Total Order Lines", f"{order_lines:,}")
    with kpi2:
        st.metric("Unique Orders", f"{orders_count:,}")
    with kpi3:
        st.metric("Total Units", f"{total_units:,}")
    with kpi4:
        st.metric("Gross Revenue", f"${total_sales:,.2f}")
    with kpi5:
        st.metric("Gross Profit", f"${total_profit:,.2f}", f"{margin_pct:.1f}% Margin")

    render_margin_disclaimer()

    # Operational Lead Time Cards (if Synthetic Layer)
    if "lead_time_days" in df.columns:
        st.markdown("### ⏱️ Operational Lead Time & Delay Summary")
        lt1, lt2, lt3, lt4 = st.columns(4)

        avg_lt = df["lead_time_days"].mean()
        med_lt = df["lead_time_days"].median()
        delay_count = int(df["is_delayed"].sum())
        delay_rate = (delay_count / len(df) * 100.0) if len(df) > 0 else 0.0
        ontime_rate = 100.0 - delay_rate

        with lt1:
            st.metric("Average Lead Time", f"{avg_lt:.2f} days")
        with lt2:
            st.metric("Median Lead Time", f"{med_lt:.2f} days")
        with lt3:
            st.metric("Delayed Shipments", f"{delay_count:,}", f"Threshold > {filters['delay_threshold']:.1f}d")
        with lt4:
            st.metric("On-Time Rate", f"{ontime_rate:.1f}%", f"{delay_rate:.1f}% delayed")

    # Module Navigation Directory
    st.divider()
    st.markdown("### 🧭 Application Navigation Directory")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            * **[1. Executive Overview](pages/1_Executive_Overview.py):** Comprehensive financial KPIs, order lines vs line items, and product COGS margins.
            * **[2. Data Quality & Method Audit](pages/2_Data_Quality_and_Method.py):** 4-metric reconciliation table, duplicate analysis, and diagnostic date reconstruction.
            * **[3. Route Efficiency Leaderboard](pages/3_Route_Efficiency.py):** Fixed 70/30 RES leaderboards, Top 10 / Bottom 10 routes, and mode-adjusted benchmarks.
            * **[4. Geographic Analysis](pages/4_Geographic_Analysis.py):** US state choropleth heatmaps with Canadian notice banner.
            """
        )
    with c2:
        st.markdown(
            """
            * **[5. Ship Mode Comparison](pages/5_Ship_Mode_Comparison.py):** Standard vs Expedited transit distributions and COGS margins by mode.
            * **[6. Potential Bottlenecks](pages/6_Potential_Bottlenecks.py):** 75th percentile screening quadrant scatter visualizer and watchlist explorer.
            * **[7. Route Drill Down](pages/7_Route_Drill_Down.py):** Route and state deep-dive explorer, order timeline visualizer, and Canadian drill-down.
            * **[8. Trends & Scenarios](pages/8_Trends_and_Scenarios.py):** Monthly volume trends, scenario comparisons, and interactive RES weight sensitivity lab.
            """
        )

    # Provenance and Metadata Card
    st.divider()
    meta = get_cached_metadata()
    if meta:
        with st.expander("🔍 System Architecture & Build Provenance Metadata", expanded=False):
            st.json(meta)

    elapsed_ms = (time.time() - start_time) * 1000.0
    st.caption(f"⚡ Page rendered in {elapsed_ms:.1f} ms | Parquet Cached Runtime")


if __name__ == "__main__":
    main()
