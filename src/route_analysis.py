"""
Route Aggregation, Sample Size Guardrails, Regional Rollups, and Leaderboard Engine.
Enforces N >= 30 sample threshold, small factory regional rollups, and strict data layer isolation.
Pure Python backend decoupled from UI libraries (Zero Streamlit imports).
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_DELAY_THRESHOLD,
    DEFAULT_RES_WEIGHT_SPEED,
    DEFAULT_RES_WEIGHT_VARIABILITY,
    DISTANCE_BAND_BINS,
    DISTANCE_BAND_LABELS,
    EXPEDITED_MODES,
    MIN_SAMPLE_SIZE,
    SHIPPING_MODES,
    SMALL_FACTORIES,
    STANDARD_MODES,
)
from src.metrics import (
    apply_delay_threshold,
    calculate_route_efficiency_scores,
)


VALID_DATA_LAYERS = {"ORIGINAL", "DERIVED", "SYNTHETIC"}


def validate_layer_isolation(df: pd.DataFrame) -> str:
    """
    Asserts AD-02 layer isolation: prevents mixing ORIGINAL, DERIVED, and SYNTHETIC
    records in the same analytical view or leaderboard.

    Returns the identified data layer.
    Raises ValueError if multiple layers are present or layer is unrecognized.
    """
    if "data_layer" not in df.columns:
        return "UNSPECIFIED"

    unique_layers = df["data_layer"].dropna().unique().tolist()
    if len(unique_layers) > 1:
        raise ValueError(
            f"Layer isolation violation: multiple data layers detected in dataset: {unique_layers}. "
            "ORIGINAL, DERIVED, and SYNTHETIC data must never be mixed."
        )
    if len(unique_layers) == 1:
        layer = str(unique_layers[0]).upper()
        if layer not in VALID_DATA_LAYERS:
            raise ValueError(f"Unrecognized data layer: {layer}. Must be one of {VALID_DATA_LAYERS}")
        return layer

    return "UNSPECIFIED"


def assign_route_hierarchy(
    df: pd.DataFrame,
    small_factories: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Assigns routing hierarchy based on factory scale:
    - Small factories (Sugar Shack, Secret Factory, The Other Factory) roll up to Region level.
    - Large factories (Lot's O' Nuts, Wicked Choccy's) evaluate at State/Province level.
    """
    df = df.copy()
    if small_factories is None:
        small_factories = SMALL_FACTORIES

    if "Factory" not in df.columns:
        raise ValueError("DataFrame must contain 'Factory' column")

    is_small = df["Factory"].isin(small_factories)
    df["is_regional_rollup"] = is_small

    if "Region" in df.columns and "State/Province" in df.columns:
        df["analysis_destination"] = np.where(is_small, df["Region"], df["State/Province"])
        df["analysis_route_key"] = df["Factory"] + " -> " + df["analysis_destination"]
    elif "State/Province" in df.columns:
        df["analysis_destination"] = df["State/Province"]
        df["analysis_route_key"] = df["Factory"] + " -> " + df["State/Province"]
    elif "Region" in df.columns:
        df["analysis_destination"] = df["Region"]
        df["analysis_route_key"] = df["Factory"] + " -> " + df["Region"]
    else:
        raise ValueError("DataFrame must contain 'State/Province' or 'Region' column")

    return df


