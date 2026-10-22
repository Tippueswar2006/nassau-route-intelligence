# Epic 6 Context: Sensitivity Verification, Research Figures & Cloud Deployment Finalization

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Execute formal robustness experiments, generate publication figures for the research paper, complete full documentation, and verify zero-PII cloud release gates for production deployment.

## Stories

- Story 6.1: Sensitivity Analysis & Seed Robustness Test Suite
- Story 6.2: Publication Figure Generation Script
- Story 6.3: Comprehensive Documentation & Data Dictionary
- Story 6.4: Cloud Deployment Validation & Zero-PII Release Gate Check

## Requirements & Constraints

- Sensitivity verification: evaluate Route Efficiency Score (RES) rankings across 5 deterministic generator seeds (`[42, 101, 202, 303, 404]`) and varying speed/variability weights (`50/50`, `70/30`, `90/10`).
- Rank correlation (Spearman $\rho$) between 70/30 baseline and alternative weight configurations must be computed, verified for high stability ($\rho \ge 0.85$), and logged.
- Top bottleneck routes (specifically *Lot's O' Nuts -> Texas*) must remain consistent and recovered across seeds under standard screening ($N \ge 30$, $\text{Volume} \ge P_{75}$, $\text{Delay Rate} \ge P_{75}$ or Watchlist).
- Standalone publication figure generation script (`scripts/generate_paper_figures.py`) generating 300 DPI figures in `docs/figures/`.
- Full repository documentation suite: `docs/data_dictionary.md`, `docs/methodology.md`, `docs/synthetic_assumptions.md`, and `README.md`.
- Cloud deployment gate check: simulated cloud startup (verifying operation when `data/original/` is absent), zero-PII compliance (no unmasked customer/order identifiers), and 100% test suite pass rate.

## Technical Decisions

- Deterministic seed evaluation: use existing generator functions with explicit seeds `[42, 101, 202, 303, 404]`.
- Pure backend test architecture: `tests/test_sensitivity.py` executes without UI dependencies (zero Streamlit imports).
- Consistent RES calculation invariants: min-max scaling, mode adjustment, and sample size guardrail ($N \ge 30$).
- Fast execution: reuse precomputed artifacts where applicable or generate in-memory synthetic datasets cleanly for multi-seed evaluations.

## Cross-Story Dependencies

- Stories 6.1–6.3 depend on completed Epics 1–5 data pipelines, analytics metrics, and dashboard pages.
- Story 6.4 depends on Stories 6.1, 6.2, and 6.3 to complete final release validation.
