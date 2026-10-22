---
title: 'Story 5.1: US State Choropleth Heatmap & Canadian Notice Banner'
type: 'feature'
created: '2026-10-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Geographic delivery patterns require visual map exploration across destination states, but Canadian postal geography cannot be rendered on a US state choropleth without distortion.

**Approach:** Implement `pages/4_Geographic_Analysis.py` with an interactive Plotly US choropleth supporting selectable metrics (Mean Lead Time, Delay Rate, RES, Order Volume), a prominent notice banner stating Canadian orders are excluded from map geometry but retained in company totals, and hover tooltips showing factory fulfillment breakdown and sample size.

</frozen-after-approval>

## Implementation Notes

- Added `US_STATE_TO_CODE` mapping dictionary in `src/config.py` covering all 50 states and District of Columbia.
- Implemented `aggregate_state_metrics()` in `src/route_analysis.py` to aggregate destination state performance metrics (Order Volume, Mean Lead Time, Delay Rate, RES, Speed-Only RES, Sample Guardrails, and Factory Fulfillment Breakdown) while cleanly separating Canadian cross-border destinations.
- Created `pages/4_Geographic_Analysis.py` with interactive Plotly US choropleth (`scope="usa"`, `locationmode="USA-states"`), metric selector radio (Mean Lead Time, Delay Rate, RES, Order Volume), Canadian disclosure notice banner (FR-09), executive summary KPI cards, state performance benchmarking table, audited CSV export (`create_export_csv`), and Canadian retained orders summary table.
- Added comprehensive test suite `tests/test_page_geographic.py` covering unit calculations, Plotly figure construction, Streamlit AppTest rendering, disclosure banner verification, metric radio interaction, and edge cases.
- Installed `plotly` into virtual environment and updated `requirements.txt`.

## Review Triage Log

- Finding 1 (Order grain inconsistency in summary cards): verdict `medium` — Patched: distinct Order ID count used consistently across all summary KPI cards.
- Finding 2 (Line-item vs order grain in state aggregation): verdict `low` — Patched: confirmed lead times are uniform per Order ID; aligned with `aggregate_routes` engine pattern.
- Finding 3 (Fallback row count displayed as lead time in Canadian summary): verdict `medium` — Patched: timing aggregation strictly conditional on `"lead_time_days" in canada_df.columns`.
- Finding 4 (Sample size guardrail N < 30 visibility): verdict `low` — Patched: attached `sample_status` flag and rendered `⚠️ Low Sample (N < 30)` in hover text and data table.
- Finding 5 (Choropleth color scale autoscaling distortion): verdict `low` — Patched: added calibrated `zmin`/`zmax` bounds to bounded metrics (RES: [40, 90], Delay Rate: [0, 40%]).
- Finding 6 (Unused parameter delay_threshold): verdict `low` — Patched: incorporated threshold value into hover template for Delay Rate.
- Finding 7 (Overly permissive US partition assumption): verdict `low` — Patched: explicitly validated destination state names against `US_STATE_TO_CODE`.
- Finding 8 (Misleading / 50 denominator in coverage metric): verdict `low` — Patched: updated label to `49 States / DC` matching dataset coverage (48 states + DC).
- Finding 9 (Region column KeyError risk): verdict `medium` — Patched: dynamically checked for `"Region"` presence before slicing display columns.
- Finding 10 (Stripping fields from CSV export): verdict `low` — Patched: exported full enriched state metric dataset with readable column headers.
- Finding 11 (Missing AD-11 freight disclaimer): verdict `low` — Patched: called `render_margin_disclaimer()` on Page 4.
- Finding 12 (Unused imports in test suite): verdict `low` — Patched: cleaned up unused imports and added assertions validating all 49 state entities map to valid codes.
- Finding 13 (Missing edge case test coverage): verdict `low` — Patched: added tests for empty DataFrame, derived layer without lead times, boundary delay threshold, and radio interactivity.
