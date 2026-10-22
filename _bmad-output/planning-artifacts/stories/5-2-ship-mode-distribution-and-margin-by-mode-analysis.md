---
title: 'Story 5.2: Ship Mode Distribution & Margin-by-Mode Analysis'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 5
story: 2
story_key: '5-2-ship-mode-distribution-and-margin-by-mode-analysis'
---

# Story 5.2: Ship Mode Distribution & Margin-by-Mode Analysis

## Intent
**Problem:** Ship mode explains over 60% of lead-time variance. Users need clear visual comparisons across shipping methods and distance bands without unwarranted causal claims.
**Approach:** Implement `pages/5_Ship_Mode_Comparison.py` presenting lead-time distributions across modes, distance-band curves, and descriptive gross profit margins by mode with clear disclaimers.

## User Story
As a logistics analyst,
I want ship-mode performance comparisons across Standard vs Expedited modes and distance bands,
So that I can understand how shipping method choices impact lead-time variance.

## Acceptance Criteria
- **Given** `pages/5_Ship_Mode_Comparison.py`,
- **When** viewed in the dashboard,
- **Then** lead-time distributions are compared across Same Day, First Class, Second Class, and Standard Class,
- **And** distance band analysis illustrates lead time versus Haversine distance,
- **And** gross profit margins by ship mode are displayed with clear non-causal disclaimers.

## Implementation Details & Boundaries
- Target file: `pages/5_Ship_Mode_Comparison.py`
