"""
Tests for Page 8: Trends & Scenarios Lab.
Verifies compliance with Story 5.5, FR-17, FR-19, AD-02, AD-07, AD-08, and AD-11 acceptance criteria:
- Monthly order volume seasonality aggregated from valid historical Original dates (2024–2025)
- Distinct Order Lines (Order ID nunique) versus Line Items (Row ID count)
- Multi-scenario monthly mean Order-to-Ship Lead-Time trajectories (Baseline, Stress Test, Distance Sensitive)
- Strict terminology: "Order-to-Ship Lead Time", never "Transit Time"
- Baseline vs. Stress Test scenario comparison highlighting Texas disruption
- Isolated RES weight sensitivity sandbox with presets (70/30, 50/50, 90/10, 100/0)
- Rank Delta arithmetic: Baseline Rank - Sensitivity Rank
- Rank stability indicators: Spearman rank correlation (rho), Top 10 retention %, mean absolute rank shift
- Strict session state isolation: Sensitivity widgets do not mutate global filter state
- Audited CSV exports through create_export_csv with complete provenance headers
- Non-causal operational screening disclosures (FR-17, AD-08) and AD-11 freight/COGS disclaimers
- Graceful degradation under DERIVED layer and empty filter selections
"""

import importlib
from typing import Any, Dict
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR, DEFAULT_DELAY_THRESHOLD, MIN_SAMPLE_SIZE
from src.exports import create_export_csv, parse_export_header
from src.load_data import load_prepared_artifacts

page_module = importlib.import_module("pages.8_Trends_and_Scenarios")
aggregate_monthly_volume = page_module.aggregate_monthly_volume
build_monthly_volume_figure = page_module.build_monthly_volume_figure
aggregate_scenario_lead_times = page_module.aggregate_scenario_lead_times
build_scenario_trend_figure = page_module.build_scenario_trend_figure
compute_res_weight_sensitivity = page_module.compute_res_weight_sensitivity


# ==============================================================================
# 1. Backend & Unit Level Verification
# ==============================================================================

