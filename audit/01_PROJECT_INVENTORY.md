# Phase 1: Project Inventory and Structural Discovery

**Project:** Nassau Candy Shipping Route Intelligence  
**Audit Date:** 2026-10-25  
**Auditor:** Antigravity Senior Engineering & QA Lead  
**Audit Target Directory:** `C:\Users\preet\OneDrive\Desktop\factory`  

---

## 1. Project Purpose

The **Nassau Candy Shipping Route Intelligence** system is an enterprise logistics analytics, decision-support, and simulation platform designed to evaluate shipping corridor performance, screen for distribution bottlenecks, and perform multi-scenario stress testing across North American confectionery supply chains.

The platform was built to address critical data anomalies and operational questions in confectionary distribution:
1. **Raw Date Interval Anomaly:** In the raw historical dataset (`10,194` records), the interval between `Order Date` and `Ship Date` ranges anomalously from 904 to 1,642 days with zero records under 30 days. The platform documents this as an export transformation anomaly rather than carrier performance, quarantining raw diagnostic dates and deploying an offline-generated, empirically calibrated synthetic timing simulation layer.
2. **Corridor Efficiency Scoring (RES):** Balances normalized speed ($70\%$) against lead-time variability ($30\%$) normalized against invariant shipping-mode benchmarks.
3. **Distribution Bottleneck Screening:** Applies dual 75th-percentile screening criteria ($P_{75}$ Volume & $P_{75}$ Delay Rate) with statistical sample-size guardrails ($N \ge 30$) to isolate high-impact commercial lanes from stochastic low-volume noise.
4. **Stress Testing & Research Pipeline:** Evaluates supply chain resilience under holiday surge disruptions ($+1.0\text{d}$ in Nov/Dec), regional metropolitan congestion ($+1.0\text{d}$ in CA/NY), and specific lane failures ($+1.5\text{d}$ on Texas routes). In addition, it provides a publication pipeline generating 300 DPI vector and raster figures for academic reporting.

---

## 2. Detected Technology Stack

| Layer / Concern | Technology / Tool | Version / Spec Detected | Verification Status |
|---|---|---|---|
| **Programming Language** | Python | `3.10.11` (x64 Windows) | Confirmed via runtime execution |
| **Data Processing & Analytics** | Pandas, NumPy | Pandas `2.3.3`, NumPy `2.2.6` | Confirmed via `importlib.metadata` |
| **Columnar Storage Engine** | Apache Parquet (pyarrow) | PyArrow `25.0.1` | Confirmed via `importlib.metadata` |
| **Interactive UI / Dashboard** | Streamlit | `1.65.0` | Confirmed via `importlib.metadata` |
| **Interactive Visualizations** | Plotly | `7.1.0` | Confirmed via `importlib.metadata` |
| **Publication Graphics** | Matplotlib, Seaborn | Matplotlib `3.10.9`, Seaborn `0.13.2` | Confirmed via `importlib.metadata` |
| **Configuration Parsing** | PyYAML | `6.0.3` | Confirmed via `importlib.metadata` |
| **Test Runner & Harness** | Pytest, Streamlit AppTest | Pytest `9.1.1` | Confirmed via pytest execution |
| **Web Server / Gateway** | Uvicorn, Starlette | Uvicorn `0.54.0`, Starlette `1.7.0` | Confirmed via Streamlit runtime |
| **VCS / Configuration Management**| Git | Branch: `main`, Commit clean | Confirmed via `git status` |

---

## 3. Project Architecture

The application adopts an **offline-prepared, auditable data pipeline** cleanly decoupled from an **interactive presentation dashboard**:

