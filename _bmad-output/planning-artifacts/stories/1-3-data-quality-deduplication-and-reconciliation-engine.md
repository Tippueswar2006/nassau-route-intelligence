---
title: 'Story 1.3: Data Quality, Deduplication & 4-Metric Reconciliation Engine'
type: 'feature'
created: '10-20-2026'
status: 'done'
epic: 1
story: 3
story_key: '1-3-data-quality-deduplication-and-reconciliation-engine'
---

# Story 1.3: Data Quality, Deduplication & 4-Metric Reconciliation Engine

## Intent
**Problem:** Raw data contains 313 duplicate records, unpadded US zip codes, partial Canadian postal codes, whitespace typos in product names, and an export date anomaly.
**Approach:** Build a data quality engine that flags duplicates, reconciles financial/unit totals to the penny, pads zip codes, normalizes product names, and computes diagnostic lead times.

## User Story
As a business analyst,
I want an automated quality engine that flags duplicate rows, reconciles units and financial totals, normalizes product names, and computes diagnostic lead times,
So that data hygiene is auditable and financial numbers match the approved baseline.

## Acceptance Criteria
- **Given** the raw 10,194 records,
- **When** `src/validate_data.py::clean_dataset()` runs,
- **Then** exactly 313 duplicate rows are flagged in `is_duplicate = True`,
- **And** `reconcile_metrics()` verifies:
  - Rows: $10,194 \rightarrow 9,881$ ($\Delta = -313$)
  - Units: $38,654 \rightarrow 37,667$ ($\Delta = -987$)
  - Sales: $\$141,783.63 \rightarrow \$138,284.12$ ($\Delta = -\$3,499.51$)
  - Gross Profit: $\$93,442.80 \rightarrow \$91,076.41$ ($\Delta = -\$2,366.39$),
- **And** 449 four-digit US postal codes are padded with leading `0`,
- **And** 200 Canadian records are tagged with `is_canadian = True` and `is_partial_postal = True`,
- **And** `Wonka Bar -Scrumdiddlyumptious` is normalized with proper spacing,
- **And** diagnostic reconstruction per-mode means match Section 3.1 within 0.01.

## Implementation Files
- `src/validate_data.py`
- `tests/test_data_quality.py::test_reconciliation_4_metrics`
- `tests/test_data_quality.py::test_postal_code_formatting`
- `tests/test_data_quality.py::test_product_name_normalization`
- `tests/test_data_quality.py::test_diagnostic_reconstruction`
