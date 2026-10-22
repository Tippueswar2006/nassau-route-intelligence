---
title: 'Story 6.1: Sensitivity Analysis & Seed Robustness Test Suite'
type: 'chore'
created: '10-20-2026'
status: 'done'
epic: 6
story: 1
story_key: '6-1-sensitivity-analysis-and-seed-robustness-test-suite'
---

# Story 6.1: Sensitivity Analysis & Seed Robustness Test Suite

## Intent
**Problem:** Academic research and business reports require statistical proof that route rankings are robust across random generator seeds and varying speed/variability weights.
**Approach:** Implement `tests/test_sensitivity.py` running automated evaluations of RES rankings under 50/50, 70/30, and 90/10 weights and 5 deterministic seeds (`[42, 101, 202, 303, 404]`).

## User Story
As a researcher,
I want an automated sensitivity test suite evaluating RES rankings across multiple weight configurations and seeds,
So that paper conclusions are verified as statistically robust.

## Acceptance Criteria
- **Given** synthetic route rankings across 5 seeds (`[42, 101, 202, 303, 404]`),
- **When** sensitivity tests run,
- **Then** rank correlation (Spearman $\rho$) between 70/30 and 50/50, 90/10 weight profiles is computed and logged,
- **And** top bottleneck routes remain consistent across seeds.

## Implementation Details & Boundaries
- Test file: `tests/test_sensitivity.py`
