---
title: 'Story 6.2: Publication Figure Generation Script'
type: 'chore'
created: '10-20-2026'
status: 'done'
epic: 6
story: 2
story_key: '6-2-publication-figure-generation-script'
---

# Story 6.2: Publication Figure Generation Script

## Intent
**Problem:** Academic paper and executive summary require high-resolution, reproducible charts generated directly from code without manual screenshotting.
**Approach:** Implement `scripts/generate_paper_figures.py` using Matplotlib and Seaborn to output 300 DPI publication figures into `docs/figures/`.

## User Story
As an author,
I want a standalone script `scripts/generate_paper_figures.py` that generates all publication-quality Matplotlib/Seaborn figures,
So that paper graphics are 100% reproducible directly from code.

## Acceptance Criteria
- **Given** `scripts/generate_paper_figures.py`,
- **When** executed via CLI,
- **Then** high-resolution figures (300 DPI) are saved to `docs/figures/`,
- **And** figures include lead-time distributions, RES quadrant scatter, and scenario comparison bars.

## Implementation Details & Boundaries
- Script path: `scripts/generate_paper_figures.py`
- Output directory: `docs/figures/`
