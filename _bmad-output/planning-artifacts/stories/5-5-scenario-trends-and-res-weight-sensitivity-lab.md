---
title: 'Story 5.5: Scenario Trends & RES Weight Sensitivity Lab'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 5
story: 5
story_key: '5-5-scenario-trends-and-res-weight-sensitivity-lab'
---

# Story 5.5: Scenario Trends & RES Weight Sensitivity Lab

## Intent
**Problem:** Long-term monthly volume trends from valid Original dates must be analyzed alongside simulated lead times, and users need a dedicated sandbox to test RES weight sensitivity (50/50, 70/30, 90/10) without destabilizing Pages 1–7.
**Approach:** Implement `pages/8_Trends_and_Scenarios.py` with monthly order volume charts (Original), monthly mean lead-time trends (Synthetic), Baseline vs Stress comparisons, and interactive RES sensitivity sliders isolated strictly to Page 8.

## User Story
As an executive strategist,
I want to analyze monthly order trends and test RES sensitivity under different speed/variability weights,
So that I can evaluate network seasonality and score robustness under alternative priorities.

## Acceptance Criteria
- **Given** `pages/8_Trends_and_Scenarios.py`,
- **When** viewed in the dashboard,
- **Then** monthly order volume is displayed using valid Original dates (2024–2025),
- **And** monthly mean lead times are displayed using Synthetic scenarios,
- **And** interactive sensitivity sliders (Page 8 only) allow testing alternative RES weights (e.g. 50/50, 70/30, 90/10) with side-by-side rank stability indicators.

## Implementation Details & Boundaries
- Target file: `pages/8_Trends_and_Scenarios.py`
