---
title: 'Story 5.3: Interactive Bottleneck Quadrant Scatter Visualizer'
type: 'feature'
created: '2026-10-21'
status: 'done'
review_loop_iteration: 1
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** Operations directors need an intuitive visual tool to isolate high-volume, high-delay fulfillment routes and potential bottlenecks across the distribution network.

**Approach:** Implement `pages/6_Potential_Bottlenecks.py` rendering an interactive Plotly quadrant scatter plot (Route Volume vs Delay Rate) with 75th percentile reference lines, Critical Bottleneck badges, Watchlist highlights, detailed route inspection tables, and audited CSV exports.

## Boundaries & Constraints

**Always:**
- Enforce sample size guardrail ($N \ge 30$) before screening bottlenecks into the quadrant plot and tables (AD-07).
- Plot Route Volume (distinct order lines) on the $x$-axis and Delay Rate (%) on the $y$-axis with dashed reference lines for 75th percentiles and median delay.
- Routes in the upper-right quadrant ($\text{Volume} \ge P_{75}$ and $\text{Delay Rate} \ge P_{75}$) are categorized as Critical Bottlenecks.
- Routes with $\text{Volume} \ge P_{75}$ and $\text{Delay Rate} > \text{Median}$ (not already Critical Bottlenecks) are categorized as Watchlist.
- Labeled clearly as "Potential Bottlenecks" (screening signals, not proven causal proof).
- Include dedicated inspection tables for Critical Bottlenecks and Watchlisted routes with sample size $N$, order lines, line items, and delay rate.
- Decouple presentation from pure backend logic in `src/` (strictly zero Streamlit imports in `src/`).

**Never:**
- Never confuse manufacturing COGS with freight transportation costs (AD-11).
- Never claim operational root cause without operational logs.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Calibrated Baseline / Stress Test | Active SYNTHETIC dataset with lead times | Plotly scatter plot with $x$=Volume, $y$=Delay Rate %, $P_{75}$ reference lines, Critical & Watchlist tables | No error expected |
| Empty Filter Selection | Filter combination yielding 0 records | Warning notice prompting user to broaden filters | Clean warning banner; no crash |
| Historical Data Layer | ORIGINAL or DERIVED layer without simulated lead times | Informative notice explaining that bottleneck screening requires calibrated timing from SYNTHETIC layer | Display notice and prevent null math crashes |

</intent-contract>

## Code Map

- `src/bottleneck_rules.py` -- `flag_bottlenecks`, `evaluate_bottleneck_recovery`, screening rules for $P_{75}$ volume and delay
- `src/route_analysis.py` -- `aggregate_routes`, `filter_eligible_routes`, `validate_layer_isolation`
- `src/config.py` -- `MIN_SAMPLE_SIZE`, `DEFAULT_DELAY_THRESHOLD`, `ROBUSTNESS_SEEDS`
- `src/exports.py` -- `create_export_csv`
- `pages/6_Potential_Bottlenecks.py` -- Main Page 6 presentation visualizer
- `tests/test_page_bottlenecks.py` -- Automated unit & AppTest test suite for Page 6

## Tasks & Acceptance

**Execution:**
- `pages/6_Potential_Bottlenecks.py` -- Build interactive quadrant scatter plot, reference lines, category badges, summary metrics, and tables -- Fulfills Story 5.3 and FR-11 requirements
- `tests/test_page_bottlenecks.py` -- Add comprehensive test suite verifying rendering, reference lines, quadrant classifications, and empty-state handling -- Verifies story acceptance criteria

**Acceptance Criteria:**
- Given `pages/6_Potential_Bottlenecks.py`, when viewed in the dashboard, then a Plotly scatter plot plots Route Volume ($x$) against Delay Rate ($y$).
- And reference lines display the 75th percentile thresholds for volume and delay rate.
- And routes in the upper-right quadrant are flagged as Critical Bottlenecks with sample size $N$ and volume metrics.
- And watchlisted routes ($\text{Delay Rate} > \text{Median}$) are highlighted.

## Spec Change Log

## Review Triage Log

- **Item 1: [MAJOR] CSV Export Schema Divergence & Test Disconnect**
  - *Triage*: Accept & Fixed. Passed un-renamed DataFrames (`critical_df`, `watchlist_df`, `flagged_df`) directly to `create_export_csv` so `sanitize_export_dataframe` can map human headers and retain full audited metadata.
- **Item 2: [MAJOR] Missing Test Coverage for Empty Filter Handling**
  - *Triage*: Accept & Fixed. Added `test_page_6_handles_empty_filters_gracefully()` asserting clean warning banner without exceptions when filters yield 0 matching orders.
- **Item 3: [MAJOR] Missing Audited CSV Export Button on Low-Sample Inspection Tab**
  - *Triage*: Accept & Fixed. Added audited CSV download button to `tab_low` (`nassau_{level}_low_sample_{scenario}.csv`) via `create_export_csv`.
- **Item 4: [MINOR] Mandatory AD-11 Margin Disclaimer Omitted on Early Returns**
  - *Triage*: Accept & Fixed. Invoked `render_margin_disclaimer()` near the top of `render_page()` before early exit guardrails.
- **Item 5: [MINOR] NumPy Array Type Coercion in Scatter Plot `customdata`**
  - *Triage*: Accept & Fixed. Packed `customdata` using `DataFrame.to_numpy()` with native data types preserved.
- **Item 6: [MINOR] Missing Visual Distinctness Beyond Color for Critical Bottlenecks**
  - *Triage*: Accept & Fixed. Added `QUADRANT_SYMBOL_MAP` assigning diamond markers and size 14 for Critical Bottlenecks, square for Watchlist, and circles/triangles for other categories.
- **Item 7: [MINOR] Display Inconsistency and Raw Floats in Low-Sample Tab**
  - *Triage*: Accept & Fixed. Formatted delay rates as percentages and applied standard column renaming to low-sample inspection table.
- **Item 8: [MINOR] Missing Widget Keys and Inaccurate State-Level Export Metadata**
  - *Triage*: Accept & Fixed. Added explicit `key` parameters (`radio_screening_level`, `dl_crit_csv`, `dl_watch_csv`, `dl_all_csv`, `dl_low_csv`) and dynamic level-aware filenames.
- **Item 9: [MINOR] Shallow Assertion Depth in State-Level Aggregation Test**
  - *Triage*: Accept & Fixed. Strengthened `test_state_level_aggregation_and_screening` with bounds checks and threshold validations.

## Design Notes

The scatter plot maps Route Volume ($x$, order lines) vs Delay Rate ($y$, percentage). Two orthogonal dashed reference lines partition the plot into four quadrants:
1. Upper-Right: Critical Bottleneck (High Volume >= P75, High Delay >= P75) - Red
2. Upper-Center: Watchlist (High Volume >= P75, Moderate Delay > Median) - Orange
3. Lower-Right: Efficient High Volume (High Volume >= P75, Low Delay <= Median) - Green
4. Upper-Left: Secondary Distress (Low Volume < P75, High Delay >= P75) - Purple
5. Lower-Left: Low Volume / Normal (Low Volume < P75, Low Delay < P75) - Gray
