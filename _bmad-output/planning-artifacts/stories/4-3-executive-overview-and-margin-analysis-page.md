---
title: 'Story 4.3: Executive Overview & Margin Analysis Page'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 4
story: 3
story_key: '4-3-executive-overview-and-margin-analysis-page'
---

# Story 4.3: Executive Overview & Margin Analysis Page

## Intent
**Problem:** Leadership needs high-level visibility into product sales, manufacturing COGS, and gross margin without confusing manufacturing costs with freight spend.
**Approach:** Implement `pages/1_Executive_Overview.py` displaying commercial KPIs, distinguishing order lines (8,549) from line items (9,881), and providing explicit freight cost out-of-scope disclaimers.

## User Story
As a C-suite executive,
I want an Executive Overview displaying product revenue, manufacturing COGS, gross margins, and volume metrics by factory and product,
So that I can evaluate commercial performance alongside operational throughput.

## Acceptance Criteria
- **Given** `pages/1_Executive_Overview.py`,
- **When** viewed in the dashboard,
- **Then** financial KPI summary cards show Total Sales, Manufacturing COGS, Gross Profit, and Gross Margin %,
- **And** explicit disclaimers state freight shipping costs are out of scope and not inferred from manufacturing COGS,
- **And** order lines (8,549) and line items (9,881) are explicitly distinguished,
- **And** all metrics respond dynamically to global sidebar filters.

## Implementation Details & Boundaries
- Target file: `pages/1_Executive_Overview.py`
