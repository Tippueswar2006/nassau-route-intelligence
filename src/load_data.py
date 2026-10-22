"""
Data Ingestion and Integrity Engine for Nassau Route Intelligence.
Dual-mode loading (Local with raw verification vs Cloud with prepared Parquet artifacts).
Decoupled from Streamlit (Zero Streamlit imports).
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from src.config import (
    RAW_DATA_PATH,
    RAW_DATA_SHA256,
    CLEAN_ORDERS_PARQUET,
    ROUTE_AGGREGATES_PARQUET,
    BASELINE_PARQUET,
    DISTANCE_PARQUET,
    STRESS_PARQUET,
    METADATA_JSON,
    TRANSFORMATION_LOG_JSON,
)


def verify_source_hash(file_path: Path = RAW_DATA_PATH) -> str:
    """
    Computes the SHA-256 checksum of the source dataset and verifies integrity.
    Raises ValueError on hash mismatch to prevent pipeline contamination.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found at: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    computed_hash = hasher.hexdigest()

    if computed_hash != RAW_DATA_SHA256:
        raise ValueError(
            f"Source file hash mismatch! Expected: {RAW_DATA_SHA256}, Got: {computed_hash}. "
            "Pipeline halted to preserve data provenance."
        )

    return computed_hash


def get_deployment_mode() -> str:
    """
    Detects whether the application is running in local development mode
    (with raw dataset access) or cloud production mode (sanitized artifacts only).
    """
    return "local" if RAW_DATA_PATH.exists() else "cloud"


def load_raw_data(
    file_path: Path = RAW_DATA_PATH, verify_hash: bool = True
) -> pd.DataFrame:
    """
    Loads the raw Nassau Candy distributor dataset in local mode.
    Preserves original columns, types, and raw values.
    """
    if verify_hash:
        verify_source_hash(file_path)

    dtype_spec = {
        "Row ID": "int64",
        "Order ID": "string",
        "Order Date": "string",
        "Ship Date": "string",
        "Ship Mode": "string",
        "Customer ID": "string",
        "Country/Region": "string",
        "City": "string",
        "State/Province": "string",
        "Postal Code": "string",
        "Division": "string",
        "Region": "string",
        "Product ID": "string",
        "Product Name": "string",
        "Sales": "float64",
        "Units": "int64",
        "Gross Profit": "float64",
        "Cost": "float64",
    }

    df = pd.read_csv(file_path, dtype=dtype_spec)
    return df


def load_prepared_artifacts() -> Dict[str, pd.DataFrame]:
    """
    Loads prepared Parquet artifacts for production dashboard consumption.
    Used in both cloud deployment and local fast-start.
    """
    artifacts: Dict[str, pd.DataFrame] = {}

    if CLEAN_ORDERS_PARQUET.exists():
        artifacts["clean_orders"] = pd.read_parquet(CLEAN_ORDERS_PARQUET)

    if ROUTE_AGGREGATES_PARQUET.exists():
        artifacts["route_aggregates"] = pd.read_parquet(ROUTE_AGGREGATES_PARQUET)

    if BASELINE_PARQUET.exists():
        artifacts["baseline"] = pd.read_parquet(BASELINE_PARQUET)

    if DISTANCE_PARQUET.exists():
        artifacts["distance_sensitive"] = pd.read_parquet(DISTANCE_PARQUET)

    if STRESS_PARQUET.exists():
        artifacts["stress_test"] = pd.read_parquet(STRESS_PARQUET)

    if not artifacts:
        raise FileNotFoundError(
            "No prepared Parquet artifacts found. Run `python scripts/build_data.py` "
            "to generate clean and synthetic artifacts before starting the application."
        )

    return artifacts


def load_metadata() -> Dict:
    """Loads metadata.json if available."""
    if METADATA_JSON.exists():
        with open(METADATA_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_transformation_log() -> Dict:
    """Loads transformation_log.json if available."""
    if TRANSFORMATION_LOG_JSON.exists():
        with open(TRANSFORMATION_LOG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
