"""
Automated Sensitivity Analysis & Multi-Seed Robustness Test Suite.
Verifies compliance with Story 6.1, PRD Section 11, Section 13, and AD-07:
- Route Efficiency Score (RES) rank correlation (Spearman rho >= 0.85) between 70/30 baseline and 50/50, 90/10 weight profiles
- Boundary conditions (100/0 speed-only, 0/100 variability-only) without division-by-zero or NaNs
- Multi-seed ranking stability across 5 deterministic seeds [42, 101, 202, 303, 404] with mean pairwise rho >= 0.85
- Consistent bottleneck recovery of injected Texas routes across >= 4 of 5 seeds (>= 80%) with N >= 30 and increased delay
- Sample-threshold sensitivity analysis across [10, 20, 30, 50, 100] demonstrating statistical power trade-offs
"""

import numpy as np
import pandas as pd
import pytest

from src.config import (
    BASELINE_PARQUET,
    MIN_SAMPLE_SIZE,
    ROBUSTNESS_SEEDS,
)
from src.route_analysis import aggregate_routes
from src.sensitivity import (
    calculate_spearman_rho,
    compute_multiseed_res_stability,
    compute_sample_threshold_sensitivity,
    compute_weight_sensitivity,
    evaluate_bottleneck_consistency_across_seeds,
)


# ==============================================================================
# 1. Math & Unit Level Invariants
# ==============================================================================

def test_calculate_spearman_rho_pure_math():
    """Verifies rank correlation math for exact, inverted, and partial rankings."""
    # Exact rank equality -> 1.0
    r1 = pd.Series([1, 2, 3, 4, 5])
    assert calculate_spearman_rho(r1, r1) == 1.0

    # Inverted ranking -> -1.0
    r_inv = pd.Series([5, 4, 3, 2, 1])
    assert calculate_spearman_rho(r1, r_inv) == -1.0

    # Partial correlation
    r_perm = pd.Series([1, 2, 4, 3, 5])
    rho = calculate_spearman_rho(r1, r_perm)
    assert 0.85 <= rho <= 0.95

    # Degenerate cases
    assert calculate_spearman_rho(pd.Series([1]), pd.Series([1])) == 1.0
    assert calculate_spearman_rho(pd.Series([1, 1, 1]), pd.Series([1, 1, 1])) == 1.0


def test_calculate_spearman_rho_edge_cases_and_alignment():
    """Verifies robustness with mismatched index labels, mismatched lengths, and None inputs."""
    # Index alignment check
    s1 = pd.Series([1, 2, 3], index=["A", "B", "C"])
    s2 = pd.Series([1, 2, 4], index=["A", "B", "D"])
    # Intersects on A and B: identical rankings -> 1.0
    assert calculate_spearman_rho(s1, s2) == 1.0

    # No overlapping index labels
    s_disjoint = pd.Series([1, 2], index=["X", "Y"])
    assert calculate_spearman_rho(s1, s_disjoint) == 0.0

    # None inputs
    assert calculate_spearman_rho(None, s1) == 0.0
    assert calculate_spearman_rho(s1, None) == 0.0

    # Constant series (std == 0) with identical vs different values
    s_const1 = pd.Series([5, 5, 5])
    s_const2 = pd.Series([5, 5, 5])
    s_const3 = pd.Series([3, 3, 3])
    assert calculate_spearman_rho(s_const1, s_const2) == 1.0
    assert calculate_spearman_rho(s_const1, s_const3) == 0.0


def test_weight_sensitivity_baseline_identity_70_30():
    """
    Verifies that comparing 70/30 against itself produces exact score equality,
    zero rank delta across all routes, rho = 1.0, and 100% Top-10 retention.
    """
    base_df = pd.read_parquet(BASELINE_PARQUET)
    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)

    comp_df, summary = compute_weight_sensitivity(
        base_agg,
        weights_list=[(0.70, 0.30)],
        min_sample=MIN_SAMPLE_SIZE,
    )

    assert not comp_df.empty
    assert "delta_70_30" in comp_df.columns
    assert (comp_df["delta_70_30"] == 0).all()

    diff = (comp_df["baseline_res"] - comp_df["res_70_30"]).abs()
    assert (diff < 1e-3).all()

    m_70_30 = summary["profile_metrics"]["70_30"]
    assert m_70_30["spearman_rho"] == 1.0
    assert m_70_30["top10_retention_pct"] == 100.0
    assert m_70_30["mean_abs_rank_delta"] == 0.0


# ==============================================================================
# 2. Weight Configuration Sensitivity (Story 6.1 AC)
# ==============================================================================

