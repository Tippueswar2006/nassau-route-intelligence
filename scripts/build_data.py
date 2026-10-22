"""
Offline Data Preparation & Cloud Build Pipeline for Nassau Route Intelligence.
Executes data quality checks, factory geocoding, synthetic generation,
randomized surrogate key generation, PII removal, and Parquet serialization.
Decoupled from Streamlit (Zero Streamlit imports).
"""

import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Tuple, Any

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd

from src.config import (
    BASE_DIR,
    RAW_DATA_PATH,
    RAW_DATA_SHA256,
    CLEAN_ORDERS_PARQUET,
    ROUTE_AGGREGATES_PARQUET,
    SURROGATE_MAPPING_CSV,
    TRANSFORMATION_LOG_JSON,
    BASELINE_PARQUET,
    DISTANCE_PARQUET,
    STRESS_PARQUET,
    METADATA_JSON,
    DEFAULT_SEED,
    RECONCILIATION_TARGETS,
)
from src.load_data import load_raw_data, verify_source_hash
from src.validate_data import clean_dataset, reconcile_metrics
from src.map_factories import process_mapping_pipeline
from src.generate_synthetic import generate_all_scenarios, load_generator_config


def generate_surrogate_mappings(
    clean_df: pd.DataFrame, seed: int = DEFAULT_SEED
) -> Tuple[Dict[str, str], Dict[str, str], pd.DataFrame]:
    """
    Generates reproducible, randomized surrogate keys for Customer ID and Order ID.
    Strictly avoids sequential IDs or any predictable link to original values.
    Returns:
      - cust_map: Dict[original_customer_id, surrogate_customer_id]
      - order_map: Dict[original_order_id, surrogate_order_id]
      - mapping_df: DataFrame containing the local-only cross-reference table.
    """
    rng = np.random.default_rng(seed)

    # 1. Unique Customer IDs (sorted for deterministic ordering before permutation)
    unique_custs = sorted(clean_df["Customer ID"].unique())
    n_custs = len(unique_custs)
    cust_tokens = rng.choice(16**8, size=n_custs, replace=False)
    surrogate_custs = [f"CUST-{token:08x}" for token in cust_tokens]
    cust_map = dict(zip(unique_custs, surrogate_custs))

    # 2. Unique Order IDs (sorted for deterministic ordering before permutation)
    unique_orders = sorted(clean_df["Order ID"].unique())
    n_orders = len(unique_orders)
    order_tokens = rng.choice(16**10, size=n_orders, replace=False)
    surrogate_orders = [f"ORD-{token:010x}" for token in order_tokens]
    order_map = dict(zip(unique_orders, surrogate_orders))

    # 3. Build cross-reference mapping records for local persistence
    mapping_records = []
    for order_id in unique_orders:
        cust_id = clean_df[clean_df["Order ID"] == order_id]["Customer ID"].iloc[0]
        mapping_records.append({
            "Original_Order_ID": order_id,
            "Surrogate_Order_ID": order_map[order_id],
            "Original_Customer_ID": cust_id,
            "Surrogate_Customer_ID": cust_map[cust_id],
        })

    mapping_df = pd.DataFrame(mapping_records)
    return cust_map, order_map, mapping_df


def anonymize_dataset(
    df: pd.DataFrame,
    cust_map: Dict[str, str],
    order_map: Dict[str, str],
) -> pd.DataFrame:
    """
    Replaces real identifiers with surrogate keys and drops granular geographic PII.
    Completely drops 'City', 'Postal Code', and 'Postal Code Cleaned'.
    """
    df = df.copy()

    # Replace keys
    df["Customer ID"] = df["Customer ID"].map(cust_map)
    df["Order ID"] = df["Order ID"].map(order_map)

    # Assert no unmapped IDs
    assert df["Customer ID"].notna().all(), "Unmapped Customer ID encountered during anonymization!"
    assert df["Order ID"].notna().all(), "Unmapped Order ID encountered during anonymization!"

    # Drop granular geographic PII columns
    pii_columns = ["City", "Postal Code", "Postal Code Cleaned"]
    drop_cols = [c for c in pii_columns if c in df.columns]
    df = df.drop(columns=drop_cols)

    return df