```
+--------------------------------------------------------------------------------------------------+
|                            OFFLINE PREPARATION & SIMULATION PIPELINE                             |
|                                     (scripts/build_data.py)                                      |
+--------------------------------------------------------------------------------------------------+
          |                                  |                                   |
          v                                  v                                   v
 [data/original/nassau_candy.csv]  [src/validate_data.py]              [src/map_factories.py]
  - SHA-256 Verified                - Flag 313 Exact Duplicates         - 15 Products -> 5 Factories
  - Immutable Source                - 4-Metric Reconciliation           - Centroid Haversine Distances
                                    - Postal Code Zero-Padding
                                             |
                                             v
                              [src/generate_synthetic.py]
                               - 5,067 Customer Shipments
                               - Seed 42 Empirical Simulation
                               - Baseline, Distance, Stress Scenarios
                               - Randomized Surrogate Key Anonymization
                                             |
                                             v
+--------------------------------------------------------------------------------------------------+
|                                  SERIALIZED PARQUET ARTIFACTS                                    |
|              data/derived/clean_orders.parquet, route_aggregates.parquet, metadata.json          |
|              data/synthetic/baseline.parquet, distance_sensitive.parquet, stress_test.parquet    |
+--------------------------------------------------------------------------------------------------+
                                             |
                                             v
+--------------------------------------------------------------------------------------------------+
|                                STREAMLIT APPLICATION RUNTIME                                     |
|                         app.py (Global State & @st.cache_data Loader)                            |
+--------------------------------------------------------------------------------------------------+
                                             |
       +-------------------------------------+-------------------------------------+
       |                                     |                                     |
       v                                     v                                     v
[src/metrics.py]                   [src/route_analysis.py]               [src/bottleneck_rules.py]
 - Pre-computed Mode Means          - N >= 30 Guardrails                  - Dual 75th %ile Screening
 - Mode-Adjusted RES (70/30)        - Top 10 / Bottom 10                  - Critical & Watchlist
 - Strict Delay Boundary (> 5d)     - Regional Rollups
       |                                     |                                     |
       +-------------------------------------+-------------------------------------+
                                             |
                                             v
+--------------------------------------------------------------------------------------------------+
|                              MULTI-PAGE PRESENTATION LAYER (pages/)                              |
|  1_Executive_Overview.py       2_Data_Quality_and_Method.py       3_Route_Efficiency.py          |
|  4_Geographic_Analysis.py      5_Ship_Mode_Comparison.py         6_Potential_Bottlenecks.py     |
|  7_Route_Drill_Down.py         8_Trends_and_Scenarios.py                                         |
+--------------------------------------------------------------------------------------------------+
                                             |
                                             v
+--------------------------------------------------------------------------------------------------+
|                                    AUDITED EXPORTS & REPORTS                                     |
|  src/exports.py (CSV + Provenance Headers)      docs/figures/ (300 DPI Camera-Ready Figures)     |
+--------------------------------------------------------------------------------------------------+
```

### Key Architectural Tenets:
1. **Decoupled Business Logic (AD-12):** All data transformations, metrics, geospatial distances, and statistical algorithms are strictly contained in `src/` with **zero imports of Streamlit**. This guarantees headless testability and CLI automation.
2. **Strict Layer Separation (AD-02):** Every dataframe and visual component is explicitly partitioned into one of three layers: `ORIGINAL` (source records), `DERIVED` (cleaned/mapped without timing alterations), or `SYNTHETIC` (calibrated simulation). Cross-layer mingling in leaderboards is structurally prohibited.
3. **Source Immutability (AD-01):** Raw input files are read-only and verified via SHA-256 (`6ae9208e...`). In-place mutation is disallowed.
4. **Zero-PII Cloud Architecture (AD-08):** Granular geographic identifiers (`City`, `Postal Code`) are excised from public cloud artifacts. Account and order identifiers are mapped to cryptographically randomized surrogate tokens (`CUST-xxxxxxxx`, `ORD-xxxxxxxxxx`). The mapping file (`surrogate_key_mapping.csv`) is excluded from version control.

---

## 4. Important Directories and Files

