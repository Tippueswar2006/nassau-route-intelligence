---
title: 'Story 5.4: Route Drill-Down & Order-to-Ship Timeline Visualizer'
type: 'feature'
created: '2026-10-21'
status: 'done'
baseline_commit: 'NO_VCS'
route: 'dispatch'
review_loop_iteration: 1
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Warehouse managers and operations leaders need lane-level granularity to investigate individual order timelines, lead times, delay frequencies, and Canadian route distances.
**Approach:** Implement `pages/7_Route_Drill_Down.py` providing route selection controls, lane summary KPI cards, an interactive order-to-ship timeline scatter chart with threshold indicators, a Canadian centroid distance badge, a detailed order lines table, and audited CSV exports.

## Boundaries & Constraints

**Always:**
- **Route Selection & Grain Consistency (AD-04):**
  - Dropdown populated with all routes matching active sidebar filters, displaying lane volume (e.g. `Lot's O' Nuts -> Texas (479 orders)`).
  - Defaults to `"Lot's O' Nuts -> Texas"` if available under current filters; otherwise defaults to the route with the highest order volume.
  - Distinguish between **Order Lines** (`Order ID` distinct count, representing customer shipments) and **Line Items** (`Row ID` count, representing individual product items).
- **KPI Summary Metrics (AD-04, AD-11):**
  - Order Lines ($N$): distinct `Order ID`s.
  - Line Items: total row count.
  - Total Units: sum of `Units`.
  - Gross Revenue: sum of `Sales` ($).
  - Manufacturing COGS: sum of `Cost` ($), strictly labeled as manufacturing costs (never freight).
  - Commercial Gross Margin: `(Gross Profit / Sales) * 100.0` (%).
  - Mean & Median Order-to-Ship Lead Time: mean and median of `lead_time_days` in days.
  - Delay Rate (%): percentage of orders exceeding the active threshold.
  - Centroid Distance (km): Haversine distance in kilometers (`distance_km`).
- **Strict Delay Rule (AD-07, PRD Section 11):**
  - Evaluated using strict inequality: `lead_time_days > threshold_days` (e.g., `lead_time > 5.0`).
  - An order with `lead_time_days == threshold_days` is strictly On-Time.
- **Strict Terminology (FR-12):**
  - Lead time must strictly be labeled **"Order-to-Ship Lead Time"**, NEVER "Transit Time" or "Carrier Delivery Time".
  - Timeline y-axis title: `"Order-to-Ship Lead Time (Days)"`.
- **Canadian Route Geographic Support (FR-09, FR-12):**
  - When a Canadian destination is selected (`is_canadian == True` or `Country/Region == 'Canada'`), display a prominent Canadian fulfillment badge displaying factory-to-province centroid distance (`distance_km`), origin and centroid coordinates, and an explanatory notice documenting that Canadian orders are retained in company financial and volume totals but excluded from US state choropleth geometries.
- **Sample Size Guardrails (AD-07):**
  - If selected route has $N \ge 30$, display a green robust sample badge.
  - If selected route has $N < 30$, display an amber statistical noise warning banner (`AD-07: Low sample size N < 30`).
- **Layer Handling & Graceful Degradation (AD-02):**
  - Under `SYNTHETIC`: Render complete timeline scatter plot with simulated lead times and threshold line.
  - Under `DERIVED` / `ORIGINAL`: Display an informative warning that lead-time simulation and delay timeline analysis require the `SYNTHETIC` layer. Render commercial metrics, centroid distance, and order lines table using historical dates.
- **Audited CSV Export (FR-14, AD-02, AD-11):**
  - Provide download button for the drilled-down order lines via `create_export_csv`, preserving commented provenance metadata (`layer`, `scenario`, `delay_threshold`, `route`, `filters`).
- **Mandatory Disclaimers:**
  - Prominent operational screening disclosure (FR-12, AD-08): non-causal screening notice.
  - AD-11 manufacturing COGS disclaimer via `render_margin_disclaimer()`.
- **Architecture Invariant:** Zero Streamlit imports in `src/`.

**Never:**
- Never use the term "Transit Time" for simulated order-to-ship fulfillment intervals.
- Never confuse manufacturing COGS with freight shipping charges (AD-11).
- Never throw unhandled exceptions on empty filters, missing lead times, or single-order routes.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Baseline Canonical Bottleneck | Select `Lot's O' Nuts -> Texas` under SYNTHETIC baseline | Summary KPIs (N=479, Delay Rate=23.4%), interactive timeline scatter chart with 5.0d threshold line, order table, CSV export | Normal render |
| Canadian Route Drill-Down | Select `Lot's O' Nuts -> Ontario` (or any Canadian lane) | Prominent 🇨🇦 Canadian Centroid Distance badge (2,959.5 km), timeline chart, order table with Canadian provinces | Normal render |
| Low-Sample Route ($N < 30$) | Select route with $N < 30$ orders | Display summary KPIs, timeline points, and an explicit amber warning: `AD-07: Sample size N < 30` | Statistical disclaimer banner |
| Historical Data Layer | DERIVED or ORIGINAL layer (missing `lead_time_days`) | Display valid commercial KPIs and order table with historical dates; display warning that timeline and delay analysis require SYNTHETIC layer | Graceful fallback; no crash |
| Zero Filter Matches | Filters yield 0 orders (`df.empty == True`) | Display `st.warning("⚠️ No orders found matching active sidebar filters.")` | Early return cleanly |
| Single Order on Route | Route with exactly 1 order line ($N = 1$) | Single point on timeline chart, scalar KPIs without variance crash | Handle $N=1$ std dev cleanly |

