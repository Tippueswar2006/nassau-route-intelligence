"""
Synthetic Lead Time Generation Engine for Nassau Route Intelligence.
Generates reproducible, distance-sensitive, and stress-tested timing at customer-shipment grain.
Pure Python backend strictly decoupled from UI libraries (Zero Streamlit imports).
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Set
import numpy as np
import pandas as pd
import yaml

from src.config import GENERATOR_YAML, SHIPPING_MODES, DEFAULT_SEED


def load_generator_config(config_path: Path = GENERATOR_YAML) -> Dict:
    """Loads the empirical calibration and scenario configuration from YAML."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def group_into_customer_shipments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups clean, mapped order lines into distinct physical customer shipments.
    Grain: (Customer ID, Order Date, Ship Mode).
    All items in a physical shipment share identical delivery timing.
    """
    shipment_keys = ["Customer ID", "Order Date", "Ship Mode"]

    def _collect_factories(series):
        return set(series.dropna())

    shipments = df.groupby(shipment_keys).agg(
        distance_km=("distance_km", "mean"),
        destination_state=("State/Province", "first"),
        destination_country=("Country/Region", "first"),
        destination_region=("Region", "first"),
        factories=("Factory", _collect_factories),
        order_line_count=("Order ID", "nunique"),
        line_item_count=("Row ID", "count"),
    ).reset_index()

    return shipments


def sample_baseline_lead_times(
    shipments: pd.DataFrame,
    gen_config: Dict,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Draws base lead times from empirical distributions per ship mode (PRD Appendix D).
    Applies base bounds: [0, 2] for Same Day and [1, 14] for other modes.
    """
    dist_cfg = gen_config["empirical_distributions"]
    lead_times = np.zeros(len(shipments), dtype=float)

    for idx, mode in enumerate(shipments["Ship Mode"]):
        spec = dist_cfg[mode]
        days = np.array(spec["days"], dtype=float)
        probs = np.array(spec["probabilities"], dtype=float)
        probs = probs / probs.sum()  # Normalize for precision
        lead_times[idx] = rng.choice(days, p=probs)

    # Apply base bounds
    is_same_day = shipments["Ship Mode"] == "Same Day"
    bounded = np.where(
        is_same_day,
        np.clip(lead_times, 0.0, 2.0),
        np.clip(lead_times, 1.0, 14.0),
    )
    return bounded


