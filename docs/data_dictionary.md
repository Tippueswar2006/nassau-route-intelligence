# Nassau Route Intelligence — Comprehensive Data Dictionary

> **Synthetic Data Disclosure (AD-02):** All lead-time durations, delivery transit intervals, and synthetic scenario dates in the analytical layers are calibrated simulations generated from empirical distribution models. Raw historical dates in the source file reflect an unverified transit interval anomaly (904–1,642 days) and must not be cited as verified historical transit performance.
>
> **Privacy Architecture Notice (AD-04):** Granular customer PII (`City`, `Postal Code`, raw 6-digit Customer IDs) is strictly isolated to local environments. Public and cloud deployment artifacts operate exclusively with randomized surrogate tokens (`CUST-xxxxxxxx`, `ORD-xxxxxxxxxx`) and aggregated regional geographies.

---

## 1. Data Architecture & Layer Provenance

The Nassau Candy Route Intelligence analytical engine enforces a strict, three-tier data separation model:

```
[ Tier 1: Original Layer ]
  └─ data/original/nassau_candy.csv (10,194 records, SHA-256 verified, read-only)
          │
          ▼ [ scripts/build_data.py ]
[ Tier 2: Derived Layer ]
  ├─ data/derived/clean_orders.parquet (9,881 unique rows, 313 exact duplicates flagged)
  ├─ data/derived/route_aggregates.parquet (196 factory-state routes with distances)
  ├─ data/derived/surrogate_key_mapping.csv (Local-only PII translation table)
  └─ data/derived/transformation_log.json (Audit trail & financial reconciliation)
          │
          ▼ [ scripts/build_data.py & src/generate_synthetic.py ]
[ Tier 3: Synthetic Simulation Layer ]
  ├─ data/synthetic/baseline.parquet (9,881 records, Seed 42 empirical distributions)
  ├─ data/synthetic/distance_sensitive.parquet (0.5d / 1,000 km centered adjustments)
  ├─ data/synthetic/stress_test.parquet (Nov/Dec peak, CA/NY, Texas route disruptions)
  └─ data/synthetic/metadata.json (Simulation settings, random seeds, provenance hashes)
```

---

## 2. Original Layer: `data/original/nassau_candy.csv`

- **Record Count:** 10,194 rows
- **Column Count:** 18 columns
- **Missing Values:** Zero nulls across all 18 columns
- **SHA-256 Checksum:** `6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f`
- **Immutability Invariant:** Strictly read-only; source file is never modified or overwritten.

### Column Specifications

| # | Column Name | Raw Type | Clean Type | Nullable | Distinct | Sample Value | Description & Profiling Notes |
|---|---|---|---|:---:|:---:|---|---|
| 1 | `Row ID` | Integer | `int64` | No | 10,194 | `1` | Arbitrary row index in original export. Excluded when evaluating exact duplicate order lines. |
| 2 | `Order ID` | String | `string` | No | 8,549 | `US-2021-103800-CHO-MIL-31000` | Order-line identifier encoding country, order-year, customer ID, and SKU. |
| 3 | `Order Date` | String | `date` | No | 664 | `03-01-2024` | Order placement date formatted as `dd-mm-yyyy`. All orders fall between 2024 and 2025. |
| 4 | `Ship Date` | String | `date` | No | 1,327 | `30-06-2026` | Recorded shipping date formatted as `dd-mm-yyyy`. Source dates span 2026 to 2030 (AD-01 unverified anomaly). |
| 5 | `Ship Mode` | String | `category` | No | 4 | `Standard Class` | Delivery service level: `Same Day`, `First Class`, `Second Class`, `Standard Class`. |
| 6 | `Customer ID` | Integer | `string` | No | 793 | `103800` | Raw customer account identifier. Replaced with surrogate token `CUST-xxxxxxxx` in cloud deployment. |
| 7 | `Country/Region` | String | `category` | No | 2 | `United States` | Destination country: 9,994 United States, 200 Canada. |
| 8 | `City` | String | `string` | No | 531 | `Houston` | Destination city. Dropped from cloud artifacts under Zero-PII deployment gates (AD-04). |
| 9 | `State/Province` | String | `category` | No | 59 | `Texas` | Destination state or province: 49 US States + DC, 10 Canadian Provinces. |
| 10 | `Postal Code` | Numeric/Str | `string` | No | 632 | `77095` | Raw postal code. 449 US zip codes had leading zeros dropped in source; padded to 5 digits in Derived layer. |
| 11 | `Division` | String | `category` | No | 3 | `Chocolate` | Business division: `Chocolate` (9,844 rows), `Other` (310 rows), `Sugar` (40 rows). |
| 12 | `Region` | String | `category` | No | 4 | `Interior` | Internal commercial sales territory: `Pacific`, `Atlantic`, `Interior`, `Gulf`. |
| 13 | `Product ID` | String | `string` | No | 15 | `CHO-MIL-31000` | Product stock keeping unit (SKU) identifier. |
| 14 | `Product Name` | String | `string` | No | 15 | `Wonka Bar - Milk Chocolate` | Product description; maps deterministically to 1 of 5 production factories. |
| 15 | `Sales` | Float | `float64` | No | 814 | `6.50` | Total order-line revenue in USD. Total raw sales: $141,783.63. |
| 16 | `Units` | Integer | `int64` | No | 14 | `2` | Quantity shipped (range: 1 to 14 units; mean: 3.8 units). Total raw units: 38,654. |
| 17 | `Gross Profit` | Float | `float64` | No | 722 | `4.22` | Gross margin in USD (`Sales - Cost`). Total raw gross profit: $93,442.80. |
| 18 | `Cost` | Float | `float64` | No | 725 | `2.28` | Product manufacturing COGS (Cost of Goods Sold); does **not** include freight transportation expense. |