def test_aggregate_monthly_volume_valid_historical_dates():
    """
    Verifies that aggregate_monthly_volume correctly aggregates order volume
    across valid 2024-2025 historical dates (FR-17), distinguishing between
    distinct orders and product line items.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    monthly_df = aggregate_monthly_volume(baseline_df)

    assert not monthly_df.empty
    assert len(monthly_df) == 24, f"Expected 24 calendar months (2024-2025), got {len(monthly_df)}"

    expected_cols = ["year_month", "order_line_count", "line_item_count", "total_units", "total_sales", "formatted_month"]
    for col in expected_cols:
        assert col in monthly_df.columns, f"Missing expected column: {col}"

    # Verify chronological sort
    assert list(monthly_df["year_month"]) == sorted(monthly_df["year_month"])
    assert monthly_df["year_month"].iloc[0] == "2024-01"
    assert monthly_df["year_month"].iloc[-1] == "2025-12"

    # Distinct orders vs product line items distinction
    total_orders = monthly_df["order_line_count"].sum()
    total_items = monthly_df["line_item_count"].sum()
    assert total_orders == baseline_df["Order ID"].nunique()
    assert total_items == len(baseline_df)
    assert total_items > total_orders, "Product line items must exceed distinct orders"

    # Total units and sales positive
    assert (monthly_df["total_units"] > 0).all()
    assert (monthly_df["total_sales"] > 0).all()
    assert monthly_df["formatted_month"].iloc[0] == "Jan 2024"


def test_aggregate_monthly_volume_empty_and_corrupt_data():
    """Verifies graceful handling of empty or invalid date data."""
    # Empty DataFrame
    assert aggregate_monthly_volume(pd.DataFrame()).empty

    # Missing Order Date column
    missing_col_df = pd.DataFrame({"Order ID": ["O1", "O2"]})
    assert aggregate_monthly_volume(missing_col_df).empty

    # Invalid/unparseable dates
    invalid_dates_df = pd.DataFrame({
        "Order ID": ["O1", "O2"],
        "Order Date": ["not-a-date", "invalid-str"],
    })
    assert aggregate_monthly_volume(invalid_dates_df).empty


def test_build_monthly_volume_figure():
    """
    Verifies build_monthly_volume_figure produces a valid Plotly bar chart
    with correct hovertemplate and strict lack of transit terminology.
    """
    artifacts = load_prepared_artifacts()
    monthly_df = aggregate_monthly_volume(artifacts["baseline"])

    fig = build_monthly_volume_figure(monthly_df)
    assert fig is not None
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"

    # Hovertemplate verification
    hovertemplate = fig.data[0].hovertemplate
    assert "Distinct Orders" in hovertemplate
    assert "Product Line Items" in hovertemplate
    assert "Total Units" in hovertemplate
    assert "Gross Sales" in hovertemplate
    assert "Transit Time" not in hovertemplate

    # Empty check
    assert build_monthly_volume_figure(pd.DataFrame()) is None


def test_aggregate_scenario_lead_times_all_three_scenarios():
    """
    Verifies aggregate_scenario_lead_times aggregates monthly mean lead times
    across Baseline, Stress Test, and Distance Sensitive scenarios (FR-17).
    Confirms Texas shock disruption produces elevated lead times and delay rates.
    """
    artifacts = load_prepared_artifacts()
    filters = {"delay_threshold": 5.0}

    trend_df = aggregate_scenario_lead_times(artifacts, filters)

    assert not trend_df.empty
    scenarios_present = set(trend_df["scenario_key"].unique())
    assert scenarios_present == {"baseline", "stress_test", "distance_sensitive"}

    # Verify required metrics
    req_cols = [
        "year_month", "formatted_month", "scenario_key", "scenario_label",
        "mean_lead_time", "median_lead_time", "delayed_count", "delay_rate_pct", "order_count"
    ]
    for c in req_cols:
        assert c in trend_df.columns, f"Missing scenario metric column: {c}"

    # Stress test must show higher overall mean lead time and delay rate than baseline
    b_mean = trend_df[trend_df["scenario_key"] == "baseline"]["mean_lead_time"].mean()
    s_mean = trend_df[trend_df["scenario_key"] == "stress_test"]["mean_lead_time"].mean()
    b_del = trend_df[trend_df["scenario_key"] == "baseline"]["delay_rate_pct"].mean()
    s_del = trend_df[trend_df["scenario_key"] == "stress_test"]["delay_rate_pct"].mean()

    assert s_mean > b_mean, f"Stress test mean lead time ({s_mean:.2f}) must exceed baseline ({b_mean:.2f})"
    assert s_del > b_del, f"Stress test delay rate ({s_del:.1f}%) must exceed baseline ({b_del:.1f}%)"


def test_aggregate_scenario_lead_times_filtering():
    """Verifies that sidebar filters are respected across all scenario aggregations."""
    artifacts = load_prepared_artifacts()
    target_factory = "Lot's O' Nuts"
    filters = {
        "delay_threshold": 5.0,
        "factories": [target_factory],
    }

    trend_df = aggregate_scenario_lead_times(artifacts, filters)
    assert not trend_df.empty

    unfiltered = aggregate_scenario_lead_times(artifacts, {"delay_threshold": 5.0})
    filt_orders = trend_df[trend_df["scenario_key"] == "baseline"]["order_count"].sum()
    unfilt_orders = unfiltered[unfiltered["scenario_key"] == "baseline"]["order_count"].sum()

    assert filt_orders < unfilt_orders
    assert filt_orders > 0


def test_build_scenario_trend_figure_and_strict_terminology():
    """
    Verifies that build_scenario_trend_figure creates a multi-trace line chart
    with strict 'Order-to-Ship Lead Time' terminology and threshold reference line.
    """
    artifacts = load_prepared_artifacts()
    trend_df = aggregate_scenario_lead_times(artifacts, {"delay_threshold": 5.0})

    fig = build_scenario_trend_figure(trend_df, delay_threshold=5.0)
    assert fig is not None
    assert len(fig.data) == 3  # Baseline, Stress, Distance

    # Strict terminology checks
    y_title = fig.layout.yaxis.title.text
    assert y_title == "Order-to-Ship Lead Time (Days)"
    assert "Transit Time" not in y_title
    assert "Transit Time" not in fig.layout.title.text

    # Reference line check
    shapes = fig.layout.shapes
    assert len(shapes) >= 1
    assert shapes[0].y0 == 5.0
    assert shapes[0].y1 == 5.0

    annotations = fig.layout.annotations
    assert any("Delay Threshold" in a.text for a in annotations)

    # Empty check
    assert build_scenario_trend_figure(pd.DataFrame(), 5.0) is None


def test_compute_res_weight_sensitivity_baseline_identity():
    """
    Verifies that sensitivity analysis at 70/30 (Baseline weights) yields
    identical RES scores, zero rank delta for all routes, and rho = 1.0.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    comp_df, metrics = compute_res_weight_sensitivity(
        df=baseline_df,
        sens_w_speed=0.70,
        sens_w_var=0.30,
        delay_threshold=5.0,
        min_sample=MIN_SAMPLE_SIZE,
    )

    assert not comp_df.empty
    assert (comp_df["sample_size"] >= MIN_SAMPLE_SIZE).all()

    # Scores must be numerically identical
    diff = (comp_df["baseline_res"] - comp_df["sensitivity_res"]).abs()
    assert (diff < 1e-3).all(), "Sensitivity RES at 70/30 must match Baseline RES"

    # All rank deltas must be 0
    assert (comp_df["rank_delta"] == 0).all()

    # Stability indicators
    assert metrics["spearman_rho"] == 1.0
    assert metrics["top10_retention_pct"] == 100.0
    assert metrics["mean_abs_rank_delta"] == 0.0
    assert metrics["max_rank_gain"] == 0
    assert metrics["max_rank_drop"] == 0
    assert metrics["route_count"] == len(comp_df)


