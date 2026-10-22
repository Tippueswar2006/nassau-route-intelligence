"""
Tests for Data Quality Engine, Deduplication, and Financial Reconciliation.
Verifies compliance with AD-01, AD-02, AD-10, and AD-12.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.config import (
    RAW_DATA_PATH,
    RAW_DATA_SHA256,
    RECONCILIATION_TARGETS,
)
from src.load_data import verify_source_hash
from src.validate_data import reconcile_metrics


def test_source_file_integrity():
    """Asserts that the raw source file matches the immutable SHA-256 baseline."""
    if not RAW_DATA_PATH.exists():
        pytest.skip("Raw source file not present in current environment.")
    computed_hash = verify_source_hash(RAW_DATA_PATH)
    assert computed_hash == RAW_DATA_SHA256, (
        f"Raw data file has been tampered with or corrupted! {computed_hash} != {RAW_DATA_SHA256}"
    )


def test_reconciliation_4_metrics(raw_df: pd.DataFrame, deduplicated_df: pd.DataFrame):
    """
    Asserts exact consistency for 4-metric reconciliation:
    Rows: 10,194 -> 9,881 (Delta: -313)
    Units: 38,654 -> 37,667 (Delta: -987)
    Sales: $141,783.63 -> $138,284.12 (Delta: -$3,499.51)
    Gross Profit: $93,442.80 -> $91,076.41 (Delta: -$2,366.39)
    """
    recon = reconcile_metrics(raw_df, deduplicated_df)

    assert recon["rows"]["raw"] == 10194
    assert recon["rows"]["clean"] == 9881
    assert recon["rows"]["delta"] == -313

    assert recon["units"]["raw"] == 38654
    assert recon["units"]["clean"] == 37667
    assert recon["units"]["delta"] == -987

    assert recon["sales"]["raw"] == 141783.63
    assert recon["sales"]["clean"] == 138284.12
    assert recon["sales"]["delta"] == -3499.51

    assert recon["profit"]["raw"] == 93442.80
    assert recon["profit"]["clean"] == 91076.41
    assert recon["profit"]["delta"] == -2366.39


def test_postal_code_formatting(cleaned_df: pd.DataFrame):
    """
    Verifies that:
    - Exactly 449 four-digit US postal codes are padded to 5 digits.
    - Exactly 200 Canadian records are flagged as is_canadian = True and is_partial_postal = True.
    - Zero US postal codes have length < 5 in Postal Code Cleaned.
    """
    us_records = cleaned_df[~cleaned_df["is_canadian"]]
    ca_records = cleaned_df[cleaned_df["is_canadian"]]

    assert len(ca_records) == 200, f"Expected 200 Canadian records, got {len(ca_records)}"
    assert ca_records["is_partial_postal"].all(), "All Canadian records must be flagged as partial postal"

    assert len(us_records) == 9994, f"Expected 9,994 US records, got {len(us_records)}"
    assert (us_records["Postal Code Cleaned"].str.len() == 5).all(), (
        "All cleaned US postal codes must be exactly 5 digits"
    )

    # Check that padded zip codes start with '0'
    raw_4digit_mask = cleaned_df["Postal Code"].astype(str).str.len() == 4
    assert raw_4digit_mask.sum() == 449, f"Expected 449 raw 4-digit zip codes, got {raw_4digit_mask.sum()}"
    padded_subset = cleaned_df[raw_4digit_mask & (~cleaned_df["is_canadian"])]
    assert padded_subset["Postal Code Cleaned"].str.startswith("0").all(), (
        "Padded US zip codes must start with leading '0'"
    )


def test_product_name_normalization(cleaned_df: pd.DataFrame):
    """Asserts that 'Wonka Bar -Scrumdiddlyumptious' typo is normalized with proper spacing."""
    assert not (cleaned_df["Product Name"] == "Wonka Bar -Scrumdiddlyumptious").any(), (
        "Typo product name 'Wonka Bar -Scrumdiddlyumptious' should be normalized"
    )
    assert (cleaned_df["Product Name"] == "Wonka Bar - Scrumdiddlyumptious").any(), (
        "Normalized product name 'Wonka Bar - Scrumdiddlyumptious' must be present"
    )


def test_diagnostic_reconstruction(cleaned_df: pd.DataFrame):
    """
    Verifies the diagnostic lead-time reconstruction from Order-ID-year floor subtraction:
    Per-mode means match PRD Section 3.1 within 0.01:
    - Same Day: ~0.38
    - First Class: ~2.55
    - Second Class: ~3.57
    - Standard Class: ~5.32
    And all reconstructed values are within [0, 11] days.
    """
    reconstructed = cleaned_df["lead_time_reconstructed_diagnostic"]
    assert reconstructed.min() >= 0, "Diagnostic lead times must be non-negative"
    assert reconstructed.max() <= 11, "Diagnostic lead times must not exceed 11 days"

    means = cleaned_df.groupby("Ship Mode")["lead_time_reconstructed_diagnostic"].mean()

    assert abs(means["Same Day"] - 0.38) <= 0.01, f"Same Day mean mismatch: {means['Same Day']}"
    assert abs(means["First Class"] - 2.55) <= 0.01, f"First Class mean mismatch: {means['First Class']}"
    assert abs(means["Second Class"] - 3.57) <= 0.01, f"Second Class mean mismatch: {means['Second Class']}"
    assert abs(means["Standard Class"] - 5.32) <= 0.01, f"Standard Class mean mismatch: {means['Standard Class']}"

    assert cleaned_df["reconstruction_is_hypothesis"].all(), (
        "All reconstructed records must be flagged with hypothesis disclaimer"
    )
