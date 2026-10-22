---
title: 'Story 4.4: Route Efficiency Leaderboard Page'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 4
story: 4
story_key: '4-4-route-efficiency-leaderboard-page'
---

# Story 4.4: Route Efficiency Leaderboard Page

## Intent
**Problem:** Route benchmarking must show Top 10 and Bottom 10 lanes based on Route Efficiency Score (RES) while filtering small samples ($N < 30$) and allowing mode-adjusted vs raw comparisons.
**Approach:** Implement `pages/3_Route_Efficiency.py` with fixed 70/30 RES scoring, mode-adjusted vs raw toggle with rank deltas, and dedicated low-sample tables.

## User Story
As a logistics manager,
I want Top 10 and Bottom 10 route leaderboards ranked by Route Efficiency Score (RES) with a toggle between mode-adjusted and raw lead time,
So that I can identify best- and worst-performing shipping lanes.

## Acceptance Criteria
- **Given** `pages/3_Route_Efficiency.py`,
- **When** viewed in the dashboard,
- **Then** Top 10 and Bottom 10 routes are displayed with RES (70% speed / 30% variability fixed weighting),
- **And** routes with $N < 30$ are excluded from leaderboards and listed in an Insufficient Sample table,
- **And** toggle allows switching between Mode-Adjusted RES (default) and Raw Lead Time RES, showing side-by-side rank delta,
- **And** changing the delay threshold slider updates delay counts and rates dynamically.

## Implementation Details & Boundaries
- Target file: `pages/3_Route_Efficiency.py`
