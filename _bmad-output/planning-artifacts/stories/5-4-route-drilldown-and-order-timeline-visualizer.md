---
title: 'Story 5.4: Route Drill-Down & Order-to-Ship Timeline Visualizer'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 5
story: 4
story_key: '5-4-route-drilldown-and-order-timeline-visualizer'
---

# Story 5.4: Route Drill-Down & Order-to-Ship Timeline Visualizer

## Intent
**Problem:** Warehouse managers need granular lane-level inspection to review individual order timelines, lead times, and Canadian route distances.
**Approach:** Implement `pages/7_Route_Drill_Down.py` with lane summary statistics, order-to-ship timeline charts with threshold indicators, and Canadian route tables with centroid distances.

## User Story
As a warehouse manager,
I want to drill down into a specific route or state to view individual order timelines and shipment details,
So that I can investigate root causes of delays on specific lanes.

## Acceptance Criteria
- **Given** `pages/7_Route_Drill_Down.py`,
- **When** a route (e.g. *Lot's O' Nuts -> Texas*) is selected,
- **Then** summary metrics and an order line table are displayed,
- **And** an interactive order timeline chart shows order date, ship date, lead time, and threshold line,
- **And** lead time is strictly labeled "Order-to-Ship Lead Time", never "Transit Time",
- **And** Canadian routes display factory-to-province centroid distances.

## Implementation Details & Boundaries
- Target file: `pages/7_Route_Drill_Down.py`
