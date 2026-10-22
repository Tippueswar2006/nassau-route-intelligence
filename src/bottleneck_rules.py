"""
Transparent Quadrant Screening Rules & Bottleneck Recovery Engine.
Screens routes based on 75th percentile volume and delay rates, assigns watchlist status,
and validates multi-seed recovery of injected stress-test bottlenecks.
Pure Python backend decoupled from UI libraries (Zero Streamlit imports).
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    MIN_SAMPLE_SIZE,
    ROBUSTNESS_SEEDS,
)
from src.generate_synthetic import (
    generate_scenario_shipments,
    merge_synthetic_timing,
)
from src.route_analysis import (
    aggregate_routes,
    filter_eligible_routes,
    validate_layer_isolation,
)


DEFAULT_TARGET_BOTTLENECK_ROUTES = [
    "Lot's O' Nuts -> Texas",
    "Wicked Choccy's -> Texas",
]


def flag_bottlenecks(
    df: pd.DataFrame,
    vol_pct: float = 0.75,
    delay_pct: float = 0.75,
    vol_col: str = "sample_size",
    delay_col: str = "delay_rate",
) -> pd.DataFrame:
    """
    Screens routes or states into performance quadrants based on percentile thresholds:
      - Critical Bottleneck: volume >= P75 and delay_rate >= P75
      - Watchlist: volume >= P75 and delay_rate > Median and ~is_bottleneck

    Parameters:
      - df: Route summary DataFrame (eligible comparison set)
      - vol_pct: Percentile for volume threshold (default 0.75)
      - delay_pct: Percentile for delay threshold (default 0.75)
      - vol_col: Column representing volume/order count (default 'sample_size')
      - delay_col: Column representing delay proportion (default 'delay_rate')
    """
    validate_layer_isolation(df)
    df = df.copy()

    # Resolve volume column
    if vol_col not in df.columns:
        if "order_line_count" in df.columns:
            vol_col = "order_line_count"
        elif "order_count" in df.columns:
            vol_col = "order_count"
        elif "line_item_count" in df.columns:
            vol_col = "line_item_count"
        else:
            raise ValueError(f"Volume column '{vol_col}' not found in DataFrame.")

    if delay_col not in df.columns:
        raise ValueError(f"Delay column '{delay_col}' not found in DataFrame.")

    # If df is empty, return empty with expected columns
    if len(df) == 0:
        df["is_bottleneck"] = pd.Series(dtype=bool)
        df["is_watchlist"] = pd.Series(dtype=bool)
        df["quadrant_category"] = pd.Series(dtype=str)
        return df

    # Calculate population thresholds
    p_vol = float(df[vol_col].quantile(vol_pct))
    p_delay = float(df[delay_col].quantile(delay_pct))
    med_delay = float(df[delay_col].median())

    # Screening rules
    is_bottleneck = (df[vol_col] >= p_vol) & (df[delay_col] >= p_delay)
    is_watchlist = (df[vol_col] >= p_vol) & (df[delay_col] > med_delay) & (~is_bottleneck)

    df["is_bottleneck"] = is_bottleneck
    df["is_watchlist"] = is_watchlist
    df["p75_volume_threshold"] = np.round(p_vol, 2)
    df["p75_delay_threshold"] = np.round(p_delay, 4)
    df["median_delay_threshold"] = np.round(med_delay, 4)

    # Assign transparent quadrant categorization
    categories = []
    for _, row in df.iterrows():
        v = row[vol_col]
        d = row[delay_col]
        if v >= p_vol and d >= p_delay:
            categories.append("Critical Bottleneck (High Vol, High Delay)")
        elif v >= p_vol and d > med_delay:
            categories.append("Watchlist (High Vol, Moderate Delay)")
        elif v >= p_vol:
            categories.append("Efficient High Volume (High Vol, Low Delay)")
        elif d >= p_delay:
            categories.append("Secondary Distress (Low Vol, High Delay)")
        else:
            categories.append("Normal / Low Volume (Low Vol, Low Delay)")

    df["quadrant_category"] = categories

    return df


def evaluate_bottleneck_recovery(
    baseline_routes_df: pd.DataFrame,
    stress_routes_df: pd.DataFrame,
    target_routes: Optional[List[str]] = None,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Dict[str, Any]:
    """
    Evaluates whether injected target bottleneck routes are mathematically recovered
    in the Stress-Test scenario compared to Baseline.

    Recovery criteria per PRD Section 11 & AD clarification:
      1. Minimum sample size N >= min_sample (default 30)
      2. Flagged as Critical Bottleneck (Vol >= P75 & Delay >= P75) OR
         Watchlist (Vol >= P75 & Delay > Median) in the Stress-Test scenario
      3. Stress-Test delay rate strictly greater than Baseline delay rate:
         delay_rate_stress > delay_rate_baseline
    """
    if target_routes is None:
        target_routes = DEFAULT_TARGET_BOTTLENECK_ROUTES

    # Filter to eligible routes (N >= min_sample)
    base_el, _ = filter_eligible_routes(baseline_routes_df, min_sample=min_sample)
    stress_el, _ = filter_eligible_routes(stress_routes_df, min_sample=min_sample)

    # Screen bottlenecks on stress eligible routes
    flagged_stress = flag_bottlenecks(stress_el)

    route_results = {}
    all_recovered = True

    for route_key in target_routes:
        base_match = base_el[base_el["route_key"] == route_key]
        stress_match = flagged_stress[flagged_stress["route_key"] == route_key]

        if base_match.empty or stress_match.empty:
            route_results[route_key] = {
                "recovered": False,
                "reason": "Route not found in eligible comparison set",
            }
            all_recovered = False
            continue

        b_row = base_match.iloc[0]
        s_row = stress_match.iloc[0]

        vol = float(s_row["sample_size"])
        b_dr = float(b_row["delay_rate"])
        s_dr = float(s_row["delay_rate"])
        is_bn = bool(s_row["is_bottleneck"])
        is_wl = bool(s_row["is_watchlist"])

        # Criterion 1: Sample size threshold
        has_min_sample = vol >= min_sample

        # Criterion 2: Flagged as bottleneck or watchlist
        is_screened = is_bn or is_wl

        # Criterion 3: Stress delay rate strictly greater than Baseline delay rate
        has_increased_delay = s_dr > b_dr

        recovered = has_min_sample and is_screened and has_increased_delay

        if not recovered:
            all_recovered = False

        route_results[route_key] = {
            "recovered": recovered,
            "sample_size": vol,
            "has_min_sample": has_min_sample,
            "is_bottleneck": is_bn,
            "is_watchlist": is_wl,
            "is_screened": is_screened,
            "baseline_delay_rate": b_dr,
            "stress_delay_rate": s_dr,
            "delay_rate_delta": np.round(s_dr - b_dr, 4),
            "has_increased_delay": has_increased_delay,
            "quadrant_category": s_row["quadrant_category"],
        }

    return {
        "all_recovered": all_recovered,
        "routes": route_results,
        "p75_volume": float(flagged_stress["p75_volume_threshold"].iloc[0]) if len(flagged_stress) > 0 else 0.0,
        "p75_delay": float(flagged_stress["p75_delay_threshold"].iloc[0]) if len(flagged_stress) > 0 else 0.0,
        "median_delay": float(flagged_stress["median_delay_threshold"].iloc[0]) if len(flagged_stress) > 0 else 0.0,
    }


def run_multiseed_recovery_benchmark(
    shipments_df: pd.DataFrame,
    mapped_df: pd.DataFrame,
    seeds: Optional[List[int]] = None,
    target_routes: Optional[List[str]] = None,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Dict[str, Any]:
    """
    Executes the 5-seed bottleneck recovery benchmark across deterministic seeds:
    [42, 101, 202, 303, 404].

    Pass criterion: Injected routes are recovered in at least 4 of 5 seeds (>= 80%).
    """
    if seeds is None:
        seeds = ROBUSTNESS_SEEDS
    if target_routes is None:
        target_routes = DEFAULT_TARGET_BOTTLENECK_ROUTES

    seed_results = {}
    passed_count = 0

    for seed in seeds:
        # Generate scenario timings for baseline and stress test under this seed
        base_shipments = generate_scenario_shipments(shipments_df, scenario="baseline", seed=seed)
        stress_shipments = generate_scenario_shipments(shipments_df, scenario="stress_test", seed=seed)

        base_df = merge_synthetic_timing(mapped_df, base_shipments)
        stress_df = merge_synthetic_timing(mapped_df, stress_shipments)

        # Aggregate routes at state level
        base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)
        stress_agg = aggregate_routes(stress_df, level="state", rollup_small_factories=False)

        eval_result = evaluate_bottleneck_recovery(
            base_agg, stress_agg, target_routes=target_routes, min_sample=min_sample
        )

        seed_results[seed] = eval_result
        if eval_result["all_recovered"]:
            passed_count += 1

    pass_rate = passed_count / len(seeds)
    passed_benchmark = pass_rate >= 0.80  # at least 4 of 5 seeds

    return {
        "passed_benchmark": passed_benchmark,
        "passed_seeds": passed_count,
        "total_seeds": len(seeds),
        "pass_rate": pass_rate,
        "seed_details": seed_results,
    }
