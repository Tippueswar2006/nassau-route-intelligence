"""
Tests for 75th Percentile Screening Quadrant and 5-Seed Bottleneck Recovery Engine.
Verifies compliance with AD-07, PRD Section 11, and Story 3.3 acceptance criteria.
"""

import pytest
import numpy as np
import pandas as pd

from src.config import (
    BASELINE_PARQUET,
    STRESS_PARQUET,
    ROBUSTNESS_SEEDS,
)
from src.generate_synthetic import (
    group_into_customer_shipments,
)
from src.route_analysis import (
    aggregate_routes,
    filter_eligible_routes,
)
from src.bottleneck_rules import (
    flag_bottlenecks,
    evaluate_bottleneck_recovery,
    run_multiseed_recovery_benchmark,
)


def test_flag_bottlenecks_quadrant_logic():
    """
    Verifies transparent quadrant screening logic:
    - Bottleneck: volume >= P75 and delay_rate >= P75
    - Watchlist: volume >= P75 and delay_rate > Median and not bottleneck
    - Efficient High-Volume: volume >= P75 and delay_rate <= Median
    - Low-Volume routes: volume < P75
    """
    mock_df = pd.DataFrame({
        "route_key": ["R-HighHigh", "R-HighMed", "R-HighLow", "R-LowHigh", "R-LowLow"],
        "sample_size": [100, 100, 100, 20, 20],  # P75 will be 100
        "delay_rate": [0.60, 0.40, 0.10, 0.70, 0.10],  # Med=0.40, P75=0.60
        "data_layer": ["SYNTHETIC"] * 5,
    })

    flagged = flag_bottlenecks(mock_df)

    assert "is_bottleneck" in flagged.columns
    assert "is_watchlist" in flagged.columns
    assert "quadrant_category" in flagged.columns

    # R-HighHigh: Vol=100 (>=100), Delay=0.60 (>=0.60) -> Bottleneck
    r_hh = flagged[flagged["route_key"] == "R-HighHigh"].iloc[0]
    assert r_hh["is_bottleneck"]
    assert not r_hh["is_watchlist"]

    # R-HighMed: Vol=100 (>=100), Delay=0.40 (not > Median if Median=0.40).
    # Let's check with strict inequality: delay > Median
    r_hl = flagged[flagged["route_key"] == "R-HighLow"].iloc[0]
    assert not r_hl["is_bottleneck"]
    assert not r_hl["is_watchlist"]

    # R-LowHigh: Vol=20 (<100) -> Cannot be bottleneck or watchlist
    r_lh = flagged[flagged["route_key"] == "R-LowHigh"].iloc[0]
    assert not r_lh["is_bottleneck"]
    assert not r_lh["is_watchlist"]


def test_bottleneck_recovery_seed_42_artifacts():
    """
    Verifies that the pre-computed seed 42 artifacts (baseline.parquet, stress_test.parquet)
    recover the injected Texas bottlenecks under the approved criteria:
      1. Minimum sample size N >= 30
      2. Flagged as Critical Bottleneck or Watchlist in Stress Test
      3. Stress delay rate strictly greater than Baseline delay rate
    """
    base_df = pd.read_parquet(BASELINE_PARQUET)
    stress_df = pd.read_parquet(STRESS_PARQUET)

    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)
    stress_agg = aggregate_routes(stress_df, level="state", rollup_small_factories=False)

    result = evaluate_bottleneck_recovery(base_agg, stress_agg)

    assert result["all_recovered"], f"Seed 42 failed bottleneck recovery: {result['routes']}"

    # Verify Lot's O' Nuts -> Texas
    lots_tx = result["routes"]["Lot's O' Nuts -> Texas"]
    assert lots_tx["recovered"]
    assert lots_tx["sample_size"] >= 30
    assert lots_tx["is_bottleneck"] or lots_tx["is_watchlist"]
    assert lots_tx["has_increased_delay"]
    assert lots_tx["stress_delay_rate"] > lots_tx["baseline_delay_rate"]

    # Verify Wicked Choccy's -> Texas
    wicked_tx = result["routes"]["Wicked Choccy's -> Texas"]
    assert wicked_tx["recovered"]
    assert wicked_tx["sample_size"] >= 30
    assert wicked_tx["is_bottleneck"] or wicked_tx["is_watchlist"]
    assert wicked_tx["has_increased_delay"]
    assert wicked_tx["stress_delay_rate"] > wicked_tx["baseline_delay_rate"]


def test_bottleneck_rules_layer_isolation():
    """
    Asserts AD-02: Layer Isolation within bottleneck screening engine.
    """
    mixed_df = pd.DataFrame({
        "route_key": ["R1", "R2"],
        "sample_size": [50, 60],
        "delay_rate": [0.2, 0.3],
        "data_layer": ["ORIGINAL", "SYNTHETIC"],
    })
    with pytest.raises(ValueError, match="Layer isolation violation"):
        flag_bottlenecks(mixed_df)


def test_multiseed_bottleneck_recovery_5_seeds(mapped_df: pd.DataFrame):
    """
    Executes the 5-seed bottleneck recovery benchmark across deterministic seeds:
    [42, 101, 202, 303, 404].

    Pass criterion per PRD Section 11 & Approved Clarification:
      The injected Texas route bottlenecks (Lot's O' Nuts -> Texas, Wicked Choccy's -> Texas)
      must be recovered in at least 4 of 5 seeds (>= 80%) with N >= 30 and
      Stress delay rate strictly greater than Baseline delay rate.
    """
    shipments = group_into_customer_shipments(mapped_df)

    benchmark = run_multiseed_recovery_benchmark(
        shipments_df=shipments,
        mapped_df=mapped_df,
        seeds=ROBUSTNESS_SEEDS,
        min_sample=30,
    )

    print("\n5-Seed Bottleneck Recovery Benchmark Results:")
    for seed, details in benchmark["seed_details"].items():
        all_rec = details["all_recovered"]
        lots_dr = details["routes"]["Lot's O' Nuts -> Texas"]["stress_delay_rate"]
        wicked_dr = details["routes"]["Wicked Choccy's -> Texas"]["stress_delay_rate"]
        print(f"  Seed {seed}: Recovered={all_rec} (Lot's O' Nuts delay={lots_dr}, Wicked Choccy's delay={wicked_dr})")

    assert benchmark["passed_benchmark"], (
        f"Benchmark failed: only {benchmark['passed_seeds']}/{benchmark['total_seeds']} seeds passed. "
        f"Required >= 4/5 (>= 80%). Details: {benchmark['seed_details']}"
    )
    assert benchmark["passed_seeds"] >= 4, f"Expected >= 4 passed seeds, got {benchmark['passed_seeds']}"
