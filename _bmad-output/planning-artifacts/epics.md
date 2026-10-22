---
status: ready-for-development
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - "docs/Nassau_Route_Intelligence_PRD_v1.3_FINAL.md"
  - "docs/ARCHITECTURE.md"
  - "docs/DATA_AUDIT.md"
---

# Nassau Route Intelligence - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Nassau Route Intelligence, decomposing requirements from PRD v1.3 and ARCHITECTURE v1.1 into implementable, testable, and dependency-ordered stories.

## Requirements Inventory

### Functional Requirements

- **FR-01 (Safe data loading):** Detects CSV or Excel; reports rows and columns; validates required columns; never overwrites source; records SHA-256 hash.
- **FR-02 (Quality report):** Missingness, duplicates (313 flagged), date anomalies, invalid values, geography and mapping issues; flagged rows exportable.
- **FR-03 (Factory mapping):** Uses supplied mapping only (15 products to 5 factories); coverage and unmatched shown; no invented factories; factory coordinates attached.
- **FR-04 (Layer separation):** Layer label on pages, charts, tables and exports (ORIGINAL, DERIVED, SYNTHETIC); no silent blending.
- **FR-05 (Overview):** KPI definitions visible; order lines and line items separate; metrics respond to filters.
- **FR-06 (Route analysis):** State and region routes show volume, timing stats, delay rate, sample size; low-sample routes listed separately; Factory -> Region rollup for small factories.
- **FR-07 (RES and leaderboard):** Formula, population, weights shown (70/30 fixed on Pages 1–7; sensitivity analysis on Page 8 only); constant-value handling; speed-only score; Top and Bottom 10; low-sample notes.
- **FR-08 (Delay threshold):** Slider 1 to 15 days (default 5.0), always visible; delay counts and rates update consistently on every page; labeled "analysis threshold".
- **FR-09 (Geographic view):** State metric selector (mean lead time, delay rate, RES, volume); legend and units; Canadian rows excluded from map with banner; volume/financial totals retained.
- **FR-10 (Ship-mode comparison):** Individual modes and Standard vs Expedited; distance bands; margin-by-mode; no causal language.
- **FR-11 (Bottleneck flags):** Configurable rules; reasons, counts and warnings visible; labeled "potential"; state and route level; 75th percentile volume and delay screening quadrant.
- **FR-12 (Drill-down):** Route or state summary and order list; order-level timeline (order date, ship date, threshold marker); order-to-ship never labeled transit time.
- **FR-13 (Filters):** Layer, scenario (Synthetic only), factory, state, region, ship mode, valid date range, minimum sample, duplicate toggle; reset control; empty-state messages.
- **FR-14 (Exports):** Filtered CSV with readable headers, layer, scenario, threshold, score settings, applied filters prepended in metadata header.
- **FR-15 (Research traceability):** Figures regenerate by script; methodology, generator settings, software versions recorded.
- **FR-16 (Error handling):** Missing columns, malformed dates, empty results, unsupported files give clear messages.
- **FR-17 (Trends):** Monthly order volume (Original layer, valid order dates) and monthly mean lead time (Synthetic).
- **FR-18 (Deployment):** Public cloud link uses sanitized Synthetic/Derived artifacts only; local run documented as backup.
- **FR-19 (Lead-time basis switch):** Toggle between mode-adjusted (default) and raw lead time for RES, rankings and map; both shown side by side with rank changes; mode reference means calculated on full scenario dataset before user filters.
- **FR-20 (Business insights):** Overview shows sales, margin and growth by year, product, factory and state from valid Original fields; each card labeled Original.
- **FR-21 (Cleaning outputs):** Derived layer applies postal-code padding, product-name standardization and the duplicate flag; each change counted in transformation log.

### Non-Functional Requirements

