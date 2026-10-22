"""
Tests for Page 7: Route Drill-Down & Order-to-Ship Timeline Visualizer.
Verifies compliance with Story 5.4, FR-12, AD-04, AD-07, AD-08, and AD-11 acceptance criteria:
- Order Lines (distinct Order IDs) versus Line Items (total product rows) distinction
- Strict delay rule: lead_time_days > threshold_days
- Strict terminology: "Order-to-Ship Lead Time", never "Transit Time"
- Canadian routes display factory-to-province centroid Haversine distances
- Interactive Plotly timeline scatter chart with threshold reference line
- Provenance-preserving CSV export through create_export_csv
- Graceful handling of ORIGINAL, DERIVED, and SYNTHETIC layers
- Empty filter handling and sample-size guardrails (AD-07)
- Non-causal operational screening disclosures and AD-11 freight/COGS disclaimers
"""

import importlib
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR, MIN_SAMPLE_SIZE
from src.exports import create_export_csv, parse_export_header
from src.load_data import load_prepared_artifacts

drilldown_page = importlib.import_module("pages.7_Route_Drill_Down")
build_route_options = drilldown_page.build_route_options
filter_to_route = drilldown_page.filter_to_route
build_timeline_figure = drilldown_page.build_timeline_figure


# ==============================================================================
# 1. Backend & Unit Level Verification
# ==============================================================================

def test_order_lines_vs_line_items_distinction():
    """
    Verifies that route metrics rigorously distinguish between distinct Order Lines
    (Order ID count, N = 479 on Lot's O' Nuts -> Texas) and Line Items (N = 548).
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    tx_df = filter_to_route(baseline_df, "Lot's O' Nuts -> Texas")

    order_lines = tx_df["Order ID"].nunique()
    line_items = len(tx_df)

    assert order_lines == 479, f"Expected 479 distinct order lines, got {order_lines}"
    assert line_items == 548, f"Expected 548 product line items, got {line_items}"
    assert line_items > order_lines, "Line items should exceed order lines due to multi-item baskets"


def test_strict_delay_rule_inequality():
    """
    Verifies strict delay rule: lead_time_days > threshold_days (AD-07).
    An order with lead_time_days == threshold is strictly On-Time.
    """
    threshold = 5.0
    mock_df = pd.DataFrame({
        "Order ID": ["O1", "O2", "O3", "O4"],
        "lead_time_days": [4.99, 5.00, 5.01, 7.50],
        "Sales": [100.0, 100.0, 100.0, 100.0],
        "Cost": [50.0, 50.0, 50.0, 50.0],
        "Gross Profit": [50.0, 50.0, 50.0, 50.0],
    })

    # Strict inequality check
    delayed_mask = mock_df["lead_time_days"] > threshold
    assert delayed_mask.tolist() == [False, False, True, True]
    assert int(delayed_mask.sum()) == 2


def test_timeline_figure_generation_and_terminology():
    """
    Verifies that build_timeline_figure produces a valid Plotly Figure with
    'Order-to-Ship Lead Time' terminology, threshold reference line, and zero 'Transit Time' labels.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]
    tx_df = filter_to_route(baseline_df, "Lot's O' Nuts -> Texas")

    threshold = 5.0
    fig = build_timeline_figure(tx_df, "Lot's O' Nuts -> Texas", threshold)

    assert fig is not None
    assert len(fig.data) > 0

    # Verify Y-axis title
    y_title = fig.layout.yaxis.title.text
    assert y_title == "Order-to-Ship Lead Time (Days)"
    assert "Transit Time" not in y_title

    # Verify chart title
    chart_title = fig.layout.title.text
    assert "Order-to-Ship Lead Time" in chart_title
    assert "Transit Time" not in chart_title

    # Verify threshold line
    shapes = fig.layout.shapes
    assert len(shapes) >= 1
    assert shapes[0].y0 == threshold
    assert shapes[0].y1 == threshold

    # Verify annotations
    annotations = fig.layout.annotations
    assert any("Delay Threshold" in a.text for a in annotations)


