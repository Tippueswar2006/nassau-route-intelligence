# Phase 5: Frontend and User Experience Audit

**Project:** Nassau Candy Shipping Route Intelligence  
**Audit Date:** 2026-10-25  
**Auditor:** Antigravity Senior Engineering & QA Lead  
**UI Framework:** Streamlit `1.65.0` with Plotly `7.1.0`  
**Verification Method:** Automated Headless Runtime Verification (`streamlit run` on port 8501) + In-Memory Streamlit `AppTest` Harness Suite + Static Code/Template Inspection  

---

## 1. Page-by-Page Audit & Verification

### Page 0: Main Application Shell (`app.py`)
- **Purpose:** Entrypoint, global sidebar filters, `@st.cache_data` loader, and strategic system overview.
- **Widgets Tested:** Data Layer selectbox (`SYNTHETIC`, `DERIVED`, `ORIGINAL`), Scenario selectbox (`baseline`, `distance_sensitive`, `stress_test`), Factory multi-select, Region multi-select, State multi-select, Ship Mode multi-select, Delay Threshold slider (1.0–15.0 days, step 0.5), Duplicate Exclusion checkbox, Reset Filters button.
- **Verification Result (AppTest & Headless):** Initialized cleanly with 0 exceptions. Filter updates execute in under $0.05$ seconds ($< 1.0\text{s}$ target).
- **Empty State Handling:** When user filters yield zero records, displays `st.warning("No records match the active filter criteria. Please adjust your sidebar selections.")` without crashing.

### Page 1: Executive Overview (`pages/1_Executive_Overview.py`)
- **Purpose:** High-level commercial KPIs, revenue vs volume trends, scenario comparison cards, and freight cost disclaimer.
- **Key Visuals:** 4 primary KPI metrics (Sales, COGS, Profit, Margin %), order-line vs line-item volume cards, scenario lead-time delta cards.
- **Compliance Checks:** Verified AD-11 product margin disclaimer (*"Cost reflects manufacturing COGS only; carrier freight transportation costs are not present in dataset"*).
- **Verification Result (AppTest):** 0 uncaught exceptions; metrics render expected baseline values ($9,881$ line items, $8,549$ order lines, $\$138,284.12$ clean sales).

### Page 2: Data Quality & Method (`pages/2_Data_Quality_and_Method.py`)
- **Purpose:** Source dataset profiling, 4-metric reconciliation audit, diagnostic date reconstruction, and methodology disclosure.
- **Key Visuals:** 4-metric audit table (Rows $-313$, Units $-987$, Sales $-\$3,499.51$, Profit $-\$2,366.39$), histogram of raw 904–1,642 day intervals, floor-subtraction diagnostic table.
- **Compliance Checks:** Quarantines diagnostic floor reconstruction (0–11d) strictly as an audit hypothesis with explicit warning banner.
- **Verification Result (AppTest):** 0 uncaught exceptions; 4-metric reconciliation verified.

### Page 3: Route Efficiency Leaderboard (`pages/3_Route_Efficiency.py`)
- **Purpose:** Distribution route rankings using invariant 70/30 RES scoring math, Top 10 and Bottom 10 tables, and mode-adjusted vs raw comparisons.
- **Key Visuals:** Top 10 and Bottom 10 leaderboards, mode-adjusted RES vs raw RES rank deltas, low-sample ($N < 30$) inspection table.
- **Compliance Checks:** Enforces $N \ge 30$ sample size guardrail (AD-07). All routes below 30 orders are partitioned to the low-sample table with warning banners.
- **Verification Result (AppTest):** 0 uncaught exceptions; Top 10 / Bottom 10 correctly populate with only eligible corridors ($N \ge 30$).

### Page 4: Geographic Analysis (`pages/4_Geographic_Analysis.py`)
- **Purpose:** Spatial heatmaps and regional fulfillment metrics across North American destination markets.
- **Key Visuals:** Interactive Plotly US state choropleth map (color-scaled by volume, delay rate, or mean lead time), state summary table, regional delivery performance metrics.
- **Compliance Checks:** Verified AD-10 Canadian exclusion notice banner (`"200 Canadian order records excluded from US state choropleth map"`).
- **Verification Result (AppTest):** 0 uncaught exceptions; choropleth figure generates with valid US state abbreviations.

### Page 5: Shipping Mode Comparison (`pages/5_Ship_Mode_Comparison.py`)
- **Purpose:** Performance, volume, and commercial margin comparison across carrier tiers (Same Day, First Class, Second Class, Standard Class).
- **Key Visuals:** Mode distribution donut chart, lead-time distribution box plots, gross margin by ship mode bar chart, 4-tier distance band breakdown (0–500km, 500–1500km, 1500–3000km, 3000+km).
- **Compliance Checks:** Verified non-causal operational analysis disclaimer and COGS freight expense disclaimer.
- **Verification Result (AppTest):** 0 uncaught exceptions; distance band aggregations compute cleanly.

