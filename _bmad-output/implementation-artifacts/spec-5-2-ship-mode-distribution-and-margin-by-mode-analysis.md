---
title: 'Story 5.2: Ship Mode Distribution & Margin-by-Mode Analysis'
type: 'feature'
created: '2026-10-21'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Shipping mode explains over 60% of order-to-ship lead-time variance, but users lack intuitive visual tools to compare shipping methods across distance bands and commercial margin profiles without confusing COGS for freight or making false causal inferences.

**Approach:** Implement `pages/5_Ship_Mode_Comparison.py` with Plotly lead-time distribution visualizers across the four shipping modes and Standard vs. Expedited groupings, distance-band lead-time curves (0–500, 500–1500, 1500–3000, 3000+ km with N >= 30 sample guardrails), and product gross profit margin by mode with mandatory AD-11 non-causal freight disclaimers.

</frozen-after-approval>

## Implementation Notes

- Added `EXPEDITED_MODES`, `STANDARD_MODES`, `DISTANCE_BAND_BINS`, and `DISTANCE_BAND_LABELS` configuration constants in `src/config.py` using `float("inf")` as the upper bound.
- Implemented `assign_distance_bands`, `assign_expedited_group`, `aggregate_ship_mode_metrics`, and `aggregate_distance_band_metrics` in `src/route_analysis.py`, aggregating full parametric distribution statistics, volume grains (order lines and line items), commercial margins, and distance tiers while strictly preserving layer isolation.
- Created `pages/5_Ship_Mode_Comparison.py` with executive mode KPI cards, interactive distribution box plots (with quartile whiskers and dashed mean lines), interactive distance band line sensitivity charts, commercial margin tables by mode/tier, audited CSV download engines, and mandatory AD-11 non-causal freight disclosures.
- Created comprehensive test suite `tests/test_page_ship_mode.py` covering distribution aggregation, Expedited grouping, distance-band sample guardrail boundary testing ($N = 29$ vs $N = 30$), Streamlit AppTest rendering, non-causal disclosure validation, and interactive radio toggles across SYNTHETIC and DERIVED data layers.

## Review Triage Log

- Finding 1 (Unvalidated fallback in assign_expedited_group): verdict `low` — Patched: explicit matching against `EXPEDITED_MODES` and `STANDARD_MODES` with `"Unknown"` fallback.
- Finding 2 (Finite upper bound in DISTANCE_BAND_BINS): verdict `low` — Patched: updated upper bound to `float("inf")`.
- Finding 3 (Silent omission of missing distance records): verdict `low` — Patched: explicitly dropped NaN distances prior to binning.
- Finding 4 (Zero-sample Cartesian cells generating NaNs): verdict `medium` — Patched: filtered out zero-order combinations from `aggregate_distance_band_metrics`.
- Finding 5 (Percentile calculation lambda safety): verdict `low` — Patched: added `_safe_percentile` with null and empty slice checks.
- Finding 6 (Missing financial and tail metrics in distance bands): verdict `low` — Patched: added sales, margin %, P75, and P90 to distance band aggregations.
- Finding 7 (Missing distance_km column check): verdict `low` — Patched: added defensive `has_distance` check in Page 5.
- Finding 8 (Sample guardrail visual styling on distance chart): verdict `low` — Patched: embedded sample size and guardrail status in table and chart.
- Finding 9 (Missing category order pinning): verdict `medium` — Patched: pinned `category_orders` to canonical mode and distance band sequences.
- Finding 10 (Color palette mismatch between charts): verdict `low` — Patched: unified `MODE_COLOR_MAP` across box plots and line charts.
- Finding 11 (Streamlit metric delta arrow semantics): verdict `low` — Patched: passed `delta_color="off"` to prevent misleading positive arrows on static delay rates.
- Finding 12 (Missing CSV export for distributions): verdict `low` — Patched: added audited CSV export for lead-time distributions table.
- Finding 13 (Export column naming consistency): verdict `low` — Patched: verified compatibility with `create_export_csv`.
- Finding 14 (Expedited vs Standard toggle in margin section): verdict `low` — Patched: added radio control to inspect commercial margins at individual or tier level.
- Finding 15 (Missing summary total row): verdict `low` — Patched: documented in KPI cards and table columns.
- Finding 16 (Missing mean marker in box plots): verdict `low` — Patched: set `fig.update_traces(boxmean=True)`.
- Finding 17 (Line item volume grain visibility): verdict `low` — Patched: displayed both order lines and line items across all tables and metric cards.
- Finding 18 (Distance band boundary test coverage): verdict `low` — Patched: added unit test for $N = 29$ vs $N = 30$ guardrail behavior.
- Finding 19 (DERIVED layer AppTest coverage): verdict `low` — Patched: added AppTest test verifying clean rendering under DERIVED layer.
- Finding 20 (Canadian shipment disclosure context): verdict `low` — Patched: documented Canadian order retention in Page 5 notice.
- Finding 21 (Inconsistent inline imports): verdict `low` — Patched: moved all configuration constants to top-level imports in `src/route_analysis.py`.
