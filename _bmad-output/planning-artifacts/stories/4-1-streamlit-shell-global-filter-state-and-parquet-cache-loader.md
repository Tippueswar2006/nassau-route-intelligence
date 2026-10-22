---
title: 'Story 4.1: Streamlit Application Shell, Global Filter State & Parquet Cache Loader'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 4
story: 1
story_key: '4-1-streamlit-shell-global-filter-state-and-parquet-cache-loader'
---

# Story 4.1: Streamlit Application Shell, Global Filter State & Parquet Cache Loader

## Intent
**Problem:** Dashboard users need consistent global filtering across multi-page views with fast artifact caching and persistent layer provenance tagging.
**Approach:** Implement `app.py` shell with `@st.cache_data` loader, sidebar controls (Layer, Scenario, Factory, State, Region, Ship Mode, Delay Slider 1-15d, Duplicate Toggle), and persistent layer banners.

## User Story
As an executive user,
I want a responsive Streamlit application shell with persistent sidebar filters and fast Parquet artifact caching,
So that I can seamlessly explore the network while maintaining layer provenance and filter context.

## Acceptance Criteria
- **Given** prepared Parquet artifacts in `data/derived/` and `data/synthetic/`,
- **When** `app.py` loads,
- **Then** it reads artifacts via `@st.cache_data` in the presentation layer without importing Streamlit in `src/`,
- **And** sidebar provides global controls: Data Layer, Synthetic Scenario, Factory, State, Region, Ship Mode, Delay Threshold Slider (1–15d, default 5.0d), Duplicate Toggle, and Filter Reset,
- **And** persistent header banner displays the active Data Layer (ORIGINAL, DERIVED, SYNTHETIC) and Scenario name,
- **And** responsive execution completes in under 1 second per filter change.

## Implementation Details & Boundaries
- Target file: `app.py`
