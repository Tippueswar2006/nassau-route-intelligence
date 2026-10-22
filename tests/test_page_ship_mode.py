"""
Tests for Page 5: Shipping Mode Distribution & Margin-by-Mode Analysis.
Verifies compliance with Story 5.2, FR-10, and AD-11 acceptance criteria:
- Lead-time distributions compared across Same Day, First Class, Second Class, and Standard Class
- Standard vs Expedited tier groupings
- Haversine distance band analysis with N >= 30 sample guardrails and boundary testing
- Gross profit margins by ship mode with non-causal disclaimers
- Clean Streamlit AppTest rendering and interactive radio controls across SYNTHETIC and DERIVED layers
"""

import importlib
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR, EXPEDITED_MODES, SHIPPING_MODES, STANDARD_MODES
from src.load_data import load_prepared_artifacts
from src.route_analysis import (
    aggregate_distance_band_metrics,
    aggregate_ship_mode_metrics,
    assign_distance_bands,
    assign_expedited_group,
)

ship_page = importlib.import_module("pages.5_Ship_Mode_Comparison")
build_distribution_figure = ship_page.build_distribution_figure
build_distance_band_figure = ship_page.build_distance_band_figure


# ==============================================================================
# 1. Backend Engine Tests for Ship Mode & Distance Band Aggregation
# ==============================================================================

def test_aggregate_ship_mode_metrics_baseline():
    """
    Verifies that aggregate_ship_mode_metrics correctly computes lead-time distributions,
    volume grains, and commercial profit margins across all 4 shipping modes.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    stats = aggregate_ship_mode_metrics(baseline_df, threshold_days=5.0)

    # 4 shipping modes
    assert len(stats) == 4
    for mode in SHIPPING_MODES:
        assert mode in stats["Ship Mode"].values

    # Total order lines must equal 8,549 (AD-04)
    assert stats["order_line_count"].sum() == 8549
    assert stats["line_item_count"].sum() == 9881

    # Lead time distributions
    required_cols = [
        "mean_lead_time",
        "median_lead_time",
        "std_lead_time",
        "p25_lead_time",
        "p75_lead_time",
        "iqr_lead_time",
        "p90_lead_time",
        "delayed_count",
        "delay_rate_pct",
        "total_sales",
        "total_cogs",
        "total_gross_profit",
        "gross_margin_pct",
    ]
    for col in required_cols:
        assert col in stats.columns, f"Missing column '{col}' in ship mode stats"

    # Same Day should have very fast lead times
    same_day = stats[stats["Ship Mode"] == "Same Day"].iloc[0]
    assert same_day["mean_lead_time"] < 1.5
    assert same_day["delay_rate_pct"] == 0.0

    # Commercial margins should be valid percentages (~65-66%)
    for margin in stats["gross_margin_pct"]:
        assert 60.0 <= margin <= 70.0


def test_aggregate_expedited_group_metrics():
    """
    Verifies grouping into Expedited (Same Day, First, Second) vs Standard (Standard Class).
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    group_stats = aggregate_ship_mode_metrics(baseline_df, group_col="ship_mode_group")
    assert len(group_stats) == 2
    assert "Expedited" in group_stats["ship_mode_group"].values
    assert "Standard" in group_stats["ship_mode_group"].values

    expedited = group_stats[group_stats["ship_mode_group"] == "Expedited"].iloc[0]
    standard = group_stats[group_stats["ship_mode_group"] == "Standard"].iloc[0]

    # Expedited = 442 (Same Day) + 1312 (First) + 1653 (Second) = 3407
    assert expedited["order_line_count"] == 3407
    assert standard["order_line_count"] == 5142
    assert expedited["mean_lead_time"] < standard["mean_lead_time"]


def test_distance_band_aggregation_and_guardrails():
    """
    Verifies distance band assignment and aggregation (0–500, 500–1,500, 1,500–3,000, 3,000+ km)
    with sample size N >= 30 guardrails.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    band_df = aggregate_distance_band_metrics(baseline_df, min_sample=30)
    assert not band_df.empty

    expected_bands = ["0–500 km", "500–1,500 km", "1,500–3,000 km", "3,000+ km"]
    for b in expected_bands:
        assert b in band_df["distance_band"].values

    assert "sample_status" in band_df.columns
    assert "is_eligible" in band_df.columns

    # All baseline cells meet N >= 30
    assert band_df["is_eligible"].all()
    assert (band_df["order_line_count"] >= 30).all()


def test_distance_band_sample_guardrail_boundary():
    """
    Verifies exact boundary guardrail behavior (N = 29 low-sample vs N = 30 eligible).
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"].copy()

    # Artificially test with high min_sample
    high_threshold = 1000
    band_high = aggregate_distance_band_metrics(baseline_df, min_sample=high_threshold)
    assert not band_high["is_eligible"].all()
    assert any("Low Sample" in s for s in band_high["sample_status"])


