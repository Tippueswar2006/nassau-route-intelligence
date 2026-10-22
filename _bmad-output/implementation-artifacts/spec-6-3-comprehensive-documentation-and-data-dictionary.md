---
title: 'Story 6.3: Comprehensive Documentation & Data Dictionary'
type: 'chore'
created: '2026-10-22'
status: 'done'
baseline_commit: 'NO_VCS'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Technical debt and maintainability risk arise when architectural decisions, mathematical formulas, data layer schemas, and simulation assumptions are dispersed across source code and test files without centralized, standardized documentation. Future maintainers, evaluators, and open-source contributors require reproducible documentation and clear quickstart/deployment procedures.

**Approach:** Author a complete, publication-grade documentation suite comprising `docs/data_dictionary.md` (defining all columns and metrics across Original, Derived, and Synthetic layers), `docs/methodology.md` (documenting RES mathematical formulations, mode adjustments, and bottleneck quadrant screening), `docs/synthetic_assumptions.md` (disclosing all empirical distributions, distance scaling, and stress injection parameters), and a polished `README.md` (providing architecture overview, local quickstart, testing, paper figure generation, and Streamlit Community Cloud deployment instructions), verified by automated test suite `tests/test_documentation.py`.

## Boundaries & Constraints

**Always:**
- **Standardized Documentation Suite:**
  - Author `docs/data_dictionary.md`: complete schemas for Original (`data/original/nassau_candy.csv`), Derived (`clean_orders.parquet`, `route_aggregates.parquet`, `surrogate_key_mapping.csv`, `transformation_log.json`), and Synthetic (`baseline.parquet`, `distance_sensitive.parquet`, `stress_test.parquet`, `metadata.json`) with data types, nullability, descriptions, and layer provenance.
  - Author `docs/methodology.md`: complete mathematical specifications for Haversine Great-Circle distance, ship-mode reference benchmarks, mode-adjusted lead times, min-max Speed and Variability penalties, composite Route Efficiency Score ($RES = 100 - [0.70 \cdot P_{\text{speed}} + 0.30 \cdot P_{\text{var}}]$), sample size guardrail ($N \ge 30$), and percentile-based quadrant screening rules ($P_{75}$ Volume & $P_{75}$ Delay Rate).
  - Author `docs/synthetic_assumptions.md`: full disclosure of simulation parameters, per-mode empirical discrete probability distributions, distance sensitivity coefficient ($0.5\text{ days}/1,000\text{ km}$), order-of-operations bounds (base $[0, 2]$ / $[1, 14]$, stress $[0, 6]$ / $[1, 20]$), temporal and geographic stress injections, surrogate key anonymization, and 5-seed robustness targets (`[42, 101, 202, 303, 404]`).
  - Author `README.md`: comprehensive project overview, research problem statement, interactive visual features, local installation/quickstart, offline pipeline build execution, testing instructions, paper figure generation, and cloud deployment procedures.
- **Architectural & Compliance Invariants:**
  - Invariant compliance with AD-01 (Source Date Anomaly): explicitly disclose that raw source dates span 904–1,642 days and represent unverified intervals; synthetic lead times represent calibrated simulation models.
  - Invariant compliance with AD-02 (Synthetic Data Disclosure): maintain prominent warnings and synthetic layer badges in all documentation and instructions.
  - Invariant compliance with AD-04 (Privacy & Zero-PII Cloud Deployment): document surrogate hashing for Customer IDs (`CUST-xxxxxxxx`) and Order IDs (`ORD-xxxxxxxxxx`), complete dropping of granular geographic PII (`City`, `Postal Code`), and standalone cloud operation from `data/synthetic/` without requiring `data/original/`.
  - Zero Streamlit imports in test suite `tests/test_documentation.py`.

**Never:**
- Never expose unmasked raw 6-digit Customer IDs or real customer/order identities in documentation examples or tables.
- Never assert that raw historical dates represent verified physical transit lead times.
- Never deviate from canonical constants established in `src/config.py` and `config/generator.yaml`.
- Never modify or overwrite existing Parquet data artifacts during documentation authoring.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Automated Doc Suite Verification | `pytest tests/test_documentation.py` | All 4 doc files exist, non-empty, contain required sections, tables, math formulas, and pass validation; exit code 0 | Assertion failure detailing missing section or formula |
| Data Dictionary Inspection | Review `docs/data_dictionary.md` | Clear tabular definitions across Original (18 cols), Derived (Clean & Aggregates), and Synthetic layers | Flag any undocumented field |
| Methodology Audit | Review `docs/methodology.md` | Complete mathematical formulas for Haversine, RES, Mode Adjustment, Guardrails, and Quadrants | Verify LaTeX and formula precision |
| Simulation Disclosure Audit | Review `docs/synthetic_assumptions.md` | Full disclosure of empirical tables, stress injections, bounds, and seed robustness | Check against `config/generator.yaml` |
| Quickstart Execution | Follow `README.md` commands | Successful setup, pipeline run, test execution, figure generation, and Streamlit launch | Step-by-step verified commands |

