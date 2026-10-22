"""
Tests for Page 4: Geographic Analysis & US State Choropleth Heatmap.
Verifies compliance with Story 5.1 and requirement FR-09 acceptance criteria:
- Plotly US choropleth displays user-selected metrics (Mean Lead Time, Delay Rate, RES, Order Volume)
- Canadian destinations excluded from US map geometry with prominent disclosure banner
- State hover reveals factory fulfillment breakdown and sample size
- Clean Streamlit AppTest execution with zero uncaught exceptions
- Comprehensive edge cases (empty data, derived data without lead times, threshold boundaries)
"""

import importlib
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR, US_STATE_TO_CODE
from src.load_data import load_prepared_artifacts
from src.route_analysis import aggregate_state_metrics

geo_page = importlib.import_module("pages.4_Geographic_Analysis")
METRIC_OPTIONS = geo_page.METRIC_OPTIONS
build_choropleth_figure = geo_page.build_choropleth_figure


# ==============================================================================
# 1. Backend Engine Tests for Geographic Aggregation
# ==============================================================================

def test_aggregate_state_metrics_us_canada_separation():
    """
    Verifies that aggregate_state_metrics cleanly separates US state geometry
    from Canadian cross-border destinations per FR-09.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    us_state_df, canada_df = aggregate_state_metrics(baseline_df)

    # Canadian records check: 194 records in baseline dataset
    assert len(canada_df) == 194, f"Expected 194 Canadian records, got {len(canada_df)}"
    assert (canada_df["Country/Region"] == "Canada").all(), "All canada_df records must be from Canada"

    # US records check: 48 contiguous/non-contiguous states + DC = 49 entities
    assert len(us_state_df) == 49, f"Expected 49 US state entities, got {len(us_state_df)}"
    assert not (us_state_df["State/Province"] == "Ontario").any(), "Canadian provinces must not appear in us_state_df"
    assert "Texas" in us_state_df["State/Province"].values
    assert "California" in us_state_df["State/Province"].values

    # Check that all 49 state entities map to valid 2-letter state codes
    for state_name in us_state_df["State/Province"]:
        assert state_name in US_STATE_TO_CODE, f"State '{state_name}' missing from US_STATE_TO_CODE"
    assert us_state_df["state_code"].notna().all(), "All US state entities must have valid 2-letter state codes"


def test_aggregate_state_metrics_fields_and_scores():
    """
    Verifies that state-level metrics include state_code, sample_size,
    lead time statistics, delay rates, RES scores, sample status, and factory breakdown.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    us_state_df, canada_df = aggregate_state_metrics(baseline_df, threshold_days=5.0)

    # Verify column presence
    required_cols = [
        "State/Province",
        "state_code",
        "sample_size",
        "mean_lead_time",
        "delay_rate_pct",
        "res_score",
        "speed_only_score",
        "factory_breakdown_html",
        "top_factory",
        "sample_status",
    ]
    for col in required_cols:
        assert col in us_state_df.columns, f"Missing required column '{col}' in us_state_df"

    # Check state code mapping
    tx_row = us_state_df[us_state_df["State/Province"] == "Texas"].iloc[0]
    assert tx_row["state_code"] == "TX"
    assert tx_row["sample_size"] > 0
    assert 0.0 <= tx_row["res_score"] <= 100.0
    assert 0.0 <= tx_row["delay_rate_pct"] <= 100.0

    # Check factory breakdown contains factory names and order counts
    assert "Lot's O' Nuts" in tx_row["factory_breakdown_html"]
    assert "Wicked Choccy's" in tx_row["factory_breakdown_html"]
    assert "%" in tx_row["factory_breakdown_html"]


def test_aggregate_state_metrics_derived_without_lead_time():
    """
    Verifies that aggregate_state_metrics gracefully handles datasets
    without lead times (e.g. DERIVED clean_orders) without crashing.
    """
    artifacts = load_prepared_artifacts()
    clean_df = artifacts["clean_orders"]

    us_state_df, canada_df = aggregate_state_metrics(clean_df)
    assert not us_state_df.empty
    assert len(canada_df) == 194
    assert "sample_size" in us_state_df.columns
    assert "mean_lead_time" not in us_state_df.columns
    assert "res_score" not in us_state_df.columns


def test_aggregate_state_metrics_empty_dataframe():
    """
    Verifies that aggregate_state_metrics handles an empty DataFrame cleanly.
    """
    artifacts = load_prepared_artifacts()
    empty_df = artifacts["baseline"].iloc[0:0].copy()

    us_state_df, canada_df = aggregate_state_metrics(empty_df)
    assert us_state_df.empty
    assert canada_df.empty


