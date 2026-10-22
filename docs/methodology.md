# Nassau Route Intelligence — Analytical & Mathematical Methodology

> **Methodological Context:** This document details the mathematical formulations, statistical normalizations, and algorithmic screening criteria implemented across the Nassau Route Intelligence analytical platform.

---

## 1. Geographic Modeling & Great-Circle Distance

To model transit logistics without requiring external proprietary routing APIs or exposing street-level destination coordinates, Nassau Route Intelligence employs spherical trigonometry via the **Haversine formula**.

### 1.1 Haversine Distance Formulation

The Great-Circle distance $d$ between production facility origin $(\phi_1, \lambda_1)$ and customer destination centroid $(\phi_2, \lambda_2)$ is defined as:

$$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$

Where:
- $R = 6,371.0088\text{ km}$ (WGS-84 volumetric mean radius of the Earth, defined in `src/map_factories.py:EARTH_RADIUS_KM`).
- $\phi_1, \phi_2$ denote origin and destination latitudes in radians ($\phi = \text{degrees} \times \frac{\pi}{180}$).
- $\Delta \phi = \phi_2 - \phi_1$ denotes the latitude difference.
- $\Delta \lambda = \lambda_2 - \lambda_1$ denotes the longitude difference.

### 1.2 Destination Centroid Approximation

- **US Destinations:** Mapped to population-weighted state geographic centroids (`config/geographic_centroids.csv`).
- **Canadian Destinations:** Mapped to provincial population centroids.
- **Distance Band Stratification:** To support stratified logistics analysis, routes are categorized into four standardized distance bands:
  - Band 1: `0–500 km` (Local / Regional Distribution)
  - Band 2: `500–1,500 km` (Short-Haul Interstate)
  - Band 3: `1,500–3,000 km` (Medium-Haul Transcontinental)
  - Band 4: `3,000+ km` (Long-Haul Cross-Country / Trans-border)

### 1.3 Production Facility Mapping

The 15 confectionery product lines map deterministically to 5 specialized manufacturing facilities (defined in `config/factories.csv` and `config/product_factory.csv`):

| Production Facility | Location | Latitude | Longitude | Primary Output / SKUs |
|---|---|:---:|:---:|---|
| **Lot's O' Nuts** | Eloy, AZ | 32.881893 | -111.768036 | Wonka Bar - Nutty Crunch Surprise, Scrumdiddlyumptious, Fudge Mallows |
| **Wicked Choccy's** | Savannah, GA | 32.076176 | -81.088371 | Wonka Bar - Milk Chocolate, Triple Dazzle Caramel |
| **Sugar Shack** | Thief River Falls, MN | 48.119140 | -96.181150 | Fizzy Lifting Drinks, Laffy Taffy, SweeTARTS, Nerds, Fun Dip |
| **Secret Factory** | Rock Island, IL | 41.446333 | -90.565487 | Wonka Gum, Lickable Wallpaper, Everlasting Gobstopper |
| **The Other Factory** | Memphis, TN | 35.117500 | -89.971107 | Kazookles, Hair Toffee |

---

## 2. Shipping Mode Normalization

A fundamental analytical challenge in multi-modal supply chains is that raw lead times reflect carrier service-level agreements (SLAs) rather than pure corridor efficiency. Standard Class shipments naturally require more transit days than Same Day or First Class air dispatches. Evaluating corridors solely on unadjusted lead times unfairly penalizes high-volume Standard Class routes.

### 2.1 Fixed Invariant Mode Reference Benchmarks

To eliminate sample-composition bias, the system applies invariant empirical mode reference means ($L_{\text{ref}, m}$) derived from baseline diagnostic calibration:

| Shipping Mode ($m$) | Reference Baseline Mean ($L_{\text{ref}, m}$) | Standard Deviation ($\sigma_{\text{ref}, m}$) | Service Level Description |
|---|:---:|:---:|---|
| **Same Day** | $0.38\text{ days}$ | $0.53\text{ days}$ | Intra-day emergency dispatch |
| **First Class** | $2.55\text{ days}$ | $0.89\text{ days}$ | Priority expedited delivery (1–3 days) |
| **Second Class** | $3.57\text{ days}$ | $1.28\text{ days}$ | Standard expedited parcel (2–5 days) |
| **Standard Class** | $5.32\text{ days}$ | $1.13\text{ days}$ | Ground freight economy (3–7 days) |