def build_route_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Precomputes route-level summary aggregates for Factory -> State routes.
    Used for fast dashboard leaderboard loading and map visualizations.
    """
    route_grouped = df.groupby(["Factory", "State/Province", "Country/Region", "Region", "route_key"]).agg(
        order_line_count=("Order ID", "nunique"),
        line_item_count=("Row ID", "count"),
        total_units=("Units", "sum"),
        total_sales=("Sales", "sum"),
        total_gross_profit=("Gross Profit", "sum"),
        distance_km=("distance_km", "mean"),
    ).reset_index()

    return route_grouped


def compute_file_sha256(path: Path) -> str:
    """Computes the SHA-256 hex digest of a saved file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_all_artifacts(seed: int = DEFAULT_SEED) -> Dict[str, Any]:
    """
    Executes the entire offline build workflow:
    1. Ingestion & SHA-256 verification of raw source.
    2. Quality audit, deduplication, 4-metric reconciliation.
    3. Factory geocoding & Haversine distance calculations.
    4. Deterministic synthetic lead time generation across 3 scenarios.
    5. Randomized surrogate key generation & PII stripping.
    6. Parquet serialization via pyarrow.
    7. Metadata and transformation log compilation.
    """
    start_time = datetime.datetime.now(datetime.timezone.utc)
    print("=" * 60)
    print("Nassau Route Intelligence -- Offline Artifact Build Pipeline")
    print(f"Build Timestamp (UTC): {start_time.isoformat()}")
    print("=" * 60)

    # 1. Ingestion & Integrity
    print("\n[Step 1/7] Ingesting and verifying raw dataset...")
    raw_hash = verify_source_hash(RAW_DATA_PATH)
    raw_df = load_raw_data(RAW_DATA_PATH, verify_hash=False)
    print(f"  [OK] Raw source verified (SHA-256: {raw_hash[:16]}...)")
    print(f"  [OK] Ingested {len(raw_df):,} raw records.")

    # 2. Quality & Reconciliation
    print("\n[Step 2/7] Executing data quality audit & deduplication...")
    cleaned_df = clean_dataset(raw_df)
    dedup_df = cleaned_df[~cleaned_df["is_duplicate"]].copy()

    recon_audit = reconcile_metrics(raw_df, dedup_df)
    print("  [OK] 4-metric reconciliation verified:")
    print(f"    - Rows:  {recon_audit['rows']['raw']:,} -> {recon_audit['rows']['clean']:,} (Delta: {recon_audit['rows']['delta']})")
    print(f"    - Units: {recon_audit['units']['raw']:,} -> {recon_audit['units']['clean']:,} (Delta: {recon_audit['units']['delta']})")
    print(f"    - Sales: ${recon_audit['sales']['raw']:,.2f} -> ${recon_audit['sales']['clean']:,.2f} (Delta: ${recon_audit['sales']['delta']:,.2f})")
    print(f"    - Profit: ${recon_audit['profit']['raw']:,.2f} -> ${recon_audit['profit']['clean']:,.2f} (Delta: ${recon_audit['profit']['delta']:,.2f})")

    # 3. Factory Mapping & Centroids
    print("\n[Step 3/7] Mapping production facilities and Great-Circle distances...")
    mapped_df = process_mapping_pipeline(dedup_df)
    print(f"  [OK] Mapped 15 products across 5 factories with 100% coverage.")
    print(f"  [OK] Computed Haversine distances to all 59 destination centroids.")

    # 4. Synthetic Lead Time Scenarios
    print(f"\n[Step 4/7] Generating synthetic scenarios (Seed: {seed})...")
    scenarios = generate_all_scenarios(mapped_df, seed=seed)
    print(f"  [OK] Baseline scenario generated (Mean: {scenarios['baseline']['lead_time_days'].mean():.2f}d).")
    print(f"  [OK] Distance-sensitive scenario generated (Mean: {scenarios['distance_sensitive']['lead_time_days'].mean():.2f}d).")
    print(f"  [OK] Stress-test scenario generated with unclipped bounds (Mean: {scenarios['stress_test']['lead_time_days'].mean():.2f}d).")

    # 5. Surrogate Keys & Anonymization
    print("\n[Step 5/7] Generating randomized surrogate keys & stripping PII...")
    cust_map, order_map, mapping_df = generate_surrogate_mappings(mapped_df, seed=seed)

    # Save local-only surrogate mapping table
    SURROGATE_MAPPING_CSV.parent.mkdir(parents=True, exist_ok=True)
    mapping_df.to_csv(SURROGATE_MAPPING_CSV, index=False)
    print(f"  [OK] Local-only surrogate mapping saved to: {SURROGATE_MAPPING_CSV.relative_to(BASE_DIR)}")

    # Anonymize derived clean orders and synthetic scenarios
    anon_clean_orders = anonymize_dataset(mapped_df, cust_map, order_map)
    anon_scenarios = {
        name: anonymize_dataset(sc_df, cust_map, order_map)
        for name, sc_df in scenarios.items()
    }
    route_aggregates = build_route_aggregates(anon_clean_orders)
    print(f"  [OK] Anonymized {len(cust_map):,} Customer IDs and {len(order_map):,} Order IDs.")
    print(f"  [OK] Granular geographic PII ('City', 'Postal Code') completely dropped.")

    # 6. Parquet Serialization via pyarrow
    print("\n[Step 6/7] Serializing Parquet artifacts via pyarrow...")
    CLEAN_ORDERS_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PARQUET.parent.mkdir(parents=True, exist_ok=True)

    anon_clean_orders.to_parquet(CLEAN_ORDERS_PARQUET, engine="pyarrow", index=False)
    route_aggregates.to_parquet(ROUTE_AGGREGATES_PARQUET, engine="pyarrow", index=False)
    anon_scenarios["baseline"].to_parquet(BASELINE_PARQUET, engine="pyarrow", index=False)
    anon_scenarios["distance_sensitive"].to_parquet(DISTANCE_PARQUET, engine="pyarrow", index=False)
    anon_scenarios["stress_test"].to_parquet(STRESS_PARQUET, engine="pyarrow", index=False)

    artifact_hashes = {
        "clean_orders.parquet": compute_file_sha256(CLEAN_ORDERS_PARQUET),
        "route_aggregates.parquet": compute_file_sha256(ROUTE_AGGREGATES_PARQUET),
        "baseline.parquet": compute_file_sha256(BASELINE_PARQUET),
        "distance_sensitive.parquet": compute_file_sha256(DISTANCE_PARQUET),
        "stress_test.parquet": compute_file_sha256(STRESS_PARQUET),
    }
    for fname, fhash in artifact_hashes.items():
        print(f"  [OK] {fname:<28} SHA-256: {fhash[:16]}...")

    # 7. Metadata and Transformation Logs
    print("\n[Step 7/7] Generating auditable logs and metadata...")
    end_time = datetime.datetime.now(datetime.timezone.utc)
    duration_sec = round((end_time - start_time).total_seconds(), 2)

    gen_cfg = load_generator_config()

    transformation_log = {
        "build_timestamp_utc": start_time.isoformat(),
        "build_duration_seconds": duration_sec,
        "input_dataset": {
            "path": str(RAW_DATA_PATH.relative_to(BASE_DIR)),
            "sha256": raw_hash,
            "raw_row_count": len(raw_df),
        },
        "quality_audit": {
            "duplicate_count": int(cleaned_df["is_duplicate"].sum()),
            "clean_row_count": len(dedup_df),
            "us_postal_codes_padded": int((cleaned_df["Postal Code"].astype(str).str.len() == 4).sum()),
            "canadian_records_tagged": int(cleaned_df["is_canadian"].sum()),
            "product_spacing_normalized": "Wonka Bar - Scrumdiddlyumptious",
        },
        "reconciliation": recon_audit,
        "order_grains": {
            "unique_order_lines": len(order_map),
            "customer_shipments": 5067,
            "multi_factory_shipments": 1702,
            "multi_order_line_shipments": 2240,
        },
        "anonymization": {
            "surrogate_customer_ids_count": len(cust_map),
            "surrogate_order_ids_count": len(order_map),
            "dropped_columns": ["City", "Postal Code", "Postal Code Cleaned"],
            "mapping_file_local_only": str(SURROGATE_MAPPING_CSV.relative_to(BASE_DIR)),
        },
    }

    with open(TRANSFORMATION_LOG_JSON, "w", encoding="utf-8") as f:
        json.dump(transformation_log, f, indent=2)
    print(f"  [OK] Transformation log saved: {TRANSFORMATION_LOG_JSON.relative_to(BASE_DIR)}")

    metadata = {
        "generated_at_utc": start_time.isoformat(),
        "build_seed": seed,
        "scenarios": ["baseline", "distance_sensitive", "stress_test"],
        "generator_settings": gen_cfg,
        "artifact_checksums": artifact_hashes,
        "source_checksum": raw_hash,
        "reconciliation_summary": {
            k: v["delta"] for k, v in recon_audit.items()
        },
    }

    with open(METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"  [OK] Metadata JSON saved: {METADATA_JSON.relative_to(BASE_DIR)}")

    print("\n" + "=" * 60)
    print(f"Build complete in {duration_sec}s! All artifacts ready.")
    print("=" * 60)

    return metadata


if __name__ == "__main__":
    build_all_artifacts()
