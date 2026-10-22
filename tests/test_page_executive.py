"""
Tests for Page 1: Executive Overview & Margin Analysis.
Verifies compliance with AD-04, AD-11, and Story 4.3 acceptance criteria.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR


def test_page_1_renders_cleanly():
    """
    Verifies that Page 1 (Executive Overview) initializes and renders cleanly
    with zero uncaught exceptions via Streamlit AppTest.
    """
    page_path = BASE_DIR / "pages" / "1_Executive_Overview.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    assert len(at.exception) == 0, f"Page 1 raised exceptions: {at.exception}"

    # Verify metrics presence
    assert len(at.metric) >= 4, "Expected at least 4 metric cards on Page 1"
    metric_labels = [m.label for m in at.metric]

    # Verify commercial KPIs
    assert any("Sales" in l or "Revenue" in l for l in metric_labels)
    assert any("COGS" in l for l in metric_labels)
    assert any("Profit" in l for l in metric_labels)
    assert any("Margin" in l for l in metric_labels)

    # Verify order grain distinction
    assert any("Line Items" in l for l in metric_labels)
    assert any("Order Lines" in l for l in metric_labels)


def test_freight_disclaimer_present():
    """
    Verifies AD-11: Freight cost out-of-scope disclaimer is explicitly rendered.
    """
    page_path = BASE_DIR / "pages" / "1_Executive_Overview.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    text_content = " ".join(
        [str(e.value) for e in at.info]
        + [str(e.value) for e in at.caption]
        + [str(e.value) for e in at.markdown]
    )

    assert "freight" in text_content.lower(), "Expected freight disclaimer on Page 1"
    assert "cogs" in text_content.lower(), "Expected COGS explanation on Page 1"
    assert "AD-11" in text_content or "ad-11" in text_content.lower(), "Expected AD-11 citation"


def test_order_grains_distinction_values():
    """
    Verifies that on clean baseline data, order lines (8,549) and line items (9,881)
    are explicitly computed and shown in metrics.
    """
    page_path = BASE_DIR / "pages" / "1_Executive_Overview.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    metric_values = [m.value for m in at.metric]
    assert any("9,881" in v for v in metric_values), f"Expected 9,881 line items, got {metric_values}"
    assert any("8,549" in v for v in metric_values), f"Expected 8,549 order lines, got {metric_values}"
