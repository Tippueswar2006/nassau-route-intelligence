---
title: 'Story 1.2: Dual-Mode Ingestion & Source Data SHA-256 Verification'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 1
story: 2
story_key: '1-2-dual-mode-ingestion-and-source-hash-verification'
---

# Story 1.2: Dual-Mode Ingestion & Source Data SHA-256 Verification

## Intent
**Problem:** Accidental source file tampering or missing data in cloud deployments can corrupt analytics or crash the application.
**Approach:** Create a pure Python ingestion module that verifies the raw file's SHA-256 hash in local mode, detects deployment mode, and loads Parquet artifacts in cloud mode with zero Streamlit dependencies.

## User Story
As a data engineer,
I want a pure Python loader that verifies the raw dataset against an immutable SHA-256 hash in local mode and gracefully handles missing raw data in cloud mode,
So that data provenance is preserved without risking data tampering or breaking cloud deployment.

## Acceptance Criteria
- **Given** `data/original/nassau_candy.csv`,
- **When** `src/load_data.py::verify_source_hash()` executes,
- **Then** it asserts equality with `6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f`,
- **And** `load_raw_data()` reads all 10,194 rows with strongly typed schemas,
- **And** `get_deployment_mode()` returns `"local"` if raw file exists, else `"cloud"`,
- **And** `src/load_data.py` contains zero Streamlit imports.

## Implementation Files
- `src/config.py`
- `src/load_data.py`
- `tests/test_data_quality.py::test_source_file_integrity`
- `tests/test_architecture.py::test_zero_streamlit_in_src`
