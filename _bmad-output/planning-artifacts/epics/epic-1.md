---
epic_num: 1
title: "Data Ingestion, Quality Audit & Factory Mapping Engine"
status: done
phase: "Phase 1 Foundation"
fr_coverage: ["FR-01", "FR-02", "FR-03", "FR-16", "FR-21"]
nfr_coverage: ["NFR-03", "NFR-05", "NFR-06", "NFR-07"]
---

# Epic 1: Data Ingestion, Quality Audit & Factory Mapping Engine

## Goal
Establish trusted, auditable raw data ingestion, duplicate reconciliation, geographic normalization, and factory-route coordinate mapping with 100% headless decoupling.

## Status: COMPLETED
All 4 stories implemented, and verified via `pytest` (15/15 tests passing in 0.74s).

## Stories
- [Story 1.1: Configuration Tables & Workspace Environment Setup](../stories/1-1-configuration-tables-and-workspace-setup.md) — *Status: DONE*
- [Story 1.2: Dual-Mode Ingestion & Source Data SHA-256 Verification](../stories/1-2-dual-mode-ingestion-and-source-hash-verification.md) — *Status: DONE*
- [Story 1.3: Data Quality, Deduplication & 4-Metric Reconciliation Engine](../stories/1-3-data-quality-deduplication-and-reconciliation-engine.md) — *Status: DONE*
- [Story 1.4: Factory Assignment, Centroid Joins & Vectorized Haversine Distance](../stories/1-4-factory-assignment-centroid-joins-and-haversine-distance.md) — *Status: DONE*

## Test Suite
- `tests/test_architecture.py` (Streamlit decoupling, .gitignore separation, config integrity)
- `tests/test_data_quality.py` (SHA-256 hash, 4-metric reconciliation, zip padding, product normalization, diagnostic lead-time reconstruction)
- `tests/test_mapping.py` (15/15 product mapping, 1 factory per Order ID across 8,549 lines, shipment grains, Haversine distance)
