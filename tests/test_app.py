"""
Tests for Streamlit Application Shell, Global Filter State, and Caching Engine.
Verifies compliance with AD-02, AD-06, AD-08, and Story 4.1 acceptance criteria.
"""

from pathlib import Path
import time
import pytest
import pandas as pd
from streamlit.testing.v1 import AppTest

from app import (
    get_cached_artifacts,
    get_cached_metadata,
    get_active_dataset,
    render_layer_banner,
)
from src.config import (
    BASE_DIR,
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
)


def test_app_test_initialization():
    """
    Verifies that the Streamlit application shell initializes and renders cleanly
    without uncaught exceptions using Streamlit AppTest.
    """
    app_path = BASE_DIR / "app.py"
    at = AppTest.from_file(str(app_path)).run(timeout=20)
    assert len(at.exception) == 0, f"AppTest raised exceptions: {at.exception}"

    # Verify sidebar widgets
    assert len(at.sidebar.selectbox) >= 1, "Expected layer selectbox in sidebar"
    assert len(at.sidebar.slider) >= 1, "Expected delay threshold slider in sidebar"
    assert len(at.sidebar.checkbox) >= 1, "Expected duplicate toggle checkbox in sidebar"


def test_cached_artifact_loader():
    """
    Verifies that get_cached_artifacts loads prepared Parquet artifacts into memory.
    """
    artifacts = get_cached_artifacts()
    assert isinstance(artifacts, dict)
    for expected_key in ["clean_orders", "route_aggregates", "baseline", "distance_sensitive", "stress_test"]:
        assert expected_key in artifacts, f"Missing key in cached artifacts: {expected_key}"
        assert isinstance(artifacts[expected_key], pd.DataFrame)
        assert len(artifacts[expected_key]) > 0

    metadata = get_cached_metadata()
    assert isinstance(metadata, dict)
    assert "artifact_checksums" in metadata


def test_filter_pipeline_speed_under_one_second():
    """
    Verifies that get_active_dataset executes responsive filtering in under 1 second.
    """
    filters = {
        "layer": "SYNTHETIC",
        "scenario": "baseline",
        "factories": ["Lot's O' Nuts"],
        "regions": ["Pacific"],
        "states": ["California"],
        "ship_modes": ["Standard Class"],
        "delay_threshold": 5.0,
        "exclude_duplicates": True,
        "weight_speed": DEFAULT_RES_WEIGHT_SPEED,
        "weight_var": DEFAULT_RES_WEIGHT_VARIABILITY,
    }

    t0 = time.time()
    filtered_df, ref_means = get_active_dataset(filters)
    elapsed = time.time() - t0

    assert elapsed < 1.0, f"Filtering took {elapsed:.3f}s (must be < 1.0s)"
    assert len(filtered_df) > 0
    assert (filtered_df["Factory"] == "Lot's O' Nuts").all()
    assert (filtered_df["Region"] == "Pacific").all()
    assert (filtered_df["State/Province"] == "California").all()
    assert (filtered_df["Ship Mode"] == "Standard Class").all()
    assert not filtered_df["is_duplicate"].any()
    assert "is_delayed" in filtered_df.columns
    assert "mode_adjusted_lead_time" in filtered_df.columns


def test_reference_means_precomputed_invariance():
    """
    Verifies AD-06: Pre-computed reference means are derived from the full scenario
    dataset before user filters, and remain invariant regardless of downstream filter selections.
    """
    # 1. Full dataset reference means
    filters_all = {
        "layer": "SYNTHETIC",
        "scenario": "baseline",
        "factories": [],
        "regions": [],
        "states": [],
        "ship_modes": [],
        "delay_threshold": 5.0,
        "exclude_duplicates": True,
    }
    _, ref_means_all = get_active_dataset(filters_all)

    # 2. Filtered subset reference means (e.g., only Texas orders)
    filters_tx = {
        "layer": "SYNTHETIC",
        "scenario": "baseline",
        "factories": [],
        "regions": [],
        "states": ["Texas"],
        "ship_modes": [],
        "delay_threshold": 5.0,
        "exclude_duplicates": True,
    }
    _, ref_means_tx = get_active_dataset(filters_tx)

    # Both must match exactly (invariant to downstream user filter)
    assert ref_means_all == ref_means_tx
    for mode in ["Same Day", "First Class", "Second Class", "Standard Class"]:
        assert mode in ref_means_all
        assert abs(ref_means_all[mode] - ref_means_tx[mode]) < 1e-6


def test_duplicate_toggle_filter():
    """
    Verifies that the duplicate toggle properly switches between 9,881 and 10,194 records
    when evaluating original data.
    """
    filters_dedup = {
        "layer": "ORIGINAL",
        "scenario": "baseline",
        "factories": [],
        "regions": [],
        "states": [],
        "ship_modes": [],
        "delay_threshold": 5.0,
        "exclude_duplicates": True,
    }
    df_dedup, _ = get_active_dataset(filters_dedup)
    assert len(df_dedup) == 9881

    filters_with_dup = {
        "layer": "ORIGINAL",
        "scenario": "baseline",
        "factories": [],
        "regions": [],
        "states": [],
        "ship_modes": [],
        "delay_threshold": 5.0,
        "exclude_duplicates": False,
    }
    df_with_dup, _ = get_active_dataset(filters_with_dup)
    assert len(df_with_dup) == 10194