def test_compute_res_weight_sensitivity_presets_and_extremes():
    """
    Verifies sensitivity calculations across preset configurations:
    - Balanced (50/50)
    - Speed-Focused (90/10)
    - Speed-Only (100/0)
    - Variability-Only (0/100)
    Ensures safe boundary math without division-by-zero or NaNs.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    presets = [
        (0.50, 0.50),
        (0.90, 0.10),
        (1.00, 0.00),
        (0.00, 1.00),
    ]

    for w_s, w_v in presets:
        comp_df, metrics = compute_res_weight_sensitivity(
            df=baseline_df,
            sens_w_speed=w_s,
            sens_w_var=w_v,
            delay_threshold=5.0,
            min_sample=MIN_SAMPLE_SIZE,
        )

        assert not comp_df.empty
        # Verify score bounds [0, 100]
        assert (comp_df["sensitivity_res"] >= 0.0).all()
        assert (comp_df["sensitivity_res"] <= 100.0).all()

        # Verify rank delta arithmetic: Delta = Baseline Rank - Sensitivity Rank
        expected_delta = comp_df["baseline_rank"] - comp_df["sensitivity_rank"]
        pd.testing.assert_series_equal(comp_df["rank_delta"], expected_delta, check_names=False)

        # Verify stability indicators are valid numbers
        assert -1.0 <= metrics["spearman_rho"] <= 1.0
        assert 0.0 <= metrics["top10_retention_pct"] <= 100.0
        assert metrics["mean_abs_rank_delta"] >= 0.0
        assert not np.isnan(metrics["spearman_rho"])


def test_compute_res_weight_sensitivity_empty():
    """Verifies graceful handling of empty dataframe in sensitivity engine."""
    comp_df, metrics = compute_res_weight_sensitivity(
        df=pd.DataFrame(),
        sens_w_speed=0.50,
        sens_w_var=0.50,
    )
    assert comp_df.empty
    assert metrics["route_count"] == 0
    assert metrics["spearman_rho"] == 1.0
    assert metrics["top10_retention_pct"] == 100.0


def test_audited_csv_exports_provenance_and_metadata():
    """
    Verifies that all three exports (volume trends, scenario trajectories, sensitivity sandbox)
    generate valid CSV bytes with audited provenance headers (FR-14, AD-11).
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    # 1. Volume export
    monthly_df = aggregate_monthly_volume(baseline_df)
    csv_vol = create_export_csv(
        df=monthly_df,
        metadata={
            "layer": "ORIGINAL",
            "scenario": "none",
            "delay_threshold": 5.0,
            "screening": "monthly_volume_trends",
        },
    )
    meta_vol, parsed_vol = parse_export_header(csv_vol.decode("utf-8"))
    assert meta_vol["layer"] == "ORIGINAL"
    assert "5.0" in meta_vol["delay_threshold"]
    assert len(parsed_vol) == len(monthly_df)

    # 2. Scenario export
    scen_df = aggregate_scenario_lead_times(artifacts, {"delay_threshold": 5.0})
    csv_scen = create_export_csv(
        df=scen_df,
        metadata={
            "layer": "SYNTHETIC",
            "scenario": "multi_scenario_comparison",
            "delay_threshold": 5.0,
            "screening": "scenario_lead_time_trends",
        },
    )
    meta_scen, parsed_scen = parse_export_header(csv_scen.decode("utf-8"))
    assert meta_scen["layer"] == "SYNTHETIC"
    assert meta_scen["scenario"] == "multi_scenario_comparison"
    assert "5.0" in meta_scen["delay_threshold"]
    assert len(parsed_scen) == len(scen_df)

    # 3. Sensitivity export
    comp_df, _ = compute_res_weight_sensitivity(baseline_df, 0.50, 0.50)
    csv_sens = create_export_csv(
        df=comp_df,
        metadata={
            "layer": "SYNTHETIC",
            "scenario": "baseline",
            "delay_threshold": 5.0,
            "w_speed_sensitivity": 0.50,
            "w_var_sensitivity": 0.50,
            "screening": "res_weight_sensitivity",
        },
    )
    meta_sens, parsed_sens = parse_export_header(csv_sens.decode("utf-8"))
    assert meta_sens["layer"] == "SYNTHETIC"
    assert meta_sens["scenario"] == "baseline"
    assert "5.0" in meta_sens["delay_threshold"]
    assert len(parsed_sens) == len(comp_df)