- **NFR-01 (Usability):** Clear labels, metric tooltips, accessible color scales, glossary, units on axes.
- **NFR-02 (Performance):** Responsive UI across 10,000 records; cached loading and aggregation via `@st.cache_data`; sub-second page interaction.
- **NFR-03 (Reliability):** Malformed inputs and empty selections produce actionable messages; zero division protection in metrics.
- **NFR-04 (Reproducibility):** Fixed seed 42, 5 deterministic robustness seeds (`[42, 101, 202, 303, 404]`), pinned dependencies, repeatable offline build script.
- **NFR-05 (Maintainability):** Modular architecture with pure headless Python engines in `src/` (strictly zero Streamlit imports), presentation caching in `app.py`.
- **NFR-06 (Traceability):** Every score and chart traces to a mathematical definition and source data layer.
- **NFR-07 (Privacy and Security):** Randomized surrogate keys for Customer ID and Order ID; `City` and `Postal Code` dropped from cloud artifacts; mapping strictly local-only and git-ignored; raw source data never deployed.

### Additional Requirements (from Architecture v1.1)

- **Starter Architecture:** Greenfield modular layout with separation of `config/`, `data/`, `src/`, `tests/`, `scripts/`, `pages/`.
- **Source Immutability:** SHA-256 of `data/original/nassau_candy.csv` must remain identical (`6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f`).
- **Surrogate Key Generation:** Randomized reproducible assignment per build seed; no sequential keys or predictable links.
- **Order of Operations Bounds:** Apply base bounds ($[0, 2]$ Same Day, $[1, 14]$ others) *before* delay injections; use expanded bounds ($[0, 6]$ Same Day, $[1, 20]$ others) in Stress-Test scenario to prevent clipping.
- **Bottleneck Recovery:** Enforce minimum sample threshold $N \ge 30$; recovery must succeed in $\ge 4/5$ seeds with Stress delay rate strictly greater than Baseline delay rate.
- **Zero Streamlit in `src/`:** Enforced by AST architectural test.

### FR Coverage Map

| Requirement | Covering Story / Stories |
|---|---|
| FR-01 | Story 1.2 |
| FR-02 | Story 1.3, Story 4.2 |
| FR-03 | Story 1.1, Story 1.4 |
| FR-04 | Story 4.1, Story 4.5 |
| FR-05 | Story 4.1, Story 4.3 |
| FR-06 | Story 3.2, Story 4.4 |
| FR-07 | Story 3.1, Story 4.4 |
| FR-08 | Story 3.1, Story 4.1 |
| FR-09 | Story 5.1 |
| FR-10 | Story 5.2 |
| FR-11 | Story 3.3, Story 5.3 |
| FR-12 | Story 5.4 |
| FR-13 | Story 4.1 |
| FR-14 | Story 4.5 |
| FR-15 | Story 6.2, Story 6.3 |
| FR-16 | Story 1.2, Story 4.1 |
| FR-17 | Story 5.5 |
| FR-18 | Story 2.2, Story 6.4 |
| FR-19 | Story 3.1, Story 4.4 |
| FR-20 | Story 4.3 |
| FR-21 | Story 1.3, Story 2.2 |

---

## Epic List

1. **Epic 1: Data Ingestion, Quality Audit & Factory Mapping Engine (Phase 1 Foundation)**
   - *Status:* **COMPLETED** (Implemented & 15/15 unit/architectural tests passing)
   - *Goal:* Establish trusted, auditable raw data ingestion, duplicate reconciliation, geographic normalization, and factory-route coordinate mapping.
2. **Epic 2: Shipment-Grain Synthetic Lead Time Generator & Privacy-Preserving Cloud Build Pipeline (Phase 2 Foundation)**
   - *Status:* **INCOMPLETE (READY FOR IMPLEMENTATION)**
   - *Goal:* Generate reproducible, distance-sensitive, and stress-tested synthetic order-to-ship lead times at customer shipment grain, and build sanitized, surrogate-keyed cloud Parquet artifacts.
3. **Epic 3: Route Efficiency Scoring, Sample Guardrails & Bottleneck Detection Engine (Phase 3 Foundation)**
   - *Status:* Incomplete (Blocked by Epic 2)
   - *Goal:* Calculate mode-adjusted Route Efficiency Scores (RES), enforce sample size thresholds ($N \ge 30$), and screen potential geographic bottlenecks.
4. **Epic 4: Core Executive Overview, Method Audit & Route Efficiency Dashboard (Phase 4 Deliverables)**
   - *Status:* Incomplete (Blocked by Epic 3)
   - *Goal:* Provide an interactive Streamlit dashboard shell with global filter controls, layer provenance badges, data quality reconciliation tables, executive financial KPIs, route efficiency leaderboards, and audited CSV exports.
