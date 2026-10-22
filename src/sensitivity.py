"""
Sensitivity Analysis & Multi-Seed Robustness Engine for Nassau Route Intelligence.
Evaluates Route Efficiency Score (RES) stability across alternative scoring weights
(70/30 baseline vs. 50/50, 90/10, 100/0, 0/100), multi-seed ranking robustness
across deterministic seeds [42, 101, 202, 303, 404], bottleneck recovery consistency,
and sample size threshold trade-offs (PRD Section 11 & Section 13, Story 6.1).
Pure Python backend strictly decoupled from UI libraries (Zero Streamlit imports).
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
    ROBUSTNESS_SEEDS,
)
from src.generate_synthetic import (
    generate_scenario_shipments,
    group_into_customer_shipments,
    merge_synthetic_timing,
)
from src.metrics import calculate_route_efficiency_scores
from src.route_analysis import (
    aggregate_routes,
    filter_eligible_routes,
)
from src.bottleneck_rules import (
    DEFAULT_TARGET_BOTTLENECK_ROUTES,
    evaluate_bottleneck_recovery,
    run_multiseed_recovery_benchmark,
)


def calculate_spearman_rho(rank1: Union[pd.Series, List, np.ndarray], rank2: Union[pd.Series, List, np.ndarray]) -> float:
    """
    Computes Spearman rank correlation coefficient between two rank series
    as Pearson correlation of the ranks, avoiding scipy dependency.
    Handles index mismatches, unequal lengths, and zero-variance series gracefully.
    Returns float in [-1.0, 1.0], or 1.0 if identical / zero variance.
    """
    if rank1 is None or rank2 is None:
        return 0.0

    s1 = pd.Series(rank1).dropna()
    s2 = pd.Series(rank2).dropna()

    if len(s1) <= 1 or len(s2) <= 1:
        if len(s1) == len(s2) and len(s1) > 0 and (s1.values == s2.values).all():
            return 1.0
        return 0.0

    # Align series: prioritize index intersection if custom index is present
    common_idx = s1.index.intersection(s2.index)
    has_custom_index = not (isinstance(s1.index, pd.RangeIndex) and isinstance(s2.index, pd.RangeIndex))

    if has_custom_index and len(common_idx) > 1:
        aligned = pd.concat([s1.loc[common_idx].rename("r1"), s2.loc[common_idx].rename("r2")], axis=1).dropna()
    elif s1.index.equals(s2.index):
        aligned = pd.concat([s1.rename("r1"), s2.rename("r2")], axis=1, join="inner").dropna()
    elif len(s1) == len(s2):
        aligned = pd.DataFrame({"r1": s1.values, "r2": s2.values}).dropna()
    else:
        if len(common_idx) > 1:
            aligned = pd.concat([s1.loc[common_idx].rename("r1"), s2.loc[common_idx].rename("r2")], axis=1).dropna()
        else:
            return 0.0

    if len(aligned) <= 1:
        return 0.0

    r1 = aligned["r1"]
    r2 = aligned["r2"]
    std1 = float(r1.std())
    std2 = float(r2.std())
    if std1 == 0.0 or std2 == 0.0 or np.isnan(std1) or np.isnan(std2):
        return 1.0 if (r1.values == r2.values).all() else 0.0

    rho = float(r1.corr(r2))
    if np.isnan(rho):
        return 1.0 if (r1.values == r2.values).all() else 0.0
    return float(np.round(np.clip(rho, -1.0, 1.0), 4))


# ──────────────────────────────────────────────────────────────────────────────
# 1. Weight Profile Sensitivity Analysis
# ──────────────────────────────────────────────────────────────────────────────

def compute_weight_sensitivity(
    routes_df: pd.DataFrame,
    weights_list: Optional[List[Tuple[float, float]]] = None,
    min_sample: int = MIN_SAMPLE_SIZE,
    basis: str = "mode_adjusted",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluates Route Efficiency Scores (RES) and ranking shifts across different
    Speed vs. Variability weight combinations against the baseline (70/30).

    Default profiles evaluated:
      - Baseline: (0.70, 0.30)
      - Balanced: (0.50, 0.50)
      - Speed-Focused: (0.90, 0.10)

    Returns:
      (comparison_df, summary_metrics)
    """
    if routes_df.empty:
        return pd.DataFrame(), {
            "profile_metrics": {},
            "route_count": 0,
        }

    if weights_list is None:
        weights_list = [
            (DEFAULT_RES_WEIGHT_SPEED, DEFAULT_RES_WEIGHT_VARIABILITY),
            (0.50, 0.50),
            (0.90, 0.10),
        ]

    # Filter to eligible routes
    sample_cols = ["sample_size", "order_line_count", "order_count"]
    if any(col in routes_df.columns for col in sample_cols):
        eligible_df, _ = filter_eligible_routes(routes_df, min_sample=min_sample)
    elif "is_eligible" in routes_df.columns:
        eligible_df = routes_df[routes_df["is_eligible"]].copy()
    else:
        eligible_df = routes_df.copy()

    if eligible_df.empty:
        return pd.DataFrame(), {
            "profile_metrics": {},
            "route_count": 0,
        }

    # 1. Baseline RES (70/30)
    base_w_speed, base_w_var = weights_list[0]
    base_scored = calculate_route_efficiency_scores(
        eligible_df,
        basis=basis,
        w_speed=base_w_speed,
        w_var=base_w_var,
    )
    base_scored["baseline_res"] = base_scored["res_score"]
    base_scored["baseline_rank"] = base_scored["baseline_res"].rank(ascending=False, method="min").astype(int)

    comparison = pd.DataFrame({
        "route_key": base_scored["route_key"],
        "sample_size": base_scored["sample_size"],
        "mean_lead_time": base_scored["mean_lead_time"] if "mean_lead_time" in base_scored.columns else 0.0,
        "std_lead_time": base_scored["std_lead_time"] if "std_lead_time" in base_scored.columns else 0.0,
        "baseline_res": base_scored["baseline_res"],
        "baseline_rank": base_scored["baseline_rank"],
    })

    top10_base = set(comparison.sort_values(by=["baseline_rank", "route_key"]).head(10)["route_key"])
    profile_metrics = {}

    # 2. Evaluate alternative configurations
    for w_s, w_v in weights_list:
        label = f"{int(w_s*100)}_{int(w_v*100)}"
        score_col = f"res_{label}"
        rank_col = f"rank_{label}"
        delta_col = f"delta_{label}"

        scored = calculate_route_efficiency_scores(
            eligible_df,
            basis=basis,
            w_speed=w_s,
            w_var=w_v,
        )
        scored[score_col] = scored["res_score"]
        scored[rank_col] = scored[score_col].rank(ascending=False, method="min").astype(int)

        comparison[score_col] = scored[score_col]
        comparison[rank_col] = scored[rank_col]
        comparison[delta_col] = comparison["baseline_rank"] - comparison[rank_col]

        # Calculate rank correlation and Top 10 retention
        rho = calculate_spearman_rho(comparison["baseline_rank"], comparison[rank_col])
        top10_alt = set(comparison.sort_values(by=[rank_col, "route_key"]).head(10)["route_key"])
        retention_count = len(top10_base.intersection(top10_alt))
        top10_retention = (retention_count / min(10, len(comparison)) * 100.0) if len(comparison) > 0 else 100.0

        profile_metrics[label] = {
            "w_speed": w_s,
            "w_var": w_v,
            "spearman_rho": float(rho),
            "top10_retention_pct": float(np.round(top10_retention, 1)),
            "mean_abs_rank_delta": float(np.round(comparison[delta_col].abs().mean(), 2)),
            "max_rank_gain": int(comparison[delta_col].max()) if not comparison.empty else 0,
            "max_rank_drop": int(comparison[delta_col].min()) if not comparison.empty else 0,
        }

    summary = {
        "profile_metrics": profile_metrics,
        "route_count": len(comparison),
    }

    return comparison, summary