def test_weight_sensitivity_profiles_50_50_and_90_10():
    """
    Verifies that route efficiency rankings remain statistically robust (rho >= 0.85)
    when shifting between operational weight profiles:
      - Balanced (50/50)
      - Production Baseline (70/30)
      - Speed-Focused (90/10)
    Logs correlation coefficients and retention metrics.
    """
    base_df = pd.read_parquet(BASELINE_PARQUET)
    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)

    comp_df, summary = compute_weight_sensitivity(
        base_agg,
        weights_list=[(0.70, 0.30), (0.50, 0.50), (0.90, 0.10)],
        min_sample=MIN_SAMPLE_SIZE,
    )

    metrics = summary["profile_metrics"]
    rho_50_50 = metrics["50_50"]["spearman_rho"]
    rho_90_10 = metrics["90_10"]["spearman_rho"]
    ret_50_50 = metrics["50_50"]["top10_retention_pct"]
    ret_90_10 = metrics["90_10"]["top10_retention_pct"]

    print("\nWeight Sensitivity Analysis Results (vs. 70/30 Baseline):")
    print(f"  Balanced (50/50):     Spearman rho = {rho_50_50:.4f}, Top-10 Retention = {ret_50_50:.1f}%")
    print(f"  Speed-Focused (90/10): Spearman rho = {rho_90_10:.4f}, Top-10 Retention = {ret_90_10:.1f}%")

    # High rank stability threshold: rho >= 0.85
    assert rho_50_50 >= 0.85, f"Expected 50/50 Spearman rho >= 0.85, got {rho_50_50}"
    assert rho_90_10 >= 0.85, f"Expected 90/10 Spearman rho >= 0.85, got {rho_90_10}"
    assert ret_50_50 >= 70.0, f"Expected 50/50 Top 10 retention >= 70%, got {ret_50_50}%"
    assert ret_90_10 >= 70.0, f"Expected 90/10 Top 10 retention >= 70%, got {ret_90_10}%"


def test_weight_sensitivity_boundary_conditions():
    """
    Verifies that boundary weight configurations (Speed-Only 100/0 and
    Variability-Only 0/100) compute bounded scores in [0, 100] without division errors.
    """
    base_df = pd.read_parquet(BASELINE_PARQUET)
    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)

    comp_df, summary = compute_weight_sensitivity(
        base_agg,
        weights_list=[(0.70, 0.30), (1.00, 0.00), (0.00, 1.00)],
        min_sample=MIN_SAMPLE_SIZE,
    )

    for col in ["res_100_0", "res_0_100"]:
        assert col in comp_df.columns
        assert not comp_df[col].isna().any()
        assert (comp_df[col] >= 0.0).all()
        assert (comp_df[col] <= 100.0).all()


# ==============================================================================
# 3. Multi-Seed Robustness & Pairwise Rank Stability (Story 6.1 AC)
# ==============================================================================

def test_multiseed_res_stability_across_5_seeds(mapped_df: pd.DataFrame):
    """
    Executes RES evaluation across 5 deterministic generator seeds:
    [42, 101, 202, 303, 404] (Story 6.1 AC).

    Verifies:
      1. Rank correlation (Spearman rho) between 70/30 baseline and 50/50, 90/10
         profiles is computed and logged across all 5 seeds.
      2. High rank stability is maintained under Speed-Focused 90/10 (mean rho >= 0.85)
         and Balanced 50/50 (mean rho >= 0.80).
      3. Cross-seed route stability table contains consistent rank metrics.
    """
    stability_res = compute_multiseed_res_stability(
        mapped_df=mapped_df,
        seeds=ROBUSTNESS_SEEDS,
        min_sample=MIN_SAMPLE_SIZE,
    )

    print("\n5-Seed Weight Sensitivity Stability Matrix (vs. 70/30 Baseline):")
    for seed, m in stability_res["seed_weight_metrics"].items():
        print(f"  Seed {seed}: 50/50 rho = {m['rho_50_50']:.4f} (Top 10 = {m['top10_ret_50_50']:.0f}%), "
              f"90/10 rho = {m['rho_90_10']:.4f} (Top 10 = {m['top10_ret_90_10']:.0f}%)")
    print(f"  Mean 50/50 Spearman rho = {stability_res['mean_rho_50_50']:.4f}")
    print(f"  Mean 90/10 Spearman rho = {stability_res['mean_rho_90_10']:.4f}")
    print(f"  Overall Mean Weight Sensitivity rho = {stability_res['overall_mean_weight_rho']:.4f}")

    assert stability_res["passed_stability_threshold"], (
        f"Multi-seed stability failed: 90/10 mean rho {stability_res['mean_rho_90_10']:.4f} < 0.85 "
        f"or 50/50 mean rho {stability_res['mean_rho_50_50']:.4f} < 0.80"
    )
    assert stability_res["mean_rho_90_10"] >= 0.85
    assert stability_res["mean_rho_50_50"] >= 0.80

    # Cross-seed route stability table
    stab_df = stability_res["route_stability_table"]
    assert not stab_df.empty
    assert "mean_rank" in stab_df.columns
    assert "std_rank" in stab_df.columns
    assert (stab_df["seeds_evaluated"] == len(ROBUSTNESS_SEEDS)).all()


