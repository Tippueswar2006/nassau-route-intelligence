# Nassau Route Intelligence — Synthetic Data Generation Assumptions & Calibration

> **Synthetic Data Disclosure (AD-02):** The lead-time durations, delivery transit intervals, and synthetic scenario dates in the Nassau Route Intelligence analytical platform are calibrated simulations generated from empirical distribution models. They represent research and testing simulations rather than verified historical carrier performance.

---

## 1. Motivation & Context

### 1.1 The Source Date Interval Anomaly (AD-01)
During initial data profiling of `data/original/nassau_candy.csv`, a pervasive date interval defect was uncovered across all 10,194 raw records:
- **Raw Interval Span:** Recorded transit intervals (`Ship Date − Order Date`) range from **904 to 1,642 days** (mean: 1,320.84 days; median: 1,274 days).
- **Zero Real-World Lead Times:** There are zero records with raw transit intervals under 30 days.
- **Root Cause Analysis:** Investigation revealed that raw ship dates fall between 2026 and 2030, while order dates fall between 2024 and 2025. The minimum lead-time floor is deterministically coupled to the year encoded inside the `Order ID` (e.g., `US-2021-...` has floor 904d; `US-2022-...` has floor 1,269d; `US-2024-...` has floor 1,634d).
- **Architectural Decision (AD-01):** Although subtracting these year-group floors produces plausible intervals of 0–11 days separating cleanly by ship mode, this reconstruction remains an unconfirmed hypothesis. Presenting unverified dates as historical truth would violate analytical integrity.

### 1.2 The Role of Synthetic Simulation
To provide a reliable, scientifically defensible platform for supply chain intelligence, Nassau Route Intelligence implements calibrated synthetic simulation. This enables:
1. **Realistic Transit Dynamics:** Generating plausible order-to-ship durations calibrated to industry empirical distributions.
2. **Controlled Logistics Stress Testing:** Injecting seasonal peak volumes and regional disruptions to test supply-chain resilience.
3. **Multi-Seed Robustness:** Demonstrating that route rankings and bottleneck detections remain stable across different stochastic realizations.
4. **Privacy-Preserving Open Deployment:** Allowing cloud deployment without exposing proprietary customer transaction timelines or sensitive PII.

---

## 2. Customer Shipment Grouping & Order Grain

A critical architectural distinction exists between **order lines** and **physical customer shipments**:

### 2.1 Order Grain Hierarchy
- **Raw Export Grain:** The source dataset represents **individual order lines** (8,549 distinct `Order ID`s across 9,881 clean rows).
- **Physical Shipment Grain:** In real-world fulfillment, a customer placing multiple orders on the same date with the same carrier service level has those lines consolidated into a single physical dispatch:
  $$\text{Shipment Grain} = (\text{Customer ID}, \text{Order Date}, \text{Ship Mode})$$
- **Consolidation Summary:**
  - Total Clean Order Lines: 9,881
  - Unique Customer Shipments: 5,067
  - Multi-Order-Line Shipments: 2,240 (44.2% of shipments contain $\ge 2$ order lines)
  - Multi-Factory Shipments: 1,702 (33.6% of shipments require products from $\ge 2$ production facilities)

### 2.2 Simulation Assignment Rule
Synthetic lead times are generated at the **customer shipment level** and joined back to constituent order lines. This prevents artificial variance within the same customer order and preserves realistic dispatch coherence.

---

## 3. Empirical Baseline Distribution Calibration

The baseline simulation scenario (`data/synthetic/baseline.parquet`) draws discrete transit durations from empirical probability distributions calibrated to commercial logistics standards across the four shipping tiers:

### 3.1 Empirical Probability Tables

#### Same Day Delivery
- **Days Distribution:** `[0, 1, 2]`
- **Discrete Probabilities:** `[0.640, 0.336, 0.024]`
- **Calibrated Mean:** $0.38\text{ days}$
- **Calibrated Standard Deviation:** $0.53\text{ days}$
- **Target SLA:** Intra-day delivery; 97.6% delivered within 24 hours.

#### First Class (Expedited Air)
- **Days Distribution:** `[1, 2, 3, 4, 5]`
- **Discrete Probabilities:** `[0.123, 0.353, 0.378, 0.145, 0.001]`
- **Calibrated Mean:** $2.55\text{ days}$
- **Calibrated Standard Deviation:** $0.89\text{ days}$
- **Target SLA:** Priority air parcel; 85.4% delivered within 3 days.

#### Second Class (Priority Ground)
- **Days Distribution:** `[1, 2, 3, 4, 5, 6]`
- **Discrete Probabilities:** `[0.001, 0.267, 0.245, 0.209, 0.204, 0.075]`
- **Calibrated Mean:** $3.57\text{ days}$
- **Calibrated Standard Deviation:** $1.28\text{ days}$
- **Target SLA:** 2-to-4 day regional priority delivery.

#### Standard Class (Economy Ground)
- **Days Distribution:** `[3, 4, 5, 6, 7, 8]`
- **Discrete Probabilities:** `[0.002, 0.276, 0.334, 0.217, 0.135, 0.036]`
- **Calibrated Mean:** $5.32\text{ days}$
- **Calibrated Standard Deviation:** $1.13\text{ days}$
- **Target SLA:** Standard national freight; 3-to-7 day window.

