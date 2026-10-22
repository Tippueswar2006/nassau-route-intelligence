"""
Lead-Time Metrics, Mode-Adjustment, and Route Efficiency Scoring (RES) Engine.
Enforces invariant reference populations, safe min-max scaling, and strict delay thresholding.
Pure Python backend decoupled from UI libraries (Zero Streamlit imports).
"""

from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    MIN_SAMPLE_SIZE,
)


def compute_mode_reference_means(df: pd.DataFrame) -> Dict[str, float]:
    """
    Computes ship-mode reference means across the full scenario dataset BEFORE filters.
    These reference means are invariant to downstream user filters.
    """
    if "lead_time_days" not in df.columns or "Ship Mode" not in df.columns:
        raise ValueError("DataFrame must contain 'Ship Mode' and 'lead_time_days'")

    means = df.groupby("Ship Mode")["lead_time_days"].mean().to_dict()
    return means


def calculate_mode_adjusted_lead_time(
    df: pd.DataFrame, reference_means: Dict[str, float]
) -> pd.DataFrame:
    """
    Calculates mode-adjusted lead times by subtracting pre-computed mode reference means:
      mode_adjusted_lead_time = lead_time_days - mean(Ship Mode)
    Ensures that routes are benchmarked fairly without penalizing Standard Class usage.
    """
    df = df.copy()
    if "Ship Mode" not in df.columns or "lead_time_days" not in df.columns:
        raise ValueError("DataFrame must contain 'Ship Mode' and 'lead_time_days'")

    mode_means = df["Ship Mode"].map(reference_means)
    if mode_means.isna().any():
        unmapped_modes = df[mode_means.isna()]["Ship Mode"].unique().tolist()
        raise ValueError(f"Unmapped shipping modes in reference means: {unmapped_modes}")

    df["mode_reference_mean"] = mode_means
    df["mode_adjusted_lead_time"] = np.round(df["lead_time_days"] - mode_means, 2)

    return df


def apply_delay_threshold(
    df: pd.DataFrame, threshold_days: float = DEFAULT_DELAY_THRESHOLD
) -> pd.DataFrame:
    """
    Evaluates delay status using strict inequality:
      is_delayed = lead_time_days > threshold_days
    Boundary behavior: An order at exactly threshold_days is NOT delayed.
    """
    df = df.copy()
    if "lead_time_days" not in df.columns:
        raise ValueError("DataFrame must contain 'lead_time_days'")

    df["is_delayed"] = df["lead_time_days"] > threshold_days
    df["delay_threshold_used"] = threshold_days

    return df


def compute_route_lead_time_stats(
    df: pd.DataFrame,
    group_col: str = "route_key",
    lead_time_col: str = "lead_time_days",
    threshold_days: float = DEFAULT_DELAY_THRESHOLD,
) -> pd.DataFrame:
    """
    Aggregates route-level statistics for lead time, variability, and delay rates.
    Includes mode-adjusted statistics if mode_adjusted_lead_time is present.
    """
    df = apply_delay_threshold(df, threshold_days=threshold_days)

    def _safe_std(x):
        return float(x.std(ddof=1)) if len(x) > 1 else 0.0

    agg_kwargs = {
        "sample_size": ("Row ID", "count") if "Row ID" in df.columns else (lead_time_col, "count"),
        "order_line_count": ("Order ID", "nunique") if "Order ID" in df.columns else (lead_time_col, "count"),
        "mean_lead_time": (lead_time_col, "mean"),
        "median_lead_time": (lead_time_col, "median"),
        "std_lead_time": (lead_time_col, _safe_std),
        "p75_lead_time": (lead_time_col, lambda x: float(np.percentile(x, 75))),
        "p90_lead_time": (lead_time_col, lambda x: float(np.percentile(x, 90))),
        "min_lead_time": (lead_time_col, "min"),
        "max_lead_time": (lead_time_col, "max"),
        "delayed_count": ("is_delayed", "sum"),
        "delay_rate": ("is_delayed", "mean"),
    }

    if "mode_adjusted_lead_time" in df.columns:
        agg_kwargs["mean_mode_adjusted"] = ("mode_adjusted_lead_time", "mean")
        agg_kwargs["std_mode_adjusted"] = ("mode_adjusted_lead_time", _safe_std)

    stats = df.groupby(group_col).agg(**agg_kwargs).reset_index()

    # Fill NaN std with 0.0 for zero variance
    stats["std_lead_time"] = stats["std_lead_time"].fillna(0.0)
    if "std_mode_adjusted" in stats.columns:
        stats["std_mode_adjusted"] = stats["std_mode_adjusted"].fillna(0.0)

    # Attach Factory and State/Region metadata if present
    meta_cols = [c for c in ["Factory", "State/Province", "Country/Region", "Region", "distance_km"] if c in df.columns]
    if meta_cols:
        meta_df = df[[group_col] + meta_cols].drop_duplicates(subset=[group_col])
        stats = stats.merge(meta_df, on=group_col, how="left")

    return stats


def calculate_route_efficiency_scores(
    route_stats: pd.DataFrame,
    basis: str = "mode_adjusted",
    w_speed: float = DEFAULT_RES_WEIGHT_SPEED,
    w_var: float = DEFAULT_RES_WEIGHT_VARIABILITY,
) -> pd.DataFrame:
    """
    Calculates Route Efficiency Scores (RES) [0, 100] across eligible routes.
      RES = 100 - (w_speed * Speed_Penalty + w_var * Variability_Penalty)
    Safe handling:
      - If min == max, penalty defaults to 0.0 without division-by-zero error.
      - Speed-only score computes RES with w_speed = 1.0, w_var = 0.0.
    """
    df = route_stats.copy()

    # Determine metric columns based on basis
    if basis == "mode_adjusted" and "mean_mode_adjusted" in df.columns:
        mean_col = "mean_mode_adjusted"
        std_col = "std_mode_adjusted" if "std_mode_adjusted" in df.columns else "std_lead_time"
    else:
        mean_col = "mean_lead_time"
        std_col = "std_lead_time"

    # Speed Penalty (Min-Max scaled across comparison population)
    l_min = df[mean_col].min()
    l_max = df[mean_col].max()
    if l_max > l_min:
        speed_penalty = 100.0 * (df[mean_col] - l_min) / (l_max - l_min)
    else:
        speed_penalty = pd.Series(0.0, index=df.index)

    # Variability Penalty (Min-Max scaled across comparison population)
    s_min = df[std_col].min()
    s_max = df[std_col].max()
    if s_max > s_min:
        var_penalty = 100.0 * (df[std_col] - s_min) / (s_max - s_min)
    else:
        var_penalty = pd.Series(0.0, index=df.index)

    df["speed_penalty"] = np.round(speed_penalty, 2)
    df["variability_penalty"] = np.round(var_penalty, 2)

    # Composite RES
    raw_res = 100.0 - (w_speed * df["speed_penalty"] + w_var * df["variability_penalty"])
    df["res_score"] = np.round(np.clip(raw_res, 0.0, 100.0), 2)

    # Speed-Only Score (100% speed, 0% variability)
    speed_only = 100.0 - df["speed_penalty"]
    df["speed_only_score"] = np.round(np.clip(speed_only, 0.0, 100.0), 2)

    return df
