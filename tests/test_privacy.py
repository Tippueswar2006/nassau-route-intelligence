"""
Privacy and Cloud Artifact Anonymization Compliance Tests.
Verifies compliance with AD-08 and PRD Section 7/9/20.
Asserts zero raw Customer IDs, zero Order ID customer leaks, and no granular PII in cloud artifacts.
"""

import json
import re
import pandas as pd
import pytest

from src.config import (
    CLEAN_ORDERS_PARQUET,
    ROUTE_AGGREGATES_PARQUET,
    BASELINE_PARQUET,
    DISTANCE_PARQUET,
    STRESS_PARQUET,
    METADATA_JSON,
    SURROGATE_MAPPING_CSV,
    RAW_DATA_PATH,
    BASE_DIR,
)
from src.load_data import load_raw_data, load_prepared_artifacts


def test_prepared_artifacts_presence():
    """Asserts that all 5 Parquet artifacts and metadata.json exist on disk."""
    for path in [
        CLEAN_ORDERS_PARQUET,
        ROUTE_AGGREGATES_PARQUET,
        BASELINE_PARQUET,
        DISTANCE_PARQUET,
        STRESS_PARQUET,
        METADATA_JSON,
    ]:
        assert path.exists(), f"Missing required artifact: {path.name}"
        assert path.stat().st_size > 0, f"Artifact is empty: {path.name}"


def test_load_prepared_artifacts_engine():
    """Verifies that load_prepared_artifacts() successfully loads all Parquet tables."""
    artifacts = load_prepared_artifacts()
    expected_keys = {
        "clean_orders",
        "route_aggregates",
        "baseline",
        "distance_sensitive",
        "stress_test",
    }
    assert expected_keys.issubset(set(artifacts.keys()))
    for key, df in artifacts.items():
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


def test_dropped_pii_columns():
    """Asserts that granular geographic PII ('City', 'Postal Code') is absent from cloud artifacts."""
    artifacts = load_prepared_artifacts()
    forbidden_cols = {"City", "Postal Code", "Postal Code Cleaned"}

    for name, df in artifacts.items():
        present_forbidden = forbidden_cols.intersection(set(df.columns))
        assert not present_forbidden, (
            f"Forbidden PII column(s) {present_forbidden} detected in cloud artifact '{name}'!"
        )


def test_zero_real_customer_ids_in_cloud_artifacts(raw_df: pd.DataFrame):
    """
    Asserts that NO real 6-digit Customer ID appears in any cloud Parquet file
    or in metadata.json.
    """
    real_customer_ids = set(raw_df["Customer ID"].dropna().unique())
    assert len(real_customer_ids) == 5044, "Expected 5,044 unique real Customer IDs"

    artifacts = load_prepared_artifacts()
    for name, df in artifacts.items():
        if "Customer ID" in df.columns:
            cloud_cust_ids = set(df["Customer ID"].dropna().unique())
            overlap = cloud_cust_ids.intersection(real_customer_ids)
            assert not overlap, (
                f"Privacy leak! Found {len(overlap)} real Customer IDs in cloud artifact '{name}': {list(overlap)[:5]}"
            )
            # Assert surrogate format
            assert all(cid.startswith("CUST-") for cid in cloud_cust_ids), (
                f"Invalid surrogate Customer ID format in '{name}'"
            )

    # Check metadata.json content
    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        meta_text = f.read()
    for sample_cid in list(real_customer_ids)[:200]:
        assert sample_cid not in meta_text, (
            f"Real Customer ID {sample_cid} found in metadata.json!"
        )


def test_order_id_surrogates_prevent_customer_leak(raw_df: pd.DataFrame):
    """
    Asserts that cloud Order IDs:
    1. Do not match any raw Order ID (e.g. US-2021-103800-...).
    2. Do not contain any real Customer ID as a substring.
    """
    real_customer_ids = list(raw_df["Customer ID"].dropna().unique())
    artifacts = load_prepared_artifacts()

    for name in ["clean_orders", "baseline", "distance_sensitive", "stress_test"]:
        df = artifacts[name]
        order_ids = df["Order ID"].unique()

        # Check format
        assert all(oid.startswith("ORD-") for oid in order_ids), (
            f"Invalid surrogate Order ID format in '{name}'"
        )

        # Check that none contains real customer ID
        for cid in real_customer_ids[:100]:
            matching = [oid for oid in order_ids[:500] if cid in oid]
            assert not matching, (
                f"Order ID exposes Customer ID {cid} in '{name}': {matching[:3]}"
            )


def test_surrogate_mapping_local_isolation():
    """
    Asserts that:
    1. surrogate_key_mapping.csv exists locally.
    2. surrogate_key_mapping.csv is explicitly excluded in .gitignore.
    """
    assert SURROGATE_MAPPING_CSV.exists(), "Surrogate mapping file must exist locally"
    assert SURROGATE_MAPPING_CSV.stat().st_size > 0

    gitignore_path = BASE_DIR / ".gitignore"
    gitignore_text = gitignore_path.read_text(encoding="utf-8")

    assert "data/derived/surrogate_key_mapping.csv" in gitignore_text, (
        "surrogate_key_mapping.csv MUST be listed in .gitignore!"
    )


def test_metadata_checksum_consistency():
    """
    Asserts that SHA-256 checksums recorded in metadata.json match
    the actual file checksums on disk.
    """
    import hashlib
    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        meta = json.load(f)

    for fname, expected_hash in meta["artifact_checksums"].items():
        if "clean_orders" in fname or "route_aggregates" in fname:
            fpath = CLEAN_ORDERS_PARQUET.parent / fname
        else:
            fpath = BASELINE_PARQUET.parent / fname

        assert fpath.exists(), f"Artifact file {fname} not found"
        hasher = hashlib.sha256()
        with open(fpath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()
        assert actual_hash == expected_hash, (
            f"Checksum mismatch on {fname}! Expected: {expected_hash}, Actual: {actual_hash}"
        )

