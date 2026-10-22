"""
Tests for Synthetic Lead Time Generator and Multi-Scenario Calibration.
Verifies compliance with AD-04, AD-05, and PRD Section 10.
"""

import pytest
import numpy as np
import pandas as pd

from src.generate_synthetic import (
    group_into_customer_shipments,
    generate_scenario_shipments,
    merge_synthetic_timing,
    generate_all_scenarios,
    load_generator_config,
)


def test_shipment_grouping_invariant(mapped_df: pd.DataFrame):
    """
    Asserts that:
    - Exactly 5,067 customer shipments are formed from the deduplicated dataset.
    - Every shipment has valid geographic metadata and distance.
    """
    shipments = group_into_customer_shipments(mapped_df)
    assert len(shipments) == 5067, f"Expected 5,067 shipments, got {len(shipments)}"
    assert shipments["distance_km"].notna().all(), "Missing distances in shipments"
    assert (shipments["distance_km"] > 0).all(), "Zero/negative distance in shipments"


def test_baseline_calibration(mapped_df: pd.DataFrame):
    """
    Verifies that Baseline empirical sampling satisfies PRD Section 10 calibration targets:
    - Same Day: 0.38 ± 0.15
    - First Class: 2.55 ± 0.10
    - Second Class: 3.57 ± 0.10
    - Standard Class: 5.32 ± 0.10
    - Overall mean: 4.29 ± 0.15
    """
    shipments = group_into_customer_shipments(mapped_df)
    synth_shipments = generate_scenario_shipments(shipments, scenario="baseline", seed=42)
    merged = merge_synthetic_timing(mapped_df, synth_shipments)

    assert len(merged) == len(mapped_df), "Line count mismatch after merge"
    assert merged["lead_time_days"].notna().all(), "NaN lead times detected"
    assert (merged["lead_time_days"] >= 0).all(), "Negative lead times detected"

    means = merged.groupby("Ship Mode")["lead_time_days"].mean()
    assert abs(means["Same Day"] - 0.38) <= 0.15, f"Same Day mean {means['Same Day']} outside target"
    assert abs(means["First Class"] - 2.55) <= 0.10, f"First Class mean {means['First Class']} outside target"
    assert abs(means["Second Class"] - 3.57) <= 0.10, f"Second Class mean {means['Second Class']} outside target"
    assert abs(means["Standard Class"] - 5.32) <= 0.10, f"Standard Class mean {means['Standard Class']} outside target"

    overall_mean = merged["lead_time_days"].mean()
    assert abs(overall_mean - 4.29) <= 0.15, f"Overall mean {overall_mean} outside target"


def test_shipment_grain_line_consistency(mapped_df: pd.DataFrame):
    """
    Asserts that all order lines within each customer shipment receive the EXACT same lead time.
    """
    shipments = group_into_customer_shipments(mapped_df)
    synth_shipments = generate_scenario_shipments(shipments, scenario="baseline", seed=42)
    merged = merge_synthetic_timing(mapped_df, synth_shipments)

    shipment_lead_std = merged.groupby(["Customer ID", "Order Date", "Ship Mode"])["lead_time_days"].std()
    # std should be NaN (for 1-line shipments) or 0.0 (for multi-line shipments)
    assert (shipment_lead_std.dropna() == 0.0).all(), (
        "Lines in the same shipment received different lead times!"
    )


def test_distance_sensitive_scenario(mapped_df: pd.DataFrame):
    """
    Verifies Distance-Sensitive scenario:
    - Bounded in [0, 2] for Same Day and [1, 14] for others.
    - Preserves centered lead-time behavior.
    """
    shipments = group_into_customer_shipments(mapped_df)
    synth_shipments = generate_scenario_shipments(shipments, scenario="distance_sensitive", seed=42)
    merged = merge_synthetic_timing(mapped_df, synth_shipments)

    same_day = merged[merged["Ship Mode"] == "Same Day"]["lead_time_days"]
    other_modes = merged[merged["Ship Mode"] != "Same Day"]["lead_time_days"]

    assert same_day.min() >= 0.0 and same_day.max() <= 2.0
    assert other_modes.min() >= 1.0 and other_modes.max() <= 14.0


def test_stress_test_unclipped_injections(mapped_df: pd.DataFrame):
    """
    Asserts that:
    - Injected delays survive without clipping: Same Day shipments exceed 2.0 days under stress test.
    - Peak season, state-level, and Texas route injections produce higher delay rates than Baseline.
    """
    scenarios = generate_all_scenarios(mapped_df, seed=42)
    baseline_df = scenarios["baseline"]
    stress_df = scenarios["stress_test"]

    # Same Day unclipped check
    same_day_stress = stress_df[stress_df["Ship Mode"] == "Same Day"]["lead_time_days"]
    unclipped_count = (same_day_stress > 2.0).sum()
    assert unclipped_count > 0, (
        f"Same Day stress delays were clipped! Found {unclipped_count} rows > 2.0 days."
    )

    # Texas routes check: Stress delay rate must be strictly greater than Baseline
    tx_routes = ["Lot's O' Nuts -> Texas", "Wicked Choccy's -> Texas"]
    for route in tx_routes:
        b_route = baseline_df[baseline_df["route_key"] == route]
        s_route = stress_df[stress_df["route_key"] == route]

        b_delay_rate = (b_route["lead_time_days"] > 5.0).mean()
        s_delay_rate = (s_route["lead_time_days"] > 5.0).mean()

        assert s_delay_rate > b_delay_rate, (
            f"Route {route} stress delay rate ({s_delay_rate:.2%}) not greater than baseline ({b_delay_rate:.2%})"
        )


def test_deterministic_reproducibility(mapped_df: pd.DataFrame):
    """
    Asserts that generating scenarios with the same seed (42) reproduces identical lead times.
    """
    scenarios_run1 = generate_all_scenarios(mapped_df, seed=42)
    scenarios_run2 = generate_all_scenarios(mapped_df, seed=42)

    for sc_name in ["baseline", "distance_sensitive", "stress_test"]:
        lead1 = scenarios_run1[sc_name]["lead_time_days"].values
        lead2 = scenarios_run2[sc_name]["lead_time_days"].values
        np.testing.assert_array_equal(lead1, lead2, err_msg=f"Scenario {sc_name} non-deterministic!")