| Directory / File | Type | Purpose / Description |
|---|---|---|
| `app.py` | Python Script | Streamlit application entrypoint, sidebar filter controller, and caching coordinator. |
| `config/factories.csv` | CSV Config | 5 factory manufacturing sites, postal codes, and geocoordinates. |
| `config/product_factory.csv` | CSV Config | Deterministic SKU-to-factory mapping rules (15 products to 5 facilities). |
| `config/geographic_centroids.csv` | CSV Config | Centroid coordinates for all 50 US States, DC, and 9 Canadian provinces. |
| `config/generator.yaml` | YAML Config | Empirical discrete probability distributions per mode, distance parameters, and target injection lanes. |
| `data/original/nassau_candy.csv` | CSV Data | Raw immutable historical source data (10,194 records, SHA-256 verified). |
| `data/derived/` | Parquet / JSON | Cleaned, mapped dataset (`clean_orders.parquet`), route aggregates, transformation log. |
| `data/synthetic/` | Parquet / JSON | Baseline, distance-sensitive, and stress-test synthetic datasets; scenario checksum metadata. |
| `docs/` | Markdown Docs | Technical architecture specification, PRD v1.3, data dictionary, methodology, synthetic assumptions, and audit reports. |
| `docs/figures/` | Graphics (PDF/PNG)| 300 DPI publication-grade figures generated by automation script. |
| `pages/` | Streamlit Pages | 8 multi-page analytical dashboard modules (Overview, Quality, RES, Map, Modes, Bottlenecks, Drill-down, Scenarios). |
| `scripts/build_data.py` | CLI Script | Offline data transformation, validation, reconciliation, simulation, and Parquet serialization engine. |
| `scripts/generate_paper_figures.py`| CLI Script | Standalone Matplotlib/Seaborn publication figure generation engine. |
| `scripts/validate_release_gates.py` | CLI Script | Automated 5-gate pre-deployment audit engine enforcing zero-PII, test pass rates, and doc completeness. |
| `src/` | Python Package | Core headless business logic (config, data loading, validation, geocoding, metrics, routes, bottlenecks, sensitivity, exports). |
| `tests/` | Pytest Suite | 22 test modules containing 167 automated unit, integration, invariant, and UI AppTest checks. |
| `pytest.ini` | Test Config | Pytest path and filter configuration. |
| `requirements.txt` | Dependency File| Production dependencies pinned for cloud deployment. |

---

## 5. Application Entry Points

1. **Interactive Web Application:**
   ```bash
   streamlit run app.py
   ```
2. **Offline Data Pipeline Build:**
   ```bash
   python scripts/build_data.py
   ```
3. **Automated Test Suite:**
   ```bash
   pytest
   ```
4. **Pre-Deployment Release Gate Audit:**
   ```bash
   python scripts/validate_release_gates.py
   ```
5. **Academic Figure Generation:**
   ```bash
   python scripts/generate_paper_figures.py
   ```

---

## 6. Frontend and Backend Structure

- **Frontend:** Streamlit multi-page interface (`pages/1_Executive_Overview.py` through `pages/8_Trends_and_Scenarios.py`), utilizing Plotly interactive charts (choropleth maps, scatter quadrants, monthly trendlines, distribution histograms) and native Streamlit metric cards and dataframes. Global filters in `app.py` manage Layer selection, Scenario, Facility multi-select, Region/State filters, Ship Mode filters, and Delay Threshold sliders.
- **Backend:** Decoupled pure Python service modules inside `src/`:
  - `src/load_data.py`: Dual-mode artifact loader (local raw vs cloud Parquet).
  - `src/validate_data.py`: Exact 4-metric reconciliation and duplicate detection.
  - `src/map_factories.py`: SKU joins and spherical Haversine distance calculations.
  - `src/generate_synthetic.py`: Seeded stochastic simulation engine.
  - `src/metrics.py`: Invariant mode-adjusted RES scoring and strict delay evaluations.
  - `src/route_analysis.py`: Grouping, guardrails ($N \ge 30$), and leaderboard ranking.
  - `src/bottleneck_rules.py`: Quadrant classification ($P_{75}$ Volume $\times$ $P_{75}$ Delay).
  - `src/sensitivity.py`: Spearman rank correlation and 5-seed stability validation.
  - `src/exports.py`: Audited CSV serialization with provenance metadata headers.

---

## 7. Database Technology and Schema