### 2.2 Mode-Adjusted Lead Time

For order line $i$ shipped under service tier $m$ with simulated transit time $L_i$, the mode-adjusted lead time $\Delta L_i$ is computed as:

$$\Delta L_i = L_i - L_{\text{ref}, m}$$

**Interpretation:**
- $\Delta L_i = 0$: Shipment executed exactly on schedule for its mode tier.
- $\Delta L_i > 0$: Shipment experienced excess transit delay relative to mode expectation.
- $\Delta L_i < 0$: Shipment arrived faster than average mode transit time.

Mode normalization ensures that a route shipping 95% Standard Class cargo can be compared objectively against a route handling predominantly expedited First Class parcels.

---

## 3. Route Efficiency Score (RES) Formulation

The **Route Efficiency Score (RES)** evaluates shipping corridors on a continuous scale from $0.0$ (lowest efficiency / severe degradation) to $100.0$ (optimal operational efficiency).

RES synthesizes two distinct operational dimensions:
1. **Speed ($70\%$ Weight):** Mean mode-adjusted transit time across all order lines on the corridor.
2. **Variability ($30\%$ Weight):** Standard deviation of transit times, reflecting delivery unpredictability and supply-chain risk.

### 3.1 Speed Penalty Calculation

The Speed Penalty $P_{\text{speed}}$ min-max scales the corridor's mean transit performance relative to the comparison population:

$$P_{\text{speed}} = 100 \cdot \frac{\bar{L} - L_{\min}}{L_{\max} - L_{\min}}$$

Where:
- $\bar{L}$ is the corridor mean mode-adjusted transit time (or mean lead time if raw basis is selected).
- $L_{\min}$ and $L_{\max}$ are the minimum and maximum mean lead times observed across all eligible corridors in the evaluation set.
- **Division-by-Zero Safeguard:** If $L_{\max} = L_{\min}$, $P_{\text{speed}} = 0.0$.

### 3.2 Variability Penalty Calculation

The Variability Penalty $P_{\text{var}}$ min-max scales delivery inconsistency across corridors:

$$P_{\text{var}} = 100 \cdot \frac{\sigma - \sigma_{\min}}{\sigma_{\max} - \sigma_{\min}}$$

Where:
- $\sigma$ is the sample standard deviation ($ddof = 1$) of transit times on the corridor. For corridors with a single order line or zero variance, $\sigma = 0.0$.
- $\sigma_{\min}$ and $\sigma_{\max}$ are the minimum and maximum standard deviations across eligible corridors.
- **Division-by-Zero Safeguard:** If $\sigma_{\max} = \sigma_{\min}$, $P_{\text{var}} = 0.0$.

### 3.3 Composite RES Score

The composite Route Efficiency Score blends speed and variability penalties:

$$RES = 100 - \left(w_{\text{speed}} \cdot P_{\text{speed}} + w_{\text{var}} \cdot P_{\text{var}}\right)$$

Subject to boundary clamping:

$$RES_{\text{final}} = \min(100.0, \max(0.0, \text{round}(RES, 2)))$$

**Canonical Weights:**
- $w_{\text{speed}} = 0.70$
- $w_{\text{var}} = 0.30$
- Note that $w_{\text{speed}} + w_{\text{var}} = 1.00$.

### 3.4 Speed-Only Benchmark Score

To assess the incremental impact of delivery variance on corridor rankings, the system computes an unweighted speed-only benchmark ($w_{\text{speed}} = 1.0, w_{\text{var}} = 0.0$):

$$RES_{\text{speed-only}} = \min(100.0, \max(0.0, \text{round}(100.0 - P_{\text{speed}}, 2)))$$

---

## 4. Sample Size Guardrails ($N \ge 30$)

In supply chain analytics, small-sample corridors (e.g., a route that shipped 2 orders in two years) introduce extreme statistical volatility. A single delayed parcel can artificially depress a corridor's performance metrics or generate misleading variance estimates.

### 4.1 Statistical Foundation (Central Limit Theorem)

Under the Central Limit Theorem (CLT), sample means of independent observations converge toward normality when sample size $N \ge 30$. At $N < 30$, sample standard deviations ($s$) have wide confidence intervals, rendering min-max penalty scaling noisy and vulnerable to outliers.

### 4.2 Guardrail Policy in Application Views