</frozen-after-approval>

## Code Map

- `docs/data_dictionary.md` -- Comprehensive documentation of columns and metrics across Original, Derived, and Synthetic layers
- `docs/methodology.md` -- Mathematical formulations for Haversine distance, Mode Adjustment, RES penalties, sample size guardrail ($N \ge 30$), and quadrant bottleneck screening
- `docs/synthetic_assumptions.md` -- Full disclosure of empirical discrete distributions, distance coefficient, Nov/Dec peak and CA/NY/TX stress injections, bounds, and 5-seed robustness
- `README.md` -- Project overview, research questions, architecture, quickstart, testing, paper figure generation, and cloud deployment guide
- `tests/test_documentation.py` -- Automated test suite validating existence, required headings, formula definitions, schema completeness, and zero UI dependencies
- Existing reference files (Read-Only):
  - `src/config.py` -- Canonical constants, file paths, reconciliation baselines, seeds, mode definitions
  - `config/generator.yaml` -- Generator configuration, empirical probabilities, stress parameters
  - `src/metrics.py` -- Mode adjustment, route lead-time statistics, RES formulas
  - `src/bottleneck_rules.py` -- Quadrant screening thresholds, watchlist rules, recovery benchmark
  - `src/map_factories.py` -- Haversine distance, centroid coordinates, factory assignments
  - `scripts/build_data.py` -- Build stages, reconciliation, surrogate key generation, Parquet serialization
  - `scripts/generate_paper_figures.py` -- Publication figure generation CLI and exports
  - `docs/DATA_AUDIT.md` -- Read-only source dataset audit findings and column profiling
  - `docs/ARCHITECTURE.md` -- Architectural decisions, layer separation, and pipeline design

## Tasks & Acceptance

**Execution:**
- [x] `docs/data_dictionary.md` -- Author complete data dictionary defining all attributes across Original, Derived, and Synthetic layers with data types, nullability, descriptions, and layer provenance -- Fulfills Story 6.3 AC1 & FR-15
- [x] `docs/methodology.md` -- Author formal methodology guide detailing Haversine distance, Mode Adjustment, RES penalties, composite RES formula, sample size guardrail ($N \ge 30$), and quadrant bottleneck screening -- Fulfills Story 6.3 AC2 & FR-19
- [x] `docs/synthetic_assumptions.md` -- Author comprehensive simulation disclosure covering empirical distributions, distance coefficient, Nov/Dec peak and CA/NY/TX stress injections, bounds, and multi-seed calibration -- Fulfills Story 6.3 AC3 & FR-15
- [x] `README.md` -- Author repository README with project overview, research findings, quickstart guide, testing commands, paper figure generation, and cloud deployment steps -- Fulfills Story 6.3 AC4 & FR-18
- [x] `tests/test_documentation.py` -- Implement automated test suite verifying documentation file integrity, required sections, formula definitions, schema completeness, and decoupled architecture -- Fulfills Story 6.3 verification

**Acceptance Criteria:**
- Given the project repository,
- When documentation is compiled,
- Then `docs/data_dictionary.md` defines all columns and metrics across Original, Derived, and Synthetic layers,
- And `docs/methodology.md` details RES math, mode adjustment, and bottleneck criteria,
- And `docs/synthetic_assumptions.md` discloses all simulation parameters and calibration targets,
- And `README.md` provides complete local quickstart and cloud deployment instructions,
- And `tests/test_documentation.py` validates 100% of documentation requirements.

## Implementation Notes

1. **`docs/data_dictionary.md`:**
   - Full tabular schemas for Original (`data/original/nassau_candy.csv`, 18 columns, SHA-256 verified), Derived (`clean_orders.parquet`, `route_aggregates.parquet`, `surrogate_key_mapping.csv`, `transformation_log.json`), and Synthetic layers (`baseline.parquet`, `distance_sensitive.parquet`, `stress_test.parquet`, `metadata.json`).
   - Detailed definitions for dynamic analytics metrics (`mode_adjusted_lead_time`, `speed_penalty`, `variability_penalty`, `res_score`, `speed_only_score`, `is_delayed`, `is_bottleneck`, `is_watchlist`).
   - Prominent AD-01 unverified date interval disclosure and AD-04 surrogate key privacy architecture.

2. **`docs/methodology.md`:**
   - Formal mathematical formulation of Great-Circle Haversine distance ($R = 6,371.0\text{ km}$) and distance bands.
   - Exact coordinates for 5 production factories and state/provincial population centroids.
   - Mode normalization with invariant empirical benchmarks ($L_{\text{ref}, m}$: Same Day 0.38, First Class 2.55, Second Class 3.57, Standard Class 5.32).
   - Min-max Speed and Variability penalty formulations with division-by-zero safeguards.
   - Composite Route Efficiency Score ($RES = 100 - [0.70 \cdot P_{\text{speed}} + 0.30 \cdot P_{\text{var}}]$) and speed-only baseline.
   - Central Limit Theorem justification for sample size guardrail ($N \ge 30$).
   - Transparent dual 75th-percentile screening quadrant matrix and multi-seed Spearman $\rho$ stability standard ($\rho \ge 0.85$).

