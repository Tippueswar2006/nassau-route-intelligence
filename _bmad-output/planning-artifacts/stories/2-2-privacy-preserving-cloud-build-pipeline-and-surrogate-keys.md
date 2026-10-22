---
title: 'Story 2.2: Privacy-Preserving Cloud Build Pipeline & Surrogate Key Generation'
type: 'feature'
created: '10-20-2026'
status: 'done'
baseline_commit: 'NO_VCS'
epic: 2
story: 2
story_key: '2-2-privacy-preserving-cloud-build-pipeline-and-surrogate-keys'
context:
  - 'src/config.py'
  - 'src/load_data.py'
  - 'src/validate_data.py'
  - 'src/map_factories.py'
  - 'src/generate_synthetic.py'
---

# Story 2.2: Privacy-Preserving Cloud Build Pipeline & Surrogate Key Generation

## Intent
**Problem:** Raw customer identifiers and granular geographic codes must never be committed to GitHub or deployed to Streamlit Community Cloud.
**Approach:** Implement `scripts/build_data.py` to orchestrate offline data preparation, generate randomized surrogate keys for Customer ID and Order ID, drop `City` and `Postal Code`, write local-only mapping, and serialize Parquet artifacts with metadata.

## User Story
As a cloud security engineer,
I want an offline data build script `scripts/build_data.py` that replaces Customer IDs and Order IDs with randomized surrogate keys, drops granular PII, and outputs optimized Parquet artifacts,
So that the application can be deployed to public cloud without exposing real customer identifiers or raw data.

## Acceptance Criteria
- **Given** the raw dataset and generated synthetic datasets,
- **When** `scripts/build_data.py` executes,
- **Then** `Customer ID` and `Order ID` are replaced with randomized surrogate keys reproducible per build seed,
- **And** the original-to-surrogate mapping is written strictly to local-only `data/derived/surrogate_key_mapping.csv` and never committed or deployed,
- **And** `City` and `Postal Code` are completely dropped from cloud artifacts,
- **And** `data/derived/clean_orders.parquet`, `data/derived/route_aggregates.parquet`, `data/synthetic/baseline.parquet`, `data/synthetic/distance_sensitive.parquet`, and `data/synthetic/stress_test.parquet` are serialized via pyarrow,
- **And** `data/derived/transformation_log.json` and `data/synthetic/metadata.json` are generated documenting build timestamp, seed 42, scenario hashes, and 4-metric reconciliation.

## Implementation Details & Boundaries
- Script path: `scripts/build_data.py`
- Functions:
  - `generate_surrogate_keys(df: pd.DataFrame, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]`
  - `anonymize_cloud_artifacts(df: pd.DataFrame) -> pd.DataFrame`
  - `precompute_route_aggregates(df: pd.DataFrame) -> pd.DataFrame`
  - `save_parquet_artifacts(...)`
  - `generate_metadata_and_logs(...)`