def generate_scenario_shipments(
    shipments_df: pd.DataFrame,
    scenario: str,
    seed: int = DEFAULT_SEED,
    gen_config: Optional[Dict] = None,
) -> pd.DataFrame:
    """
    Generates synthetic lead times for a specified scenario across all shipments.
    Scenarios:
      - 'baseline': Empirical per-mode distribution without geographic/temporal effects.
      - 'distance_sensitive': Baseline + 0.5 * (distance_km - mean_distance) / 1000 km,
        bounded in [0, 2] for Same Day and [1, 14] for others.
      - 'stress_test': Applied to Distance-Sensitive foundation with base bounds applied
        *before* delay injections (+1.0d peak season in Nov/Dec, +1.0d CA/NY,
        +1.5d for Texas routes Lot's O' Nuts & Wicked Choccy's). Expanded bounds
        [0, 6] for Same Day and [1, 20] for others prevent clipping.
    """
    if gen_config is None:
        gen_config = load_generator_config()

    shipments = shipments_df.copy()
    rng = np.random.default_rng(seed)

    # 1. Base empirical lead times
    base_lead_times = sample_baseline_lead_times(shipments, gen_config, rng)

    if scenario == "baseline":
        shipments["lead_time_days"] = np.round(base_lead_times, 2)
        shipments["scenario_name"] = "baseline"
        shipments["is_synthetic"] = True
        return shipments

    # 2. Distance adjustment (centered so overall mean is preserved)
    mean_dist = shipments["distance_km"].mean()
    coeff = gen_config.get("distance_sensitivity", {}).get("coefficient_per_1000km", 0.5)
    dist_effect = coeff * (shipments["distance_km"] - mean_dist) / 1000.0

    distance_lead_times = base_lead_times + dist_effect

    # Apply base bounds before injections
    is_same_day = shipments["Ship Mode"] == "Same Day"
    bounded_distance = np.where(
        is_same_day,
        np.clip(distance_lead_times, 0.0, 2.0),
        np.clip(distance_lead_times, 1.0, 14.0),
    )

    if scenario == "distance_sensitive":
        shipments["lead_time_days"] = np.round(bounded_distance, 2)
        shipments["scenario_name"] = "distance_sensitive"
        shipments["is_synthetic"] = True
        return shipments

    if scenario == "stress_test":
        # Start from bounded distance foundation
        stress_lead_times = bounded_distance.copy()

        # Injections
        order_dates = pd.to_datetime(shipments["Order Date"], format="%d-%m-%Y")
        months = order_dates.dt.month

        # Peak season: Nov & Dec (+1.0d)
        is_peak = months.isin([11, 12])
        stress_lead_times += np.where(is_peak, 1.0, 0.0)

        # State delay: California & New York (+1.0d)
        is_ca_ny = shipments["destination_state"].isin(["California", "New York"])
        stress_lead_times += np.where(is_ca_ny, 1.0, 0.0)

        # Route delay: Texas destination from Lot's O' Nuts or Wicked Choccy's (+1.5d)
        is_texas = shipments["destination_state"] == "Texas"
        has_lon = shipments["factories"].apply(lambda f_set: "Lot's O' Nuts" in f_set)
        has_wc = shipments["factories"].apply(lambda f_set: "Wicked Choccy's" in f_set)
        is_tx_injection = is_texas & (has_lon | has_wc)
        stress_lead_times += np.where(is_tx_injection, 1.5, 0.0)

        # Apply expanded bounds to prevent clipping injected delays
        final_stress = np.where(
            is_same_day,
            np.clip(stress_lead_times, 0.0, 6.0),
            np.clip(stress_lead_times, 1.0, 20.0),
        )

        shipments["lead_time_days"] = np.round(final_stress, 2)
        shipments["scenario_name"] = "stress_test"
        shipments["is_synthetic"] = True
        return shipments

    raise ValueError(f"Unknown scenario: '{scenario}'. Must be 'baseline', 'distance_sensitive', or 'stress_test'.")


def merge_synthetic_timing(
    orders_df: pd.DataFrame,
    synthetic_shipments: pd.DataFrame,
) -> pd.DataFrame:
    """
    Broadcasts shipment-level synthetic lead times across all constituent order lines.
    Calculates synthetic ship date and retains original date fields verbatim.
    """
    df = orders_df.copy()
    shipment_keys = ["Customer ID", "Order Date", "Ship Mode"]

    # Select timing fields to merge
    timing_cols = shipment_keys + ["lead_time_days", "scenario_name", "is_synthetic"]
    df = df.merge(synthetic_shipments[timing_cols], on=shipment_keys, how="left")

    # Retain original dates under explicit names
    df["Order_Date_Original"] = df["Order Date"]
    df["Ship_Date_Original"] = df["Ship Date"]

    # Calculate synthetic ship date
    order_dates_dt = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")
    days_to_add = pd.to_timedelta(np.round(df["lead_time_days"]), unit="D")
    synthetic_ship_dates = order_dates_dt + days_to_add
    df["Ship_Date_Synthetic"] = synthetic_ship_dates.dt.strftime("%d-%m-%Y")

    return df


def generate_all_scenarios(
    orders_df: pd.DataFrame,
    seed: int = DEFAULT_SEED,
) -> Dict[str, pd.DataFrame]:
    """
    Generates full synthetic datasets for all three scenarios:
    'baseline', 'distance_sensitive', and 'stress_test'.
    Returns a dictionary mapping scenario name to line-level DataFrame (9,881 rows each).
    """
    gen_config = load_generator_config()
    shipments = group_into_customer_shipments(orders_df)

    scenarios = {}
    for scenario_name in ["baseline", "distance_sensitive", "stress_test"]:
        synth_shipments = generate_scenario_shipments(
            shipments, scenario=scenario_name, seed=seed, gen_config=gen_config
        )
        scenarios[scenario_name] = merge_synthetic_timing(orders_df, synth_shipments)

    return scenarios