---

## 3. Derived Layer: `data/derived/`

The Derived Layer represents de-duplicated, geocoded, and reconciled operational data produced by `scripts/build_data.py`.

### 3.1 `clean_orders.parquet` (9,881 records, 29 columns)
Contains the de-duplicated clean order lines, with 313 exact duplicate rows removed. Reconciled against financial targets (Clean Units: 37,667, Clean Sales: $138,284.12, Clean Profit: $91,076.41).

| Column Name | Data Type | Nullable | Description & Layer Provenance |
|---|---|:---:|---|
| `Row ID` | `int64` | No | Clean row index (1 to 9,881). |
| `Order ID` | `object` / `string` | No | Order identifier (surrogate token `ORD-xxxxxxxxxx` in cloud builds). |
| `Order Date` | `string` | No | Order placement date (`dd-mm-yyyy`). |
| `Ship Date` | `string` | No | Source recorded ship date (`dd-mm-yyyy`). |
| `Ship Mode` | `string` | No | Carrier service tier (`Same Day`, `First Class`, `Second Class`, `Standard Class`). |
| `Customer ID` | `object` / `string` | No | Customer identifier (surrogate token `CUST-xxxxxxxx` in cloud builds). |
| `Country/Region` | `object` | No | Destination country (`United States` or `Canada`). |
| `State/Province` | `object` | No | Destination US state or Canadian province name. |
| `Division` | `string` | No | Product division (`Chocolate`, `Other`, `Sugar`). |
| `Region` | `string` | No | Commercial sales region (`Pacific`, `Atlantic`, `Interior`, `Gulf`). |
| `Product ID` | `string` | No | Product SKU code. |
| `Product Name` | `string` | No | Normalized product name (typographical defect corrected). |
| `Sales` | `float64` | No | Transaction revenue in USD. |
| `Units` | `int64` | No | Quantity shipped. |
| `Gross Profit` | `float64` | No | Gross margin in USD (`Sales - Cost`). |
| `Cost` | `float64` | No | Manufacturing cost in USD. |
| `is_duplicate` | `bool` | No | Flag indicating row was evaluated for duplicates (`False` for retained rows). |
| `is_canadian` | `boolean` | No | Provenance flag: `True` if destination is in Canada (200 records). |
| `is_partial_postal` | `boolean` | No | Audit flag: `True` if original postal code was truncated (449 records). |
| `raw_interval_days` | `int64` | No | Raw unverified interval (`Ship Date - Order Date`, 904 to 1,642 days). |
| `lead_time_reconstructed_diagnostic` | `int64` | No | Hypothetical reconstructed interval (offset subtracted; diagnostic only). |
| `reconstruction_is_hypothesis` | `bool` | No | Constant `True` flagging diagnostic reconstruction as unverified (AD-01). |
| `Factory` | `object` | No | Production facility name mapped from Product Name (1 of 5 factories). |
| `factory_lat` | `float64` | No | Latitude of production factory facility. |
| `factory_lon` | `float64` | No | Longitude of production factory facility. |
| `dest_lat` | `float64` | No | Latitude of destination state/province population centroid. |
| `dest_lon` | `float64` | No | Longitude of destination state/province population centroid. |
| `distance_km` | `float64` | No | Great-Circle Haversine distance in kilometers between factory and destination centroid. |
| `route_key` | `object` | No | Canonical route identifier formatted as `Factory -> State/Province`. |
| `route_key_region` | `string` | No | Extended route identifier formatted as `Factory -> State/Province (Region)`. |

### 3.2 `route_aggregates.parquet` (196 routes, 11 columns)
Aggregates order volumes, financial totals, and Haversine distances for all 196 active shipping corridors.