5. **Epic 5: Interactive Geographic, Ship Mode, Bottleneck & Drill-Down Analytics (Phase 5 Deep Dives)**
   - *Status:* Incomplete (Blocked by Epic 4)
   - *Goal:* Deliver rich visual analytics including US state choropleth heatmaps with Canadian exclusion banners, ship-mode cost/transit comparisons, interactive bottleneck quadrant scatter plots, order timelines, and monthly volume/timing trends.
6. **Epic 6: Sensitivity Verification, Research Figures & Cloud Deployment Finalization (Phase 6 Finalization)**
   - *Status:* Incomplete (Blocked by Epic 5)
   - *Goal:* Conduct sensitivity experiments, generate publication-grade research figures, produce project documentation, and verify cloud deployment readiness.

---

## Epic 1: Data Ingestion, Quality Audit & Factory Mapping Engine (Phase 1 Foundation)

**Goal:** Provide an immutable, auditable, and decoupled ingestion engine that verifies raw source checksums, identifies duplicate rows, reconciles financial and unit balances, pads postal codes, attaches factory coordinates, and calculates Haversine distances.

### Story 1.1: Configuration Tables & Workspace Environment Setup
*Status: COMPLETED*
As an operations analyst and developer,
I want standardized reference tables for factories, product mappings, geographic centroids, and generator parameters,
So that all downstream spatial and simulation algorithms rely on single sources of truth.

**Acceptance Criteria:**
- **Given** the workspace root,
- **When** the configuration tables are loaded,
- **Then** `config/factories.csv` contains all 5 production facilities with valid coordinates,
- **And** `config/product_factory.csv` maps all 15 products to the 5 facilities,
- **And** `config/geographic_centroids.csv` contains all 59 destinations (49 US jurisdictions + 10 Canadian provinces),
- **And** `config/generator.yaml` defines empirical distributions, 5 seeds (`[42, 101, 202, 303, 404]`), and stress injection parameters,
- **And** `.gitignore` excludes `data/original/` and `data/derived/surrogate_key_mapping.csv`.

### Story 1.2: Dual-Mode Ingestion & Source Data SHA-256 Verification
*Status: COMPLETED*
As a data engineer,
I want a pure Python loader that verifies the raw dataset against an immutable SHA-256 hash in local mode and gracefully handles missing raw data in cloud mode,
So that data provenance is preserved without risking data tampering or breaking cloud deployment.

**Acceptance Criteria:**
- **Given** `data/original/nassau_candy.csv`,
- **When** `src/load_data.py::verify_source_hash()` executes,
- **Then** it asserts equality with `6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f`,
- **And** `load_raw_data()` reads all 10,194 rows with strongly typed schemas,
- **And** `get_deployment_mode()` returns `"local"` if raw file exists, else `"cloud"`,
- **And** `src/load_data.py` contains zero Streamlit imports.

### Story 1.3: Data Quality, Deduplication & 4-Metric Reconciliation Engine
*Status: COMPLETED*
As a business analyst,
I want an automated quality engine that flags duplicate rows, reconciles units and financial totals, normalizes product names, and computes diagnostic lead times,
So that data hygiene is auditable and financial numbers match the approved baseline.

**Acceptance Criteria:**
- **Given** the raw 10,194 records,
- **When** `src/validate_data.py::clean_dataset()` runs,
- **Then** exactly 313 duplicate rows are flagged in `is_duplicate = True`,
- **And** `reconcile_metrics()` verifies:
  - Rows: $10,194 \rightarrow 9,881$ ($\Delta = -313$)
  - Units: $38,654 \rightarrow 37,667$ ($\Delta = -987$)
  - Sales: $\$141,783.63 \rightarrow \$138,284.12$ ($\Delta = -\$3,499.51$)
  - Gross Profit: $\$93,442.80 \rightarrow \$91,076.41$ ($\Delta = -\$2,366.39$),
- **And** 449 four-digit US postal codes are padded with leading `0`,
- **And** 200 Canadian records are tagged with `is_canadian = True` and `is_partial_postal = True`,
- **And** `Wonka Bar -Scrumdiddlyumptious` is normalized with proper spacing,
- **And** diagnostic reconstruction per-mode means match Section 3.1 within 0.01.

