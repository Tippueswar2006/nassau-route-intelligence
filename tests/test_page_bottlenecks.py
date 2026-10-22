"""
Tests for Page 6: Potential Bottlenecks & Quadrant Screening.
Verifies compliance with Story 5.3, FR-11, AD-07, AD-08, and AD-11 acceptance criteria:
- Screening fulfillment routes into performance quadrants based on 75th percentile volume and delay rates
- Upper-right quadrant routes flagged as Critical Bottlenecks with sample size N and volume metrics
- High-volume routes with delay rate above median but below P75 flagged as Watchlist
- Sample size guardrails (N >= 30) enforced before screening
- Interactive Plotly quadrant visualizer with P75 reference lines and median delay line
- Dual analysis levels: Factory -> State routes vs Destination States overall
- Non-causal operational screening disclosures and AD-11 freight/COGS disclaimers
- Audited CSV export generation across tabs
- Clean Streamlit AppTest rendering and interactive radio controls
"""

import importlib
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.bottleneck_rules import evaluate_bottleneck_recovery, flag_bottlenecks
from src.config import BASE_DIR, MIN_SAMPLE_SIZE
from src.exports import create_export_csv, parse_export_header
from src.load_data import load_prepared_artifacts
from src.route_analysis import (
    aggregate_routes,
    aggregate_state_metrics,
    filter_eligible_routes,
)

bottlenecks_page = importlib.import_module("pages.6_Potential_Bottlenecks")
build_quadrant_scatter_figure = bottlenecks_page.build_quadrant_scatter_figure


# ==============================================================================
# 1. Backend Screening & Quadrant Classification Tests
# ==============================================================================

