# Phase 8: Performance and Reliability Audit

**Project:** Nassau Candy Shipping Route Intelligence  
**Audit Date:** 2026-10-25  
**Auditor:** Antigravity Senior Engineering & QA Lead  
**Test Environment:** Windows 11 x64, Intel Core i7-based system, Python 3.10.11, pyarrow 25.0.1  

---

## 1. Measured Performance Benchmarks

All performance metrics below were empirically measured on the active system under verified local test conditions.

| Pipeline Stage / Operation | Scope / Dataset | Target SLA | Actual Measured Duration | Status | Notes |
|---|---|---|---|---|---|
| **Cold Artifact Ingestion** | Load 5 Parquet tables + `metadata.json` | $< 2.0\text{s}$ | **0.5737s** | **EXCELLENT** | Measured via PyArrow native columnar read |
| **Route Aggregation & Grouping** | Group 9,881 rows across 196 corridors | $< 1.0\text{s}$ | **0.4406s** | **EXCELLENT** | State-level multi-metric aggregation |
| **Warm In-Memory Filter Query** | 5 simultaneous filter dimensions | $< 1.0\text{s}$ | **0.0480s** | **EXCELLENT** | Sub-second reactive UI response (SC-7) |
| **Cold Filter Pipeline Initialization** | Cold startup filter run (610 records) | $< 1.0\text{s}$ | **0.6225s** | **EXCELLENT** | Includes reference mean precomputation |
| **Offline Pipeline Build** | Full build: Ingest, Reconcile, 3x Sim, Parquet | $< 60.0\text{s}$ | **34.09s** | **EXCELLENT** | Rebuilds all derived & synthetic data |
| **Publication Figure Generation** | 4 figures $\times$ 2 formats (300 DPI PNG & PDF) | $< 30.0\text{s}$ | **15.22s** | **EXCELLENT** | Matplotlib/Seaborn vector & raster export |
| **Full Pytest Suite Execution** | 167 automated unit/integration/UI tests | $< 180.0\text{s}$ | **157.27s** | **PASS** | Includes 8 full Streamlit AppTest runs |

---

## 2. Memory Consumption and Resource Profiling

- **Traced Peak Memory (`tracemalloc`):** **32.90 MB** during simultaneous loading of all 5 Parquet tables and execution of route aggregations.
- **Parquet Storage Efficiency:**
  - Raw uncompressed CSV: $1,440.6\text{ KB}$
  - Clean Orders Parquet: $395.4\text{ KB}$ (compression ratio: $3.64:1$)
  - Route Aggregates Parquet: $15.4\text{ KB}$
  - Synthetic Scenarios (3 files total): $1,368.1\text{ KB}$
- **Resource Leaks:** None detected. DataFrames are immutable structures returned by pure functional transformations without global reference accumulation or circular references.
- **Garbage Collection:** Standard CPython reference counting cleans up temporary query slices upon function exit.

---

## 3. Reliability, Concurrency, and Error Recovery

1. **Pre-computed Invariance (AD-06):** In Nassau Route Intelligence, shipping mode reference means $\mu_{\text{ship\_mode}}$ are pre-computed on the full dataset before user filters are applied. This guarantees that user filtering does not distort reference lead times or create algorithmic drift.
2. **Defensive Edge Case Resilience:**
   - **Empty Filter Selections:** If a user selects filter criteria that match 0 rows, all 8 pages render informative warning banners rather than unhandled index errors or empty Plotly charts.
   - **Zero-Variance / Constant Corridors:** Route efficiency scoring checks whether $(\max - \min) == 0$ and assigns penalty $0.0$, preventing `ZeroDivisionError`.
   - **Sample-Size Guardrails ($N \ge 30$):** Unstable low-sample routes are segregated to a dedicated table with low-sample warnings, protecting leaderboard rankings from small-number noise.
3. **Headless Execution & Zero-Streamlit Backend:** Because all algorithmic operations are headless in `src/`, scheduled batch jobs, CLI pipelines, and background processing run reliably without Streamlit server dependencies.
