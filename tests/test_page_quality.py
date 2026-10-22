"""
Tests for Page 2: Data Quality & Method Audit.
Verifies compliance with AD-03, AD-10, AD-12, and Story 4.2 acceptance criteria.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from src.config import BASE_DIR, RECONCILIATION_TARGETS


def test_page_2_renders_cleanly():
    """
    Verifies that Page 2 (Data Quality & Method) initializes and renders cleanly
    with zero uncaught exceptions via Streamlit AppTest.
    """
    page_path = BASE_DIR / "pages" / "2_Data_Quality_and_Method.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    assert len(at.exception) == 0, f"Page 2 raised exceptions: {at.exception}"

    # Verify presence of tables and markdown headers
    assert len(at.table) >= 1, "Expected reconciliation table on Page 2"
    reconciliation_table = at.table[0].value

    # Check that reconciliation table contains 4 metrics
    metrics_in_table = reconciliation_table["Metric"].tolist()
    assert any("Rows" in m for m in metrics_in_table)
    assert any("Units" in m for m in metrics_in_table)
    assert any("Sales" in m for m in metrics_in_table)
    assert any("Profit" in m for m in metrics_in_table)

    # Verify deltas match approved targets
    for _, row in reconciliation_table.iterrows():
        if "Rows" in row["Metric"]:
            assert "-313" in row["Delta (Exclusion)"]
        elif "Units" in row["Metric"]:
            assert "-987" in row["Delta (Exclusion)"]
        elif "Sales" in row["Metric"]:
            assert "-3,499.51" in row["Delta (Exclusion)"]
        elif "Profit" in row["Metric"]:
            assert "-2,366.39" in row["Delta (Exclusion)"]


def test_diagnostic_quarantine_disclaimer_present():
    """
    Verifies AD-03 (Option A): Quarantine policy disclaimer is prominently rendered.
    """
    page_path = BASE_DIR / "pages" / "2_Data_Quality_and_Method.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    # Search for quarantine keywords in error/warning alerts and markdown text
    quarantine_keywords = ["QUARANTINE POLICY", "UNVERIFIED DIAGNOSTIC HYPOTHESIS", "AD-03"]
    text_content = " ".join([str(e.value) for e in at.error] + [str(e.value) for e in at.markdown])

    for kw in quarantine_keywords:
        assert kw in text_content, f"Expected '{kw}' in Page 2 text content"


def test_geographic_and_canadian_scope_disclosure():
    """
    Verifies AD-10: 449 postal codes and 200 Canadian orders disclosure.
    """
    page_path = BASE_DIR / "pages" / "2_Data_Quality_and_Method.py"
    at = AppTest.from_file(str(page_path)).run(timeout=20)

    text_content = " ".join([str(e.value) for e in at.markdown] + [str(e.value) for e in at.info] + [str(e.value) for e in at.success])

    assert "449" in text_content, "Expected 449 US postal codes mention on Page 2"
    assert "200" in text_content, "Expected 200 Canadian orders mention on Page 2"
