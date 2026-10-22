---
title: 'Story 3.1: Pre-computed Mode Adjustment & Route Efficiency Scoring Engine'
type: 'feature'
created: '10-20-2026'
status: 'done'
baseline_commit: 'NO_VCS'
epic: 3
story: 1
story_key: '3-1-precomputed-mode-adjustment-and-route-efficiency-scoring'
context:
  - 'src/config.py'
---

# Story 3.1: Pre-computed Mode Adjustment & Route Efficiency Scoring Engine

## Intent
**Problem:** Raw lead-time rankings unfairly penalize routes with high Standard Class usage. Scoring must isolate genuine route performance from shipping mode selection.
**Approach:** Implement `src/metrics.py` calculating scenario-level mode reference means before filters, mode-adjusted lead times, fixed 70/30 speed/variability penalty math ($[0, 100]$), and strict delay inequality.

## User Story
As a supply chain analyst,
I want route efficiency scores computed using fixed 70% Speed and 30% Variability penalties with mode-adjusted lead times pre-computed on the full dataset,
So that routes are benchmarked fairly without penalizing routes with high Standard Class volume.

## Acceptance Criteria
- **Given** synthetic shipment lead times,
- **When** `src/metrics.py` evaluates Route Efficiency Scores (RES),
- **Then** ship-mode reference means are pre-computed on the full scenario dataset before user filters and remain invariant to filter changes,
- **And** $\text{Mode-Adjusted Lead Time} = \text{Lead Time} - \mu_{\text{mode}}$,
- **And** $\text{RES} = 100 - (0.70 \times \text{Speed Penalty} + 0.30 \times \text{Variability Penalty})$, bounded in $[0, 100]$,
- **And** constant-value or zero-variance routes safely assign penalty = 0 without math errors,
- **And** delay condition enforces strict inequality: $\text{Lead Time} > \text{Threshold}$ (with threshold slider 1–15d, default 5.0d).

## Implementation Details & Boundaries
- Target module: `src/metrics.py`
- Test file: `tests/test_metrics.py`
