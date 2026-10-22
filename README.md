# Nassau Candy Shipping Route Intelligence

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42%2B-FF4B4B.svg)](https://streamlit.io/)
[![Pytest Suite](https://img.shields.io/badge/pytest-142%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Privacy Compliant](https://img.shields.io/badge/Privacy-Zero--PII%20Cloud--Ready-success.svg)](#cloud-deployment-guide)
[![Synthetic Disclosure](https://img.shields.io/badge/Simulation-Synthetic%20Calibrated-orange.svg)](#synthetic-data--privacy-architecture)

> **Synthetic Data Disclosure (AD-02):** All lead-time metrics and delivery dates are calibrated simulations generated from empirical distribution models. Raw historical source records feature an unverified transit interval anomaly (904–1,642 days) and must not be presented as verified carrier transit performance.
>
> **Zero-PII Compliance (AD-04):** Customer account IDs and order identifiers are irreversibly masked using cryptographic surrogate tokens (`CUST-xxxxxxxx`, `ORD-xxxxxxxxxx`). Granular postal codes and cities are omitted in cloud distributions.

---

## 1. Project Vision & Capabilities

**Nassau Route Intelligence** is an enterprise-grade logistics analytics and simulation platform designed to evaluate shipping corridor efficiency, detect operational bottlenecks, and perform multi-scenario stress testing across North American confectionary distribution networks.

Built on an **offline-prepared, auditable data pipeline** and a high-performance **interactive Streamlit analytical application**, the system transforms raw order-line transaction data into actionable supply chain intelligence.

### Core Capabilities:
- **Corridor Efficiency Scoring (RES):** Balances transit speed ($70\%$) with delivery variability ($30\%$) normalized against invariant carrier mode benchmarks.
- **Transparent Bottleneck Screening:** Flags high-risk distribution lanes using dual 75th-percentile screening criteria ($P_{75}$ Volume & $P_{75}$ Delay Rate) with sample-size guardrails ($N \ge 30$).
- **Multi-Scenario Stress Lab:** Simulates holiday demand surges (Nov/Dec $+1.0\text{d}$), regional metropolitan congestion (CA/NY $+1.0\text{d}$), and target route failures ($+1.5\text{d}$).
- **Interactive Multi-Page Analytics:** 8 dedicated analytical modules featuring US State choropleth maps, route drill-down timelines, and parameter sensitivity sliders.
- **Academic Publication Pipeline:** Generates 300 DPI, camera-ready vector/raster figures for technical reports and academic papers.

---

## 2. Key Research Questions Answered

1. **How does delivery unpredictability (variance) alter route efficiency rankings compared to pure speed?**
   - The Route Efficiency Score (RES) penalizes erratic delivery timelines. Comparing composite RES ($70/30$) against the speed-only baseline reveals corridors where high transit variance creates hidden operational risks despite acceptable average transit speeds.
2. **Which shipping corridors constitute systematic distribution bottlenecks versus low-volume noise?**
   - Applying the $N \ge 30$ sample size guardrail alongside dual $P_{75}$ thresholds cleanly isolates high-impact commercial corridors requiring carrier intervention from low-volume stochastic fluctuations.
3. **How resilient is the distribution network under compounding seasonal and regional disruptions?**
   - Controlled synthetic simulation demonstrates that compounding Q4 holiday surges and coastal hub delays increase national delay rates by over $28\%$ and depress mean corridor efficiency by $14.2$ points.
4. **What is the commercial margin contribution across expedited versus standard ground shipping tiers?**
   - Analysis confirms that expedited tiers (Same Day, First Class) deliver higher gross margin per unit while maintaining predictable transit timelines, whereas Standard Class accounts for $60.2\%$ of overall volume with wider transit variance.

---

## 3. Repository Architecture & Directory Tree

```
factory/
├── config/                                 # Configuration tables and generator settings
│   ├── factories.csv                       # 5 manufacturing facilities and coordinates
│   ├── product_factory.csv                 # 15 SKU-to-factory mapping rules
│   ├── geographic_centroids.csv            # US State and Canadian province centroids
│   └── generator.yaml                      # Synthetic generator parameters and distributions
├── data/
│   ├── original/                           # Source dataset (Read-only, SHA-256 verified)
│   │   └── nassau_candy.csv                # 10,194 raw records
│   ├── derived/                            # De-duplicated, reconciled Parquet tables
│   │   ├── clean_orders.parquet            # 9,881 unique order lines
│   │   ├── route_aggregates.parquet        # 196 corridor summaries
│   │   ├── surrogate_key_mapping.csv       # Local PII token mapping (Excluded from cloud)
│   │   └── transformation_log.json         # Build audit log and financial reconciliation
│   └── synthetic/                          # Calibrated simulation datasets
│       ├── baseline.parquet                # Empirical baseline scenario (Seed 42)
│       ├── distance_sensitive.parquet      # Haversine distance-adjusted scenario
│       ├── stress_test.parquet             # Compounding disruption scenario
│       └── metadata.json                   # Simulation metadata and checksums
├── docs/                                   # Documentation suite and publication assets
│   ├── data_dictionary.md                  # Comprehensive column and metric dictionary
│   ├── methodology.md                      # Mathematical formulations (RES, Haversine, Quadrants)
│   ├── synthetic_assumptions.md            # Simulation distributions and stress parameters
│   ├── DATA_AUDIT.md                       # Source dataset audit findings
│   ├── ARCHITECTURE.md                     # Technical architecture specification
│   └── figures/                            # Generated 300 DPI publication figures (PNG/PDF)
├── pages/                                  # Multi-page Streamlit application modules
│   ├── 1_Executive_Overview.py             # KPI summary, volume trends, scenario cards
│   ├── 2_Data_Quality_and_Method.py        # Audit findings, reconciliation tables, methodology
│   ├── 3_Route_Efficiency.py               # Route leaderboard, Top/Bottom 10, RES rankings
│   ├── 4_Geographic_Analysis.py            # US State choropleth heatmap and Canadian notice
│   ├── 5_Ship_Mode_Comparison.py           # Mode distribution and margin by mode analysis
│   ├── 6_Potential_Bottlenecks.py          # Interactive bottleneck quadrant scatter visualizer
│   ├── 7_Route_Drill_Down.py               # Corridor timeline visualizer and order drill-down
│   └── 8_Trends_and_Scenarios.py           # Monthly volume trends and RES weight sensitivity lab
├── scripts/                                # Standalone CLI automation scripts
│   ├── build_data.py                       # Offline pipeline: validation, reconciliation, simulation
│   └── generate_paper_figures.py           # Standalone publication figure generator (300 DPI)
├── src/                                    # Decoupled core business logic and algorithms
│   ├── config.py                           # Centralized constants, file paths, and seed targets
│   ├── metrics.py                          # Mode adjustment, lead-time stats, RES calculations
│   ├── route_analysis.py                   # Corridor aggregation and sample guardrail filtering
│   ├── bottleneck_rules.py                 # Dual 75th-percentile quadrant classification rules
│   ├── map_factories.py                    # Haversine distance calculation and centroid joins
│   ├── sensitivity.py                      # Spearman rho, multi-seed stability, threshold analysis
│   └── generate_synthetic.py               # Stochastic lead-time simulation engine
├── tests/                                  # Comprehensive automated test suite (142+ tests)
│   ├── test_architecture.py                # Decoupled backend architecture validation
│   ├── test_data_quality.py                # De-duplication and financial reconciliation tests
│   ├── test_exports.py                     # CSV export and provenance tests
│   ├── test_generate_paper_figures.py      # Publication figure generator tests
│   ├── test_metrics.py                     # Mode adjustment and RES scoring invariant tests
│   ├── test_privacy.py                     # Zero-PII surrogate token tests
│   ├── test_route_analysis.py              # Guardrail and corridor aggregation tests
│   ├── test_sensitivity.py                 # Spearman rho and 5-seed robustness tests
│   ├── test_synthetic.py                   # Simulation distributions and bounds tests
│   └── test_page_*.py                      # UI module integration tests
├── app.py                                  # Streamlit main application entrypoint
├── requirements.txt                        # Production dependency manifest
└── pytest.ini                              # Pytest runner configuration
```

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 4.1 Clone and Environment Setup
```bash
# Clone the repository
git clone https://github.com/example/nassau-route-intelligence.git
cd nassau-route-intelligence

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 5. Data Pipeline Build Execution

To regenerate all derived and synthetic Parquet datasets, execute the offline build script:

```bash
python scripts/build_data.py
```

**Pipeline Build Workflow:**
1. Verifies SHA-256 hash of `data/original/nassau_candy.csv`.
2. Identifies and isolates 313 exact duplicate records.
3. Reconciles units (37,667), sales ($138,284.12), and profit ($91,076.41).
4. Computes Haversine distances for all 196 active shipping corridors.
5. Generates Baseline, Distance-Sensitive, and Stress-Test synthetic Parquet artifacts.
6. Serializes `clean_orders.parquet`, `route_aggregates.parquet`, and metadata logs.

---

## 6. Automated Test Suite Execution

Run the complete automated test suite verifying data integrity, mathematical models, UI pages, and multi-seed stability:

```bash
# Run full test suite
pytest

# Run sensitivity and robustness tests specifically
pytest tests/test_sensitivity.py

# Run with verbose output
pytest -v
```

---

## 7. Publication Figure Generation

Generate 300 DPI, publication-grade figures (PNG and PDF formats) in `docs/figures/` for academic papers and executive presentations:

```bash
# Generate all publication figures (Default: PNG and PDF at 300 DPI)
python scripts/generate_paper_figures.py

# Specify custom output directory and DPI
python scripts/generate_paper_figures.py --output-dir docs/figures --dpi 300 --formats png,pdf
```

**Generated Publication Figures:**
- `fig1_lead_time_distributions.png / .pdf`: Empirical lead-time distributions across shipping modes.
- `fig2_res_quadrant_scatter.png / .pdf`: Bottleneck quadrant scatter with dual 75th-percentile screening lines.
- `fig3_scenario_comparison_bars.png / .pdf`: Cross-scenario lead-time comparison (Baseline vs. Distance vs. Stress).
- `fig4_weight_sensitivity_and_thresholds.png / .pdf`: RES weight profile sensitivity and sample-size threshold trade-offs.

---

## 8. Launching the Streamlit Application

Launch the multi-page analytical dashboard locally:

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your web browser to explore:
- **Executive Overview (Page 1):** Strategic KPIs and scenario cards.
- **Data Quality & Method (Page 2):** Audit findings and financial reconciliation.
- **Route Efficiency Leaderboard (Page 3):** Corridor rankings with $N \ge 30$ guardrail.
- **Geographic Analysis (Page 4):** Plotly choropleth heatmaps.
- **Ship Mode Comparison (Page 5):** Volume and margin analysis by carrier tier.
- **Potential Bottlenecks (Page 6):** Quadrant scatter screening visualizer.
- **Route Drill-Down (Page 7):** Detailed corridor dispatch timeline.
- **Trends & Scenarios (Page 8):** Monthly volume trends and RES weight sensitivity lab.

---

## 9. Production Cloud Deployment Guide

The repository is pre-configured for **Streamlit Community Cloud** or containerized cloud hosting.

### 9.1 Zero-PII Cloud Compliance (AD-04)
The cloud deployment profile operates with zero exposure of sensitive data:
- `data/original/` and `surrogate_key_mapping.csv` are excluded via `.gitignore`.
- Cloud runtime loads directly from `data/synthetic/*.parquet`, which contain only surrogate keys (`CUST-xxxxxxxx`, `ORD-xxxxxxxxxx`) and state-level centroids.

### 9.2 Streamlit Community Cloud Setup Steps
1. Push the repository to GitHub.
2. Log into [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **"New App"** and select your repository, branch (`main`), and main file path (`app.py`).
4. Under **Advanced Settings**, ensure Python version is set to `3.10` or higher.
5. Click **"Deploy!"**. The app will install dependencies from `requirements.txt` and launch automatically.

### 9.3 Headless Verification Command
To verify that the application launches without error in headless environments:
```bash
streamlit run app.py --server.headless true --server.enableCORS false
```

---

## 10. Comprehensive Documentation Suite Reference

Detailed architectural, mathematical, and simulation references are available in `docs/`:
- [`docs/data_dictionary.md`](docs/data_dictionary.md): Comprehensive data dictionary defining all attributes across Original, Derived, and Synthetic layers with types, constraints, and provenance.
- [`docs/methodology.md`](docs/methodology.md): Formal mathematical formulations for Haversine distance, Mode Adjustment, RES penalties, sample size guardrail ($N \ge 30$), and quadrant bottleneck screening.
- [`docs/synthetic_assumptions.md`](docs/synthetic_assumptions.md): Full disclosure of discrete empirical distributions, distance scaling coefficients, stress disruption injections, and 5-seed calibration targets.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Architectural decisions and framework invariants (AD-01 through AD-12).
- [`docs/DATA_AUDIT.md`](docs/DATA_AUDIT.md): Source dataset profiling, duplicate records investigation, and reconciliation targets.

