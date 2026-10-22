---
title: 'Story 5.5: Scenario Trends & RES Weight Sensitivity Lab'
type: 'feature'
created: '2026-10-21'
status: 'done'
baseline_commit: 'NO_VCS'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Executive strategists need to analyze long-term monthly order volume seasonality from valid Original dates alongside synthetic scenario lead-time trends, and require a dedicated sandbox to test Route Efficiency Score (RES) sensitivity across alternative speed/variability weights (50/50, 70/30, 90/10) without destabilizing Pages 1–7.
**Approach:** Implement `pages/8_Trends_and_Scenarios.py` with monthly order volume charts (Original), multi-scenario monthly mean lead-time trends (Baseline vs Stress Test vs Distance Sensitive), and an isolated interactive RES weight sensitivity lab with rank stability indicators and audited CSV exports.

## Boundaries & Constraints

**Always:**
- **Monthly Order Volume Trends (FR-17, AD-02):**
  - Evaluated on valid Original/Derived dates (distinct `Order ID`s aggregated by month).
  - Explicitly labeled as sourced from the **Original/Derived Layer (Valid Order Dates)**.
- **Monthly Lead-Time Trends (FR-17, AD-02):**
  - Evaluated on Synthetic scenarios (Baseline, Stress Test, Distance Sensitive).
  - Strictly labeled **"Order-to-Ship Lead Time"**, NEVER "Transit Time" or "Delivery Time".
  - Plotly multi-line chart comparing monthly mean lead times across scenarios.
- **Baseline vs. Stress Test Scenario Comparison (FR-17, Section 11):**
  - Side-by-side or overlaid comparison highlighting network disruption effects under the Stress Test scenario (e.g., Texas route delay spikes).
- **Isolated RES Weight Sensitivity Lab (FR-19, Section 13):**
  - Interactive slider for Speed Weight ($w_{\text{speed}} \in [0.0, 1.0]$) with Variability Weight dynamically constrained to $w_{\text{var}} = 1.0 - w_{\text{speed}}$.
  - Preset configuration buttons: `Default (70/30)`, `Balanced (50/50)`, `Speed-Focused (90/10)`, `Speed-Only (100/0)`.
  - Sensitivity slider state is strictly isolated to Page 8 (does not mutate global `st.session_state` filter weights used by Pages 1–7).
  - Side-by-side table displaying Route Lane, Volume ($N$), Mean Lead Time, Std Dev, Baseline RES (70/30), Sensitivity RES, and Rank Delta ($\Delta\text{Rank} = \text{Rank}_{70/30} - \text{Rank}_{\text{Sens}}$).
  - Rank stability indicators: Spearman rank correlation ($\rho$) and Top 10 retention percentage.
- **Sample Size Guardrails (AD-07):**
  - Enforce $N \ge 30$ sample size guardrail on route ranking sensitivity table.
- **Audited CSV Export (FR-14, AD-11):**
  - Provide download buttons via `create_export_csv` for both monthly trends and sensitivity rank delta tables, preserving provenance headers (`# Data Layer`, `# Active Scenario`, `# Delay Threshold`, `# Active Filters`).
- **Disclaimers & Disclosures:**
  - Mandatory non-causal operational screening disclosure (FR-17, AD-08).
  - Mandatory manufacturing COGS vs freight shipping disclaimer via `render_margin_disclaimer()` (AD-11).
- **Architecture Invariant:** Zero Streamlit imports in `src/`.

**Never:**
- Never use the term "Transit Time" for simulated lead times.
- Never allow Page 8 sensitivity sliders to mutate global sidebar session state used by Pages 1–7.
- Never confuse manufacturing COGS with freight transportation expenses (AD-11).
- Never throw unhandled exceptions on empty filter states or missing columns.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Default Load | Baseline SYNTHETIC active | Monthly volume bar chart (Original), multi-scenario lead time line chart, 70/30 default sensitivity lab with $\Delta\text{Rank}=0$ | Clean render |
| Preset Switch to 50/50 | Click `Balanced (50/50)` button | Speed slider updates to 0.50, Variability to 0.50, re-computes Sensitivity RES, displays rank shift and stability $\rho$ | Update table and metrics |
| Extreme Weighting (100/0) | Click `Speed-Only (100/0)` | Speed=1.0, Var=0.0; variability penalty set to 0; pure speed ranking displayed | Handle zero variability cleanly |
| Historical Data Layer | DERIVED or ORIGINAL active | Monthly volume trend renders normally; synthetic scenario trends and sensitivity lab display informative notice that scenario analysis requires SYNTHETIC layer | Graceful degradation; no crash |
| Empty Filter Selection | Filters yield 0 orders | Display `st.warning("⚠️ No orders found matching active sidebar filters.")` | Clean early return |

</frozen-after-approval>

## Code Map