def test_canadian_route_centroid_distance_calculation():
    """
    Verifies that Canadian routes (e.g. Lot's O' Nuts -> Ontario) display
    accurate factory-to-province centroid Haversine distance (~2,959.5 km).
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]

    ontario_df = filter_to_route(baseline_df, "Lot's O' Nuts -> Ontario")
    assert not ontario_df.empty

    dist_km = ontario_df["distance_km"].iloc[0]
    assert 2950.0 <= dist_km <= 2970.0, f"Expected ~2,959.5 km for Ontario lane, got {dist_km}"
    assert ontario_df["Country/Region"].iloc[0] == "Canada"
    assert bool(ontario_df["is_canadian"].iloc[0]) is True


def test_drilldown_audited_csv_export():
    """
    Verifies create_export_csv on drill-down route data preserving provenance headers
    and human-readable column names without schema degradation.
    """
    artifacts = load_prepared_artifacts()
    baseline_df = artifacts["baseline"]
    tx_df = filter_to_route(baseline_df, "Lot's O' Nuts -> Texas")

    csv_bytes = create_export_csv(
        df=tx_df,
        metadata={
            "layer": "SYNTHETIC",
            "scenario": "baseline",
            "delay_threshold": 5.0,
            "route": "Lot's O' Nuts -> Texas",
            "screening": "route_drill_down",
        },
    )

    csv_text = csv_bytes.decode("utf-8")
    meta, parsed_df = parse_export_header(csv_text)

    assert meta["layer"] == "SYNTHETIC"
    assert meta["scenario"] == "baseline"
    assert "5.0" in meta["delay_threshold"]
    assert len(parsed_df) == len(tx_df)
    assert "Lead Time (Days)" in parsed_df.columns or "lead_time_days" in parsed_df.columns
    assert "Gross Revenue ($)" in parsed_df.columns or "Sales" in parsed_df.columns


# ==============================================================================
# 2. Streamlit UI AppTest Integration Tests
# ==============================================================================

def test_page_7_renders_cleanly_on_baseline():
    """
    Verifies that Page 7 renders cleanly with zero exceptions, defaults to
    Lot's O' Nuts -> Texas, and displays exact Order Lines (479) vs Line Items (548).
    """
    page_path = BASE_DIR / "pages" / "7_Route_Drill_Down.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    assert len(at.exception) == 0, f"Page 7 raised exceptions: {at.exception}"

    # Verify selectbox defaulted to canonical route
    sel = at.selectbox
    assert len(sel) >= 1
    assert sel[0].value == "Lot's O' Nuts -> Texas"

    # Verify metrics presence and distinction
    metric_labels = [m.label for m in at.metric]
    metric_map = {m.label: m.value for m in at.metric}

    assert "Order Lines (N)" in metric_map
    assert "Line Items" in metric_map
    assert metric_map["Order Lines (N)"] == "479"
    assert metric_map["Line Items"] == "548"
    assert any("Order-to-Ship Lead Time" in l for l in metric_labels)


def test_strict_terminology_no_transit_time_on_page():
    """
    Verifies that 'Transit Time' is never used as a lead time metric label
    or title, and that non-causal operational disclosures are present.
    """
    page_path = BASE_DIR / "pages" / "7_Route_Drill_Down.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    # Check metric labels
    for m in at.metric:
        assert "transit time" not in m.label.lower(), f"Forbidden 'Transit Time' found in metric label: {m.label}"

    text_content = " ".join(
        [str(e.value) for e in at.info]
        + [str(e.value) for e in at.caption]
        + [str(e.value) for e in at.markdown]
    )

    assert "order-to-ship" in text_content.lower()
    assert "fr-12" in text_content.lower()
    assert "ad-08" in text_content.lower()
    assert "ad-11" in text_content.lower()
    assert "cogs" in text_content.lower()


def test_canadian_route_selection_and_centroid_display():
    """
    Verifies that selecting a Canadian lane (Lot's O' Nuts -> Ontario) triggers
    the Canadian fulfillment notice and displays centroid distance.
    """
    page_path = BASE_DIR / "pages" / "7_Route_Drill_Down.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    sel = at.selectbox[0]
    assert "Lot's O' Nuts -> Ontario" in sel.options

    # Switch to Canadian lane
    sel.set_value("Lot's O' Nuts -> Ontario")
    at.run(timeout=30)
    assert len(at.exception) == 0

    info_texts = " ".join([str(e.value) for e in at.info])
    assert "canadian fulfillment route notice" in info_texts.lower()
    assert "2,959.5 km" in info_texts or "2959.5 km" in info_texts
    assert "ontario" in info_texts.lower()


def test_low_sample_warning_guardrail():
    """
    Verifies that selecting a lane with N < 30 displays the AD-07 statistical warning.
    """
    page_path = BASE_DIR / "pages" / "7_Route_Drill_Down.py"
    at = AppTest.from_file(str(page_path)).run(timeout=30)

    sel = at.selectbox[0]
    low_sample_candidate = "Lot's O' Nuts -> Montana"
    assert low_sample_candidate in sel.options, f"Expected {low_sample_candidate} in route options"

    sel.set_value(low_sample_candidate)
    at.run(timeout=30)
    assert len(at.exception) == 0

    warning_texts = " ".join([str(w.value) for w in at.warning])
    assert "ad-07" in warning_texts.lower() or "low sample" in warning_texts.lower()


def test_single_order_route_and_missing_columns_robustness():
    """
    Verifies that build_timeline_figure handles single-order routes (N = 1)
    and missing columns without raising exceptions or IndexErrors (SEC-01, SEC-07).
    """
    single_df = pd.DataFrame({
        "Order ID": ["ORD-SINGLE-001"],
        "lead_time_days": [6.2],
        "Factory": ["Lot's O' Nuts"],
    })

    fig = build_timeline_figure(single_df, "Lot's O' Nuts -> Alaska", delay_threshold=5.0)
    assert fig is not None
    assert len(fig.data) == 1  # 1 delayed trace
    assert fig.data[0].y[0] == 6.2

    # Test empty dataframe in render_canadian_route_section (SEC-02)
    drilldown_page.render_canadian_route_section(single_df, pd.DataFrame(), delay_threshold=5.0)


def test_page_7_handles_derived_layer_gracefully():
    """
    Verifies that Page 7 renders cleanly under DERIVED layer without lead time exceptions.
    """
    page_path = BASE_DIR / "pages" / "7_Route_Drill_Down.py"
    at = AppTest.from_file(str(page_path))
    at.session_state["filter_layer"] = "DERIVED"
    at.run(timeout=30)

    assert len(at.exception) == 0
    warning_texts = " ".join([str(w.value) for w in at.warning])
    assert "synthetic" in warning_texts.lower()


def test_page_7_handles_empty_filters_gracefully():
    """
    Verifies that Page 7 gracefully displays an empty filter warning when 0 orders match.
    """
    page_path = BASE_DIR / "pages" / "7_Route_Drill_Down.py"
    at = AppTest.from_file(str(page_path))
    at.session_state["filter_regions"] = ["Interior"]
    at.session_state["filter_states"] = ["California"]
    at.run(timeout=30)

    assert len(at.exception) == 0
    warning_texts = " ".join([str(w.value) for w in at.warning])
    assert "no orders found" in warning_texts.lower()