# ==============================================================================
# 2. Streamlit UI AppTest Integration Tests
# ==============================================================================

def test_page_8_renders_cleanly_on_baseline():
    """
    Verifies that Page 8 renders cleanly with 0 exceptions on baseline synthetic data,
    displaying volume KPIs, scenario comparison metrics, and sensitivity indicators.
    """
    page_path = BASE_DIR / "pages" / "8_Trends_and_Scenarios.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    assert len(at.exception) == 0, f"Page 8 raised exceptions: {at.exception}"

    metric_map = {m.label: m.value for m in at.metric}

    # Volume Tab KPIs
    assert "Total Filtered Orders" in metric_map
    assert "Monthly Order Average" in metric_map
    assert "Peak Volume Month" in metric_map
    assert "Lowest Volume Month" in metric_map

    # Scenario Tab KPIs
    assert "Baseline Overall Mean Lead Time" in metric_map
    assert "Stress Test Overall Mean Lead Time" in metric_map
    assert "Distance Sensitive Overall Mean" in metric_map

    # Sensitivity Tab Stability Indicators
    assert any("Spearman Rank Correlation" in k for k in metric_map)
    assert "Top 10 Retention Rate" in metric_map
    assert "Mean Absolute Rank Shift" in metric_map
    assert "Max Rank Gain / Drop" in metric_map


