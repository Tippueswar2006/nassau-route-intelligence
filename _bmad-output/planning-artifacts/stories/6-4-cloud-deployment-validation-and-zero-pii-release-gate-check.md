---
title: 'Story 6.4: Cloud Deployment Validation & Zero-PII Release Gate Check'
type: 'chore'
created: '10-20-2026'
status: 'done'
epic: 6
story: 4
story_key: '6-4-cloud-deployment-validation-and-zero-pii-release-gate-check'
---

# Story 6.4: Cloud Deployment Validation & Zero-PII Release Gate Check

## Intent
**Problem:** Final deployment to Streamlit Community Cloud requires formal automated verification that raw datasets are absent, surrogate anonymization is 100% leak-proof, and all release gates pass.
**Approach:** Implement `scripts/validate_release_gates.py` executing release-gate checks (cloud mode startup, zero-PII regex audit, test pass rate, documentation completeness).

## User Story
As a release engineer,
I want a comprehensive release-gate validation script that checks cloud startup, zero-PII artifacts, and test pass rate,
So that public deployment to Streamlit Community Cloud is 100% compliant with privacy and architecture standards.

## Acceptance Criteria
- **Given** a simulated cloud environment (where `data/original/` is absent),
- **When** the application starts up,
- **Then** it loads prepared Parquet artifacts without failing on missing raw CSV,
- **And** zero 6-digit Customer IDs or unmasked Order IDs exist in deployed files,
- **And** 100% of automated tests pass,
- **And** all PRD release gates are verified.

## Implementation Details & Boundaries
- Script path: `scripts/validate_release_gates.py`
