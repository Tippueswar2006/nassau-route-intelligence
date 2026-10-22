---
title: 'Story 5.1: US State Choropleth Heatmap & Canadian Notice Banner'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 5
story: 1
story_key: '5-1-us-state-choropleth-heatmap-and-canadian-notice-banner'
---

# Story 5.1: US State Choropleth Heatmap & Canadian Notice Banner

## Intent
**Problem:** Geographic delivery patterns require visual map exploration, but Canadian postal geography cannot be rendered on a US state choropleth without distortion.
**Approach:** Implement `pages/4_Geographic_Analysis.py` with Plotly US choropleth (selectable metric: Mean Lead Time, Delay Rate, RES, Volume) and a persistent notice banner stating Canadian orders are excluded from map geometry but retained in company totals.

## User Story
As a regional director,
I want an interactive US state choropleth heatmap showing delivery performance metrics by destination state,
So that geographic patterns in lead time and delay frequency are immediately visible.

## Acceptance Criteria
- **Given** `pages/4_Geographic_Analysis.py`,
- **When** viewed in the dashboard,
- **Then** a Plotly US choropleth displays user-selected metrics: Mean Lead Time, Delay Rate, RES, or Order Volume,
- **And** Canadian destinations are excluded from the US map geometry and a prominent notification banner states Canadian orders are retained in overall financial and volume metrics,
- **And** hovering over a state reveals factory fulfillment breakdown and sample size.

## Implementation Details & Boundaries
- Target file: `pages/4_Geographic_Analysis.py`