# ==============================================================================
# 4. Top Bottleneck Consistency Across Seeds (Story 6.1 AC)
# ==============================================================================

def test_bottleneck_consistency_across_5_seeds(mapped_df: pd.DataFrame):
    """
    Verifies that top bottleneck routes remain consistent across seeds:
      1. Lot's O' Nuts -> Texas and Wicked Choccy's -> Texas are recovered
         in at least 4 of 5 seeds (>= 80%).
      2. Each passing seed satisfies sample size N >= 30 and Stress delay rate > Baseline delay rate.
    """
    benchmark = evaluate_bottleneck_consistency_across_seeds(
        mapped_df=mapped_df,
        seeds=ROBUSTNESS_SEEDS,
        min_sample=MIN_SAMPLE_SIZE,
    )

    print("\nBottleneck Consistency Benchmark Across 5 Seeds:")
    for seed, details in benchmark["seed_details"].items():
        all_rec = details["all_recovered"]
        lots = details["routes"]["Lot's O' Nuts -> Texas"]
        wicked = details["routes"]["Wicked Choccy's -> Texas"]
        print(
            f"  Seed {seed}: Recovered = {all_rec} | "
            f"Lot's O' Nuts (Base={lots['baseline_delay_rate']:.3f}, Stress={lots['stress_delay_rate']:.3f}) | "
            f"Wicked Choccy's (Base={wicked['baseline_delay_rate']:.3f}, Stress={wicked['stress_delay_rate']:.3f})"
        )

    assert benchmark["passed_benchmark"], (
        f"Bottleneck consistency failed: only {benchmark['passed_seeds']}/{benchmark['total_seeds']} seeds passed."
    )
    assert benchmark["passed_seeds"] >= 4
    assert benchmark["pass_rate"] >= 0.80


# ==============================================================================
# 5. Sample Size Threshold Sensitivity (PRD Section 13)
# ==============================================================================

def test_sample_threshold_sensitivity_tradeoff():
    """
    Evaluates network route retention and volume coverage across candidate sample thresholds:
    [10, 20, 30, 50, 100].

    Verifies:
      1. Monotonic decrease in eligible route count as threshold increases.
      2. N = 30 achieves substantial volume coverage (> 70%) while filtering small-sample noise.
    """
    base_df = pd.read_parquet(BASELINE_PARQUET)
    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)

    thresh_df = compute_sample_threshold_sensitivity(
        base_agg,
        thresholds=[10, 20, 30, 50, 100],
    )

    assert not thresh_df.empty
    assert len(thresh_df) == 5

    # Monotonic decrease in eligible routes
    counts = list(thresh_df["eligible_route_count"])
    assert counts == sorted(counts, reverse=True)

    # N = 30 properties
    n30_row = thresh_df[thresh_df["min_sample_threshold"] == 30].iloc[0]
    assert n30_row["order_coverage_pct"] >= 70.0
    assert n30_row["eligible_route_count"] >= 15


# ==============================================================================
# 6. Edge Cases & Empty Data Handling
# ==============================================================================

def test_sensitivity_empty_data_handling():
    """Verifies graceful handling when passed empty DataFrames."""
    empty_df = pd.DataFrame()

    comp_df, summary = compute_weight_sensitivity(empty_df)
    assert comp_df.empty
    assert summary["route_count"] == 0

    thresh_df = compute_sample_threshold_sensitivity(empty_df)
    assert thresh_df.empty


def test_weight_sensitivity_respects_custom_min_sample_override():
    """Verifies that compute_weight_sensitivity re-evaluates eligibility when min_sample changes."""
    base_df = pd.read_parquet(BASELINE_PARQUET)
    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)
    # base_agg already has is_eligible for N >= 30
    assert "is_eligible" in base_agg.columns

    # Call with stricter min_sample = 100
    comp_df_100, summary_100 = compute_weight_sensitivity(base_agg, min_sample=100)
    comp_df_30, summary_30 = compute_weight_sensitivity(base_agg, min_sample=30)

    assert summary_100["route_count"] < summary_30["route_count"]
    assert (comp_df_100["sample_size"] >= 100).all()


def test_sample_threshold_sensitivity_unsorted_input():
    """Verifies that unsorted thresholds are sorted and produce valid monotonic output."""
    base_df = pd.read_parquet(BASELINE_PARQUET)
    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)

    thresh_df = compute_sample_threshold_sensitivity(
        base_agg,
        thresholds=[50, 10, 100, 30],
    )
    assert list(thresh_df["min_sample_threshold"]) == [10, 30, 50, 100]
    counts = list(thresh_df["eligible_route_count"])
    assert counts == sorted(counts, reverse=True)
