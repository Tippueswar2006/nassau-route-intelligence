# Epic 5 Context: Interactive Geographic, Ship Mode, Bottleneck & Drill-Down Analytics (Phase 5 Deep Dives)

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Provide interactive deep-dive analytics for Nassau Route Intelligence, including Plotly US state choropleths with Canadian notices, ship mode cost-transit trade-offs, interactive bottleneck quadrant scatter plots, order-level timelines, and sensitivity trend labs.

## Stories

- Story 5.1: US State Choropleth Heatmap & Canadian Notice Banner
- Story 5.2: Ship Mode Distribution & Margin-by-Mode Analysis
- Story 5.3: Interactive Bottleneck Quadrant Scatter Visualizer
- Story 5.4: Route Drill-Down & Order-to-Ship Timeline Visualizer
- Story 5.5: Scenario Trends & RES Weight Sensitivity Lab

## Requirements & Constraints

- FR-09 (Geographic view): State metric selector (Mean Lead Time, Delay Rate, RES, Order Volume); clear legend and units; Canadian destinations excluded from US map geometry with a persistent banner noting Canadian orders are retained in company financial and volume metrics; state hover reveals factory fulfillment breakdown and sample size.
- FR-10 (Ship-mode comparison): Distributions across Standard vs Expedited modes and distance bands; margin-by-mode analysis with explicit non-causal language.
- FR-11 (Bottleneck flags): Plotly scatter plot (Volume vs Delay Rate) with 75th percentile screening quadrant, sample size N, and watchlist highlights.
- FR-12 (Drill-down): Route/state summary, order-to-ship timeline with threshold marker, strictly labeled "Order-to-Ship Lead Time", never "Transit Time".
- FR-17 & FR-19 (Trends & Lead-time basis): Valid original dates for volume trends, synthetic scenarios for lead time trends; toggle between mode-adjusted and raw lead time.
- NFR-01 to NFR-07: Sub-second UI interactions via cached data, zero Streamlit imports in `src/`, explicit layer badges, accessible color scales, and zero PII leaks.

## Technical Decisions

- Architecture: Pure headless calculation engines in `src/` (zero Streamlit imports); presentation rendering, caching (`@st.cache_data`), and filters in `pages/` and `app.py`.
- US State Choropleth: Render using Plotly Express / Graph Objects `choropleth` with `locationmode="USA-states"` and US postal 2-letter state codes (`locations='State_Code'`).
- Canada Exclusion: Canadian postal geography (3-character partial postal codes) cannot render on US state choropleth without distortion. Filter out Canadian rows from map visualization and show a persistent notice banner stating Canadian orders are retained in company totals.
- Metrics on Map: State-level aggregation of Mean Lead Time, Delay Rate (based on active analysis threshold), RES (mode-adjusted by default), and Order Volume.
- Hover details: Must show factory fulfillment breakdown (counts/percentages per factory for the hovered state) and total sample size.

## Cross-Story Dependencies

- Depends on Epic 4: Application shell, global filters, dataset caching (`get_active_dataset`), layer provenance banners (`render_layer_banner`), and RES scoring engine (`src/metrics.py`, `src/route_analysis.py`).
- Precedes remaining Epic 5 stories (5.2 through 5.5).