def test_flag_bottlenecks_baseline_classification():
    """
    Verifies that flag_bottlenecks computes P75 volume and delay thresholds,
    identifies Critical Bottlenecks and Watchlist routes, and assigns quadrant categories.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    raw_agg = aggregate_routes(baseline_df, level="state", min_sample=MIN_SAMPLE_SIZE)
    eligible_df, low_sample_df = filter_eligible_routes(raw_agg, min_sample=MIN_SAMPLE_SIZE)

    # 59 eligible routes in baseline
    assert len(eligible_df) >= 50
    assert (eligible_df["sample_size"] >= MIN_SAMPLE_SIZE).all()

    flagged = flag_bottlenecks(eligible_df)

    # Check required columns
    expected_cols = [
        "is_bottleneck",
        "is_watchlist",
        "p75_volume_threshold",
        "p75_delay_threshold",
        "median_delay_threshold",
        "quadrant_category",
    ]
    for col in expected_cols:
        assert col in flagged.columns, f"Missing required column '{col}'"

    # Threshold checks
    p_vol = flagged["p75_volume_threshold"].iloc[0]
    p_delay = flagged["p75_delay_threshold"].iloc[0]
    med_delay = flagged["median_delay_threshold"].iloc[0]

    assert p_vol > 0
    assert 0.0 <= med_delay <= p_delay <= 1.0

    # In baseline, there are 3 Critical Bottlenecks and 3 Watchlist routes
    critical = flagged[flagged["is_bottleneck"]]
    watchlist = flagged[flagged["is_watchlist"]]

    assert len(critical) == 3
    assert len(watchlist) == 3

    # Critical routes must satisfy Volume >= P75 AND Delay >= P75
    for _, r in critical.iterrows():
        assert r["sample_size"] >= p_vol
        assert r["delay_rate"] >= p_delay
        assert r["quadrant_category"] == "Critical Bottleneck (High Vol, High Delay)"

    # Watchlist routes must satisfy Volume >= P75 AND Delay > Median AND Delay < P75
    for _, r in watchlist.iterrows():
        assert r["sample_size"] >= p_vol
        assert r["delay_rate"] > med_delay
        assert r["delay_rate"] < p_delay
        assert r["quadrant_category"] == "Watchlist (High Vol, Moderate Delay)"


def test_stress_test_bottleneck_recovery():
    """
    Verifies that stress test synthetic data injected routes are recovered
    as Critical Bottlenecks in the upper-right quadrant (PRD Section 12).
    """
    artifacts = load_prepared_artifacts()
    base_df = artifacts["baseline"]
    stress_df = artifacts["stress_test"]

    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)
    stress_agg = aggregate_routes(stress_df, level="state", rollup_small_factories=False)

    recovery_results = evaluate_bottleneck_recovery(base_agg, stress_agg)
    assert recovery_results["all_recovered"] is True

    # Check that both routes are classified as Critical Bottlenecks
    lots_tx = recovery_results["routes"]["Lot's O' Nuts -> Texas"]
    assert lots_tx["recovered"] is True
    assert lots_tx["is_bottleneck"] is True
    assert lots_tx["stress_delay_rate"] > 0.70

    wicked_tx = recovery_results["routes"]["Wicked Choccy's -> Texas"]
    assert wicked_tx["recovered"] is True
    assert wicked_tx["is_bottleneck"] is True
    assert wicked_tx["stress_delay_rate"] > 0.70


def test_state_level_aggregation_and_screening():
    """
    Verifies that Destination State overall aggregation level computes valid
    metrics and screens bottlenecks at the state grain.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    state_agg, _ = aggregate_state_metrics(baseline_df, threshold_days=5.0, min_sample=MIN_SAMPLE_SIZE)
    eligible_states, low_sample_states = filter_eligible_routes(state_agg, min_sample=MIN_SAMPLE_SIZE)

    assert not eligible_states.empty
    assert (eligible_states["sample_size"] >= MIN_SAMPLE_SIZE).all()

    flagged_states = flag_bottlenecks(eligible_states)
    assert "quadrant_category" in flagged_states.columns
    assert "is_bottleneck" in flagged_states.columns
    assert "is_watchlist" in flagged_states.columns

    # Threshold checks for state level
    assert flagged_states["p75_volume_threshold"].iloc[0] > 0
    assert 0.0 <= flagged_states["median_delay_threshold"].iloc[0] <= flagged_states["p75_delay_threshold"].iloc[0] <= 1.0
    assert flagged_states["is_bottleneck"].dtype == bool
    assert flagged_states["is_watchlist"].dtype == bool


def test_sample_size_guardrail_enforcement():
    """
    Verifies that filter_eligible_routes strictly segregates routes with N < 30.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    # All routes without sample size pre-filtering
    raw_agg = aggregate_routes(baseline_df, level="state", min_sample=1)
    eligible, low_sample = filter_eligible_routes(raw_agg, min_sample=MIN_SAMPLE_SIZE)

    assert (eligible["sample_size"] >= 30).all()
    assert (low_sample["sample_size"] < 30).all()
    assert len(eligible) + len(low_sample) == len(raw_agg)


# ==============================================================================
# 2. Plotly Visualizer Figure Generation Tests
# ==============================================================================

def test_build_quadrant_scatter_figure():
    """
    Verifies that build_quadrant_scatter_figure produces a valid Plotly Figure
    with scatter traces, P75 reference lines, median line, and formatted annotations.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    raw_agg = aggregate_routes(baseline_df, level="state", min_sample=MIN_SAMPLE_SIZE)
    eligible_df, _ = filter_eligible_routes(raw_agg, min_sample=MIN_SAMPLE_SIZE)
    flagged = flag_bottlenecks(eligible_df)

    p_vol = float(flagged["p75_volume_threshold"].iloc[0])
    p_delay_pct = float(flagged["p75_delay_threshold"].iloc[0]) * 100.0
    med_delay_pct = float(flagged["median_delay_threshold"].iloc[0]) * 100.0

    fig = build_quadrant_scatter_figure(
        flagged,
        vol_threshold=p_vol,
        delay_threshold_pct=p_delay_pct,
        med_delay_pct=med_delay_pct,
        level_label="Route",
    )

    # Validate figure structure
    assert fig is not None
    assert len(fig.data) > 0  # At least one scatter trace

    # Check shapes/lines (1 vline, 2 hlines)
    shapes = fig.layout.shapes
    assert len(shapes) == 3, f"Expected 3 reference lines (P75 vol, P75 delay, median delay), found {len(shapes)}"

    # Check annotations on reference lines
    annotations = fig.layout.annotations
    annotation_texts = [a.text for a in annotations]
    assert any("P75 Vol" in t for t in annotation_texts)
    assert any("P75 Delay" in t for t in annotation_texts)
    assert any("Median Delay" in t for t in annotation_texts)

    # Check that Critical Bottleneck trace uses diamond symbol for visual distinctness
    crit_trace = next(
        (t for t in fig.data if "Critical Bottleneck" in t.name),
        None,
    )
    assert crit_trace is not None
    assert crit_trace.marker.symbol == "diamond"
    assert crit_trace.marker.size >= 14