- `pages/8_Trends_and_Scenarios.py` -- Main Page 8 Streamlit application module with monthly volume trends, multi-scenario lead time comparisons, isolated RES sensitivity sandbox, rank stability metrics, and export engines
- `src/route_analysis.py` -- `aggregate_routes`, `filter_eligible_routes`, `assign_route_hierarchy`
- `src/metrics.py` -- `compute_route_res`, `generate_leaderboards`, `DEFAULT_RES_WEIGHT_SPEED`, `DEFAULT_RES_WEIGHT_VARIABILITY`
- `src/exports.py` -- `create_export_csv`, `parse_export_header`
- `src/load_data.py` -- `load_prepared_artifacts`
- `src/config.py` -- `MIN_SAMPLE_SIZE`, `DEFAULT_DELAY_THRESHOLD`
- `app.py` -- `get_active_dataset`, `render_sidebar_filters`, `render_layer_banner`, `render_margin_disclaimer`
- `tests/test_page_trends_and_scenarios.py` -- Automated unit & Streamlit AppTest test suite for Page 8

## Tasks & Acceptance

**Execution:**
- [x] `pages/8_Trends_and_Scenarios.py` -- Implement Trends & Scenarios page with monthly volume trends, scenario lead-time lines, isolated RES sensitivity lab, rank stability metrics, and CSV exports -- Fulfills Story 5.5 and FR-17/FR-19
- [x] `tests/test_page_trends_and_scenarios.py` -- Implement automated unit and AppTest test suite verifying volume trends, scenario comparisons, RES slider isolation, rank stability, and exports -- Verifies Story 5.5 acceptance criteria

**Acceptance Criteria:**
- Given `pages/8_Trends_and_Scenarios.py`, when viewed in the dashboard, then monthly order volume is displayed using valid Original dates (2024–2025).
- And monthly mean lead times are displayed using Synthetic scenarios.
- And interactive sensitivity sliders (Page 8 only) allow testing alternative RES weights (e.g. 50/50, 70/30, 90/10) with side-by-side rank stability indicators.

## Implementation Notes

- **Implementation File:** `pages/8_Trends_and_Scenarios.py`
  - Monthly Volume Trends: Aggregates distinct orders (`Order ID` nunique) and product line items (`Row ID` count) across 24 calendar months (2024-2025). Displays bar chart with hover metrics and breakdown table.
  - Multi-Scenario Lead-Time Trajectories: Computes monthly mean and median lead times across Baseline, Stress Test, and Distance Sensitive scenarios. Multi-line Plotly chart with delay threshold reference line and strict "Order-to-Ship Lead Time" terminology.
  - Scenario Comparison Cards: Side-by-side cards highlighting disruption effects under Texas shock stress test (+delay rate and lead time delta).
  - Isolated RES Weight Sensitivity Sandbox: Interactive speed weight slider with preset buttons (70/30, 50/50, 90/10, 100/0). Enforces sample size guardrail ($N \ge 30$). Computes side-by-side Baseline RES vs Sensitivity RES, Rank Delta ($\text{Rank}_{70/30} - \text{Rank}_{\text{Sens}}$), Spearman rank correlation ($\rho$), Top 10 retention %, mean absolute rank shift, and max gain/drop.
  - Audited CSV Exports: Three download buttons using `create_export_csv`, prepending provenance metadata headers.
  - Disclaimers: Non-causal operational screening disclosure (FR-17, AD-08) and manufacturing COGS disclaimer (AD-11).
- **Test File:** `tests/test_page_trends_and_scenarios.py`
  - 15 comprehensive automated tests covering unit functions, math invariants, extreme weights, CSV provenance, and Streamlit AppTest integration.
  - 100% test pass rate across all 123 tests in repository suite.

## Spec Change Log

## Review Triage Log

## Design Notes

1. **Monthly Volume Aggregation (Original Dates):**
   Parse `Order Date` with `pd.to_datetime(..., errors='coerce', dayfirst=True)`.
   Extract `year_month = dt.to_period("M").astype(str)`.
   Aggregate distinct orders: `df.groupby("year_month")["Order ID"].nunique()`.
   Plotly bar chart with formatted dates (e.g., `Jan 2024`, `Feb 2024`).

2. **Scenario Lead-Time Trends:**
   Load artifacts for `baseline`, `stress_test`, and `distance_sensitive`.
   For each scenario, compute monthly mean of `lead_time_days`.
   Plotly multi-trace line chart: Baseline (Blue, `#1f77b4`), Stress Test (Red, `#d62728`), Distance Sensitive (Orange, `#ff7f0e`).
   Strictly label y-axis `"Order-to-Ship Lead Time (Days)"`.

3. **Isolated RES Weight Sensitivity Sandbox:**
   Use unique widget keys prefixed with `sens_` (e.g. `sens_w_speed`, `sens_w_var`) to prevent interference with global sidebar filters.
   Compute RES under baseline weights (0.70 / 0.30) and sensitivity weights ($w_{\text{speed}} / w_{\text{var}}$).
   Compute Rank Delta: $\Delta\text{Rank} = \text{Rank}_{\text{Baseline}} - \text{Rank}_{\text{Sensitivity}}$. Positive delta indicates improved rank under sensitivity weights; negative indicates drop.
   Rank Stability: Spearman rank correlation $\rho = \text{corr}(r_{\text{base}}, r_{\text{sens}})$.