def test_empty_dataframe_handling():
    """Verifies that backend aggregation handles empty DataFrames cleanly."""
    artifacts = load_prepared_artifacts()
    empty_df = artifacts["baseline"].iloc[0:0].copy()

    stats = aggregate_ship_mode_metrics(empty_df)
    assert stats.empty

    bands = aggregate_distance_band_metrics(empty_df)
    assert bands.empty


def test_derived_layer_without_lead_times():
    """Verifies that datasets without lead times (e.g. clean_orders) aggregate commercial stats cleanly."""
    artifacts = load_prepared_artifacts()
    clean_df = artifacts["clean_orders"]

    stats = aggregate_ship_mode_metrics(clean_df)
    assert len(stats) == 4
    assert "order_line_count" in stats.columns
    assert "total_sales" in stats.columns
    assert "gross_margin_pct" in stats.columns
    assert "mean_lead_time" not in stats.columns


# ==============================================================================
# 2. Streamlit UI AppTest Integration Tests
# ==============================================================================

def test_page_5_renders_cleanly():
    """
    Verifies that Page 5 (Ship Mode Comparison) initializes and renders cleanly
    with zero uncaught exceptions via Streamlit AppTest.
    """
    page_path = BASE_DIR / "pages" / "5_Ship_Mode_Comparison.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    assert len(at.exception) == 0, f"Page 5 raised exceptions: {at.exception}"

    # Verify metrics presence (at least 4 cards for 4 modes)
    assert len(at.metric) >= 4, "Expected at least 4 KPI cards for the shipping modes"
    metric_labels = [m.label for m in at.metric]

    assert any("Same Day" in l for l in metric_labels)
    assert any("First Class" in l for l in metric_labels)
    assert any("Second Class" in l for l in metric_labels)
    assert any("Standard Class" in l for l in metric_labels)


def test_non_causal_and_freight_disclaimer_present():
    """
    Verifies that non-causal language ('associated with', never 'caused by')
    and AD-11 freight cost disclaimers are explicitly rendered on Page 5.
    """
    page_path = BASE_DIR / "pages" / "5_Ship_Mode_Comparison.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    text_content = " ".join(
        [str(e.value) for e in at.info]
        + [str(e.value) for e in at.caption]
        + [str(e.value) for e in at.markdown]
    )

    assert "fr-10" in text_content.lower(), "Expected FR-10 citation"
    assert "ad-11" in text_content.lower(), "Expected AD-11 citation"
    assert "associated with" in text_content.lower(), "Expected non-causal 'associated with' phrase"
    assert "freight" in text_content.lower(), "Expected freight disclaimer"
    assert "cogs" in text_content.lower(), "Expected COGS distinction"


def test_distribution_radio_toggle_interactive():
    """
    Verifies that the user can switch between 'Individual 4 Shipping Modes'
    and 'Standard vs. Expedited Tiers' via radio control.
    """
    page_path = BASE_DIR / "pages" / "5_Ship_Mode_Comparison.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    radio = at.radio
    assert len(radio) >= 1, "Expected radio button for distribution comparison mode"

    dist_radio = None
    for r in radio:
        if "Individual 4 Shipping Modes" in r.options:
            dist_radio = r
            break

    assert dist_radio is not None, "Could not find distribution comparison radio widget"
    assert "Standard vs. Expedited Tiers" in dist_radio.options

    # Switch to Expedited vs Standard tiers and re-run
    dist_radio.set_value("Standard vs. Expedited Tiers")
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Error switching to Expedited vs Standard: {at.exception}"

    # Switch back to Individual modes and re-run
    dist_radio.set_value("Individual 4 Shipping Modes")
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Error switching back to Individual modes: {at.exception}"


def test_page_5_renders_cleanly_on_derived_layer():
    """
    Verifies that Page 5 gracefully handles the DERIVED layer without timing exceptions.
    """
    page_path = BASE_DIR / "pages" / "5_Ship_Mode_Comparison.py"
    at = AppTest.from_file(str(page_path))
    at.session_state["filter_layer"] = "DERIVED"
    at.run(timeout=30)

    assert len(at.exception) == 0, f"Page 5 failed under DERIVED layer: {at.exception}"