def aggregate_routes(
    df: pd.DataFrame,
    level: str = "state",
    min_sample: int = MIN_SAMPLE_SIZE,
    threshold_days: float = DEFAULT_DELAY_THRESHOLD,
    rollup_small_factories: bool = True,
    w_speed: float = DEFAULT_RES_WEIGHT_SPEED,
    w_var: float = DEFAULT_RES_WEIGHT_VARIABILITY,
) -> pd.DataFrame:
    """
    Aggregates order lines into route-level performance summaries.

    Parameters:
      - df: Input shipment/order DataFrame (e.g. clean_orders, baseline, stress_test)
      - level: Aggregation level ('state', 'region', or 'auto').
               When 'auto' or rollup_small_factories=True, small factories roll up to Region.
      - min_sample: Minimum order count threshold (default N=30)
      - threshold_days: Delay threshold (default 5.0d, strict inequality)
      - rollup_small_factories: If True and level=='state', roll small factories to Region.
      - w_speed, w_var: RES scoring weights (default 0.70 / 0.30)
    """
    validate_layer_isolation(df)
    df = df.copy()

    # Determine grouping column and destination column
    if rollup_small_factories and level == "state":
        df = assign_route_hierarchy(df)
        group_key = "analysis_route_key"
        dest_col = "analysis_destination"
    elif level == "region":
        if "route_key_region" in df.columns:
            group_key = "route_key_region"
        else:
            df["route_key_region"] = df["Factory"] + " -> " + df["Region"]
            group_key = "route_key_region"
        dest_col = "Region"
        df["is_regional_rollup"] = True
    else:  # standard state level
        if "route_key" in df.columns:
            group_key = "route_key"
        else:
            df["route_key"] = df["Factory"] + " -> " + df["State/Province"]
            group_key = "route_key"
        dest_col = "State/Province"
        df["is_regional_rollup"] = False

    has_lead_time = "lead_time_days" in df.columns
    if has_lead_time:
        df = apply_delay_threshold(df, threshold_days=threshold_days)

    def _safe_std(x):
        return float(x.std(ddof=1)) if len(x) > 1 else 0.0

    # Build aggregation specifications
    agg_kwargs = {
        "sample_size": ("Order ID", "nunique") if "Order ID" in df.columns else ("Row ID", "count"),
        "order_line_count": ("Order ID", "nunique") if "Order ID" in df.columns else ("Row ID", "count"),
        "line_item_count": ("Row ID", "count") if "Row ID" in df.columns else (group_key, "count"),
    }

    if "Units" in df.columns:
        agg_kwargs["total_units"] = ("Units", "sum")
    if "Sales" in df.columns:
        agg_kwargs["total_sales"] = ("Sales", "sum")
    if "Gross Profit" in df.columns:
        agg_kwargs["total_gross_profit"] = ("Gross Profit", "sum")
    if "distance_km" in df.columns:
        agg_kwargs["distance_km"] = ("distance_km", "mean")

    if has_lead_time:
        agg_kwargs["mean_lead_time"] = ("lead_time_days", "mean")
        agg_kwargs["median_lead_time"] = ("lead_time_days", "median")
        agg_kwargs["std_lead_time"] = ("lead_time_days", _safe_std)
        agg_kwargs["p75_lead_time"] = ("lead_time_days", lambda x: float(np.percentile(x, 75)))
        agg_kwargs["p90_lead_time"] = ("lead_time_days", lambda x: float(np.percentile(x, 90)))
        agg_kwargs["min_lead_time"] = ("lead_time_days", "min")
        agg_kwargs["max_lead_time"] = ("lead_time_days", "max")
        agg_kwargs["delayed_count"] = ("is_delayed", "sum")
        agg_kwargs["delay_rate"] = ("is_delayed", "mean")

    if "mode_adjusted_lead_time" in df.columns:
        agg_kwargs["mean_mode_adjusted"] = ("mode_adjusted_lead_time", "mean")
        agg_kwargs["std_mode_adjusted"] = ("mode_adjusted_lead_time", _safe_std)

    route_stats = df.groupby(group_key).agg(**agg_kwargs).reset_index()

    # Rename grouping column to route_key for consistent downstream API
    if group_key != "route_key":
        route_stats = route_stats.rename(columns={group_key: "route_key"})

    # Attach metadata columns
    meta_cols = [c for c in ["Factory", dest_col, "Country/Region", "Region", "is_regional_rollup", "data_layer"] if c in df.columns]
    if meta_cols:
        meta_df = df[[group_key] + meta_cols].drop_duplicates(subset=[group_key])
        if group_key != "route_key":
            meta_df = meta_df.rename(columns={group_key: "route_key"})
        route_stats = route_stats.merge(meta_df, on="route_key", how="left")

    # Round numeric fields
    round_cols = ["distance_km", "total_sales", "total_gross_profit"]
    if has_lead_time:
        round_cols += [
            "mean_lead_time",
            "median_lead_time",
            "std_lead_time",
            "p75_lead_time",
            "p90_lead_time",
            "min_lead_time",
            "max_lead_time",
            "delay_rate",
        ]
    if "mean_mode_adjusted" in route_stats.columns:
        round_cols += ["mean_mode_adjusted", "std_mode_adjusted"]

    for col in round_cols:
        if col in route_stats.columns:
            route_stats[col] = np.round(route_stats[col], 2)

    # Flag sample eligibility
    route_stats["is_eligible"] = route_stats["sample_size"] >= min_sample
    route_stats["is_low_sample"] = route_stats["sample_size"] < min_sample
    route_stats["min_sample_threshold"] = min_sample

    # Calculate RES if lead time data is present
    if has_lead_time:
        route_stats = calculate_route_efficiency_scores(
            route_stats,
            basis="mode_adjusted" if "mean_mode_adjusted" in route_stats.columns else "raw",
            w_speed=w_speed,
            w_var=w_var,
        )

    return route_stats