1. **Route Leaderboard (Page 3):** Corridors with $N < 30$ are filtered out by default from Top/Bottom efficiency rankings. An explicit toggle allows users to inspect low-volume routes with prominent sample-size warnings.
2. **Bottleneck Quadrant (Page 6):** Quadrant screening applies strictly to corridors meeting $N \ge 30$. Low-volume corridors are displayed as hollow markers or relegated to an auxiliary low-volume audit table.
3. **Robustness Trade-Offs:** The sample threshold sensitivity analysis confirms that while $N \ge 10$ admits 128 corridors, $N \ge 30$ retains 85 core commercial corridors representing $91.4\%$ of total shipment volume while suppressing small-sample noise.

---

## 5. Transparent Bottleneck Quadrant Screening

Rather than relying on opaque black-box scoring, bottleneck detection utilizes a **transparent, dual 75th-percentile screening quadrant**:

### 5.1 Dual-Threshold Criteria

For all eligible corridors meeting the sample size guardrail ($N \ge 30$):
1. **Volume Threshold ($T_{\text{vol}}$):** 75th percentile of corridor order-line volume:
   $$T_{\text{vol}} = P_{75}(\{N_k\})$$
2. **Delay Rate Threshold ($T_{\text{delay}}$):** 75th percentile of corridor delay rate (percentage of shipments exceeding $5.0\text{ days}$):
   $$T_{\text{delay}} = P_{75}(\{\text{DelayRate}_k\})$$

### 5.2 Quadrant Categorization Matrix

| Quadrant | Volume Condition | Delay Rate Condition | Operational Status | Management Action |
|---|:---:|:---:|:---:|---|
| **Q1: Critical Bottlenecks** | $N \ge T_{\text{vol}}$ | $\text{DelayRate} \ge T_{\text{delay}}$ | **Severe Risk** | Immediate carrier renegotiation, alternate DC routing |
| **Q2: Watchlist (High Delay)** | $N < T_{\text{vol}}$ | $\text{DelayRate} \ge T_{\text{delay}}$ | **Moderate Risk** | Monitor carrier SLA compliance; investigate local depot |
| **Q3: Watchlist (High Volume)** | $N \ge T_{\text{vol}}$ | $\text{DelayRate} < T_{\text{delay}}$ | **High Exposure** | Protect capacity; minor operational disruptions impact high volume |
| **Q4: High Performers** | $N < T_{\text{vol}}$ | $\text{DelayRate} < T_{\text{delay}}$ | **Optimal** | Maintain standard operating procedures |

### 5.3 Target Injected Bottlenecks

In the synthetic stress test simulation, deliberate disruptions are injected into:
- `Lot's O' Nuts -> Texas` ($+1.5\text{ days}$)
- `Wicked Choccy's -> Texas` ($+1.5\text{ days}$)

The dual-threshold algorithm successfully isolates both corridors into Quadrant 1 (Critical Bottlenecks) across $\ge 80\%$ of randomized simulation seeds.

---

## 6. Sensitivity & Multi-Seed Robustness Framework

To prove that analytical insights are robust and not artifacts of specific mathematical weights or random seeds, the methodology incorporates a rigorous sensitivity verification framework.

### 6.1 Spearman Rank Correlation ($\rho$)

Corridor ranking stability across varying weight profiles and seeds is evaluated using Spearman's rank correlation coefficient:

$$\rho = 1 - \frac{6 \sum_{i=1}^n d_i^2}{n(n^2 - 1)}$$

Where:
- $d_i = R(x_i) - R(y_i)$ represents the rank difference of corridor $i$ between two scoring configurations.
- $n$ is the number of eligible corridors ($N \ge 30$).

### 6.2 Robustness Standards & Acceptance Gates

1. **Weight Sensitivity:**
   - Evaluated across $50/50$ ($w_s=0.50, w_v=0.50$), $70/30$ (baseline), and $90/10$ ($w_s=0.90, w_v=0.10$).
   - **Acceptance Gate:** Spearman $\rho \ge 0.85$ between $70/30$ baseline and alternative weight configurations.
2. **Multi-Seed Stability:**
   - Evaluated across 5 deterministic seeds: `[42, 101, 202, 303, 404]`.
   - **Acceptance Gate:** Mean pairwise rank correlation across all 10 seed pairs must satisfy $\bar{\rho} \ge 0.85$.
3. **Bottleneck Consistency:**
   - Target Texas bottleneck corridors must be recovered in Quadrant 1 in at least 4 out of 5 simulation seeds ($\ge 80\%$ recovery rate).