# ──────────────────────────────────────────────────────────────────────────────
# 2. Multi-Seed Robustness Analysis
# ──────────────────────────────────────────────────────────────────────────────

def compute_multiseed_res_stability(
    mapped_df: pd.DataFrame,
    seeds: Optional[List[int]] = None,
    min_sample: int = MIN_SAMPLE_SIZE,
    w_speed: float = DEFAULT_RES_WEIGHT_SPEED,
    w_var: float = DEFAULT_RES_WEIGHT_VARIABILITY,
) -> Dict[str, Any]:
    """
    Evaluates RES ranking stability across 5 deterministic seeds:
    [42, 101, 202, 303, 404] (PRD Section 11 & Section 13, Story 6.1).

    Computes:
      1. Weight profile rank correlation (Spearman rho) between 70/30 baseline
         and 50/50, 90/10 profiles across all seeds (Story 6.1 AC).
      2. Pairwise cross-seed rank correlations and route rank variance.
    """
    if seeds is None:
        seeds = ROBUSTNESS_SEEDS

    shipments = group_into_customer_shipments(mapped_df)
    seed_rankings: Dict[int, pd.DataFrame] = {}
    seed_weight_metrics: Dict[int, Dict[str, float]] = {}

    for seed in seeds:
        synth_shipments = generate_scenario_shipments(shipments, scenario="baseline", seed=seed)
        seed_df = merge_synthetic_timing(mapped_df, synth_shipments)
        agg_df = aggregate_routes(seed_df, level="state", rollup_small_factories=False)
        el_df, _ = filter_eligible_routes(agg_df, min_sample=min_sample)

        # 1. Weight sensitivity for this seed
        _, weight_summary = compute_weight_sensitivity(
            el_df,
            weights_list=[(w_speed, w_var), (0.50, 0.50), (0.90, 0.10)],
            min_sample=min_sample,
        )
        p_metrics = weight_summary["profile_metrics"]
        seed_weight_metrics[seed] = {
            "rho_50_50": p_metrics["50_50"]["spearman_rho"],
            "rho_90_10": p_metrics["90_10"]["spearman_rho"],
            "top10_ret_50_50": p_metrics["50_50"]["top10_retention_pct"],
            "top10_ret_90_10": p_metrics["90_10"]["top10_retention_pct"],
        }

        # 2. Store baseline ranking for cross-seed comparison
        scored = calculate_route_efficiency_scores(
            el_df,
            basis="mode_adjusted",
            w_speed=w_speed,
            w_var=w_var,
        )
        scored["rank"] = scored["res_score"].rank(ascending=False, method="min").astype(int)
        seed_rankings[seed] = scored[["route_key", "sample_size", "res_score", "rank"]].copy()

    # Aggregate cross-seed weight correlations
    rhos_50 = [m["rho_50_50"] for m in seed_weight_metrics.values()]
    rhos_90 = [m["rho_90_10"] for m in seed_weight_metrics.values()]
    mean_rho_50 = float(np.round(np.mean(rhos_50), 4))
    mean_rho_90 = float(np.round(np.mean(rhos_90), 4))
    overall_mean_weight_rho = float(np.round(np.mean(rhos_50 + rhos_90), 4))

    # Calculate pairwise Spearman correlations across all distinct pairs (s_i, s_j) for i < j
    pairwise_corrs = {}
    rho_values = []

    for i in range(len(seeds)):
        for j in range(i + 1, len(seeds)):
            s1 = seeds[i]
            s2 = seeds[j]
            pair_key = f"{s1}_vs_{s2}"

            df1 = seed_rankings[s1]
            df2 = seed_rankings[s2]

            # Merge on common eligible routes
            merged = df1.merge(df2, on="route_key", suffixes=(f"_{s1}", f"_{s2}"))
            if len(merged) > 1:
                rho = calculate_spearman_rho(merged[f"rank_{s1}"], merged[f"rank_{s2}"])
            else:
                rho = 1.0

            pairwise_corrs[pair_key] = rho
            rho_values.append(rho)

    mean_pairwise_rho = float(np.round(np.mean(rho_values), 4)) if rho_values else 1.0
    min_pairwise_rho = float(np.round(np.min(rho_values), 4)) if rho_values else 1.0
    max_pairwise_rho = float(np.round(np.max(rho_values), 4)) if rho_values else 1.0

    # Build cross-seed route rank summary table
    route_keys = sorted(list(set.union(*[set(df["route_key"]) for df in seed_rankings.values()])))
    route_rows = []

    for r_key in route_keys:
        ranks = []
        res_scores = []
        for s in seeds:
            sub = seed_rankings[s][seed_rankings[s]["route_key"] == r_key]
            if not sub.empty:
                ranks.append(sub["rank"].iloc[0])
                res_scores.append(sub["res_score"].iloc[0])

        if ranks:
            route_rows.append({
                "route_key": r_key,
                "mean_res": float(np.round(np.mean(res_scores), 2)),
                "std_res": float(np.round(np.std(res_scores), 2)),
                "mean_rank": float(np.round(np.mean(ranks), 2)),
                "std_rank": float(np.round(np.std(ranks), 2)),
                "min_rank": int(np.min(ranks)),
                "max_rank": int(np.max(ranks)),
                "seeds_evaluated": len(ranks),
            })

    route_stability_df = pd.DataFrame(route_rows).sort_values(by="mean_rank").reset_index(drop=True)

    passed_weight_stability = (mean_rho_90 >= 0.85) and (mean_rho_50 >= 0.80)

    return {
        "passed_stability_threshold": passed_weight_stability,
        "seed_weight_metrics": seed_weight_metrics,
        "mean_rho_50_50": mean_rho_50,
        "mean_rho_90_10": mean_rho_90,
        "overall_mean_weight_rho": overall_mean_weight_rho,
        "mean_pairwise_rho": mean_pairwise_rho,
        "min_pairwise_rho": min_pairwise_rho,
        "max_pairwise_rho": max_pairwise_rho,
        "pairwise_correlations": pairwise_corrs,
        "total_pairs": len(rho_values),
        "seeds": seeds,
        "route_stability_table": route_stability_df,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 3. Bottleneck Consistency Across Seeds
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_bottleneck_consistency_across_seeds(
    mapped_df: pd.DataFrame,
    seeds: Optional[List[int]] = None,
    target_routes: Optional[List[str]] = None,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Dict[str, Any]:
    """
    Executes bottleneck recovery benchmarks across the 5 deterministic seeds
    [42, 101, 202, 303, 404] to verify that target Texas bottlenecks
    consistently appear as critical bottlenecks in >= 4 of 5 seeds (>= 80%).
    """
    if seeds is None:
        seeds = ROBUSTNESS_SEEDS
    if target_routes is None:
        target_routes = DEFAULT_TARGET_BOTTLENECK_ROUTES

    shipments = group_into_customer_shipments(mapped_df)
    benchmark = run_multiseed_recovery_benchmark(
        shipments_df=shipments,
        mapped_df=mapped_df,
        seeds=seeds,
        target_routes=target_routes,
        min_sample=min_sample,
    )

    return benchmark


# ──────────────────────────────────────────────────────────────────────────────
# 4. Sample Size Threshold Sensitivity Analysis
# ──────────────────────────────────────────────────────────────────────────────

def compute_sample_threshold_sensitivity(
    route_df: pd.DataFrame,
    thresholds: Optional[List[int]] = None,
    sample_col: str = "sample_size",
) -> pd.DataFrame:
    """
    Evaluates route retention and network volume coverage across candidate
    sample size thresholds: [10, 20, 30, 50, 100] (PRD Section 13).
    Demonstrates why N = 30 provides the optimal balance of statistical power
    and route coverage.
    """
    if route_df.empty:
        return pd.DataFrame()

    if thresholds is None:
        thresholds = [10, 20, 30, 50, 100]
    else:
        thresholds = sorted(thresholds)

    if sample_col not in route_df.columns:
        if "order_line_count" in route_df.columns:
            sample_col = "order_line_count"
        elif "order_count" in route_df.columns:
            sample_col = "order_count"
        else:
            return pd.DataFrame()

    total_routes = len(route_df)
    total_orders = route_df[sample_col].sum() if total_routes > 0 else 0

    records = []
    base_route_count = None

    for thresh in thresholds:
        eligible_sub = route_df[route_df[sample_col] >= thresh]
        el_count = len(eligible_sub)
        el_orders = eligible_sub[sample_col].sum() if el_count > 0 else 0

        if base_route_count is None:
            base_route_count = el_count if el_count > 0 else 1

        route_retention = (el_count / base_route_count * 100.0) if base_route_count > 0 else 0.0
        volume_coverage = (el_orders / total_orders * 100.0) if total_orders > 0 else 0.0

        records.append({
            "min_sample_threshold": thresh,
            "eligible_route_count": el_count,
            "low_sample_route_count": total_routes - el_count,
            "orders_covered": int(el_orders),
            "order_coverage_pct": float(np.round(volume_coverage, 1)),
            "route_retention_pct": float(np.round(route_retention, 1)),
        })

    return pd.DataFrame(records)