def filter_eligible_routes(
    route_df: pd.DataFrame,
    min_sample: int = MIN_SAMPLE_SIZE,
    sample_col: str = "sample_size",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits route aggregates into eligible routes (N >= min_sample) and low-sample routes (N < min_sample).

    Enforces strict boundary checks:
      - N = 29 -> Ineligible (low sample)
      - N = 30 -> Eligible
      - N = 31 -> Eligible

    Returns (eligible_df, low_sample_df).
    """
    df = route_df.copy()

    # Resolve sample size column
    if sample_col not in df.columns:
        if "order_line_count" in df.columns:
            sample_col = "order_line_count"
        elif "order_count" in df.columns:
            sample_col = "order_count"
        else:
            raise ValueError(f"Sample size column '{sample_col}' not found in DataFrame.")

    df["is_eligible"] = df[sample_col] >= min_sample
    df["is_low_sample"] = df[sample_col] < min_sample

    eligible_df = df[df["is_eligible"]].copy().reset_index(drop=True)
    low_sample_df = df[df["is_low_sample"]].copy().reset_index(drop=True)

    return eligible_df, low_sample_df


def generate_leaderboards(
    eligible_df: pd.DataFrame,
    top_n: int = 10,
    score_col: str = "res_score",
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates Top N (most efficient) and Bottom N (least efficient) route leaderboards.

    Guarantees:
      - Enforces AD-02: Asserts layer isolation (no mixing ORIGINAL, DERIVED, SYNTHETIC).
      - Enforces AD-07: Ineligible low-sample routes (N < min_sample) are excluded.
      - Top N sorted descending by score_col (higher RES is better).
      - Bottom N sorted ascending by score_col (lower RES is worse).
    """
    validate_layer_isolation(eligible_df)

    # Determine sample column
    sample_col = "sample_size" if "sample_size" in eligible_df.columns else "order_line_count"
    if sample_col in eligible_df.columns:
        low_sample_mask = eligible_df[sample_col] < min_sample
        if low_sample_mask.any():
            # Exclude low-sample routes if inadvertently passed
            eligible_df = eligible_df[~low_sample_mask].copy()

    if score_col not in eligible_df.columns:
        raise ValueError(f"Score column '{score_col}' not found in DataFrame.")

    # Top N (Highest Efficiency)
    top_df = eligible_df.sort_values(by=score_col, ascending=False).head(top_n).copy().reset_index(drop=True)
    top_df["rank"] = range(1, len(top_df) + 1)
    top_df["leaderboard_type"] = "Top 10 (Most Efficient)"

    # Bottom N (Lowest Efficiency)
    bottom_df = eligible_df.sort_values(by=score_col, ascending=True).head(top_n).copy().reset_index(drop=True)
    bottom_df["rank"] = range(1, len(bottom_df) + 1)
    bottom_df["leaderboard_type"] = "Bottom 10 (Least Efficient)"

    return top_df, bottom_df


def aggregate_state_metrics(
    df: pd.DataFrame,
    threshold_days: float = DEFAULT_DELAY_THRESHOLD,
    w_speed: float = DEFAULT_RES_WEIGHT_SPEED,
    w_var: float = DEFAULT_RES_WEIGHT_VARIABILITY,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregates performance metrics at the destination State/Province level for geographic analysis.
    Explicitly separates US states from Canadian destinations to protect map geometry (FR-09).

    Parameters:
      - df: Input shipment/order DataFrame (e.g. baseline, clean_orders)
      - threshold_days: Delay threshold (strict inequality: lead_time_days > threshold_days)
      - w_speed, w_var: RES scoring weights (default 0.70 / 0.30)
      - min_sample: Minimum order count threshold

    Returns:
      (us_state_df, canada_df)
      - us_state_df: Aggregated by US State/Province with state_code, sample_size,
        order_line_count, line_item_count, total_units, total_sales, total_gross_profit,
        mean_lead_time, median_lead_time, std_lead_time, delayed_count, delay_rate,
        delay_rate_pct, res_score, speed_only_score, factory_breakdown_html, top_factory.
      - canada_df: Canadian order records excluded from US map geometry.
    """
    validate_layer_isolation(df)
    df = df.copy()

    # Separate Canada and US records
    is_canada = pd.Series(False, index=df.index)
    if "is_canadian" in df.columns:
        is_canada = df["is_canadian"].astype(bool)
    elif "Country/Region" in df.columns:
        is_canada = df["Country/Region"].astype(str).str.strip().str.lower() == "canada"

    from src.config import US_STATE_TO_CODE

    canada_df = df[is_canada].copy()
    us_candidate_df = df[~is_canada].copy()

    state_col = "State/Province" if "State/Province" in us_candidate_df.columns else "State"
    if "Country/Region" in us_candidate_df.columns:
        is_us = us_candidate_df["Country/Region"].astype(str).str.strip() == "United States"
        us_df = us_candidate_df[is_us | us_candidate_df[state_col].isin(US_STATE_TO_CODE)].copy()
    else:
        us_df = us_candidate_df[us_candidate_df[state_col].isin(US_STATE_TO_CODE)].copy()

    if us_df.empty:
        return pd.DataFrame(), canada_df

    has_lead_time = "lead_time_days" in us_df.columns
    if has_lead_time:
        us_df = apply_delay_threshold(us_df, threshold_days=threshold_days)

    def _safe_std(x):
        return float(x.std(ddof=1)) if len(x) > 1 else 0.0

    state_col = "State/Province" if "State/Province" in us_df.columns else "State"

    agg_kwargs = {
        "sample_size": ("Order ID", "nunique") if "Order ID" in us_df.columns else ("Row ID", "count"),
        "order_line_count": ("Order ID", "nunique") if "Order ID" in us_df.columns else ("Row ID", "count"),
        "line_item_count": ("Row ID", "count") if "Row ID" in us_df.columns else (state_col, "count"),
    }

    if "Units" in us_df.columns:
        agg_kwargs["total_units"] = ("Units", "sum")
    if "Sales" in us_df.columns:
        agg_kwargs["total_sales"] = ("Sales", "sum")
    if "Gross Profit" in us_df.columns:
        agg_kwargs["total_gross_profit"] = ("Gross Profit", "sum")
    if "distance_km" in us_df.columns:
        agg_kwargs["mean_distance_km"] = ("distance_km", "mean")

    if has_lead_time:
        agg_kwargs["mean_lead_time"] = ("lead_time_days", "mean")
        agg_kwargs["median_lead_time"] = ("lead_time_days", "median")
        agg_kwargs["std_lead_time"] = ("lead_time_days", _safe_std)
        agg_kwargs["p75_lead_time"] = ("lead_time_days", lambda x: float(np.percentile(x, 75)))
        agg_kwargs["p90_lead_time"] = ("lead_time_days", lambda x: float(np.percentile(x, 90)))
        agg_kwargs["min_lead_time"] = ("lead_time_days", "min")
        agg_kwargs["max_lead_time"] = ("lead_time_days", "max")
        agg_kwargs["delayed_count"] = ("is_delayed", "sum")
        agg_kwargs["delay_rate"] = ("is_delayed", "mean")

    if "mode_adjusted_lead_time" in us_df.columns:
        agg_kwargs["mean_mode_adjusted"] = ("mode_adjusted_lead_time", "mean")
        agg_kwargs["std_mode_adjusted"] = ("mode_adjusted_lead_time", _safe_std)

    state_stats = us_df.groupby(state_col).agg(**agg_kwargs).reset_index()

    # Map state codes
    from src.config import US_STATE_TO_CODE
    state_stats["state_code"] = state_stats[state_col].map(US_STATE_TO_CODE)

    # Attach Region if available
    if "Region" in us_df.columns:
        region_map = us_df[[state_col, "Region"]].drop_duplicates().groupby(state_col)["Region"].first().to_dict()
        state_stats["Region"] = state_stats[state_col].map(region_map)

    # Factory fulfillment breakdown per state
    if "Factory" in us_df.columns:
        order_key = "Order ID" if "Order ID" in us_df.columns else "Row ID"
        fb = us_df.groupby([state_col, "Factory"])[order_key].nunique().unstack(fill_value=0)
        fb_totals = fb.sum(axis=1)
        fb_pcts = fb.div(fb_totals, axis=0) * 100.0

        def _fmt_breakdown(st_name):
            if st_name not in fb.index:
                return "N/A"
            row = fb.loc[st_name]
            p_row = fb_pcts.loc[st_name]
            active = row[row > 0].sort_values(ascending=False)
            if active.empty:
                return "No orders"
            return "<br>".join([f"{fac}: {cnt:,} ({p_row[fac]:.1f}%)" for fac, cnt in active.items()])

        def _get_top_factory(st_name):
            if st_name not in fb.index:
                return "N/A"
            row = fb.loc[st_name]
            p_row = fb_pcts.loc[st_name]
            active = row[row > 0].sort_values(ascending=False)
            if active.empty:
                return "None"
            top_fac = active.index[0]
            return f"{top_fac} ({p_row[top_fac]:.1f}%)"

        state_stats["factory_breakdown_html"] = state_stats[state_col].apply(_fmt_breakdown)
        state_stats["top_factory"] = state_stats[state_col].apply(_get_top_factory)
    else:
        state_stats["factory_breakdown_html"] = "No factory data"
        state_stats["top_factory"] = "N/A"

    # Round numeric fields
    round_cols = ["mean_distance_km", "total_sales", "total_gross_profit"]
    if has_lead_time:
        round_cols += [
            "mean_lead_time",
            "median_lead_time",
            "std_lead_time",
            "p75_lead_time",
            "p90_lead_time",
            "min_lead_time",
            "max_lead_time",
            "delay_rate",
        ]
    if "mean_mode_adjusted" in state_stats.columns:
        round_cols += ["mean_mode_adjusted", "std_mode_adjusted"]

    for col in round_cols:
        if col in state_stats.columns:
            state_stats[col] = np.round(state_stats[col], 2)

    # Convert delay_rate to percentage display column
    if "delay_rate" in state_stats.columns:
        state_stats["delay_rate_pct"] = np.round(state_stats["delay_rate"] * 100.0, 1)

    # Sample eligibility flag
    state_stats["is_eligible"] = state_stats["sample_size"] >= min_sample
    state_stats["is_low_sample"] = state_stats["sample_size"] < min_sample
    state_stats["min_sample_threshold"] = min_sample
    state_stats["sample_status"] = np.where(
        state_stats["is_eligible"],
        f"Eligible (N >= {min_sample})",
        f"⚠️ Low Sample (N < {min_sample})",
    )

    # Calculate RES if lead time data is present
    if has_lead_time:
        state_stats = calculate_route_efficiency_scores(
            state_stats,
            basis="mode_adjusted" if "mean_mode_adjusted" in state_stats.columns else "raw",
            w_speed=w_speed,
            w_var=w_var,
        )

    return state_stats, canada_df


def assign_distance_bands(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorizes shipments into distance bands per FR-10:
    0–500 km, 500–1,500 km, 1,500–3,000 km, 3,000+ km.
    """
    df = df.copy()
    if "distance_km" not in df.columns:
        raise ValueError("DataFrame must contain 'distance_km' column")

    df["distance_band"] = pd.cut(
        df["distance_km"],
        bins=DISTANCE_BAND_BINS,
        labels=DISTANCE_BAND_LABELS,
        right=False,
    )
    return df


def assign_expedited_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns shipping mode tier (FR-10):
    - Expedited: Same Day, First Class, Second Class
    - Standard: Standard Class
    - Unknown: Unrecognized or missing mode
    """
    df = df.copy()
    if "Ship Mode" not in df.columns:
        raise ValueError("DataFrame must contain 'Ship Mode' column")

    is_exp = df["Ship Mode"].isin(EXPEDITED_MODES)
    is_std = df["Ship Mode"].isin(STANDARD_MODES)
    df["ship_mode_group"] = np.where(is_exp, "Expedited", np.where(is_std, "Standard", "Unknown"))
    return df


def aggregate_ship_mode_metrics(
    df: pd.DataFrame,
    threshold_days: float = DEFAULT_DELAY_THRESHOLD,
    group_col: str = "Ship Mode",
) -> pd.DataFrame:
    """
    Aggregates lead-time distribution statistics, volume grains, and commercial
    gross profit margins across individual shipping modes or Expedited vs Standard groups.

    Parameters:
      - df: Input dataset (e.g. baseline, clean_orders)
      - threshold_days: Strict inequality threshold (lead_time_days > threshold_days)
      - group_col: Grouping dimension ('Ship Mode' or 'ship_mode_group')
    """
    validate_layer_isolation(df)
    df = df.copy()

    if group_col == "ship_mode_group" and "ship_mode_group" not in df.columns:
        df = assign_expedited_group(df)

    has_lead_time = "lead_time_days" in df.columns
    if has_lead_time:
        df = apply_delay_threshold(df, threshold_days=threshold_days)

    def _safe_std(x):
        return float(x.std(ddof=1)) if len(x) > 1 else 0.0

    def _safe_percentile(p):
        return lambda x: float(np.percentile(x.dropna(), p)) if len(x.dropna()) > 0 else 0.0

    def _iqr(x):
        valid = x.dropna()
        return float(np.percentile(valid, 75) - np.percentile(valid, 25)) if len(valid) > 0 else 0.0

    agg_kwargs = {
        "order_line_count": ("Order ID", "nunique") if "Order ID" in df.columns else ("Row ID", "count"),
        "line_item_count": ("Row ID", "count") if "Row ID" in df.columns else (group_col, "count"),
    }

    if "Units" in df.columns:
        agg_kwargs["total_units"] = ("Units", "sum")
    if "Sales" in df.columns:
        agg_kwargs["total_sales"] = ("Sales", "sum")
    if "Cost" in df.columns:
        agg_kwargs["total_cogs"] = ("Cost", "sum")
    if "Gross Profit" in df.columns:
        agg_kwargs["total_gross_profit"] = ("Gross Profit", "sum")
    if "distance_km" in df.columns:
        agg_kwargs["mean_distance_km"] = ("distance_km", "mean")

    if has_lead_time:
        agg_kwargs["mean_lead_time"] = ("lead_time_days", "mean")
        agg_kwargs["median_lead_time"] = ("lead_time_days", "median")
        agg_kwargs["std_lead_time"] = ("lead_time_days", _safe_std)
        agg_kwargs["p25_lead_time"] = ("lead_time_days", _safe_percentile(25))
        agg_kwargs["p75_lead_time"] = ("lead_time_days", _safe_percentile(75))
        agg_kwargs["iqr_lead_time"] = ("lead_time_days", _iqr)
        agg_kwargs["p90_lead_time"] = ("lead_time_days", _safe_percentile(90))
        agg_kwargs["min_lead_time"] = ("lead_time_days", "min")
        agg_kwargs["max_lead_time"] = ("lead_time_days", "max")
        agg_kwargs["delayed_count"] = ("is_delayed", "sum")
        agg_kwargs["delay_rate"] = ("is_delayed", "mean")

    stats = df.groupby(group_col).agg(**agg_kwargs).reset_index()

    # Commercial Product Margin % (COGS basis, AD-11)
    if "total_gross_profit" in stats.columns and "total_sales" in stats.columns:
        stats["gross_margin_pct"] = np.where(
            stats["total_sales"] > 0,
            (stats["total_gross_profit"] / stats["total_sales"]) * 100.0,
            0.0,
        )

    # Round numeric columns
    round_cols = ["total_sales", "total_cogs", "total_gross_profit", "gross_margin_pct", "mean_distance_km"]
    if has_lead_time:
        round_cols += [
            "mean_lead_time",
            "median_lead_time",
            "std_lead_time",
            "p25_lead_time",
            "p75_lead_time",
            "iqr_lead_time",
            "p90_lead_time",
            "min_lead_time",
            "max_lead_time",
            "delay_rate",
        ]

    for col in round_cols:
        if col in stats.columns:
            stats[col] = np.round(stats[col], 2)

    if "delay_rate" in stats.columns:
        stats["delay_rate_pct"] = np.round(stats["delay_rate"] * 100.0, 1)

    return stats


def aggregate_distance_band_metrics(
    df: pd.DataFrame,
    threshold_days: float = DEFAULT_DELAY_THRESHOLD,
    min_sample: int = MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    """
    Aggregates lead-time, volume, and commercial metrics by Ship Mode and Distance Band.
    Applies guardrails: flags cells with sample size N < min_sample.
    """
    validate_layer_isolation(df)
    df = df.copy()

    if "distance_km" not in df.columns:
        raise ValueError("DataFrame must contain 'distance_km' column")

    # Filter records with valid distance values
    df = df.dropna(subset=["distance_km"]).copy()

    if "distance_band" not in df.columns:
        df = assign_distance_bands(df)

    has_lead_time = "lead_time_days" in df.columns
    if has_lead_time:
        df = apply_delay_threshold(df, threshold_days=threshold_days)

    def _safe_std(x):
        return float(x.std(ddof=1)) if len(x) > 1 else 0.0

    def _safe_percentile(p):
        return lambda x: float(np.percentile(x.dropna(), p)) if len(x.dropna()) > 0 else 0.0

    agg_kwargs = {
        "order_line_count": ("Order ID", "nunique") if "Order ID" in df.columns else ("Row ID", "count"),
        "line_item_count": ("Row ID", "count") if "Row ID" in df.columns else ("Ship Mode", "count"),
    }

    if "Units" in df.columns:
        agg_kwargs["total_units"] = ("Units", "sum")
    if "Sales" in df.columns:
        agg_kwargs["total_sales"] = ("Sales", "sum")
    if "Cost" in df.columns:
        agg_kwargs["total_cogs"] = ("Cost", "sum")
    if "Gross Profit" in df.columns:
        agg_kwargs["total_gross_profit"] = ("Gross Profit", "sum")
    if "distance_km" in df.columns:
        agg_kwargs["mean_distance_km"] = ("distance_km", "mean")

    if has_lead_time:
        agg_kwargs["mean_lead_time"] = ("lead_time_days", "mean")
        agg_kwargs["median_lead_time"] = ("lead_time_days", "median")
        agg_kwargs["std_lead_time"] = ("lead_time_days", _safe_std)
        agg_kwargs["p75_lead_time"] = ("lead_time_days", _safe_percentile(75))
        agg_kwargs["p90_lead_time"] = ("lead_time_days", _safe_percentile(90))
        agg_kwargs["delayed_count"] = ("is_delayed", "sum")
        agg_kwargs["delay_rate"] = ("is_delayed", "mean")

    # Group by Ship Mode and distance_band
    stats = df.groupby(["Ship Mode", "distance_band"], observed=False).agg(**agg_kwargs).reset_index()

    # Exclude zero-observation ghost rows from Cartesian product
    stats = stats[stats["order_line_count"] > 0].copy().reset_index(drop=True)

    if "total_gross_profit" in stats.columns and "total_sales" in stats.columns:
        stats["gross_margin_pct"] = np.where(
            stats["total_sales"] > 0,
            (stats["total_gross_profit"] / stats["total_sales"]) * 100.0,
            0.0,
        )

    round_cols = ["mean_distance_km", "total_sales", "total_cogs", "total_gross_profit", "gross_margin_pct"]
    if has_lead_time:
        round_cols += ["mean_lead_time", "median_lead_time", "std_lead_time", "p75_lead_time", "p90_lead_time", "delay_rate"]

    for col in round_cols:
        if col in stats.columns:
            stats[col] = np.round(stats[col], 2)

    if "delay_rate" in stats.columns:
        stats["delay_rate_pct"] = np.round(stats["delay_rate"] * 100.0, 1)

    # Sample guardrails
    stats["is_eligible"] = stats["order_line_count"] >= min_sample
    stats["sample_status"] = np.where(
        stats["is_eligible"],
        f"Eligible (N >= {min_sample})",
        f"⚠️ Low Sample (N < {min_sample})",
    )

    return stats


