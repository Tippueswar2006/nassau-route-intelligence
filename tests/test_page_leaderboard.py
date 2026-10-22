"""
Tests for Page 3: Route Efficiency Leaderboard.
Verifies compliance with AD-06, AD-07, and Story 4.4 acceptance criteria.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR


def test_page_3_renders_cleanly():
    """
    Verifies that Page 3 (Route Efficiency Leaderboard) initializes and renders cleanly
    with zero uncaught exceptions via Streamlit AppTest.
    """
    page_path = BASE_DIR / "pages" / "3_Route_Efficiency.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    assert len(at.exception) == 0, f"Page 3 raised exceptions: {at.exception}"

    # Verify metrics presence
    assert len(at.metric) >= 4, "Expected at least 4 metric cards on Page 3"
    metric_labels = [m.label for m in at.metric]
    assert any("Eligible" in l for l in metric_labels)
    assert any("Low-Sample" in l for l in metric_labels)

    # Verify tabs presence
    assert len(at.tabs) >= 3, "Expected Top 10, Bottom 10, and Full Rankings tabs"

    # Verify dataframes presence
    assert len(at.dataframe) >= 2, "Expected Top 10 and Bottom 10 dataframes on Page 3"


def test_mode_adjusted_vs_raw_toggle_and_rank_delta():
    """
    Verifies radio control for switching between Mode-Adjusted RES and Raw Lead Time RES,
    and checks that rank deltas are computed.
    """
    page_path = BASE_DIR / "pages" / "3_Route_Efficiency.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    # Check radio button for scoring basis
    assert len(at.radio) >= 1, "Expected scoring basis radio button on Page 3"
    radio = at.radio[0]
    assert "Mode-Adjusted" in radio.options[0]
    assert "Raw" in radio.options[1]

    # Verify top 10 table columns
    top_table = at.dataframe[0].value
    assert "Rank Delta (Δ)" in top_table.columns or "Rank Delta" in str(top_table.columns)
    assert "Mode-Adjusted RES" in top_table.columns
    assert "Raw RES" in top_table.columns
    assert "Speed-Only (100/0)" in top_table.columns


def test_low_sample_guardrail_exclusion():
    """
    Verifies AD-07: All routes in Top 10 and Bottom 10 have N >= 30,
    and routes with N < 30 are excluded from leaderboards.
    """
    page_path = BASE_DIR / "pages" / "3_Route_Efficiency.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    # Top 10 dataframe
    top_df = at.dataframe[0].value
    sample_sizes = top_df["Sample (N)"].astype(int)
    assert (sample_sizes >= 30).all(), "Found route with N < 30 in Top 10 leaderboard"

    # Bottom 10 dataframe
    bottom_df = at.dataframe[1].value
    bottom_samples = bottom_df["Sample (N)"].astype(int)
    assert (bottom_samples >= 30).all(), "Found route with N < 30 in Bottom 10 leaderboard"

    # Verify fixed weighting policy notice is displayed
    text_content = " ".join([str(e.value) for e in at.info] + [str(e.value) for e in at.markdown])
    assert "70% Speed / 30% Variability" in text_content, "Expected 70/30 weighting notice"
