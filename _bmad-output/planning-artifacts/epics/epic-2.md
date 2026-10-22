---
epic_num: 2
title: "Shipment-Grain Synthetic Lead Time Generator & Privacy-Preserving Cloud Build Pipeline"
status: done
phase: "Phase 2 Foundation"
depends_on: ["epic-1"]
fr_coverage: ["FR-18", "FR-21"]
nfr_coverage: ["NFR-04", "NFR-05", "NFR-07"]
---

# Epic 2: Shipment-Grain Synthetic Lead Time Generator & Privacy-Preserving Cloud Build Pipeline

## Goal
Generate reproducible, distance-sensitive, and stress-tested synthetic order-to-ship lead times at customer shipment grain, and build sanitized, surrogate-keyed cloud Parquet artifacts with complete PII removal.

## Status: COMPLETED

## Stories
- [Story 2.1: Customer Shipment Grouping & Multi-Scenario Synthetic Lead Time Generator](../stories/2-1-customer-shipment-grouping-and-synthetic-lead-time-generator.md) — *Status: DONE*
- [Story 2.2: Privacy-Preserving Cloud Build Pipeline & Surrogate Key Generation](../stories/2-2-privacy-preserving-cloud-build-pipeline-and-surrogate-keys.md) — *Status: DONE*
- [Story 2.3: Synthetic Calibration & Privacy Compliance Verification Suite](../stories/2-3-synthetic-calibration-and-privacy-compliance-test-suite.md) — *Status: DONE*

## Dependencies & Invariants
- Depends on completed Epic 1 modules (`src/config.py`, `src/load_data.py`, `src/validate_data.py`, `src/map_factories.py`).
- 5,067 customer shipments `(Customer ID, Order Date, Ship Mode)`. All lines in each shipment share one lead time.
- Unclipped bounds: base bounds ($[0, 2]$ Same Day, $[1, 14]$ others) applied *before* delay injections; expanded bounds ($[0, 6]$ Same Day, $[1, 20]$ others) in Stress-Test.
- Surrogate keys for both Customer ID and Order ID; `City` and `Postal Code` dropped from cloud artifacts.
- Target tests: `tests/test_synthetic.py`, `tests/test_privacy.py`.
