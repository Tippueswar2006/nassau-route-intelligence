# Phase 9: Data, Algorithms, and Domain Logic Validation

**Project:** Nassau Candy Shipping Route Intelligence  
**Audit Date:** 2026-10-25  
**Auditor:** Antigravity Senior Engineering & QA Lead  
**Scope:** Mathematical Formulations, Statistical Algorithms, Geospatial Modeling, and Simulation Calibration  

---

## 1. Data Integrity and Layer Governance Audit

The system enforces strict architectural boundaries across three distinct data layers (AD-02):

```
+--------------------------------------------------------------------------------------------------+
|                                    THREE-TIER LAYER GOVERNANCE                                   |
+--------------------------------------------------------------------------------------------------+
| LAYER       | SOURCE OF RECORD         | MUTABILITY | PERMITTED ANALYTICAL USE                   |
|-------------+--------------------------+------------+--------------------------------------------|
| ORIGINAL    | data/original/           | Read-Only  | Data profiling, duplicate audits, sales/   |
|             | nassau_candy.csv         | Immutable  | margin summaries, 24-month order trends    |
|-------------+--------------------------+------------+--------------------------------------------|
| DERIVED     | data/derived/            | Pre-Built  | Route construction, factory geocoding,     |
|             | clean_orders.parquet     | Parquet    | Haversine distance calculations            |
|-------------+--------------------------+------------+--------------------------------------------|
| SYNTHETIC   | data/synthetic/          | Pre-Built  | Lead-time performance, RES benchmarking,   |
|             | baseline, distance,      | Parquet    | bottleneck screening, stress testing       |
|             | stress_test.parquet      |            |                                            |
+--------------------------------------------------------------------------------------------------+
```

### Audited Data Facts:
1. **Raw Date Interval Anomaly:** In the raw dataset (`data/original/nassau_candy.csv`), `Ship Date − Order Date` ranges from 904 to 1,642 days. Every single record exceeds 900 days; zero records fall under 30 days. The diagnostic floor reconstruction (subtracting 904, 1,269, 1,269, and 1,634 days according to the year embedded in the Order ID) reduces the interval to 0–11 days. **Audited Finding:** This reconstruction is strictly quarantined to Page 2 (*Data Quality & Method*) as an audit calibration hypothesis. It is never presented as verified carrier transit time.
2. **Duplicate Deduplication & 4-Metric Reconciliation:**
   - Exact duplicate rows (all columns identical except `Row ID`): **313 rows** across 307 content groups (620 rows involved).
   - Rows: $10,194 \rightarrow 9,881$ ($\Delta = -313$)
   - Units: $38,654 \rightarrow 37,667$ ($\Delta = -987$)
   - Sales: $\$141,783.63 \rightarrow \$138,284.12$ ($\Delta = -\$3,499.51$, $-2.47\%$)
   - Gross Profit: $\$93,442.80 \rightarrow \$91,076.41$ ($\Delta = -\$2,366.39$, $-2.53\%$)
   - Cleaned rows reconcile to approved constants with $100\%$ precision in automated tests.
3. **Product-to-Factory Resolution:**
   - 15 products map to 5 facilities with $100\%$ coverage ($0$ unmatched rows).
   - Order-line single factory invariant: Because the product SKU is embedded directly in the Order ID, every Order ID maps to exactly one factory by construction.

---

## 2. Mathematical Algorithms and Algorithmic Correctness

### A. Great-Circle Haversine Distance
- **Formula:**
  $$d = 2 R \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)} \right)$$
  Where $R = 6,371\text{ km}$, $\phi$ is latitude in radians, and $\lambda$ is longitude in radians.
- **Verification:** Evaluated against known coordinate pairs (e.g. Secret Factory in Lancaster, PA to California centroid at $36.7783^\circ\text{N}, 119.4179^\circ\text{W}$). Hand-computed test vectors match implementation within $0.01\%$. Canadian province centroids are explicitly included, preventing zero-distance errors on international corridors.

### B. Mode-Adjusted Route Efficiency Score (RES)
- **Formulation:**
  $$\text{LeadTime}_{\text{mode\_adj}} = \text{LeadTime} - \mu_{\text{ship\_mode}}$$
  $$\text{SpeedPenalty} = \frac{\mu_{\text{route}} - \min(\mu)}{\max(\mu) - \min(\mu)}$$
  $$\text{VariabilityPenalty} = \frac{\sigma_{\text{route}} - \min(\sigma)}{\max(\sigma) - \min(\sigma)}$$
  $$\text{RES} = 100 \times \left[1 - (0.70 \times \text{SpeedPenalty} + 0.30 \times \text{VariabilityPenalty})\right]$$