---

## 4. Distance Sensitivity Model

In real supply chains, physical distance introduces transit friction. The distance-sensitive scenario (`data/synthetic/distance_sensitive.parquet`) incorporates Great-Circle Haversine distances between production factories and destination centroids.

### 4.1 Sensitivity Formulation
For each shipment corridor with distance $d$ (in km) and mode mean distance $\bar{d}_m$, a centered distance adjustment is applied:

$$\Delta_{\text{distance}} = \beta_{\text{dist}} \cdot \left(\frac{d - \bar{d}_m}{1,000}\right)$$

Where:
- $\beta_{\text{dist}} = 0.50\text{ days per 1,000 km}$ ($0.0005\text{ days/km}$).
- Centering around the mode mean distance $\bar{d}_m$ ensures that the overall population mean transit time remains anchored to empirical benchmarks.

### 4.2 Base Order-of-Operations Clamping
To prevent physically impossible negative durations or extreme unbounded values, baseline and distance adjustments are strictly bounded:
- **Same Day Mode:** Clamped to $[0.0, 2.0]\text{ days}$.
- **All Other Modes:** Clamped to $[1.0, 14.0]\text{ days}$.

---

## 5. Stress-Test Disruption Scenarios

The stress-test scenario (`data/synthetic/stress_test.parquet`) evaluates logistics resilience under compounding seasonal, geographic, and facility-specific disruptions:

### 5.1 Injected Disruption Layers

1. **Peak Season Congestion (Q4 Holiday Surge):**
   - **Condition:** Order placed in November or December (`Order Date` month $\in \{11, 12\}$).
   - **Disruption:** $+1.0\text{ day}$ transit delay added to simulate carrier terminal congestion.
2. **State-Level Depot Bottlenecks:**
   - **Condition:** Destination state is California (`CA`) or New York (`NY`).
   - **Disruption:** $+1.0\text{ day}$ transit delay added to simulate coastal metropolitan hub delays.
3. **Targeted Factory-Route Corridor Disruption:**
   - **Condition:** Shipments originating from **Lot's O' Nuts** destined for **Texas**, or originating from **Wicked Choccy's** destined for **Texas**.
   - **Disruption:** $+1.5\text{ days}$ transit delay injected to model regional carrier capacity breakdown.

### 5.2 Compounding Injections & Expanded Bounds
Because multiple stress factors can coincide (e.g., a December shipment from Wicked Choccy's to Texas), delays compound additively. To accommodate severe delays without artificial truncation, clamping boundaries are expanded:
- **Same Day Mode:** Clamped to $[0.0, 6.0]\text{ days}$.
- **All Other Modes:** Clamped to $[1.0, 20.0]\text{ days}$.

---

## 6. Privacy & Surrogate Key Anonymization (AD-04)

To support public demonstration and cloud hosting without exposing proprietary data or personally identifiable information:

1. **Customer ID Masking:**
   - Raw 6-digit Customer IDs (`103800`, `107153`) are replaced with randomized surrogate hex tokens formatted as:
     $$\text{Surrogate Customer ID} = \text{"CUST-"} + \text{hex8}$$
   - Example: `CUST-7457a143`.
2. **Order ID Masking:**
   - Raw Order IDs embedding customer accounts and years are replaced with randomized surrogate tokens:
     $$\text{Surrogate Order ID} = \text{"ORD-"} + \text{hex10}$$
   - Example: `ORD-0e1037e94b`.
3. **Granular Geography Elimination:**
   - `City` and `Postal Code` fields are completely omitted from public and cloud analytical Parquet tables.
   - Analysis operates exclusively at the state/provincial and regional level.
4. **Standalone Cloud Operation:**
   - Cloud deployments run directly from precomputed synthetic Parquet tables (`data/synthetic/`).
   - The original raw data directory `data/original/` and surrogate mapping file `surrogate_key_mapping.csv` are excluded from cloud repository checkouts.

---

## 7. Multi-Seed Robustness Standards

To ensure conclusions are statistically reproducible and not dependent on an arbitrary pseudorandom number sequence:

### 7.1 Seed Standard
The generator configuration defines 5 fixed, reproducible random seeds:
$$\mathcal{S} = \{42, 101, 202, 303, 404\}$$

- **Canonical Baseline:** Seed `42` is utilized for standard artifact generation.
- **Robustness Test Suite (`tests/test_sensitivity.py`):** Evaluates all 5 seeds systematically to verify:
  1. **Corridor Rank Stability:** Mean pairwise Spearman rank correlation $\bar{\rho} \ge 0.85$ across all 10 seed combinations.
  2. **Injected Bottleneck Recovery:** $\ge 80\%$ recovery rate ($\ge 4$ of 5 seeds) of the target Texas corridors into Quadrant 1 (Critical Bottlenecks).
  3. **Sample Size Sensitivity:** Demonstrates that the $N \ge 30$ guardrail consistently isolates high-volume corridors across all seeds.
