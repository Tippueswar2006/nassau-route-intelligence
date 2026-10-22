---
epic_num: 3
title: "Route Efficiency Scoring, Sample Guardrails & Bottleneck Detection Engine"
status: done
phase: "Phase 3 Foundation"
depends_on: ["epic-2"]
fr_coverage: ["FR-06", "FR-07", "FR-08", "FR-11", "FR-19"]
nfr_coverage: ["NFR-03", "NFR-04", "NFR-05", "NFR-06"]
---

# Epic 3: Route Efficiency Scoring, Sample Guardrails & Bottleneck Detection Engine

## Goal
Calculate mode-adjusted Route Efficiency Scores (RES), enforce sample size thresholds ($N \ge 30$), and screen potential geographic bottlenecks verified across 5 seeds.

## Status: COMPLETED (100%)

## Stories
- [Story 3.1: Pre-computed Mode Adjustment & Route Efficiency Scoring Engine](../stories/3-1-precomputed-mode-adjustment-and-route-efficiency-scoring.md) — *Status: DONE*
- [Story 3.2: Route Aggregation, Sample Size Guardrails & Regional Rollups](../stories/3-2-route-aggregation-sample-guardrails-and-regional-rollups.md) — *Status: DONE*
- [Story 3.3: 75th Percentile Screening Quadrant & 5-Seed Bottleneck Recovery Engine](../stories/3-3-bottleneck-screening-quadrant-and-5-seed-recovery-engine.md) — *Status: DONE*

## Dependencies & Invariants
- Depends on Epic 2 generated Parquet artifacts.
- Ship-mode reference means pre-computed on full scenario dataset before filters.
- Fixed 70/30 RES math on Pages 1–7.
- Minimum sample size $N \ge 30$ for state-level route rankings. Small factories rolled up to Region.
- 5-seed bottleneck recovery passes in $\ge 4/5$ seeds with Stress delay rate strictly greater than Baseline delay rate.
- Target tests: `tests/test_metrics.py`, `tests/test_route_analysis.py`, `tests/test_bottlenecks.py`.
