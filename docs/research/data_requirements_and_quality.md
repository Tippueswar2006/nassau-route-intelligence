# Data Requirements and Data Quality Governance Report

**Project:** Nassau Candy Shipping Route Intelligence  
**Role:** Senior Data Analytics Consultant & Technical Research Specialist  
**Document Status:** Complete Deliverable 8  

---

## 1. Executive Data Quality Statement & Constraints

Data integrity is the bedrock of credible logistics analytics. In accordance with strict project guidelines, the Nassau Candy Shipping Route Intelligence project enforces three absolute rules:
1. **Source Immutability:** The raw uploaded dataset must remain 100% read-only and unedited. No source row may be silently corrected, overwritten, imputed, or dropped in place.
2. **Epistemic Honesty:** All analytical findings originating from synthetic data must be explicitly demarcated. Synthetic lead times must never be presented as actual corporate performance.
3. **Financial Separation:** The column labelled `Cost` in the Nassau Candy dataset represents **Cost of Goods Sold (COGS)** (manufacturing/product cost), NOT carrier freight transportation cost. Conflating COGS with shipping spend is strictly prohibited.

---

## 2. Comprehensive Data Requirements Matrix

The matrix below evaluates the 13 essential data attributes required for comprehensive shipping route intelligence, benchmarking their presence, role, validation rules, and remediation paths:

| Field Name | Functional Importance | Dependent Analyses | Presence in Baseline Dataset | Validation & Integrity Rules | Remediation Strategy if Missing or Unreliable |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **Order ID** | Primary transactional key; distinguishes orders from line items | Volume measurement, unique order KPIs, drill-down | **Present** | Non-null; alphanumeric string; check if orders span multiple rows | If missing, generate synthetic surrogate key `SYN_ORD_{index}` |
| **Order Date** | Temporal baseline for order entry | Fulfillment lead time, monthly trend, seasonality | **Present** | ISO-8601 date parse; non-null; chronological consistency | Present, but gap to Ship Date is corrupted (904–1,642 days). Profile in DQ; replace with synthetic timing for time metrics |
| **Ship Date** | Warehouse outbound dispatch timestamp | Fulfillment lead time, delay rate, efficiency score | **Present** | ISO-8601 date parse; must occur $\ge$ Order Date | Corrupted in raw file (904–1,642 days later). Retain in Original layer; generate `Ship_Date_Synthetic` for demo |
| **Actual Delivery Date** | In-transit termination timestamp (customer dock) | Carrier transit lead time, true On-Time Delivery (OTD) | **Missing** | Must occur $\ge$ Ship Date | Missing in source. Derive `Promised_Delivery_Date` and `Delivery_Date_Synthetic` in synthetic layer |
| **Factory Identifier** | Origin node for physical manufacturing and dispatch | Factory-to-state routing, network reallocation | **Derived** (via Product Lookup) | Categorical; 5 distinct factories (`Factory A` to `E`) | Map via Product-to-Factory lookup table. Flag and report unmatched products; do not invent a factory |
| **Product Name / SKU** | Identifies commodity and drives factory mapping | Volume by category, product-factory mapping | **Present** | String; non-null; trim leading/trailing whitespace | Check mapping coverage. If unmatched, assign to "Unmapped / Unknown Factory" and exclude from route scores |
| **Customer State** | Destination spatial node for geographic routing | Route aggregation ($Factory \to State$), US choropleth | **Present** | 2-letter standard US FIPS/postal code | Standardize uppercase; validate against 50 US states + DC. Flag unrecognized state codes |
| **Customer Region** | Macro-geographic cluster (East, West, Central, South) | Regional volume aggregation, macro bottleneck view | **Present** | Categorical; consistent with US Census regions | If missing, derive deterministically from Customer State mapping dictionary |
| **Shipping Mode** | Logistics service level (Same Day, First, Second, Standard) | Modal comparison, lead-time distribution, cost-time | **Present** | Categorical string; non-null | Validate against allowed set (`Same Day`, `First Class`, `Second Class`, `Standard Class`) |
| **Sales (Revenue)** | Financial transaction value | Revenue throughput by lane, commercial importance | **Present** | Numeric float; $\ge 0.0$ | Retain original values; used for commercial volume weighting |
| **Units Shipped** | Physical volume count | Physical throughput, package density | **Present** | Integer $\ge 1$ | Retain original values; used for physical volume KPIs |
| **Cost (COGS)** | Product manufacturing / wholesale acquisition cost | Gross margin calculation ($\text{Sales} - \text{Cost}$) | **Present** | Numeric float; $\ge 0.0$ | **CRITICAL:** Do NOT treat as freight cost. Label explicitly as "Product Manufacturing Cost / COGS" |
| **Carrier Information** | Identifies freight service provider (e.g., FedEx, UPS) | Carrier scorecards, contract SLA compliance | **Missing** | String identifier | Missing in raw file. Exclude carrier benchmarking from v1; document as data requirement for v2 |
| **Route Distance (km)** | Spatial haul length between factory and customer | Distance-stratified modal analysis, lead-time model | **Derived** | Numeric float; Haversine formula from Lat/Lon | Compute deterministically using factory coordinates and customer state centroid coordinates |