# ==============================================================================
# 3. Streamlit UI AppTest Integration Tests
# ==============================================================================

def test_page_6_renders_cleanly():
    """
    Verifies that Page 6 (Potential Bottlenecks) initializes and renders cleanly
    with zero uncaught exceptions via Streamlit AppTest.
    """
    page_path = BASE_DIR / "pages" / "6_Potential_Bottlenecks.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    assert len(at.exception) == 0, f"Page 6 raised exceptions: {at.exception}"

    # Verify summary KPI metrics are rendered
    assert len(at.metric) >= 5, "Expected 5 summary KPI cards"
    metric_labels = [m.label for m in at.metric]

    assert any("Evaluated" in l for l in metric_labels)
    assert any("Critical Bottlenecks" in l for l in metric_labels)
    assert any("Watchlist Lanes" in l for l in metric_labels)
    assert any("P75 Volume" in l for l in metric_labels)
    assert any("P75 Delay" in l for l in metric_labels)

    # Verify critical bottleneck count in baseline is 3
    crit_metric = next(m for m in at.metric if "Critical Bottlenecks" in m.label)
    assert crit_metric.value == "3"

    # Verify watchlist metric in baseline is 3
    watch_metric = next(m for m in at.metric if "Watchlist Lanes" in m.label)
    assert watch_metric.value == "3"


def test_non_causal_screening_and_margin_disclaimer_present():
    """
    Verifies that operational screening disclosures (FR-11, AD-08) and
    AD-11 margin disclaimers are explicitly displayed on Page 6.
    """
    page_path = BASE_DIR / "pages" / "6_Potential_Bottlenecks.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    text_content = " ".join(
        [str(e.value) for e in at.info]
        + [str(e.value) for e in at.caption]
        + [str(e.value) for e in at.markdown]
    )

    assert "fr-11" in text_content.lower(), "Expected FR-11 citation"
    assert "ad-08" in text_content.lower(), "Expected AD-08 citation"
    assert "screening" in text_content.lower(), "Expected screening disclosure"
    assert "diagnostic" in text_content.lower(), "Expected diagnostic classification note"
    assert "ad-11" in text_content.lower(), "Expected AD-11 margin disclaimer citation"
    assert "freight" in text_content.lower(), "Expected freight disclosure"


