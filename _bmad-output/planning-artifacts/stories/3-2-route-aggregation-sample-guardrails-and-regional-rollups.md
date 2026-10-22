---
title: 'Story 3.2: Route Aggregation, Sample Size Guardrails & Regional Rollups'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 3
story: 2
story_key: '3-2-route-aggregation-sample-guardrails-and-regional-rollups'
---

# Story 3.2: Route Aggregation, Sample Size Guardrails & Regional Rollups

## Intent
**Problem:** Routes with very small sample sizes (e.g. $N < 30$, or small factories with $< 100$ total orders) introduce extreme statistical volatility into leaderboards.
**Approach:** Implement `src/route_analysis.py` enforcing a minimum sample guardrail ($N \ge 30$) for state-level rankings, rolling small factories up to regional level (`Factory -> Region`), and preserving layer isolation.

## User Story
As a network planner,
I want route aggregation that enforces a strict $N \ge 30$ sample threshold for state-level rankings and automatically rolls up small factories to the regional level,
So that low-volume sample noise does not distort operational leaderboards.

## Acceptance Criteria
- **Given** the route dataset,
- **When** `src/route_analysis.py` aggregates Factory -> State routes,
- **Then** routes with $N \ge 30$ order lines qualify for Top 10 / Bottom 10 leaderboards,
- **And** boundary tests verify $N=29$ is ineligible, $N=30$ is eligible, and $N=31$ is eligible,
- **And** routes with $N < 30$ are segregated into a "Low Sample / Insufficient Data" table,
- **And** Sugar Shack, Secret Factory, and The Other Factory automatically roll up to `Factory -> Region` level,
- **And** layer isolation prevents mixing ORIGINAL, DERIVED, and SYNTHETIC data in the same ranked table.

## Implementation Details & Boundaries
- Target module: `src/route_analysis.py`
- Test file: `tests/test_route_analysis.py`
