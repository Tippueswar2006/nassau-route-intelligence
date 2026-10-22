---
epic_num: 5
title: "Interactive Geographic, Ship Mode, Bottleneck & Drill-Down Analytics"
status: ready-for-dev
phase: "Phase 5 Deep Dives"
depends_on: ["epic-4"]
fr_coverage: ["FR-09", "FR-10", "FR-11", "FR-12", "FR-17"]
nfr_coverage: ["NFR-01", "NFR-02", "NFR-05"]
---

# Epic 5: Interactive Geographic, Ship Mode, Bottleneck & Drill-Down Analytics

## Goal
Deliver advanced visual analytics including Plotly US state choropleths with Canadian notices, ship mode cost-transit trade-offs, interactive bottleneck quadrant scatter plots, order timelines, and sensitivity trend labs.

## Status: READY-FOR-DEV (FIRST INCOMPLETE EPIC)

## Stories
- [Story 5.1: US State Choropleth Heatmap & Canadian Notice Banner](../stories/5-1-us-state-choropleth-heatmap-and-canadian-notice-banner.md) — *Status: READY-FOR-DEV*
- [Story 5.2: Ship Mode Distribution & Margin-by-Mode Analysis](../stories/5-2-ship-mode-distribution-and-margin-by-mode-analysis.md) — *Status: BACKLOG*
- [Story 5.3: Interactive Bottleneck Quadrant Scatter Visualizer](../stories/5-3-interactive-bottleneck-quadrant-scatter-visualizer.md) — *Status: BACKLOG*
- [Story 5.4: Route Drill-Down & Order-to-Ship Timeline Visualizer](../stories/5-4-route-drilldown-and-order-timeline-visualizer.md) — *Status: BACKLOG*
- [Story 5.5: Scenario Trends & RES Weight Sensitivity Lab](../stories/5-5-scenario-trends-and-res-weight-sensitivity-lab.md) — *Status: BACKLOG*

## Dependencies & Invariants
- Depends on Epic 4 Streamlit application shell and state management.
- Canadian orders excluded from US choropleth with visible notification banner; totals retained.
- Strict wording: "Order-to-ship lead time", never carrier transit or delivery time.
- Weight sensitivity sliders (50/50, 70/30, 90/10) isolated to Page 8 only.