### Story 1.4: Factory Assignment, Centroid Joins & Vectorized Haversine Distance
*Status: COMPLETED*
As a logistics engineer,
I want to map products to factories, join destination centroids, and compute great-circle shipping distances in kilometers,
So that route-level spatial analytics and distance-sensitive simulations have accurate inputs.

**Acceptance Criteria:**
- **Given** the deduplicated dataset,
- **When** `src/map_factories.py::process_mapping_pipeline()` runs,
- **Then** 100% of products map to factories with zero unmapped lines,
- **And** every Order ID maps to exactly 1 factory across all 8,549 clean order lines,
- **And** 5,067 customer shipments are identified (1,702 multi-factory [33.6%], 2,240 multi-order-line),
- **And** vectorized Haversine calculates non-zero distance for all US and Canadian destinations,
- **And** `route_key` (`Factory -> State/Province`) and `route_key_region` (`Factory -> Region`) are generated.

---

## Epic 2: Shipment-Grain Synthetic Lead Time Generator & Privacy-Preserving Cloud Build Pipeline (Phase 2 Foundation)

**Goal:** Implement the reproducible multi-scenario synthetic generator at customer-shipment grain, unclipped delay bounds, and the offline build pipeline that produces sanitized Parquet artifacts with surrogate keys for cloud deployment.

### Story 2.1: Customer Shipment Grouping & Multi-Scenario Synthetic Lead Time Generator
*Status: READY FOR IMPLEMENTATION*
As a simulation modeler,
I want to generate synthetic lead times at the customer-shipment grain `(Customer ID, Order Date, Ship Mode)` across Baseline, Distance-Sensitive, and Stress-Test scenarios using fixed seed 42,
So that all order lines in the same physical shipment share identical lead times while testing network stress conditions without clipping delays.