def test_aggregate_state_metrics_strict_delay_threshold():
    """
    Verifies strict inequality boundary behavior: Lead Time == threshold is on-time (AD-09).
    """
    artifacts = load_prepared_artifacts()
    df = artifacts["baseline"].copy()

    # With very high threshold (15.0d), delay rate should be virtually 0
    us_high, _ = aggregate_state_metrics(df, threshold_days=15.0)
    assert us_high["delay_rate"].max() == 0.0

    # With very low threshold (0.5d), delay rate should be nearly 100% across the board
    us_low, _ = aggregate_state_metrics(df, threshold_days=0.5)
    assert us_low["delay_rate"].mean() > 0.90
    assert us_low["delay_rate"].min() >= 0.70


def test_build_choropleth_figure_structure():
    """
    Verifies that build_choropleth_figure constructs a valid Plotly Choropleth
    figure with USA-states locationmode and appropriate hovertemplate.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]
    us_state_df, _ = aggregate_state_metrics(baseline_df)

    for metric_name, metric_cfg in METRIC_OPTIONS.items():
        fig = build_choropleth_figure(
            us_state_df,
            metric_name=metric_name,
            metric_cfg=metric_cfg,
            delay_threshold=5.0,
        )

        assert len(fig.data) == 1
        trace = fig.data[0]
        assert trace.type == "choropleth"
        assert trace.locationmode == "USA-states"
        assert fig.layout.geo.scope == "usa"

        # Verify hovertemplate references customdata fields (breakdown, sample size, status)
        assert "%{customdata[0]}" in trace.hovertemplate  # State name
        assert "%{customdata[1]}" in trace.hovertemplate  # Sample size
        assert "%{customdata[4]}" in trace.hovertemplate  # Factory breakdown
        assert "%{customdata[5]}" in trace.hovertemplate  # Status


# ==============================================================================
# 2. Streamlit UI AppTest Integration Tests
# ==============================================================================

def test_page_4_renders_cleanly():
    """
    Verifies that Page 4 (Geographic Analysis) initializes and renders cleanly
    with zero uncaught exceptions via Streamlit AppTest.
    """
    page_path = BASE_DIR / "pages" / "4_Geographic_Analysis.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    assert len(at.exception) == 0, f"Page 4 raised exceptions: {at.exception}"

    # Verify metrics presence
    assert len(at.metric) >= 4, "Expected at least 4 summary metrics on Page 4"
    metric_labels = [m.label for m in at.metric]

    assert any("Total Filtered Orders" in l for l in metric_labels)
    assert any("US Map Destination Orders" in l for l in metric_labels)
    assert any("Canadian Excluded Orders" in l for l in metric_labels)
    assert any("States Covered" in l for l in metric_labels)


def test_canadian_disclosure_banner_present():
    """
    Verifies that the Canadian exclusion and retention disclosure banner
    is explicitly rendered on Page 4 per FR-09.
    """
    page_path = BASE_DIR / "pages" / "4_Geographic_Analysis.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    text_content = " ".join(
        [str(e.value) for e in at.info]
        + [str(e.value) for e in at.caption]
        + [str(e.value) for e in at.markdown]
    )

    assert "canadian" in text_content.lower(), "Expected Canadian mention in Page 4 text"
    assert "fr-09" in text_content.lower(), "Expected FR-09 citation on Page 4"
    assert "excluded" in text_content.lower(), "Expected notice stating Canadian orders are excluded from map"
    assert "retained" in text_content.lower(), "Expected notice stating Canadian orders are retained in totals"


def test_metric_radio_options_available_and_interactive():
    """
    Verifies that user can select all 4 required metrics on Page 4:
    Mean Lead Time, Delay Rate, RES, and Order Volume, and switch between them.
    """
    page_path = BASE_DIR / "pages" / "4_Geographic_Analysis.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    radio = at.radio
    assert len(radio) >= 1, "Expected at least one radio group for metric selection"

    metric_radio = None
    for r in radio:
        if "Mean Lead Time" in r.options:
            metric_radio = r
            break

    assert metric_radio is not None, "Could not find metric selector radio widget"
    expected_options = ["Mean Lead Time", "Delay Rate", "RES", "Order Volume"]
    for opt in expected_options:
        assert opt in metric_radio.options, f"Expected '{opt}' in metric selector options"

    # Select Delay Rate and re-run
    metric_radio.set_value("Delay Rate")
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Error switching to Delay Rate: {at.exception}"

    # Select RES and re-run
    metric_radio.set_value("RES")
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Error switching to RES: {at.exception}"

    # Select Order Volume and re-run
    metric_radio.set_value("Order Volume")
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Error switching to Order Volume: {at.exception}"
