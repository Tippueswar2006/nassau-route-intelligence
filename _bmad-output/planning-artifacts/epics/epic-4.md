---
epic_num: 4
title: "Core Executive Overview, Method Audit & Route Efficiency Dashboard"
status: done
phase: "Phase 4 Deliverables"
depends_on: ["epic-3"]
fr_coverage: ["FR-02", "FR-04", "FR-05", "FR-06", "FR-07", "FR-08", "FR-13", "FR-14", "FR-16", "FR-19", "FR-20"]
nfr_coverage: ["NFR-01", "NFR-02", "NFR-05", "NFR-06"]
---

# Epic 4: Core Executive Overview, Method Audit & Route Efficiency Dashboard

## Goal
Build the primary multi-page Streamlit dashboard application with global filtering, layer provenance badges, data quality reconciliation tables, executive financial KPIs, 70/30 fixed RES leaderboards, and audited CSV exports.

## Status: COMPLETED (100%)

## Stories
- [Story 4.1: Streamlit Application Shell, Global Filter State & Parquet Cache Loader](../stories/4-1-streamlit-shell-global-filter-state-and-parquet-cache-loader.md) — *Status: DONE*
- [Story 4.2: Data Quality & Method Audit Page](../stories/4-2-data-quality-and-method-audit-page.md) — *Status: DONE*
- [Story 4.3: Executive Overview & Margin Analysis Page](../stories/4-3-executive-overview-and-margin-analysis-page.md) — *Status: DONE*
- [Story 4.4: Route Efficiency Leaderboard Page](../stories/4-4-route-efficiency-leaderboard-page.md) — *Status: DONE*
- [Story 4.5: Provenance-Preserving Filtered CSV Export Engine](../stories/4-5-provenance-preserving-filtered-csv-export-engine.md) — *Status: DONE*

## Dependencies & Invariants
- Depends on Epic 3 calculation engines and Epic 2 Parquet artifacts.
- Presentation caching `@st.cache_data` lives in `app.py`, keeping `src/` modules 100% headless.
- Delay threshold slider (1–15d, default 5.0d) updates counts and rates on all pages.
- Target test: `tests/test_exports.py`.