3. **`docs/synthetic_assumptions.md`:**
   - Detailed diagnosis of the raw date anomaly (904–1,642 days) and hypothesis offset subtraction.
   - Order grain consolidation (8,549 lines -> 5,067 customer shipments; 1,702 multi-factory shipments).
   - Discrete empirical probability tables for all 4 shipping modes.
   - Distance sensitivity model ($0.50\text{ days}/1,000\text{ km}$) and base boundary clamping ($[0, 2]$ / $[1, 14]$).
   - Stress-test disruption injections: Nov/Dec peak ($+1.0\text{d}$), CA/NY state delays ($+1.0\text{d}$), Texas routes ($+1.5\text{d}$), and expanded bounds ($[0, 6]$ / $[1, 20]$).
   - Zero-PII surrogate token masking (`CUST-xxxxxxxx`, `ORD-xxxxxxxxxx`) and omission of granular postal codes/cities.
   - 5-seed robustness evaluation standards (`[42, 101, 202, 303, 404]`).

4. **`README.md`:**
   - Publication badges, project vision, and research questions answered.
   - Comprehensive repository directory tree.
   - Step-by-step quickstart, pipeline build (`python scripts/build_data.py`), testing (`pytest`), figure generation (`python scripts/generate_paper_figures.py`), and Streamlit app execution (`streamlit run app.py`).
   - Production cloud deployment and Zero-PII compliance instructions.

5. **`tests/test_documentation.py`:**
   - 9 automated verification tests confirming file existence (>1,000 bytes), header structures, mathematical formulas, schema completeness, parameter disclosures, CLI commands, and decoupled architecture (zero Streamlit imports).
   - 100% test pass rate across all documentation checks.

## Spec Change Log

- No spec changes or intent renegotiations required. All implementation deliverables strictly satisfied boundaries and acceptance criteria.

## Review Triage Log

| ID | Finding / Claim | Location | Severity | Route | Verification Evidence & Disposition |
|---|---|---|---|---|---|
| F-01 | Size assertion floor should guarantee substantial content for each doc file (>1,000 bytes) | `tests/test_documentation.py:65` | `medium` | `patch` | Parameterized test verifies all 4 docs exceed 1,000 bytes. |
| F-02 | Invariant AD-01 date anomaly range must be explicitly cited across docs | `docs/data_dictionary.md:5`, `docs/synthetic_assumptions.md:12` | `medium` | `patch` | Explicitly documented 904–1,642 day anomaly in data dictionary and synthetic assumptions. |
| F-03 | Mathematical division-by-zero safeguards in RES calculation must match `src/metrics.py` | `docs/methodology.md:95` | `low` | `patch` | Added explicit zero penalty fallback when min equals max in speed and variability formulas. |
| F-04 | Cloud deployment instructions needed headless execution verification command | `README.md:210` | `low` | `patch` | Added headless Streamlit execution flags for CI/cloud health checks. |
| F-05 | README figure generation command used space-separated `--formats png pdf` instead of comma-separated `--formats png,pdf` | `README.md:181` | `medium` | `patch` | Patched CLI example command to use comma-separated formats matching argparse specification. |
| F-06 | Methodology facility coordinates, locations, and products diverged from configuration tables | `docs/methodology.md:38-44` | `high` | `patch` | Realigned factory table to match canonical records in `config/factories.csv` and `config/product_factory.csv`. |
| F-07 | Earth radius constant stated 6,371.0 km instead of exact 6,371.0088 km | `docs/methodology.md:18` | `low` | `patch` | Updated Earth radius to 6,371.0088 km matching `src/map_factories.py:EARTH_RADIUS_KM`. |
| F-08 | Metric descriptions for `is_delayed` and `is_watchlist` required exact inequality parity | `docs/data_dictionary.md:167-169` | `low` | `patch` | Documented strict inequality ($L_i > \theta$) and exact quadrant Boolean logic. |

## Design Notes

1. **Documentation Hierarchy:**
   - `docs/data_dictionary.md` serves as the authoritative tabular schema reference.
   - `docs/methodology.md` serves as the formal mathematical and algorithmic reference.
   - `docs/synthetic_assumptions.md` serves as the simulation parameter disclosure document.
   - `README.md` serves as the public landing page and quickstart guide.

2. **Decoupled Architecture Invariant:**
   - `tests/test_documentation.py` uses AST parsing to enforce zero Streamlit imports, maintaining clean decoupling between backend verification and presentation layer.

## Verification

**Commands:**
- `.venv\Scripts\pytest tests/test_documentation.py` -- Output: 9 passed in 0.09s (100% pass rate)
- `.venv\Scripts\pytest` -- Output: 151 passed in 52.42s (100% pass rate across entire suite)
