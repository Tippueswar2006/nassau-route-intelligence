---
title: 'Story 6.2: Publication Figure Generation Script'
type: 'chore'
created: '2026-10-21'
status: 'done'
baseline_commit: 'NO_VCS'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Academic research papers and executive briefings require high-resolution (300 DPI), fully reproducible figures generated directly from codebase artifacts without manual UI screenshotting.
**Approach:** Implement `scripts/generate_paper_figures.py` using Matplotlib and Seaborn to generate 300 DPI publication figures (PNG and PDF formats) into `docs/figures/`, supported by automated integration test `tests/test_generate_paper_figures.py`.

## Boundaries & Constraints

**Always:**
- **Standalone CLI Execution:**
  - Runnable via CLI: `python scripts/generate_paper_figures.py` with standard CLI argument parsing (`--output-dir`, `--dpi`, `--formats`).
- **Publication-Quality Standards:**
  - Strictly 300 DPI (`dpi=300`) with tight bounding boxes (`bbox_inches="tight"`).
  - Clean academic aesthetic using Seaborn `whitegrid` theme with legible fonts, defined units ("Days", "%", "km"), and clear legends.
  - Generates both PNG (high-res raster) and PDF (vector format for academic LaTeX).
- **Core Figures Generated:**
  1. `fig1_lead_time_distributions`: KDE density and boxplot comparison of lead-time distributions across Baseline, Distance-Sensitive, and Stress-Test scenarios.
  2. `fig2_res_quadrant_scatter`: Route Efficiency Score (RES) screening quadrant scatter (Speed Penalty vs. Variability Penalty) with point sizing by volume and prominent callout annotations for injected Texas bottlenecks (*Lot's O' Nuts -> Texas*, *Wicked Choccy's -> Texas*).
  3. `fig3_scenario_comparison_bars`: Multi-metric bar chart comparing Mean Lead Time, P90 Lead Time, and Delay Rate across scenarios for the entire network vs. Texas routes.
  4. `fig4_weight_sensitivity_and_thresholds`: Dual-panel figure displaying RES rank correlations (Spearman $\rho$) across weight profiles (50/50, 70/30, 90/10) and sample size threshold trade-offs ($N \in [10, 20, 30, 50, 100]$).
- **Compliance with AD-02 (Layer Badge):**
  - Every figure derived from synthetic data must display the explicit disclosure badge or subtitle: `"SYNTHETIC - NOT ACTUAL PERFORMANCE"`.
- **Architecture Invariant:**
  - Zero Streamlit imports in `scripts/generate_paper_figures.py` and `tests/test_generate_paper_figures.py` (`tests/test_architecture.py`).

**Never:**
- Never depend on interactive Streamlit runtime or active browser session.
- Never mutate or overwrite source Parquet files during figure generation.
- Never output unlabelled synthetic figures without the required synthetic disclosure badge.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Default CLI Invocation | `python scripts/generate_paper_figures.py` | 4 figures generated in `docs/figures/` as `.png` (300 DPI) and `.pdf`, exit code 0 | Log clear progress messages |
| Custom Output Directory | `--output-dir custom/dir` | Directory created if missing, all 4 figures saved to custom path | Standard Pathlib mkdir |
| Custom DPI & Formats | `--dpi 150 --formats png` | Only `.png` saved at specified DPI resolution | Validated format choices |
| Missing Synthetic Parquet | Parquet file missing from `data/synthetic/` | Graceful CLI error message and exit code 1 | Catch FileNotFoundError with path |
| Empty Filter Aggregates | Empty DataFrame input to plotting function | Graceful error/warning, empty figure avoided | Check `df.empty` before plotting |

</frozen-after-approval>

## Code Map

- `scripts/generate_paper_figures.py` -- Standalone publication figure generation script (Matplotlib / Seaborn)
- `src/config.py` -- `BASELINE_PARQUET`, `DISTANCE_PARQUET`, `STRESS_PARQUET`, `MIN_SAMPLE_SIZE`, `DEFAULT_DELAY_THRESHOLD`
- `src/route_analysis.py` -- `aggregate_routes`, `filter_eligible_routes`
- `src/metrics.py` -- `calculate_route_efficiency_scores`
- `src/bottleneck_rules.py` -- `flag_bottlenecks`, `DEFAULT_TARGET_BOTTLENECK_ROUTES`
- `src/sensitivity.py` -- `compute_weight_sensitivity`, `compute_sample_threshold_sensitivity`
- `tests/test_generate_paper_figures.py` -- Automated test suite verifying CLI execution, output files, DPI metadata, and zero UI imports

## Tasks & Acceptance

**Execution:**
- [x] `scripts/generate_paper_figures.py` -- Implement standalone publication figure generation script producing 4 high-res figures in PNG & PDF formats -- Fulfills Story 6.2 and FR-15
- [x] `tests/test_generate_paper_figures.py` -- Implement automated test suite verifying CLI execution, figure file generation, non-empty outputs, 300 DPI resolution, and decoupled backend -- Fulfills Story 6.2 AC

**Acceptance Criteria:**
- Given `scripts/generate_paper_figures.py`,
- When executed via CLI,
- Then high-resolution figures (300 DPI) are saved to `docs/figures/`,
- And figures include lead-time distributions, RES quadrant scatter, and scenario comparison bars.

## Implementation Notes

- **Figure Generator Implementation:** `scripts/generate_paper_figures.py`
  - Fully headless (`matplotlib.use("Agg")`) with zero Streamlit imports.
  - Figure 1 (`fig1_lead_time_distributions`): KDE density plots and scenario boxplots comparing Baseline, Distance-Sensitive, and Stress-Test distributions with delay threshold line ($\theta = 6.0$ days).
  - Figure 2 (`fig2_res_quadrant_scatter`): Speed Penalty vs Variability Penalty scatter with sample size point scaling, quadrant labels (Q1-Q4), and annotated callouts for *Lot's O' Nuts -> Texas*, *Wicked Choccy's -> Texas*, and *Hicksville -> New York*.
  - Figure 3 (`fig3_scenario_comparison_bars`): Multi-panel grouped bar chart comparing Network-wide vs Texas routes for Mean Lead Time and Delay Rate (%) under disruption shock.
  - Figure 4 (`fig4_weight_sensitivity_and_thresholds`): Spearman $\rho$ across weight profiles (50/50, 70/30, 90/10, 100/0, 0/100) and dual-axis sample size threshold trade-off curve ($N \in [10, 20, 30, 50, 100]$) highlighting $N=30$.
  - Generates both PNG (raster, 300 DPI) and PDF (vector) formats into `docs/figures/`.
  - Prominent synthetic disclosure badge on every figure in compliance with AD-02: `"SYNTHETIC - NOT ACTUAL PERFORMANCE | Nassau Route Intelligence"`.
- **Test Implementation:** `tests/test_generate_paper_figures.py`
  - 8 comprehensive tests covering CLI subprocess execution, dual format export, 300 DPI metadata validation via PIL, figure object integrity, artifact missing error handling, empty DataFrame fallback, custom format filtering, unsupported format error raising, and AST zero-Streamlit verification.
  - 100% test pass rate across focused and full test suites (142 tests).

## Spec Change Log

- No spec modifications or intent renegotiations required. All implementations satisfied specification constraints and acceptance criteria.

## Review Triage Log

| ID | Finding / Claim | Location | Severity | Route | Verification Evidence & Disposition |
|---|---|---|---|---|---|
| F-01 | `_save_figure` did not validate requested format extensions against supported Matplotlib backends, potentially causing unhandled exceptions on invalid extensions | `scripts/generate_paper_figures.py:65` | `medium` | `patch` | Added explicit `SUPPORTED_FORMATS` validation raising `ValueError` on unsupported formats. |
| F-02 | `generate_fig2_res_quadrant_scatter` hardcoded `sample_size` without checking for fallback `order_line_count` | `scripts/generate_paper_figures.py:226` | `medium` | `patch` | Added resilient column resolution checking `sample_size` then `order_line_count`. |
| F-03 | `generate_fig3_scenario_comparison_bars` assumed `"State/Province"` was the only destination column without checking `"analysis_destination"` | `scripts/generate_paper_figures.py:330` | `medium` | `patch` | Added fallback to `analysis_destination` if `State/Province` is absent. |
| F-04 | `generate_all_figures` lacked a `try...finally: plt.close("all")` safety block if generation failed midway | `scripts/generate_paper_figures.py:570` | `low` | `patch` | Wrapped figure generation in `try...finally: plt.close("all")` to prevent dangling in-memory figures. |
| F-05 | CLI tests did not verify single-format CLI flags (e.g., SVG-only export) | `tests/test_generate_paper_figures.py:240` | `low` | `patch` | Added `test_custom_single_format_cli` asserting correct single-format export. |
| F-06 | Missing unit test asserting `ValueError` on unsupported format extension inputs | `tests/test_generate_paper_figures.py:230` | `medium` | `patch` | Added `test_unsupported_format_error` asserting clean `ValueError` with supported list. |

## Design Notes

1. **Figure Structure & Styling:**
   - Styling: `sns.set_theme(style="whitegrid", font="sans-serif")`
   - DPI: Default 300 DPI (`plt.savefig(..., dpi=dpi, bbox_inches="tight")`)
   - Watermark/Layer Disclosure: Figure subtitle `plt.suptitle(..., fontsize=12)` with `ax.text(..., "SYNTHETIC - NOT ACTUAL PERFORMANCE", ...)` or subtitle badge.

2. **Figure 1 (Lead-Time Distributions):**
   - Subplot 1: KDE distributions of `lead_time_days` across Baseline (Blue), Distance-Sensitive (Orange), and Stress-Test (Red).
   - Subplot 2: Boxplot of lead times with median, IQR, and threshold reference line ($\theta = 6.0$ days).

3. **Figure 2 (RES Screening Quadrant Scatter):**
   - X-axis: Speed Penalty ($P_{\text{speed}}$).
   - Y-axis: Variability Penalty ($P_{\text{var}}$).
   - Route points sized by `sample_size`, color-coded by Bottleneck / Watchlist / Efficient status.
   - Quadrant divider lines at 50.0 (or medians) with annotations for top bottlenecks (*Lot's O' Nuts -> Texas*, *Wicked Choccy's -> Texas*).

4. **Figure 3 (Scenario Comparison Bars):**
   - Grouped bar chart comparing Network-wide vs. Texas Routes across scenarios for Mean Lead Time and Delay Rate (%).

5. **Figure 4 (Weight Sensitivity & Sample Size Trade-offs):**
   - Panel A: Rank correlation (Spearman $\rho$) across 50/50, 70/30, 90/10, 100/0, 0/100 weight configurations.
   - Panel B: Route retention % and volume coverage % vs. candidate sample thresholds $N \in [10, 20, 30, 50, 100]$, highlighting $N=30$ selection.
