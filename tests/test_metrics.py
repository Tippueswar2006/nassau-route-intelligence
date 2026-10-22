"""
Tests for Lead-Time Metrics, Mode-Adjustment, and Route Efficiency Scoring (RES).
Verifies compliance with AD-06, AD-09, and Story 3.1 acceptance criteria.
"""

import pytest
import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
)
from src.metrics import (
    compute_mode_reference_means,
    calculate_mode_adjusted_lead_time,
    apply_delay_threshold,
    compute_route_lead_time_stats,
    calculate_route_efficiency_scores,
)
from src.generate_synthetic import (
    group_into_customer_shipments,
    generate_scenario_shipments,
    merge_synthetic_timing,
)


@pytest.fixture
def sample_shipments_df() -> pd.DataFrame:
    """Creates a controlled test dataframe with known shipping modes and lead times."""
    return pd.DataFrame({
        "Row ID": [1, 2, 3, 4, 5, 6],
        "Order ID": ["ORD-1", "ORD-2", "ORD-3", "ORD-4", "ORD-5", "ORD-6"],
        "route_key": ["F1 -> CA", "F1 -> CA", "F1 -> NY", "F1 -> NY", "F2 -> TX", "F2 -> TX"],
        "Factory": ["F1", "F1", "F1", "F1", "F2", "F2"],
        "State/Province": ["California", "California", "New York", "New York", "Texas", "Texas"],
        "Ship Mode": [
            "Same Day",
            "First Class",
            "Second Class",
            "Standard Class",
            "Standard Class",
            "Standard Class",
        ],
        "lead_time_days": [0.5, 2.5, 3.5, 5.0, 6.0, 7.0],
    })


def test_mode_reference_means_computation(sample_shipments_df: pd.DataFrame):
    """
    Verifies reference mean calculation across ship modes.
    """
    ref_means = compute_mode_reference_means(sample_shipments_df)
    assert isinstance(ref_means, dict)
    assert ref_means["Same Day"] == 0.5
    assert ref_means["First Class"] == 2.5
    assert ref_means["Second Class"] == 3.5
    assert ref_means["Standard Class"] == 6.0  # mean of 5.0, 6.0, 7.0


def test_reference_means_missing_columns():
    """
    Asserts ValueError when required columns are missing.
    """
    bad_df = pd.DataFrame({"some_col": [1, 2]})
    with pytest.raises(ValueError, match="DataFrame must contain"):
        compute_mode_reference_means(bad_df)


def test_mode_adjusted_lead_time_calculation(sample_shipments_df: pd.DataFrame):
    """
    Verifies that Mode-Adjusted Lead Time = Lead Time - mean(Ship Mode).
    """
    ref_means = compute_mode_reference_means(sample_shipments_df)
    adjusted_df = calculate_mode_adjusted_lead_time(sample_shipments_df, ref_means)

    assert "mode_adjusted_lead_time" in adjusted_df.columns
    assert "mode_reference_mean" in adjusted_df.columns

    # Standard Class mean is 6.0. Row 4 (5.0) -> -1.0; Row 5 (6.0) -> 0.0; Row 6 (7.0) -> +1.0
    expected = [0.0, 0.0, 0.0, -1.0, 0.0, 1.0]
    np.testing.assert_allclose(adjusted_df["mode_adjusted_lead_time"], expected, atol=1e-2)


def test_reference_means_invariance(sample_shipments_df: pd.DataFrame):
    """
    Asserts that pre-computed reference means remain invariant even when downstream
    filters select a subset of the data.
    """
    full_ref_means = compute_mode_reference_means(sample_shipments_df)

    # Filter to only Texas (where Standard Class is 6.0 and 7.0, local mean would be 6.5)
    tx_subset = sample_shipments_df[sample_shipments_df["State/Province"] == "Texas"].copy()
    adjusted_tx = calculate_mode_adjusted_lead_time(tx_subset, full_ref_means)

    # Mode adjusted lead time must use global mean (6.0), NOT filtered local mean (6.5)
    # Texas lead times: 6.0 - 6.0 = 0.0, 7.0 - 6.0 = 1.0
    np.testing.assert_allclose(adjusted_tx["mode_adjusted_lead_time"], [0.0, 1.0], atol=1e-2)


def test_strict_delay_boundary():
    """
    Verifies AD-09: Strict Delay Boundary Evaluation.
    lead_time_days > threshold is delayed.
    lead_time_days == threshold is NOT delayed (strictly on-time).
    """
    df = pd.DataFrame({
        "lead_time_days": [4.99, 5.00, 5.0000001, 5.01, 6.0]
    })
    result = apply_delay_threshold(df, threshold_days=5.0)

    assert not result.loc[0, "is_delayed"], "4.99 should NOT be delayed"
    assert not result.loc[1, "is_delayed"], "5.00 should NOT be delayed (strict inequality)"
    assert result.loc[2, "is_delayed"], "5.0000001 should be delayed"
    assert result.loc[3, "is_delayed"], "5.01 should be delayed"
    assert result.loc[4, "is_delayed"], "6.00 should be delayed"


