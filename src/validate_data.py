"""
Data Quality, Deduplication, and Financial Reconciliation Engine for Nassau Route Intelligence.
Enforces non-negotiable reconciliation baselines and diagnostic lead time reconstruction.
Decoupled from Streamlit (Zero Streamlit imports).
"""

from typing import Dict, Any
import numpy as np
import pandas as pd

from src.config import RECONCILIATION_TARGETS


def flag_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies exact duplicate records across business attributes, excluding system 'Row ID'.
    Marks the first occurrence as False and subsequent repeated lines as True in 'is_duplicate'.
    """
    df = df.copy()
    business_cols = [
        c for c in df.columns
        if c != "Row ID"
        and not c.startswith("is_")
        and not c.startswith("lead_time_")
        and c != "Factory"
    ]
    df["is_duplicate"] = df.duplicated(subset=business_cols, keep="first")
    return df


def reconcile_metrics(
    df_raw: pd.DataFrame, df_clean: pd.DataFrame
) -> Dict[str, Dict[str, float]]:
    """
    Performs 4-metric audit reconciling Rows, Units, Sales, and Gross Profit
    between the original raw file and de-duplicated dataset.
    Asserts exact consistency with approved baseline targets (AD-12).
    """
    raw_rows = len(df_raw)
    clean_rows = len(df_clean)
    delta_rows = clean_rows - raw_rows

    raw_units = int(df_raw["Units"].sum())
    clean_units = int(df_clean["Units"].sum())
    delta_units = clean_units - raw_units

    raw_sales = round(float(df_raw["Sales"].sum()), 2)
    clean_sales = round(float(df_clean["Sales"].sum()), 2)
    delta_sales = round(clean_sales - raw_sales, 2)

    raw_profit = round(float(df_raw["Gross Profit"].sum()), 2)
    clean_profit = round(float(df_clean["Gross Profit"].sum()), 2)
    delta_profit = round(clean_profit - raw_profit, 2)

    reconciliation = {
        "rows": {
            "raw": raw_rows,
            "clean": clean_rows,
            "delta": delta_rows,
            "pct_change": round((delta_rows / raw_rows) * 100, 2),
        },
        "units": {
            "raw": raw_units,
            "clean": clean_units,
            "delta": delta_units,
            "pct_change": round((delta_units / raw_units) * 100, 2),
        },
        "sales": {
            "raw": raw_sales,
            "clean": clean_sales,
            "delta": delta_sales,
            "pct_change": round((delta_sales / raw_sales) * 100, 2),
        },
        "profit": {
            "raw": raw_profit,
            "clean": clean_profit,
            "delta": delta_profit,
            "pct_change": round((delta_profit / raw_profit) * 100, 2),
        },
    }

    # Verify against approved baselines
    for metric, targets in RECONCILIATION_TARGETS.items():
        actual = reconciliation[metric]
        assert actual["raw"] == targets["raw"], (
            f"Reconciliation failure on {metric} raw: expected {targets['raw']}, got {actual['raw']}"
        )
        assert actual["clean"] == targets["clean"], (
            f"Reconciliation failure on {metric} clean: expected {targets['clean']}, got {actual['clean']}"
        )
        assert actual["delta"] == targets["delta"], (
            f"Reconciliation failure on {metric} delta: expected {targets['delta']}, got {actual['delta']}"
        )

    return reconciliation


def clean_geographic_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans geographic codes and tags international records:
    - Left-pads 4-digit US postal codes with leading '0' to standard 5 digits.
    - Flags 3-character Canadian postal codes as partial postal codes.
    - Adds boolean 'is_canadian' tag.
    """
    df = df.copy()

    # Canadian flag
    df["is_canadian"] = df["Country/Region"].str.strip() == "Canada"

    # Postal code handling
    def _clean_postal(row):
        postal = str(row["Postal Code"]).strip() if pd.notna(row["Postal Code"]) else ""
        if row["is_canadian"]:
            return postal  # Keep Canadian 3-char FSA as-is
        # US postal codes
        if len(postal) == 4:
            return f"0{postal}"
        return postal

    df["Postal Code Cleaned"] = df.apply(_clean_postal, axis=1)
    df["is_partial_postal"] = df["is_canadian"] | (df["Postal Code Cleaned"].str.len() < 5)

    return df


def normalize_product_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes whitespace in typographical product names (e.g. Wonka Bar -Scrumdiddlyumptious).
    """
    df = df.copy()
    df["Product Name"] = df["Product Name"].str.replace(
        "Wonka Bar -Scrumdiddlyumptious",
        "Wonka Bar - Scrumdiddlyumptious",
        regex=False,
    )
    return df


def compute_diagnostic_reconstruction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes diagnostic reconstructed order-to-ship lead time based on the
    Order-ID-year export shift hypothesis (PRD Section 3.1).
    Strictly isolated to diagnostic exploration (Page 2); never treated as verified ground truth.
    """
    df = df.copy()

    order_dates = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")
    ship_dates = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y")
    raw_interval = (ship_dates - order_dates).dt.days

    # Extract year embedded in Order ID (e.g., 'US-2021-103800-CHO-MIL-31000' -> 2021)
    order_years = df["Order ID"].str.split("-").str[1].astype(int)

    # Floor offsets by embedded year
    floor_map = {2021: 904, 2022: 1269, 2023: 1269, 2024: 1634}
    floors = order_years.map(floor_map).fillna(0).astype(int)

    df["raw_interval_days"] = raw_interval
    df["lead_time_reconstructed_diagnostic"] = raw_interval - floors
    df["reconstruction_is_hypothesis"] = True

    return df


def clean_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Executes the full Phase 1 data cleaning and quality pipeline on raw input data.
    """
    df = flag_duplicates(df_raw)
    df = clean_geographic_fields(df)
    df = normalize_product_names(df)
    df = compute_diagnostic_reconstruction(df)
    return df