**Acceptance Criteria:**
- **Given** the deduplicated mapped dataset,
- **When** `src/generate_synthetic.py` groups lines into customer shipments,
- **Then** exactly 5,067 customer shipments are formed,
- **And** all order lines within each shipment receive the identical simulated lead time,
- **And** **Baseline scenario** samples empirical distributions per mode from `config/generator.yaml` bounded in $[0, 2]$ for Same Day and $[1, 14]$ for others,
- **And** **Distance-Sensitive scenario** applies $0.5 \times (\text{Distance\_km} - \mu_{\text{dist}}) / 1000$ days to Baseline, bounded in $[0, 2]$ for Same Day and $[1, 14]$ for others,
- **And** **Stress-Test scenario** applies base bounds *before* adding injections (+1.0d peak season in Nov/Dec, +1.0d California/New York, +1.5d Lot's O' Nuts -> Texas, +1.5d Wicked Choccy's -> Texas) and enforces expanded bounds ($[0, 6]$ for Same Day, $[1, 20]$ for others) so that injected delays are not clipped,
- **And** synthetic lead times are non-negative and labeled as simulated data.

### Story 2.2: Privacy-Preserving Cloud Build Pipeline & Surrogate Key Generation
*Status: Incomplete (Depends on Story 2.1)*
As a cloud security engineer,
I want an offline data build script `scripts/build_data.py` that replaces Customer IDs and Order IDs with randomized surrogate keys, drops granular PII, and outputs optimized Parquet artifacts,
So that the application can be deployed to public cloud without exposing real customer identifiers or raw data.

**Acceptance Criteria:**
- **Given** the raw dataset and generated synthetic datasets,
- **When** `scripts/build_data.py` executes,
- **Then** `Customer ID` and `Order ID` are replaced with randomized surrogate keys reproducible per build seed,
- **And** the original-to-surrogate mapping is written strictly to local-only `data/derived/surrogate_key_mapping.csv` and never committed or deployed,
- **And** `City` and `Postal Code` are completely dropped from cloud artifacts,
- **And** `data/derived/clean_orders.parquet`, `data/derived/route_aggregates.parquet`, `data/synthetic/baseline.parquet`, `data/synthetic/distance_sensitive.parquet`, and `data/synthetic/stress_test.parquet` are serialized via pyarrow,
- **And** `data/derived/transformation_log.json` and `data/synthetic/metadata.json` are generated documenting build timestamp, seed 42, scenario hashes, and 4-metric reconciliation.

### Story 2.3: Synthetic Calibration & Privacy Compliance Verification Suite
*Status: Incomplete (Depends on Story 2.2)*
As a quality assurance engineer,
I want automated test suites `tests/test_synthetic.py` and `tests/test_privacy.py`,
So that reproducibility, unclipped delay survival (including Same Day), and complete cloud anonymization are verified before dashboard development.

**Acceptance Criteria:**
- **Given** the generated Parquet artifacts and build outputs,
- **When** `tests/test_synthetic.py` and `tests/test_privacy.py` run under pytest,
- **Then** seed 42 reproduces identical synthetic DataFrames across runs,
- **And** Same Day shipments under Stress-Test survive with $> 2.0$ days lead time when injected (proving delay bounds do not clip),
- **And** zero raw 6-digit Customer IDs appear anywhere in cloud Parquet files or `metadata.json`,
- **And** Order ID surrogate keys contain no substring matching original Customer IDs,
- **And** `City` and `Postal Code` columns are confirmed absent from cloud Parquet schemas,
- **And** the raw file SHA-256 is verified unchanged.

---

## Epic 3: Route Efficiency Scoring, Sample Guardrails & Bottleneck Detection Engine (Phase 3 Foundation)

**Goal:** Implement mode-adjusted lead times, fixed 70/30 Route Efficiency Score (RES) math, minimum sample size guardrails ($N \ge 30$), and 75th percentile bottleneck screening rules verified across 5 seeds.

### Story 3.1: Pre-computed Mode Adjustment & Route Efficiency Scoring Engine
*Status: Incomplete (Depends on Epic 2)*
As a supply chain analyst,
I want route efficiency scores computed using fixed 70% Speed and 30% Variability penalties with mode-adjusted lead times pre-computed on the full dataset,
So that routes are benchmarked fairly without penalizing routes with high Standard Class volume.

**Acceptance Criteria:**
- **Given** synthetic shipment lead times,
- **When** `src/metrics.py` evaluates Route Efficiency Scores (RES),
- **Then** ship-mode reference means are pre-computed on the full scenario dataset before user filters and remain invariant to filter changes,
- **And** $\text{Mode-Adjusted Lead Time} = \text{Lead Time} - \mu_{\text{mode}}$,
- **And** $\text{RES} = 100 - (0.70 \times \text{Speed Penalty} + 0.30 \times \text{Variability Penalty})$, bounded in $[0, 100]$,
- **And** constant-value or zero-variance routes safely assign penalty = 0 without math errors,
- **And** delay condition enforces strict inequality: $\text{Lead Time} > \text{Threshold}$ (with threshold slider 1–15d, default 5.0d).

### Story 3.2: Route Aggregation, Sample Size Guardrails & Regional Rollups
*Status: Incomplete (Depends on Story 3.1)*
As a network planner,
I want route aggregation that enforces a strict $N \ge 30$ sample threshold for state-level rankings and automatically rolls up small factories to the regional level,
So that low-volume sample noise does not distort operational leaderboards.

**Acceptance Criteria:**
- **Given** the route dataset,
- **When** `src/route_analysis.py` aggregates Factory -> State routes,
- **Then** routes with $N \ge 30$ order lines qualify for Top 10 / Bottom 10 leaderboards,
- **And** boundary tests verify $N=29$ is ineligible, $N=30$ is eligible, and $N=31$ is eligible,
- **And** routes with $N < 30$ are segregated into a "Low Sample / Insufficient Data" table,
- **And** Sugar Shack, Secret Factory, and The Other Factory automatically roll up to `Factory -> Region` level,
- **And** layer isolation prevents mixing ORIGINAL, DERIVED, and SYNTHETIC data in the same ranked table.

### Story 3.3: 75th Percentile Screening Quadrant & 5-Seed Bottleneck Recovery Engine
*Status: Incomplete (Depends on Story 3.2)*
As a risk analyst,
I want an automated bottleneck screening engine that identifies high-volume, high-delay routes using 75th percentile thresholds and passes a 5-seed recovery test,
So that critical fulfillment bottlenecks are reliably detected across random seeds.

**Acceptance Criteria:**
- **Given** route aggregates under Baseline and Stress-Test scenarios,
- **When** `src/bottleneck_rules.py` screens for bottlenecks,
- **Then** routes with $\text{Volume} \ge P_{75}$ and $\text{Delay Rate} \ge P_{75}$ (at 5-day threshold) are flagged as Critical Bottlenecks,
- **And** routes with $\text{Delay Rate} > \text{Median}$ are flagged on the Watchlist,
- **And** `tests/test_bottlenecks.py` runs across 5 deterministic seeds (`[42, 101, 202, 303, 404]`),
- **And** the injected Texas routes (*Lot's O' Nuts -> Texas* and *Wicked Choccy's -> Texas*, enforcing $N \ge 30$) are recovered in at least 4 of the 5 seeds ($\ge 4/5$, i.e. $\ge 80\%$) with Stress delay rate strictly greater than Baseline delay rate.

---

## Epic 4: Core Executive Overview, Method Audit & Route Efficiency Dashboard (Phase 4 Deliverables)

**Goal:** Build the primary Streamlit dashboard application with global filtering, layer badges, data quality audit tables, executive margin cards, 70/30 fixed RES leaderboards, and provenance-stamped CSV exports.

### Story 4.1: Streamlit Application Shell, Global Filter State & Parquet Cache Loader
*Status: Incomplete (Depends on Epic 3)*
As an executive user,
I want a responsive Streamlit application shell with persistent sidebar filters and fast Parquet artifact caching,
So that I can seamlessly explore the network while maintaining layer provenance and filter context.

**Acceptance Criteria:**
- **Given** prepared Parquet artifacts in `data/derived/` and `data/synthetic/`,
- **When** `app.py` loads,
- **Then** it reads artifacts via `@st.cache_data` in the presentation layer without importing Streamlit in `src/`,
- **And** sidebar provides global controls: Data Layer, Synthetic Scenario, Factory, State, Region, Ship Mode, Delay Threshold Slider (1–15d, default 5.0d), Duplicate Toggle, and Filter Reset,
- **And** persistent header banner displays the active Data Layer (ORIGINAL, DERIVED, SYNTHETIC) and Scenario name,
- **And** responsive execution completes in under 1 second per filter change.

### Story 4.2: Data Quality & Method Audit Page
*Status: Incomplete (Depends on Story 4.1)*
As an auditor,
I want a dedicated Data Quality & Method page showing the 4-metric reconciliation table and diagnostic date interval analysis,
So that all cleaning steps, exclusions, and date hypotheses are transparently documented.

**Acceptance Criteria:**
- **Given** `pages/2_Data_Quality_and_Method.py`,
- **When** viewed in the dashboard,
- **Then** the 4-metric unit and financial reconciliation table is displayed (Units $38,654 \rightarrow 37,667$, $\Delta = -987$; Sales $\$141,783.63 \rightarrow \$138,284.12$, $\Delta = -\$3,499.51$; Profit $\$93,442.80 \rightarrow \$91,076.41$, $\Delta = -\$2,366.39$; Rows $10,194 \rightarrow 9,881$, $\Delta = -313$),
- **And** diagnostic date interval histogram (904 to 1,642 days) and Order-ID-year floor subtraction are displayed with prominent "Unverified Diagnostic Hypothesis" labels,
- **And** Canadian partial postal code disclosure is clearly presented.

### Story 4.3: Executive Overview & Margin Analysis Page
*Status: Incomplete (Depends on Story 4.1)*
As a C-suite executive,
I want an Executive Overview displaying product revenue, manufacturing COGS, gross margins, and volume metrics by factory and product,
So that I can evaluate commercial performance alongside operational throughput.

**Acceptance Criteria:**
- **Given** `pages/1_Executive_Overview.py`,
- **When** viewed in the dashboard,
- **Then** financial KPI summary cards show Total Sales, Manufacturing COGS, Gross Profit, and Gross Margin %,
- **And** explicit disclaimers state freight shipping costs are out of scope and not inferred from manufacturing COGS,
- **And** order lines (8,549) and line items (9,881) are explicitly distinguished,
- **And** all metrics respond dynamically to global sidebar filters.

### Story 4.4: Route Efficiency Leaderboard Page
*Status: Incomplete (Depends on Story 4.1)*
As a logistics manager,
I want Top 10 and Bottom 10 route leaderboards ranked by Route Efficiency Score (RES) with a toggle between mode-adjusted and raw lead time,
So that I can identify best- and worst-performing shipping lanes.

**Acceptance Criteria:**
- **Given** `pages/3_Route_Efficiency.py`,
- **When** viewed in the dashboard,
- **Then** Top 10 and Bottom 10 routes are displayed with RES (70% speed / 30% variability fixed weighting),
- **And** routes with $N < 30$ are excluded from leaderboards and listed in an Insufficient Sample table,
- **And** toggle allows switching between Mode-Adjusted RES (default) and Raw Lead Time RES, showing side-by-side rank delta,
- **And** changing the delay threshold slider updates delay counts and rates dynamically.

### Story 4.5: Provenance-Preserving Filtered CSV Export Engine
*Status: Incomplete (Depends on Story 4.4)*
As a data analyst,
I want to export filtered data and route tables with prepended metadata headers,
So that exported files maintain full provenance for audits and downstream reporting.

**Acceptance Criteria:**
- **Given** filtered tables in the dashboard,
- **When** `src/exports.py` generates a CSV download,
- **Then** `tests/test_exports.py` verifies the file contains a prepended commented header documenting Data Layer, Scenario, Threshold, active filters, and generation timestamp,
- **And** table columns have human-readable headers without raw internal IDs.

---

## Epic 5: Interactive Geographic, Ship Mode, Bottleneck & Drill-Down Analytics (Phase 5 Deep Dives)

**Goal:** Provide advanced visual analytics including Plotly US state choropleths with Canadian notices, ship mode cost-transit trade-offs, interactive bottleneck quadrant scatter plots, order timelines, and sensitivity trend labs.

### Story 5.1: US State Choropleth Heatmap & Canadian Notice Banner
*Status: Incomplete (Depends on Epic 4)*
As a regional director,
I want an interactive US state choropleth heatmap showing delivery performance metrics by destination state,
So that geographic patterns in lead time and delay frequency are immediately visible.

**Acceptance Criteria:**
- **Given** `pages/4_Geographic_Analysis.py`,
- **When** viewed in the dashboard,
- **Then** a Plotly US choropleth displays user-selected metrics: Mean Lead Time, Delay Rate, RES, or Order Volume,
- **And** Canadian destinations are excluded from the US map geometry and a prominent notification banner states Canadian orders are retained in overall financial and volume metrics,
- **And** hovering over a state reveals factory fulfillment breakdown and sample size.

### Story 5.2: Ship Mode Distribution & Margin-by-Mode Analysis
*Status: Incomplete (Depends on Epic 4)*
As a logistics analyst,
I want ship-mode performance comparisons across Standard vs Expedited modes and distance bands,
So that I can understand how shipping method choices impact lead-time variance.

**Acceptance Criteria:**
- **Given** `pages/5_Ship_Mode_Comparison.py`,
- **When** viewed in the dashboard,
- **Then** lead-time distributions are compared across Same Day, First Class, Second Class, and Standard Class,
- **And** distance band analysis illustrates lead time versus Haversine distance,
- **And** gross profit margins by ship mode are displayed with clear non-causal disclaimers.

### Story 5.3: Interactive Bottleneck Quadrant Scatter Visualizer
*Status: Incomplete (Depends on Epic 4)*
As an operations director,
I want an interactive quadrant scatter plot of route volume versus delay rate,
So that high-volume, high-delay bottleneck lanes can be isolated and prioritized.

**Acceptance Criteria:**
- **Given** `pages/6_Potential_Bottlenecks.py`,
- **When** viewed in the dashboard,
- **Then** a Plotly scatter plot plots Route Volume ($x$) against Delay Rate ($y$),
- **And** reference lines display the 75th percentile thresholds for volume and delay rate,
- **And** routes in the upper-right quadrant are flagged as Critical Bottlenecks with sample size $N$ and volume metrics,
- **And** watchlisted routes ($\text{Delay Rate} > \text{Median}$) are highlighted.

### Story 5.4: Route Drill-Down & Order-to-Ship Timeline Visualizer
*Status: Incomplete (Depends on Epic 4)*
As a warehouse manager,
I want to drill down into a specific route or state to view individual order timelines and shipment details,
So that I can investigate root causes of delays on specific lanes.

**Acceptance Criteria:**
- **Given** `pages/7_Route_Drill_Down.py`,
- **When** a route (e.g. *Lot's O' Nuts -> Texas*) is selected,
- **Then** summary metrics and an order line table are displayed,
- **And** an interactive order timeline chart shows order date, ship date, lead time, and threshold line,
- **And** lead time is strictly labeled "Order-to-Ship Lead Time", never "Transit Time",
- **And** Canadian routes display factory-to-province centroid distances.

### Story 5.5: Scenario Trends & RES Weight Sensitivity Lab
*Status: Incomplete (Depends on Epic 4)*
As an executive strategist,
I want to analyze monthly order trends and test RES sensitivity under different speed/variability weights,
So that I can evaluate network seasonality and score robustness under alternative priorities.

**Acceptance Criteria:**
- **Given** `pages/8_Trends_and_Scenarios.py`,
- **When** viewed in the dashboard,
- **Then** monthly order volume is displayed using valid Original dates (2024–2025),
- **And** monthly mean lead times are displayed using Synthetic scenarios,
- **And** interactive sensitivity sliders (Page 8 only) allow testing alternative RES weights (e.g. 50/50, 70/30, 90/10) with side-by-side rank stability indicators.

---

## Epic 6: Sensitivity Verification, Research Figures & Cloud Deployment Finalization (Phase 6 Finalization)

**Goal:** Execute formal robustness experiments, generate publication figures for the research paper, complete full documentation, and verify zero-PII cloud release gates.

### Story 6.1: Sensitivity Analysis & Seed Robustness Test Suite
*Status: Incomplete (Depends on Epic 5)*
As a researcher,
I want an automated sensitivity test suite evaluating RES rankings across multiple weight configurations and seeds,
So that paper conclusions are verified as statistically robust.

**Acceptance Criteria:**
- **Given** synthetic route rankings across 5 seeds (`[42, 101, 202, 303, 404]`),
- **When** sensitivity tests run,
- **Then** rank correlation (Spearman $\rho$) between 70/30 and 50/50, 90/10 weight profiles is computed and logged,
- **And** top bottleneck routes remain consistent across seeds.

### Story 6.2: Publication Figure Generation Script
*Status: Incomplete (Depends on Epic 5)*
As an author,
I want a standalone script `scripts/generate_paper_figures.py` that generates all publication-quality Matplotlib/Seaborn figures,
So that paper graphics are 100% reproducible directly from code.

**Acceptance Criteria:**
- **Given** `scripts/generate_paper_figures.py`,
- **When** executed via CLI,
- **Then** high-resolution figures (300 DPI) are saved to `docs/figures/`,
- **And** figures include lead-time distributions, RES quadrant scatter, and scenario comparison bars.

### Story 6.3: Comprehensive Documentation & Data Dictionary
*Status: Incomplete (Depends on Epic 5)*
As a maintainer,
I want complete project documentation including data dictionary, methodology, and synthetic assumptions,
So that future contributors and mentors can understand and reproduce the entire pipeline.

**Acceptance Criteria:**
- **Given** the project repository,
- **When** documentation is compiled,
- **Then** `docs/data_dictionary.md` defines all columns and metrics across Original, Derived, and Synthetic layers,
- **And** `docs/methodology.md` details RES math, mode adjustment, and bottleneck criteria,
- **And** `docs/synthetic_assumptions.md` discloses all simulation parameters and calibration targets,
- **And** `README.md` provides complete local quickstart and cloud deployment instructions.

### Story 6.4: Cloud Deployment Validation & Zero-PII Release Gate Check
*Status: Incomplete (Depends on Epic 6 Stories 6.1–6.3)*
As a release engineer,
I want a comprehensive release-gate validation script that checks cloud startup, zero-PII artifacts, and test pass rate,
So that public deployment to Streamlit Community Cloud is 100% compliant with privacy and architecture standards.

**Acceptance Criteria:**
- **Given** a simulated cloud environment (where `data/original/` is absent),
- **When** the application starts up,
- **Then** it loads prepared Parquet artifacts without failing on missing raw CSV,
- **And** zero 6-digit Customer IDs or unmasked Order IDs exist in deployed files,
- **And** 100% of automated tests pass,
- **And** all PRD release gates are verified.