- **Verification:**
  1. Unit tests assert that RES strictly falls within $[0, 100]$.
  2. Fixed 70/30 weights are enforced on Pages 1–7.
  3. Pre-computed reference means $\mu_{\text{ship\_mode}}$ remain invariant regardless of downstream user filters (AD-06).
  4. Safe normalization handling: If $\max(\mu) == \min(\mu)$ or $\max(\sigma) == \min(\sigma)$, penalties are defensively set to $0.0$, preventing zero-division crashes.

### C. Sample Size Guardrail ($N \ge 30$)
- **Formulation:** Corridors with sample size $N < 30$ are excluded from Top 10 / Bottom 10 leaderboards and partitioned to a low-sample table.
- **Verification:** Tested at exact integer boundaries: $N=29$ (ineligible), $N=30$ (eligible), $N=31$ (eligible). Small manufacturing facilities (`Sugar Shack`, `Secret Factory`, `The Other Factory`) are automatically aggregated to Factory $\rightarrow$ Region rollups.

### D. Dual 75th-Percentile Bottleneck Quadrant Screening
- **Formulation:**
  - Critical Bottleneck: $\text{Volume} \ge P_{75}(\text{Volume}) \land \text{Delay Rate} \ge P_{75}(\text{Delay Rate})$
  - Watchlist: $\text{Volume} \ge P_{75}(\text{Volume}) \land \text{Delay Rate} > \text{Median}(\text{Delay Rate}) \land \neg \text{is\_bottleneck}$
- **Verification:** Tested across 5 random seeds (`[42, 101, 202, 303, 404]`). Injected stress bottlenecks on Texas routes are recovered in $5\text{ of }5$ seeds ($100\%$ recovery rate, exceeding the $\ge 80\%$ acceptance threshold).

### E. Parameter Sensitivity & Rank Stability Metrics
- **Formulation:**
  $$\rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}$$
  Where $d_i = \text{Rank}_{\text{Baseline}} - \text{Rank}_{\text{Sensitivity}}$, alongside Top 10 Retention $\%$ and Mean Absolute Rank Shift.
- **Verification:** Tested on identity profiles ($70/30 \rightarrow \rho = 1.0$), alternative presets ($50/50$, $90/10$, $100/0$), and boundary extremes.

---

## 3. Synthetic Simulation Architecture and Assumptions

| Parameter / Dimension | Baseline Scenario | Distance-Sensitive Scenario | Stress-Test Scenario |
|---|---|---|---|
| **Base Distribution** | Empirical per-mode discrete sampling | Empirical per-mode discrete sampling | Empirical per-mode discrete sampling |
| **Same Day Mean** | $0.38\text{ days}$ | $0.38\text{ days}$ | Elevated via injections |
| **First Class Mean** | $2.55\text{ days}$ | $2.55\text{ days}$ | Elevated via injections |
| **Second Class Mean** | $3.57\text{ days}$ | $3.57\text{ days}$ | Elevated via injections |
| **Standard Class Mean**| $5.32\text{ days}$ | $5.32\text{ days}$ | Elevated via injections |
| **Distance Coefficient**| None ($0.0$) | $+0.5 \times \frac{\text{Dist} - \mu_{\text{dist}}}{1000}$ | Centered distance adjustment |
| **Peak Season Injection**| None | None | $+1.0\text{d}$ in November and December |
| **Metro Delay Injection**| None | None | $+1.0\text{d}$ for CA and NY destinations |
| **Target Route Injection**| None | None | $+1.5\text{d}$ for *Lot's O' Nuts $\rightarrow$ TX* & *Wicked Choccy's $\rightarrow$ TX* |
| **Same Day Bounds** | $[0, 2]\text{ days}$ | $[0, 2]\text{ days}$ | $[0, 6]\text{ days}$ (unclipped bounds) |
| **Other Modes Bounds** | $[1, 14]\text{ days}$ | $[1, 14]\text{ days}$ | $[1, 20]\text{ days}$ (unclipped bounds) |
| **Overall Dataset Mean**| $4.29\text{ days}$ | $4.30\text{ days}$ | $5.04\text{ days}$ |
| **Seed Target** | Seed 42 | Seed 42 | Seed 42 |

### Explicit Research Assumptions & Scientific Limitations:
1. **Timing is Synthetic:** All lead times represent empirical simulations. They must never be cited as verified carrier transit performance.
2. **COGS vs Freight:** The `Cost` field in historical records represents internal manufacturing cost of goods sold (COGS). Freight transportation expenses are not captured in the source dataset.
3. **Geographic Centroid Approximation:** Corridor distances represent great-circle Haversine distances to state/province centroids rather than odometer road mileage or actual carrier delivery routing.