---

## 3. Deep Investigation: The Date Interval Anomaly

### 3.1 Observed Phenomenon
In the raw Nassau Candy dataset, computing the elapsed interval between order placement and shipment reveals a severe defect:
$$\Delta T_i = \text{Ship Date}_i - \text{Order Date}_i$$
* **Minimum Observed Interval:** $904\text{ days}$ ($\approx 2.5\text{ years}$)
* **Maximum Observed Interval:** $1,642\text{ days}$ ($\approx 4.5\text{ years}$)
* **Records Under 30 Days:** $0\text{ rows}$ ($0.00\%$)
* **Total Exact Duplicate Rows:** $313\text{ rows}$

### 3.2 Root-Cause Hypotheses
While the true technical cause can only be confirmed by Nassau Candy's IT database administrator, four plausible hypotheses explain this defect:
1. **ERP Migration Epoch Shift:** When legacy databases are migrated, date fields stored in differing integer formats (e.g., seconds since 1970 vs. days since 1900, or Julian calendar conversion errors) frequently incur constant year offsets (e.g., 2-to-4 year shifts).
2. **Mismatched Source Tables / Cartesian Join:** The SQL query extracting the export may have joined an active order table from one fiscal period (e.g., 2018–2020) against an archived historical fulfillment table from an earlier epoch (e.g., 2014–2016), misaligning primary keys.
3. **Synthetic Staging / Test Environment Artifacts:** The export may originate from a pre-production testing database where automated load-testing scripts injected randomized future timestamps.
4. **Data Masking / Anonymization Artifact:** The organization may have intentionally scrambled or perturbed date columns to obfuscate true commercial performance prior to academic release.

### 3.3 Methodological Response
* **DO NOT Silently Adjust Dates:** It is academically unethical to apply an arbitrary subtractor (e.g., $\Delta T - 1000\text{ days}$) and claim the resulting dates represent real operational history.
* **DO NOT Conclude Company Incompetence:** The dashboard and paper must explicitly state that this interval represents an **export data defect**, not evidence that Nassau Candy actually took 4 years to ship candy bars.
* **Isolate in Data Quality View:** Profile the distribution of $\Delta T$ in full transparency on the Data Quality page.

---

## 4. Separation of Capabilities: Real vs. Synthetic Layer

To maintain absolute scientific validity, dashboard capabilities are strictly partitioned across data layers:

```
+--------------------------------------------------------------------------------------------------+
| LAYER 1: ORIGINAL DATASET (Pure Empirical Facts)                                                 |
| What can be analyzed with 100% validity:                                                          |
| - Total order count and physical units shipped                                                   |
| - Geographic volume distribution (Sales and Units by Customer State & Region)                    |
| - Product mix and commercial revenue totals                                                      |
| - Shipping mode market share (percentage of orders placed via Standard vs. Expedited)             |
| - Data quality profiling (date interval distributions, exact duplicate rows, missing fields)      |
|                                                                                                  |
| What CANNOT be analyzed:                                                                         |
| - Real-world fulfillment speed, on-time delivery rates, or operational delivery bottlenecks      |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 2: DERIVED DATASET (Deterministic Spatial & Mapping Extensions)                            |
| What can be analyzed with 100% validity:                                                          |
| - Product-to-Factory mapping coverage and unmapped SKU counts                                    |
| - Factory-to-Customer State geographic routing paths                                             |
| - Physical haul distances in kilometers (Haversine formula between coordinates)                  |
| - Multi-factory volume balance (evaluating factory production concentration)                     |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 3: SYNTHETIC DATASET (Parametric Lead-Time Demonstration)                                  |
| What is demonstrated methodologically (explicitly labelled as simulation):                       |
| - Fulfillment and transit lead-time distributions (realistic 1–10 day ranges)                    |
| - Interactive delay threshold slider sensitivity                                                 |
| - Route Efficiency Scoring (RES) and Top 10 / Bottom 10 leaderboards                             |
| - Multi-criteria Bottleneck Priority Quadrant (Volume vs. Delay Rate)                           |
| - Distance-stratified Standard vs. Expedited shipping performance                                |
| - Illustrative "What-If" factory reallocation simulation                                         |
+--------------------------------------------------------------------------------------------------+
```