def test_analysis_level_radio_toggle_interactive():
    """
    Verifies that toggling the radio button between 'Factory → State Routes'
    and 'Destination States Overall' switches aggregation grain cleanly.
    """
    page_path = BASE_DIR / "pages" / "6_Potential_Bottlenecks.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    radio = at.radio
    assert len(radio) >= 1, "Expected radio button for analysis level"

    level_radio = None
    for r in radio:
        if "Factory → State Routes (Default)" in r.options:
            level_radio = r
            break

    assert level_radio is not None, "Could not find screening aggregation dimension radio widget"
    assert "Destination States Overall" in level_radio.options

    # Switch to Destination States Overall and re-run
    level_radio.set_value("Destination States Overall")
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Error switching to Destination States: {at.exception}"

    # Verify metric label updated to reflect State grain
    state_metric_labels = [m.label for m in at.metric]
    assert any("Evaluated States" in l for l in state_metric_labels)

    # Switch back to Route level and re-run
    level_radio.set_value("Factory → State Routes (Default)")
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Error switching back to Route level: {at.exception}"


def test_page_6_handles_derived_layer_gracefully():
    """
    Verifies that Page 6 displays the synthetic requirement warning and
    does not throw uncaught exceptions when DERIVED layer is selected.
    """
    page_path = BASE_DIR / "pages" / "6_Potential_Bottlenecks.py"
    at = AppTest.from_file(str(page_path))
    at.session_state["filter_layer"] = "DERIVED"
    at.run(timeout=30)

    assert len(at.exception) == 0, f"Page 6 failed under DERIVED layer: {at.exception}"

    warning_text = " ".join([str(w.value) for w in at.warning])
    assert "synthetic" in warning_text.lower(), "Expected synthetic layer warning when lead times missing"


def test_page_6_handles_empty_filters_gracefully():
    """
    Verifies that Page 6 gracefully displays a warning message when active filters yield 0 rows.
    """
    page_path = BASE_DIR / "pages" / "6_Potential_Bottlenecks.py"
    at = AppTest.from_file(str(page_path))
    # Region Interior and State California do not overlap -> yields 0 matching orders
    at.session_state["filter_regions"] = ["Interior"]
    at.session_state["filter_states"] = ["California"]
    at.run(timeout=30)

    assert len(at.exception) == 0, f"Page 6 failed on empty filters: {at.exception}"
    warning_text = " ".join([str(w.value) for w in at.warning])
    assert "no orders found" in warning_text.lower(), "Expected empty filter warning"


def test_bottleneck_csv_export_format():
    """
    Verifies that create_export_csv generates valid audited CSV exports
    with provenance metadata and standardized human column headers for
    bottleneck screening and low-sample inspection tables.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    raw_agg = aggregate_routes(baseline_df, level="state", min_sample=1)
    eligible_df, low_sample_df = filter_eligible_routes(raw_agg, min_sample=MIN_SAMPLE_SIZE)
    flagged = flag_bottlenecks(eligible_df)
    critical_df = flagged[flagged["is_bottleneck"]]

    # 1. Critical Bottleneck Export Verification
    csv_bytes = create_export_csv(
        critical_df,
        metadata={
            "layer": "SYNTHETIC",
            "scenario": "baseline",
            "delay_threshold": 5.0,
            "screening": "route_critical_bottlenecks",
        },
    )

    csv_text = csv_bytes.decode("utf-8")
    meta, parsed_df = parse_export_header(csv_text)

    assert meta["layer"] == "SYNTHETIC"
    assert meta["scenario"] == "baseline"
    assert "5.0" in meta["delay_threshold"]
    assert "Route Key" in parsed_df.columns
    assert "Sample Size (N)" in parsed_df.columns
    assert "Delay Rate" in parsed_df.columns
    assert len(parsed_df) == len(critical_df)

    # 2. Low Sample Export Verification
    csv_low_bytes = create_export_csv(
        low_sample_df,
        metadata={
            "layer": "SYNTHETIC",
            "scenario": "baseline",
            "delay_threshold": 5.0,
            "screening": "route_low_sample_ineligible",
        },
    )
    meta_low, parsed_low_df = parse_export_header(csv_low_bytes)
    assert meta_low["layer"] == "SYNTHETIC"
    assert "Route Key" in parsed_low_df.columns
    assert len(parsed_low_df) == len(low_sample_df)