def test_compute_route_lead_time_stats(sample_shipments_df: pd.DataFrame):
    """
    Verifies route-level statistical aggregation including mode-adjusted metrics.
    """
    ref_means = compute_mode_reference_means(sample_shipments_df)
    adjusted_df = calculate_mode_adjusted_lead_time(sample_shipments_df, ref_means)

    stats = compute_route_lead_time_stats(
        adjusted_df, group_col="route_key", threshold_days=5.0
    )

    assert len(stats) == 3  # F1 -> CA, F1 -> NY, F2 -> TX
    assert "mean_lead_time" in stats.columns
    assert "mean_mode_adjusted" in stats.columns
    assert "std_lead_time" in stats.columns
    assert "std_mode_adjusted" in stats.columns
    assert "delay_rate" in stats.columns

    # F2 -> TX: lead times are 6.0 and 7.0. Both > 5.0, so delay_rate = 1.0
    f2_tx = stats[stats["route_key"] == "F2 -> TX"].iloc[0]
    assert f2_tx["sample_size"] == 2
    assert f2_tx["mean_lead_time"] == 6.5
    assert f2_tx["delay_rate"] == 1.0

    # F1 -> CA: lead times 0.5, 2.5. Neither > 5.0, so delay_rate = 0.0
    f1_ca = stats[stats["route_key"] == "F1 -> CA"].iloc[0]
    assert f1_ca["delay_rate"] == 0.0


def test_res_scoring_math():
    """
    Verifies Route Efficiency Score (RES) calculation:
      RES = 100 - (0.70 * Speed_Penalty + 0.30 * Var_Penalty)
      Speed_Only = 100 - Speed_Penalty
    """
    stats_df = pd.DataFrame({
        "route_key": ["Route A", "Route B", "Route C"],
        "mean_mode_adjusted": [-1.0, 0.0, 1.0],  # Min=-1, Max=1 => penalties: 0, 50, 100
        "std_mode_adjusted": [0.5, 1.0, 1.5],   # Min=0.5, Max=1.5 => penalties: 0, 50, 100
    })

    res_df = calculate_route_efficiency_scores(
        stats_df, basis="mode_adjusted", w_speed=0.70, w_var=0.30
    )

    # Route A: Speed_pen = 0, Var_pen = 0 => RES = 100 - 0 = 100
    route_a = res_df[res_df["route_key"] == "Route A"].iloc[0]
    assert route_a["speed_penalty"] == 0.0
    assert route_a["variability_penalty"] == 0.0
    assert route_a["res_score"] == 100.0
    assert route_a["speed_only_score"] == 100.0

    # Route B: Speed_pen = 50, Var_pen = 50 => RES = 100 - (0.7*50 + 0.3*50) = 100 - 50 = 50
    route_b = res_df[res_df["route_key"] == "Route B"].iloc[0]
    assert route_b["speed_penalty"] == 50.0
    assert route_b["variability_penalty"] == 50.0
    assert route_b["res_score"] == 50.0
    assert route_b["speed_only_score"] == 50.0

    # Route C: Speed_pen = 100, Var_pen = 100 => RES = 100 - 100 = 0
    route_c = res_df[res_df["route_key"] == "Route C"].iloc[0]
    assert route_c["speed_penalty"] == 100.0
    assert route_c["variability_penalty"] == 100.0
    assert route_c["res_score"] == 0.0
    assert route_c["speed_only_score"] == 0.0


def test_zero_variance_and_constant_routes():
    """
    Verifies safe handling of constant-value or zero-variance routes:
    - Min == Max produces penalty = 0.0 (no division by zero).
    - Single-route dataframe safely computes RES = 100.0.
    """
    constant_df = pd.DataFrame({
        "route_key": ["Route X", "Route Y"],
        "mean_lead_time": [4.0, 4.0],  # Constant means
        "std_lead_time": [0.0, 0.0],   # Zero variance
    })

    res_df = calculate_route_efficiency_scores(constant_df, basis="raw")
    assert (res_df["speed_penalty"] == 0.0).all()
    assert (res_df["variability_penalty"] == 0.0).all()
    assert (res_df["res_score"] == 100.0).all()

    # Single route
    single_df = pd.DataFrame({
        "route_key": ["Only Route"],
        "mean_lead_time": [5.2],
        "std_lead_time": [1.1],
    })
    single_res = calculate_route_efficiency_scores(single_df, basis="raw")
    assert single_res.iloc[0]["speed_penalty"] == 0.0
    assert single_res.iloc[0]["variability_penalty"] == 0.0
    assert single_res.iloc[0]["res_score"] == 100.0


def test_metrics_on_full_synthetic_baseline(mapped_df: pd.DataFrame):
    """
    Verifies metrics pipeline on actual synthetic baseline data generated from mapped_df:
    - Pre-computed mode reference means
    - Mode-adjusted lead times
    - Route aggregation and RES calculation
    """
    shipments = group_into_customer_shipments(mapped_df)
    synth = generate_scenario_shipments(shipments, scenario="baseline", seed=42)
    merged = merge_synthetic_timing(mapped_df, synth)

    ref_means = compute_mode_reference_means(merged)
    assert len(ref_means) == 4

    adjusted = calculate_mode_adjusted_lead_time(merged, ref_means)
    assert not adjusted["mode_adjusted_lead_time"].isna().any()

    # Mean of mode_adjusted_lead_time across all rows should be approximately 0
    assert abs(adjusted["mode_adjusted_lead_time"].mean()) < 0.05

    route_stats = compute_route_lead_time_stats(adjusted, group_col="route_key")
    scored_routes = calculate_route_efficiency_scores(route_stats, basis="mode_adjusted")

    assert len(scored_routes) > 0
    assert (scored_routes["res_score"] >= 0.0).all()
    assert (scored_routes["res_score"] <= 100.0).all()
    assert (scored_routes["speed_only_score"] >= 0.0).all()
    assert (scored_routes["speed_only_score"] <= 100.0).all()