</frozen-after-approval>

## Code Map

- `pages/7_Route_Drill_Down.py` -- Main Page 7 Streamlit application module with route selector, KPI cards, timeline scatter plot, Canadian centroid distance badge, order table, and export button
- `src/route_analysis.py` -- Pure calculation functions: `aggregate_routes`, `filter_eligible_routes`, `haversine_distance_km`
- `src/exports.py` -- `create_export_csv`, `parse_export_header` for audited provenance CSV exports
- `src/config.py` -- `MIN_SAMPLE_SIZE`, `DEFAULT_DELAY_THRESHOLD`, `EXPEDITED_MODES`, `SHIPPING_MODES`
- `app.py` -- `get_active_dataset`, `render_sidebar_filters`, `render_layer_banner`, `render_margin_disclaimer`
- `tests/test_page_drill_down.py` -- Unit and Streamlit `AppTest` test suite covering rendering, route selection, timeline chart, Canadian routes, empty filters, and exports

## Tasks & Acceptance

**Execution:**
- [x] `pages/7_Route_Drill_Down.py` -- Implement Route Drill-Down page with KPI summary cards, timeline chart with threshold line, Canadian centroid badge, order lines table, and audited export -- Fulfills Story 5.4 and FR-12
- [x] `tests/test_page_drill_down.py` -- Create comprehensive unit and Streamlit AppTest test suite -- Verifies Story 5.4 acceptance criteria

**Acceptance Criteria:**
- Given `pages/7_Route_Drill_Down.py`, when a route (e.g. *Lot's O' Nuts -> Texas*) is selected, then summary metrics and an order line table are displayed.
- And an interactive order timeline chart shows order date, ship date, lead time, and threshold line.
- And lead time is strictly labeled "Order-to-Ship Lead Time", never "Transit Time".
- And Canadian routes display factory-to-province centroid distances.

## Implementation Notes

- Rigorously enforced the distinction between Order Lines (distinct `Order ID` count, N=479 for Lot's O' Nuts -> Texas) and Line Items (total product rows, N=548).
- Implemented `build_timeline_figure` with Order Date on x-axis, strictly labeled "Order-to-Ship Lead Time (Days)" on y-axis, threshold reference line, and hover tooltip displaying Order ID, Customer ID, Order Date, Ship Date, Ship Mode, and Status.
- Implemented Canadian fulfillment lane notice with Haversine factory-to-province centroid distance (2,959.5 km for Ontario) and Canadian network order table.
- Connected audited CSV export engine via existing `create_export_csv` in `src/exports.py` passing route DataFrames directly with complete provenance metadata (`layer`, `scenario`, `delay_threshold`, `route`, `screening`).
- Verified 11/11 tests passing in `tests/test_page_drill_down.py` and 107/107 tests passing across the entire repository.

## Spec Change Log

## Review Triage Log

- **SEC-01: [MAJOR] IndexError on missing Order Date in `build_timeline_figure`**: Fixed by resetting DataFrame index after `dropna(subset=['lead_time_days'])` and using NumPy-based boolean indexing for trace mapping.
- **SEC-02: [MAJOR] IndexError in `render_canadian_route_section` on empty DataFrames**: Fixed by adding an immediate empty DataFrame guard `if route_df.empty: return`.
- **SEC-03: [MINOR] Table vs Tooltip Ship Date Discrepancy under Synthetic Layer**: Fixed by mapping `Ship_Date_Synthetic` to `Ship Date (Synthetic)` in order lines table.
- **SEC-04: [MINOR] Conditional Assertion Bypass in `test_low_sample_warning_guardrail`**: Fixed by asserting candidate presence `assert low_sample_candidate in sel.options` before setting widget values.
- **SEC-05: [MINOR] HTML `<br>` tags in `st.info`**: Replaced with standard markdown formatting.
- **SEC-07: [MINOR] Missing Edge-Case Tests**: Added `test_single_order_route_and_missing_columns_robustness` testing $N = 1$, missing date/mode columns, and empty DataFrames. Total test suite expanded to 12 tests.

## Design Notes

1. **Timeline Chart Construction:**
   Plotly scatter plot with `x="Order Date"`, `y="lead_time_days"`, `color="delay_status"` (`Delayed` = `#d62728`, `On-Time` = `#1f77b4`).
   Add horizontal dashed line at `y=filters["delay_threshold"]` annotated as `Delay Threshold: {threshold:.1f}d`.
   Y-axis title: `"Order-to-Ship Lead Time (Days)"`. Hover template includes `Order ID`, `Customer ID`, `Ship Mode`, `Product Name`, `Order Date`, `Ship Date`, and `Order-to-Ship Lead Time`.

2. **Canadian Centroid Distance Badge:**
   For Canadian routes (`is_canadian == True` or `Country/Region == 'Canada'`), retrieve `distance_km` from the route record and display:
   `🇨🇦 Canadian Fulfillment Lane: Factory-to-Province Centroid Distance = {distance_km:,.1f} km`.

3. **Audited CSV Export:**
   Export selected route order lines via `create_export_csv(route_df, metadata={...})` preserving provenance headers and data layer context.