def test_strict_terminology_no_transit_time_on_page():
    """
    Verifies strict terminology across all text, metric labels, captions, and disclosures:
    - Never uses 'Transit Time' to describe lead times
    - Contains required FR-17, AD-08, and AD-11 disclaimers
    """
    page_path = BASE_DIR / "pages" / "8_Trends_and_Scenarios.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    for m in at.metric:
        assert "transit time" not in m.label.lower(), f"Forbidden 'Transit Time' found in metric label: {m.label}"

    text_content = " ".join(
        [str(e.value) for e in at.info]
        + [str(e.value) for e in at.caption]
        + [str(e.value) for e in at.markdown]
    )

    assert "order-to-ship lead time" in text_content.lower()
    assert "fr-17" in text_content.lower()
    assert "ad-08" in text_content.lower()
    assert "ad-11" in text_content.lower()
    assert "cogs" in text_content.lower()


def test_sensitivity_presets_and_slider_isolation():
    """
    Verifies that clicking sensitivity presets (e.g. 50/50, 90/10) dynamically updates
    the sensitivity slider and session state, without polluting global sidebar filter state.
    """
    page_path = BASE_DIR / "pages" / "8_Trends_and_Scenarios.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    # Initial slider value is default 0.70
    speed_sliders = [s for s in at.slider if "Speed" in s.label]
    assert len(speed_sliders) == 1
    assert speed_sliders[0].value == 0.70

    # Record baseline global filter state
    initial_layer = at.session_state.get("filter_layer", "SYNTHETIC")
    initial_scenario = at.session_state.get("filter_scenario", "baseline")

    # Click Balanced (50/50) Preset
    btn_50_50 = [b for b in at.button if "50/50" in b.label][0]
    btn_50_50.click().run(timeout=30)

    assert len(at.exception) == 0
    assert at.session_state.get("sens_speed_weight") == 0.50
    speed_sliders_after = [s for s in at.slider if "Speed" in s.label]
    assert speed_sliders_after[0].value == 0.50

    # Verify global filter states remain uncorrupted
    assert at.session_state.get("filter_layer") == initial_layer
    assert at.session_state.get("filter_scenario") == initial_scenario

    # Click Speed-Only (100/0) Preset
    btn_100_0 = [b for b in at.button if "100/0" in b.label][0]
    btn_100_0.click().run(timeout=30)

    assert len(at.exception) == 0
    assert at.session_state.get("sens_speed_weight") == 1.00
    speed_sliders_100 = [s for s in at.slider if "Speed" in s.label]
    assert speed_sliders_100[0].value == 1.00


def test_page_8_handles_derived_layer_gracefully():
    """
    Verifies that Page 8 renders cleanly under DERIVED layer:
    - Tab 1 displays monthly volume seasonality
    - Tabs 2 & 3 display informative warning that SYNTHETIC layer is required
    """
    page_path = BASE_DIR / "pages" / "8_Trends_and_Scenarios.py"
    at = AppTest.from_file(str(page_path))
    at.session_state["filter_layer"] = "DERIVED"
    at.run(timeout=30)

    assert len(at.exception) == 0

    warnings = [str(w.value) for w in at.warning]
    assert any("synthetic" in w.lower() for w in warnings)

    # Volume KPIs should still be present
    metric_map = {m.label: m.value for m in at.metric}
    assert "Total Filtered Orders" in metric_map


def test_page_8_handles_empty_filters_gracefully():
    """
    Verifies that Page 8 displays an early warning when zero orders match active filters.
    """
    page_path = BASE_DIR / "pages" / "8_Trends_and_Scenarios.py"
    at = AppTest.from_file(str(page_path))
    at.session_state["filter_regions"] = ["Interior"]
    at.session_state["filter_states"] = ["California"]
    at.run(timeout=30)

    assert len(at.exception) == 0
    warnings = [str(w.value) for w in at.warning]
    assert any("no orders found" in w.lower() for w in warnings)