- **Storage Engine:** Embedded columnar file storage using Apache Parquet (Snappy compression via PyArrow). No external SQL or NoSQL database server is required.
- **Data Layers & Table Schemas:**
  1. **Raw Source (`data/original/nassau_candy.csv`):** 10,194 rows, 18 columns (`Row ID`, `Order ID`, `Order Date`, `Ship Date`, `Ship Mode`, `Customer ID`, `Country/Region`, `City`, `State/Province`, `Postal Code`, `Division`, `Region`, `Product ID`, `Product Name`, `Sales`, `Units`, `Gross Profit`, `Cost`).
  2. **Derived Clean Orders (`data/derived/clean_orders.parquet`):** 9,881 unique rows, 30 columns. Includes attached `Factory`, factory geocoordinates, destination centroids, Haversine `distance_km`, normalized product names, padded postal codes, and randomized surrogate keys (`CUST-xxxxxxxx`, `ORD-xxxxxxxxxx`).
  3. **Route Aggregates (`data/derived/route_aggregates.parquet`):** 196 active shipping corridors (`Factory` $\rightarrow$ `State/Province`), aggregating distinct order lines, line items, units, sales, profit, and mean distance.
  4. **Synthetic Scenarios (`baseline.parquet`, `distance_sensitive.parquet`, `stress_test.parquet`):** 9,881 rows, 36 columns. Includes synthetic `Ship_Date_Synthetic`, generated `lead_time_days`, `lead_time_mode_adjusted`, delay flags, and scenario descriptors.

---

## 8. External Services and Integrations

- **External Database:** None required. System is self-contained.
- **Cloud Infrastructure:** Configured for **Streamlit Community Cloud** (zero-PII, headless startup, git-ignored local credentials and raw datasets).
- **Network Calls:** None at runtime. Map visualizations use offline Plotly GeoJSON / state coordinate configurations.

---

## 9. Existing Test Infrastructure

- **Runner:** `pytest 9.1.1` configured via `pytest.ini`.
- **Test Modules:** 22 automated test files in `tests/`.
- **Test Categories:**
  - Architecture decoupling: `test_architecture.py`
  - Invariant reconciliation and data quality: `test_data_quality.py`
  - Product-to-factory mapping: `test_mapping.py`
  - Synthetic simulation calibration and bounds: `test_synthetic.py`
  - RES mathematical formulations: `test_metrics.py`
  - Route guardrails and aggregations: `test_route_analysis.py`
  - Bottleneck quadrant recovery across 5 seeds: `test_bottlenecks.py`
  - Privacy and surrogate key anonymization: `test_privacy.py`
  - UI page rendering via Streamlit `AppTest`: `test_app.py`, `test_page_*.py` (8 modules)
  - Parameter sensitivity and Spearman rank tests: `test_sensitivity.py`
  - Documentation suite and metadata verification: `test_documentation.py`
  - CSV export headers and provenance: `test_exports.py`
  - Pre-deployment release gates: `test_release_gates.py`

---

## 10. Build and Execution Commands

| Target Action | CLI Command |
|---|---|
| Run all automated tests | `pytest` |
| Run release gate verification | `python scripts/validate_release_gates.py` |
| Fast release gate dry-run | `python scripts/validate_release_gates.py --skip-tests` |
| Re-build derived and synthetic artifacts | `python scripts/build_data.py` |
| Generate publication figures | `python scripts/generate_paper_figures.py` |
| Launch Streamlit dashboard | `streamlit run app.py` |
| Launch headless verification | `streamlit run app.py --server.headless true --server.enableCORS false` |

---

## 11. Missing Configuration or Setup Gaps

- **Virtual Environment (`.venv`):** Python 3.10.11 virtual environment is functional with all runtime dependencies installed. However, `pip` is not installed inside the virtual environment (`python -m pip` returns `No module named pip`), though all required wheels are already placed in `site-packages`.
- **Environment Variables:** No `.env` or external secret configurations are required, as the project intentionally maintains zero external cloud service dependencies.

---

## 12. Initial Observations and Potential Risks

1. **Test Suite Duration:** Pytest execution runs 167 tests in ~157 seconds. Streamlit `AppTest` suites execute simulated page rendering in memory, which contributes to runtime duration.
2. **Reconstruction Isolation:** The PRD mandates strict quarantine of the reconstructed diagnostic lead times (0–11 days) to Page 2 only. Verification is required to ensure no diagnostic lead time leaks into Pages 3–8.
3. **Strict Delay Rule:** PRD and Architecture specify strict inequality `lead_time > threshold` (not `>=`). Must verify this invariant holds across all filtering routines.
4. **Zero-PII Compliance:** Source files in `data/original/` and `data/derived/surrogate_key_mapping.csv` must be strictly git-ignored before any deployment.