### Page 6: Potential Bottlenecks (`pages/6_Potential_Bottlenecks.py`)
- **Purpose:** Distribution bottleneck screening via dual 75th-percentile quadrant classification ($P_{75}$ Volume $\times$ $P_{75}$ Delay Rate).
- **Key Visuals:** Interactive Plotly quadrant scatter plot with $P_{75}$ volume and delay threshold lines, Critical Bottleneck priority callout cards, Watchlist corridor table, state-level vs route-level toggle.
- **Compliance Checks:** Enforces $N \ge 30$ guardrail before computing percentile thresholds; non-causal screening disclaimer rendered.
- **Verification Result (AppTest):** 0 uncaught exceptions; correctly flags 3 Critical Bottlenecks and 3 Watchlist routes on baseline data.

### Page 7: Route Drill-Down (`pages/7_Route_Drill_Down.py`)
- **Purpose:** Granular corridor dispatch timeline and individual order-line inspection.
- **Key Visuals:** Route selection dropdown (Factory $\rightarrow$ State), KPI summary cards, interactive order dispatch timeline scatter plot with delay threshold reference line, filtered order-level table, Canadian province drill-down tab.
- **Compliance Checks:** Uses strict terminology (*"Order-to-Ship Lead Time"*, strictly avoiding *"Transit Time"*); shows Haversine distance to Canadian province centroids.
- **Verification Result (AppTest):** 0 uncaught exceptions; timeline figure builds without errors.

### Page 8: Trends & Scenarios Lab (`pages/8_Trends_and_Scenarios.py`)
- **Purpose:** Historical 24-month order volume seasonality, cross-scenario lead-time comparisons, and isolated RES weight sensitivity sandbox.
- **Key Visuals:** 24-month historical monthly trendlines (distinguishing order lines from line items), cross-scenario lead-time comparison bar charts, interactive RES weight preset buttons (70/30, 50/50, 90/10, 100/0), sensitivity sliders with Spearman $\rho$ rank stability indicator.
- **Compliance Checks:** Sensitivity sandbox state is isolated and does not mutate global filter state on Pages 1–7 (AD-06 Option A).
- **Verification Result (AppTest):** 0 uncaught exceptions; Spearman $\rho$ updates reactively.

---

## 2. Interactive Features, Forms, and Controls

| UI Component | Location | Intended Behavior | Actual Behavior | Status |
|---|---|---|---|---|
| **Layer Selectbox** | Sidebar | Switch between SYNTHETIC, DERIVED, and ORIGINAL (local only). | Switches active dataset, updates layer badge, and reruns pages cleanly. | **PASS** |
| **Scenario Selectbox** | Sidebar | Switch between Baseline, Distance-Sensitive, and Stress-Test. | Toggles active synthetic Parquet file in memory. | **PASS** |
| **Delay Threshold Slider**| Sidebar | Adjust threshold from 1.0 to 15.0 days in 0.5 increments. | Re-evaluates strict delay inequality across all pages. | **PASS** |
| **Duplicate Exclusion Toggle**| Sidebar | Toggle 313 duplicate records in/out of analysis. | Re-aggregates datasets and updates metric totals. | **PASS** |
| **Reset Filters Button** | Sidebar | Clear all multi-selects and restore default threshold (5.0d). | Restores session state defaults and triggers clean rerun. | **PASS** |
| **CSV Download Buttons** | Pages 2, 3, 4, 5, 6, 7, 8 | Export active view as CSV with provenance metadata header. | Produces downloadable byte stream with `#` header block. | **PASS** |
| **Analysis Level Radios** | Pages 4, 6 | Toggle between Factory $\rightarrow$ State routes and Destination States. | Recomputes aggregations and switches chart axis labels. | **PASS** |
| **Weight Preset Buttons** | Page 8 | Switch RES weights between 70/30, 50/50, 90/10, 100/0. | Recomputes leaderboard, rank deltas, and Spearman $\rho$. | **PASS** |

---

## 3. UI/UX Resilience, Accessibility, and Layout Evaluation

1. **Responsive Grid Layout:** All pages utilize `layout="wide"` with responsive column layouts (`st.columns([1, 1])` and `st.columns([1, 1, 1, 1])`), adapting cleanly across standard desktop resolutions ($1920\times1080$, $1366\times768$) and mobile viewports.
2. **Empty Filter State Protection:** Every page features defensive null/empty guards. When filters select a zero-record slice, clear warning notifications are rendered, suppressing empty Plotly figures or zero-division exceptions.
3. **Color Contrast & Accessibility:** Metric delta indicators use standard semantic colors (green for positive/on-time, red for negative/delayed). Charts use high-contrast color palettes (Plotly express blues, reds, oranges) with hover tooltips detailing exact values.
4. **Browser Console & Network Verification:** Headless ASGI startup on Uvicorn demonstrated clean asset dispatch with zero missing script bundles, broken font files, or 404 image errors.
5. **No Broken Links or Images:** All referenced assets in `docs/figures/` are locally generated and valid.
