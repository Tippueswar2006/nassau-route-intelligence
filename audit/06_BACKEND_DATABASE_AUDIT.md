# Phase 6: Backend, API, and Database Audit

**Project:** Nassau Candy Shipping Route Intelligence  
**Audit Date:** 2026-10-25  
**Auditor:** Antigravity Senior Engineering & QA Lead  
**Architecture:** Headless Python Service Architecture (`src/`) with Apache Parquet Columnar Storage  

---

## 1. Backend Service Layer & Architecture

The application adopts a decoupled headless service architecture. All business logic, mathematical modeling, and geospatial operations reside in pure Python modules under `src/`, with strict static separation from presentation libraries (verified by AST test `test_zero_streamlit_in_src`).

### Key Modules and Responsibilities:
1. **`src/load_data.py` (Ingestion & Schema Enforcement):**
   - Implements dual-mode loading: local mode reads and verifies raw source CSV; cloud mode operates strictly from sanitized Parquet tables.
   - Enforces SHA-256 integrity verification (`verify_source_hash`).
   - Applies strict data type casting (`Row ID`: int64, `Order ID`: string, `Units`: int64, `Sales`/`Gross Profit`/`Cost`: float64).
2. **`src/validate_data.py` (Quality & Reconciliation Engine):**
   - Implements `flag_duplicates`: Identifies exact duplicates across all business fields excluding `Row ID`.
   - Implements `reconcile_metrics`: Enforces non-negotiable 4-metric reconciliation (Rows, Units, Sales, Gross Profit).
   - Implements `clean_geographic_fields`: Padds 4-digit US postal codes with leading `0` and flags international Canadian rows.
   - Implements `compute_diagnostic_reconstruction`: Quarantined date floor subtraction by Order-ID year.
3. **`src/map_factories.py` (Geospatial & Relational Join Engine):**
   - Relational resolution: Performs inner join from 15 product lines to 5 manufacturing facilities via `config/product_factory.csv`. Asserts 100% match rate.
   - Computes spherical great-circle distances via Haversine formula from facility coordinates to 59 destination state and Canadian province centroids (`config/geographic_centroids.csv`).
4. **`src/generate_synthetic.py` (Simulation Engine):**
   - Groups line items into 5,067 customer shipments (`Customer ID` + `Order Date` + `Ship Mode`).
   - Simulates empirical lead times across 3 scenarios (Baseline, Distance-Sensitive, Stress-Test) using deterministic seed 42.
5. **`src/metrics.py` (Scoring & Algorithmic Modeling):**
   - Pre-computes invariant ship-mode reference means prior to downstream filtering.
   - Evaluates strict delay inequality ($\text{lead\_time} > \text{threshold}$).
   - Computes Route Efficiency Score (RES) via min-max penalty normalization:
     $$\text{RES} = 100 \times [1 - (0.70 \times \text{SpeedPenalty} + 0.30 \times \text{VariabilityPenalty})]$$
6. **`src/route_analysis.py` (Aggregation & Filtering Engine):**
   - Groups order lines by Factory $\rightarrow$ State and Factory $\rightarrow$ Region.
   - Enforces statistical guardrail ($N \ge 30$) before ranking.
7. **`src/bottleneck_rules.py` (Quadrant Screening):**
   - Classifies routes into 4 quadrants based on dual 75th-percentile volume and delay thresholds.
8. **`src/exports.py` (Provenance Serializer):**
   - Generates CSV exports with prepended metadata headers documenting data layer, active filters, and run timestamp.

---

## 2. Data Storage, Schema, and Integrity Audit

### Storage Standard
The persistence layer utilizes **Apache Parquet (pyarrow engine)** with Snappy compression for production artifacts. The original raw dataset is preserved as read-only CSV.

| Storage Artifact | Format | Row Count | Column Count | File Size | SHA-256 Checksum Verified |
|---|---|---|---|---|---|
| `data/original/nassau_candy.csv` | CSV | 10,194 | 18 | 1,440.6 KB | `6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f` |
| `data/derived/clean_orders.parquet` | Parquet | 9,881 | 30 | 395.4 KB | `a86aaf0dd53c70e176fa1c0c17a8698a287959dc3c47313a48e77c525166f2b7` |
| `data/derived/route_aggregates.parquet` | Parquet | 196 | 11 | 15.4 KB | `42f0f1d7f3297a003f5dbd9d8be8d58ff9029dbb71fa08846c7ceb10c9c71638` |
| `data/synthetic/baseline.parquet` | Parquet | 9,881 | 36 | 446.1 KB | `385b9a6a88efa940eaec1858a8a472c678a3c8fbfa72b53eb9d592a832e8bf5f` |
| `data/synthetic/distance_sensitive.parquet` | Parquet | 9,881 | 36 | 455.9 KB | `ab8e0ad7d794bbe05a30e84b80e816a76e9389280df05527a29e61c57223b207` |
| `data/synthetic/stress_test.parquet` | Parquet | 9,881 | 36 | 456.1 KB | `293b1f9c7a596252960686940a4cfc8d4ce7c10b806129188e401ec86208cb28` |

### Relational Integrity & Key Constraints:
1. **Primary Grains:**
   - Base Line Item: 10,194 raw rows $\rightarrow$ 9,881 unique rows.
   - Distinct Order Lines: 8,549 distinct `Order ID`s.
   - Customer Shipments: 5,067 consolidated dispatches.
2. **One-to-One Factory Invariant:** Every `Order ID` maps to exactly one factory by construction because the SKU is embedded in the Order ID. Confirmed by `test_order_line_single_factory_invariant` across all 8,549 distinct Order IDs.
3. **Foreign Key Integrity:** 15 of 15 products successfully resolve against `config/product_factory.csv`. Zero unmapped products exist.
4. **Distance Integrity:** All 196 active shipping corridors have valid, non-zero Haversine distances to destination state/province centroids. No missing distances are treated as zero.

---

## 3. Transaction Handling, Concurrency, and Error Handling

1. **Read-Only Concurrency:** The Streamlit runtime treats all Parquet datasets as read-only in-memory structures cached via `@st.cache_data`. Multi-user access operates without write-lock contention, deadlocks, or dirty reads.
2. **Defensive Invariant Assertions:**
   - Ingestion raises `ValueError` if the SHA-256 hash of the raw dataset does not match the approved constant.
   - `reconcile_metrics` asserts exact integer and float values matching `RECONCILIATION_TARGETS`; any divergence halts pipeline execution immediately.
   - Geocoding asserts that unmapped SKUs raise `AssertionError` rather than defaulting to null factories.
   - Scoring algorithms defensively check for empty datasets and zero standard deviations, preventing `ZeroDivisionError` or invalid array indexing.
3. **Data Mutation Isolation:** Pipeline regeneration in `scripts/build_data.py` writes to atomic Parquet files. Raw input files are opened strictly in binary read mode (`"rb"`).
