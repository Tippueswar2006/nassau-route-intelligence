---
title: 'Story 5.3: Interactive Bottleneck Quadrant Scatter Visualizer'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 5
story: 3
story_key: '5-3-interactive-bottleneck-quadrant-scatter-visualizer'
---

# Story 5.3: Interactive Bottleneck Quadrant Scatter Visualizer

## Intent
**Problem:** Operations leaders need an intuitive visual tool to isolate high-volume, high-delay fulfillment routes from the broader network.
**Approach:** Implement `pages/6_Potential_Bottlenecks.py` rendering an interactive Plotly quadrant scatter plot (Volume vs Delay Rate) with 75th percentile reference lines and bottleneck badges.

## User Story
As an operations director,
I want an interactive quadrant scatter plot of route volume versus delay rate,
So that high-volume, high-delay bottleneck lanes can be isolated and prioritized.

## Acceptance Criteria
- **Given** `pages/6_Potential_Bottlenecks.py`,
- **When** viewed in the dashboard,
- **Then** a Plotly scatter plot plots Route Volume ($x$) against Delay Rate ($y$),
- **And** reference lines display the 75th percentile thresholds for volume and delay rate,
- **And** routes in the upper-right quadrant are flagged as Critical Bottlenecks with sample size $N$ and volume metrics,
- **And** watchlisted routes ($\text{Delay Rate} > \text{Median}$) are highlighted.

## Implementation Details & Boundaries
- Target file: `pages/6_Potential_Bottlenecks.py`
