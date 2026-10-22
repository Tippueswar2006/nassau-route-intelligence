---
epic_num: 6
title: "Sensitivity Verification, Research Figures & Cloud Deployment Finalization"
status: backlog
phase: "Phase 6 Finalization"
depends_on: ["epic-4", "epic-5"]
fr_coverage: ["FR-15", "FR-18"]
nfr_coverage: ["NFR-04", "NFR-06", "NFR-07"]
---

# Epic 6: Sensitivity Verification, Research Figures & Cloud Deployment Finalization

## Goal
Conduct sensitivity experiments, generate publication-grade research figures, produce project documentation, and verify cloud deployment readiness.

## Status: BACKLOG (BLOCKED BY EPICS 4 & 5)

## Stories
- [Story 6.1: Sensitivity Analysis & Seed Robustness Test Suite](../stories/6-1-sensitivity-analysis-and-seed-robustness-test-suite.md) — *Status: BACKLOG*
- [Story 6.2: Publication Figure Generation Script](../stories/6-2-publication-figure-generation-script.md) — *Status: BACKLOG*
- [Story 6.3: Comprehensive Documentation & Data Dictionary](../stories/6-3-comprehensive-documentation-and-data-dictionary.md) — *Status: BACKLOG*
- [Story 6.4: Cloud Deployment Validation & Zero-PII Release Gate Check](../stories/6-4-cloud-deployment-validation-and-zero-pii-release-gate-check.md) — *Status: BACKLOG*

## Dependencies & Invariants
- Depends on fully completed dashboard application and analytics engines.
- Matplotlib/Seaborn publication figures saved at 300 DPI in `docs/figures/`.
- Full release gate check asserts zero raw data presence in cloud mode, zero Customer IDs, and 100% test pass.
