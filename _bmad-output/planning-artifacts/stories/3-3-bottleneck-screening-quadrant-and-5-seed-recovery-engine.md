---
title: 'Story 3.3: 75th Percentile Screening Quadrant & 5-Seed Bottleneck Recovery Engine'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 3
story: 3
story_key: '3-3-bottleneck-screening-quadrant-and-5-seed-recovery-engine'
---

# Story 3.3: 75th Percentile Screening Quadrant & 5-Seed Bottleneck Recovery Engine

## Intent
**Problem:** Geographic bottleneck detection must distinguish operational distress from low-volume noise, and synthetic stress injections must be mathematically recoverable across multiple seeds.
**Approach:** Implement `src/bottleneck_rules.py` screening routes on $P_{75}$ volume and delay rate, and write `tests/test_bottlenecks.py` asserting Texas bottleneck recovery in $\ge 4/5$ seeds with $N \ge 30$.

## User Story
As a risk analyst,
I want an automated bottleneck screening engine that identifies high-volume, high-delay routes using 75th percentile thresholds and passes a 5-seed recovery test,
So that critical fulfillment bottlenecks are reliably detected across random seeds.

## Acceptance Criteria
- **Given** route aggregates under Baseline and Stress-Test scenarios,
- **When** `src/bottleneck_rules.py` screens for bottlenecks,
- **Then** routes with $\text{Volume} \ge P_{75}$ and $\text{Delay Rate} \ge P_{75}$ (at 5-day threshold) are flagged as Critical Bottlenecks,
- **And** routes with $\text{Delay Rate} > \text{Median}$ are flagged on the Watchlist,
- **And** `tests/test_bottlenecks.py` runs across 5 deterministic seeds (`[42, 101, 202, 303, 404]`),
- **And** the injected Texas routes (*Lot's O' Nuts -> Texas* and *Wicked Choccy's -> Texas*, enforcing $N \ge 30$) are recovered in at least 4 of the 5 seeds ($\ge 4/5$, i.e. $\ge 80\%$) with Stress delay rate strictly greater than Baseline delay rate.

## Implementation Details & Boundaries
- Target module: `src/bottleneck_rules.py`
- Test file: `tests/test_bottlenecks.py`
