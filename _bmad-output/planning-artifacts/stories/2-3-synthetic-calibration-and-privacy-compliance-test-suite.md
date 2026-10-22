---
title: 'Story 2.3: Synthetic Calibration & Privacy Compliance Verification Suite'
type: 'chore'
created: '10-20-2026'
status: 'done'
baseline_commit: 'NO_VCS'
epic: 2
story: 3
story_key: '2-3-synthetic-calibration-and-privacy-compliance-test-suite'
context:
  - 'tests/test_data_quality.py'
  - 'tests/test_mapping.py'
---

# Story 2.3: Synthetic Calibration & Privacy Compliance Verification Suite

## Intent
**Problem:** Injected stress delays must be guaranteed to survive without clipping, seed reproducibility must be mathematically verified, and zero PII leaks must be enforced.
**Approach:** Create `tests/test_synthetic.py` and `tests/test_privacy.py` under pytest validating unclipped injections (especially Same Day), hash determinism, and complete surrogate anonymization.

## User Story
As a quality assurance engineer,
I want automated test suites `tests/test_synthetic.py` and `tests/test_privacy.py`,
So that reproducibility, unclipped delay survival (including Same Day), and complete cloud anonymization are verified before dashboard development.

## Acceptance Criteria
- **Given** the generated Parquet artifacts and build outputs,
- **When** `tests/test_synthetic.py` and `tests/test_privacy.py` run under pytest,
- **Then** seed 42 reproduces identical synthetic DataFrames across runs,
- **And** Same Day shipments under Stress-Test survive with $> 2.0$ days lead time when injected (proving delay bounds do not clip),
- **And** zero raw 6-digit Customer IDs appear anywhere in cloud Parquet files or `metadata.json`,
- **And** Order ID surrogate keys contain no substring matching original Customer IDs,
- **And** `City` and `Postal Code` columns are confirmed absent from cloud Parquet schemas,
- **And** the raw file SHA-256 is verified unchanged.

## Implementation Details & Boundaries
- Test files:
  - `tests/test_synthetic.py`
  - `tests/test_privacy.py`