| Column Name | Data Type | Description |
|---|---|---|
| `Factory` | `object` | Origin production facility name. |
| `State/Province` | `object` | Destination state or province. |
| `Country/Region` | `object` | Destination country (`United States` or `Canada`). |
| `Region` | `string` | Commercial sales territory. |
| `route_key` | `object` | Route corridor identifier (`Factory -> State/Province`). |
| `order_line_count` | `int64` | Total order lines traversing corridor. |
| `line_item_count` | `int64` | Total line items shipped across corridor. |
| `total_units` | `int64` | Total unit volume delivered. |
| `total_sales` | `float64` | Cumulative transaction revenue in USD. |
| `total_gross_profit` | `float64` | Cumulative gross margin in USD. |
| `distance_km` | `float64` | Great-Circle distance in kilometers. |

### 3.3 Supporting Derived Artifacts
- **`surrogate_key_mapping.csv` (8,549 rows):** Local mapping between `Original_Order_ID`, `Surrogate_Order_ID`, `Original_Customer_ID`, and `Surrogate_Customer_ID`. Excluded from public release.
- **`transformation_log.json`:** JSON document containing execution timestamps, SHA-256 source hash, duplicate audit findings, financial reconciliation numbers, and order grain statistics.

---

## 4. Synthetic Simulation Layer: `data/synthetic/`

The Synthetic Layer provides calibrated, plausible lead-time models across three distinct scenarios.

### 4.1 Parquet Schemas (`baseline.parquet`, `distance_sensitive.parquet`, `stress_test.parquet`)
Each file contains 9,881 records across 36 columns. All columns from `clean_orders.parquet` are inherited, augmented by the following simulation attributes:

| Column Name | Data Type | Nullable | Description & Formulation |
|---|---|:---:|---|
| `lead_time_days` | `float64` | No | Calibrated order-to-ship transit time in days for the given scenario. |
| `scenario_name` | `object` | No | Scenario identifier: `baseline`, `distance_sensitive`, or `stress_test`. |
| `is_synthetic` | `bool` | No | Invariant compliance flag: constant `True` indicating simulated data (AD-02). |
| `Order_Date_Original` | `string` | No | Preserved original order date (`dd-mm-yyyy`). |
| `Ship_Date_Original` | `string` | No | Preserved raw unverified ship date (`dd-mm-yyyy`). |
| `Ship_Date_Synthetic` | `object` | No | Coherent synthetic dispatch date computed as `Order Date + lead_time_days`. |

### 4.2 `metadata.json`
Machine-readable audit manifest recording:
- `generated_at_utc`: Generation timestamp.
- `build_seed`: Default pseudorandom number generator seed (42).
- `scenarios`: List of generated scenarios `["baseline", "distance_sensitive", "stress_test"]`.
- `generator_settings`: Parameter configurations including distance coefficients, boundary clipping thresholds, and multi-seed arrays (`[42, 101, 202, 303, 404]`).
- `artifact_checksums`: SHA-256 hashes of all output Parquet tables.

---

## 5. Computed Analytics & Route Efficiency Metrics

Metrics computed dynamically during analytics runtime (`src/metrics.py` and `src/bottleneck_rules.py`):

| Metric / Attribute | Type | Formula / Logic | Description |
|---|---|---|---|
| `mode_adjusted_lead_time` | Float | $\Delta L_i = L_i - L_{\text{ref}, m}$ | Deviation of lead time from invariant empirical mode benchmark. |
| `speed_penalty` | Float | $100 \cdot \frac{\bar{L} - L_{\min}}{L_{\max} - L_{\min}}$ | Min-max scaled mean lead-time penalty (0 = fastest, 100 = slowest). |
| `variability_penalty` | Float | $100 \cdot \frac{\sigma - \sigma_{\min}}{\sigma_{\max} - \sigma_{\min}}$ | Min-max scaled lead-time variance penalty (0 = most consistent, 100 = most erratic). |
| `res_score` | Float | $100 - (0.70 \cdot P_{\text{speed}} + 0.30 \cdot P_{\text{var}})$ | Route Efficiency Score on 0–100 scale (100 = optimal efficiency). |
| `speed_only_score` | Float | $100 - P_{\text{speed}}$ | Baseline benchmark isolating speed without variability weighting ($w_s=1.0, w_v=0.0$). |
| `is_delayed` | Boolean | $\text{lead\_time\_days} > 5.0\text{ days}$ | Strict binary delay indicator based on strict inequality ($L_i > \theta$; boundary $5.0\text{d}$ is not delayed). |
| `is_bottleneck` | Boolean | $N \ge P_{75}(N) \land \text{DelayRate} \ge P_{75}(\text{DelayRate})$ | Route flagged in Critical Bottleneck quadrant ($N \ge 30$). |
| `is_watchlist` | Boolean | $N \ge P_{75}(N) \land \text{DelayRate} > \operatorname{Median}(\text{DelayRate}) \land \neg\text{is\_bottleneck}$ | High-volume corridor with elevated delay rate above median, requiring monitoring. |