---

## 5. Specification for the Synthetic Timing Generator

To ensure absolute reproducibility, the synthetic timing generator must operate deterministically via a documented mathematical equation and a fixed random seed (`seed = 42`):

### 5.1 Generative Lead-Time Model
For each order record $i$, synthetic lead time ($LT_i$) is computed as:
$$LT_i = \text{round}\left( \text{Base}_{\text{mode}} + \beta_{\text{dist}} \cdot \left(\frac{D_i}{1000}\right) + \gamma_{\text{congestion}} + \delta_{\text{season}} + \epsilon_i \right)$$
$$\text{Subject to: } LT_i \ge 0$$

### 5.2 Component Parameter Calibration:
1. **Ship Mode Base ($\text{Base}_{\text{mode}}$):**
   * `Same Day`: $0.5\text{ days}$
   * `First Class`: $2.0\text{ days}$
   * `Second Class`: $3.0\text{ days}$
   * `Standard Class`: $5.0\text{ days}$
2. **Distance Coefficient ($\beta_{\text{dist}}$):**
   * $+0.5\text{ days}$ per $1,000\text{ km}$ of Haversine distance ($D_i$) between origin factory and customer state centroid.
3. **Planted Regional Congestion ($\gamma_{\text{congestion}}$):**
   * $+1.5\text{ days}$ for customer destinations in highly congested metropolitan corridors (e.g., NY, CA, IL), ensuring the bottleneck quadrant has realistic empirical phenomena to detect.
4. **Planted Macro Seasonality ($\delta_{\text{season}}$):**
   * $+1.0\text{ days}$ for orders placed during the Q4 confectionery holiday rush (November and December).
5. **Random Error ($\epsilon_i$):**
   * Gaussian white noise: $\epsilon_i \sim \mathcal{N}(\mu = 0, \sigma = 0.7\text{ days})$.
6. **Synthetic Target Fields Generated:**
   * `Promised_Delivery_Date` = $\text{Order Date} + \text{SLA}_{\text{mode}}$
   * `Ship_Date_Synthetic` = $\text{Order Date} + LT_i$
   * `Lead_Time_Days` = $LT_i$
   * `Data_Source` = `"Synthetic"` (hardcoded on every row)

---

## 6. End-to-End Data Quality Pipeline Architecture

```
[Raw Excel / CSV File Upload]
             |
             v
+---------------------------------------------------------------------------------------+
| STEP 1: SCHEMA VALIDATION GATE                                                        |
| - Verify required columns: Order ID, Order Date, Ship Date, State, Product, Sales, Units |
| - If missing critical columns -> Terminate execution with descriptive UI error message|
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| STEP 2: DUPLICATE ROW DETECTION                                                       |
| - Execute df.duplicated(); identify 313 exact duplicate rows                          |
| - Flag duplicates in Derived Layer; allow user toggle to include/exclude              |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| STEP 3: DATE INTEGRITY & INTERVAL PROFILING                                           |
| - Compute raw delta: Ship Date - Order Date                                           |
| - Flag rows where delta < 0 or delta > 30 days                                        |
| - Quarantine raw lead times from operational KPI scorecards                           |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| STEP 4: FACTORY MAPPING VERIFICATION                                                  |
| - Left-join product master against product-to-factory lookup table                    |
| - Compute Mapping Coverage Rate (Target: > 95%)                                       |
| - Route unmapped products to "Unassigned Facility" category                           |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| STEP 5: PROVENANCE-TAGGED ANALYTICAL CONSUMPTION                                      |
| - Feed Original Layer to Volume & Data Quality Pages                                  |
| - Feed Derived Layer to Spatial Mapping Pages                                         |
| - Feed Synthetic Layer to Route Scoring, Threshold Slider, and Bottleneck Explorer    |
+---------------------------------------------------------------------------------------+
```
