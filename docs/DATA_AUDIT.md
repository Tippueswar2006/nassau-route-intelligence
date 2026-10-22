# Nassau Candy Shipping Route Intelligence
## Read-Only Source Dataset Audit Report

| Audit Metadata | Details |
|---|---|
| **File Path** | `data/original/nassau_candy.csv` (also verified identical to `data/original/Nassau Candy Distributor - Copy.csv`) |
| **Audit Date** | October 2026 |
| **File SHA-256 Hash** | `6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f` |
| **Integrity Status** | Strictly Read-Only; source file preserved verbatim with zero modifications |
| **Audit Scope** | Schema profiling, duplicate analysis, date anomaly diagnostics, raw lead-time distributions, geography, factory mapping, row grain verification, and architectural recommendations |
| **Reference Authority** | Nassau Route Intelligence PRD v1.3 (Final) |

---

## 1. Executive Summary

A comprehensive, non-destructive, read-only audit of `data/original/nassau_candy.csv` was conducted. The dataset contains **10,194 records across 18 columns** with zero missing values in any column.

### Primary Audit Findings:
1. **Pervasive Date Anomaly:** Every single record possesses an unverified raw lead time (`Ship Date − Order Date`) spanning **904 to 1,642 days** (mean: 1,320.84 days; median: 1,274 days). There are **zero records under 30 days** and zero negative intervals.
2. **Deterministic Offset by Order-ID Year:** The minimum lead-time floor is strictly coupled to the year encoded inside the `Order ID` (e.g., `US-2021-...` has floor 904d; `US-2022-...` has floor 1,269d; `US-2023-...` has floor 1,269d; `US-2024-...` has floor 1,634d). While subtracting these group floors produces plausible intervals of 0–11 days separating cleanly by ship mode, **this reconstruction remains an unconfirmed hypothesis** and must not be presented as factual historical performance.
3. **Exact Duplicates:** There are **313 redundant duplicate records** across 307 content groups (620 rows involved) with identical values in all columns except `Row ID`, accounting for $3,499.51 in sales (2.5% of total) and 987 units. De-duplicating leaves **9,881 unique rows**.
4. **Order Grain Hierarchy:** The dataset represents **order lines** (8,549 distinct `Order ID`s), not whole customer shipments. An `Order ID` embeds a single customer and product code, thus mapping to exactly one factory. However, real customer shipments (`Customer ID` + `Order Date` + `Ship Mode`) frequently consolidate multiple lines, with **33.6% (1,702 shipments) spanning two or more distinct factories**.
5. **Postal Code Truncation:** 449 US postal codes were truncated to 4 digits due to dropped leading zeros. 200 records belong to Canada and have postal codes cut to 3 characters.
6. **100% Factory Mapping Coverage:** All 15 distinct product names map perfectly to the 5 designated production factories with zero unmapped lines. One product name contains a minor typographical spacing defect (`Wonka Bar -Scrumdiddlyumptious` lacking a space after the hyphen).
7. **Financial Consistency:** `Gross Profit = Sales − Cost` holds with zero mathematical discrepancy across all 10,194 rows. The `Cost` field represents manufacturing COGS, not freight transportation expenses.

---

## 2. Schema and Column Profiling

The table below details the 18 columns, inferred data types, non-null counts, and descriptive role in the analytical architecture:

| # | Column Name | Inferred Type | Null Count | Distinct Values | Sample Value | Analytical Role |
|---|---|---|---|---|---|---|
| 1 | `Row ID` | Integer | 0 | 10,194 | `1` | Arbitrary row index; excluded during de-duplication |
| 2 | `Order ID` | String | 0 | 8,549 | `US-2021-103800-CHO-MIL-31000` | Order-line identifier; embeds year, customer, and product code |
| 3 | `Order Date` | Date (`dd-mm-yyyy`) | 0 | 664 | `03-01-2024` | Order placement date (all fall in 2024–2025) |
| 4 | `Ship Date` | Date (`dd-mm-yyyy`) | 0 | 1,327 | `30-06-2026` | Shipping dispatch date (all fall in 2026–2030) |
| 5 | `Ship Mode` | Categorical (4) | 0 | 4 | `Standard Class` | Delivery service tier (Standard, First, Second, Same Day) |
| 6 | `Customer ID` | String / Integer | 0 | 793 | `103800` | Customer account identifier (must be hashed for public deployment) |
| 7 | `Country/Region` | Categorical (2) | 0 | 2 | `United States` | Country: 9,994 United States, 200 Canada |
| 8 | `City` | String | 0 | 531 | `Houston` | Destination city |
| 9 | `State/Province` | Categorical (59) | 0 | 59 | `Texas` | Customer state (49 US states + DC, 10 Canadian provinces) |
| 10 | `Postal Code` | String / Integer | 0 | 632 | `77095` | Destination postal code; requires text formatting and padding |
| 11 | `Division` | Categorical (3) | 0 | 3 | `Chocolate` | Product category: Chocolate (9,844), Other (310), Sugar (40) |
| 12 | `Region` | Categorical (4) | 0 | 4 | `Interior` | Geographic sales territory: Pacific, Atlantic, Interior, Gulf |
| 13 | `Product ID` | String | 0 | 15 | `CHO-MIL-31000` | Stock keeping unit (SKU) code |
| 14 | `Product Name` | String | 0 | 15 | `Wonka Bar - Milk Chocolate` | Product description; joins to production factory |
| 15 | `Sales` | Float | 0 | 814 | `6.5` | Transaction revenue (USD) |
| 16 | `Units` | Integer | 0 | 14 | `2` | Quantity shipped (range: 1 to 14; mean: 3.8) |
| 17 | `Gross Profit` | Float | 0 | 722 | `4.22` | Gross margin in USD (`Sales − Cost`) |
| 18 | `Cost` | Float | 0 | 725 | `2.28` | Product manufacturing COGS (NOT freight/shipping cost) |

---

## 3. Duplicate Records Investigation

The audit compared exact row copies across all attributes excluding the arbitrary surrogate `Row ID`:

```text
Total Rows Supplied:                          10,194
Unique Content Tuples:                         9,881
Exact Redundant Duplicate Copies:                313
Content Groups with Duplicates:                  307 (301 pairs, 6 triples)
Total Rows Involved in Duplication:              620
Sales Attributable to Extra Duplicate Copies:    $3,499.51 (2.47% of total sales)
Units Attributable to Extra Duplicate Copies:    987 units (118 in 2024, 195 in 2025)
```

### Multi-Line Orders vs. Exact Duplicates
* **Repeated Order IDs:** 1,373 distinct `Order ID`s appear more than once in the dataset, accounting for 3,018 rows.
* **Semantic Difference:** Rows that share an `Order ID` but contain distinct quantities, dates, or items are legitimate split line items. In contrast, the 313 extra copies match their counterparts across every single column (Order ID, dates, customer, geography, product, units, sales, profit, cost).
* **Positional Check:** Only ~35% of duplicate rows are adjacent in the CSV. Because they could represent repeated order submissions or data collection duplicates, the system must not silently drop them.

---

## 4. Date Anomaly and Reconstruction Diagnostics

### Date Boundaries (Source Format: `dd-mm-yyyy`)
* **Order Date Range:** 2024-01-02 to 2025-12-31 (exactly two complete calendar years).
* **Ship Date Range:** 2026-06-30 to 2030-06-28 (future dates relative to order placement).
* **Date Parsing Failures:** 0 rows.
* **Negative Intervals (`Ship Date < Order Date`):** 0 rows.
* **Rows with Lead Time $< 30$ Days:** 0 rows (100% of rows fail reasonable logistics plausibility).

### Interval Floor Grouping by Order-ID Year
An inspection of the Order ID syntax (`US-YYYY-XXXXXX-...`) reveals an empirical shift pattern:

| Year in Order ID | Record Count | Min Raw Interval | Max Raw Interval | Mean Raw Interval | Hypothesized Offset Floor |
|---|---|---|---|---|---|
| **2021** | 2,051 | 904 days | 915 days | 908.07 days | **904 days** |
| **2022** | 2,130 | 1,269 days | 1,277 days | 1,273.07 days | **1,269 days** |
| **2023** | 2,634 | 1,269 days | 1,276 days | 1,272.95 days | **1,269 days** |
| **2024** | 3,379 | 1,634 days | 1,642 days | 1,638.83 days | **1,634 days** |

### Hypothesis Test (Floor Subtraction Diagnostic)
Subtracting each group's base floor yields an adjusted interval range between **0 and 11 calendar days**:

| Ship Mode | Rows | Mean (Days) | Min | Max | Standard Deviation |
|---|---|---|---|---|---|
| **Same Day** | 547 | 0.384 | 0 | 2 | 0.53 |
| **First Class** | 1,548 | 2.548 | 1 | 5 | 0.89 |
| **Second Class** | 1,979 | 3.572 | 1 | 6 | 1.28 |
| **Standard Class** | 6,120 | 5.316 | 3 | 11 | 1.13 |

> **Audit Caution:** This floor subtraction cleanly separates shipping modes and explains 62.3% of the variance. However, it is an **unverified diagnostic hypothesis**. The original raw dates must remain unchanged in the `ORIGINAL` layer.

---

## 5. Raw Lead-Time Statistical Distribution

Calculated strictly as `Ship Date − Order Date` without altering dates:

| Statistic | Raw Interval (Calendar Days) |
|---|---|
| **Minimum** | 904.0 days |
| **25th Percentile ($P_{25}$)** | 1,271.0 days |
| **Median ($P_{50}$)** | 1,274.0 days |
| **Mean** | 1,320.84 days |
| **75th Percentile ($P_{75}$)** | 1,638.0 days |
| **90th Percentile ($P_{90}$)** | 1,640.0 days |
| **95th Percentile ($P_{95}$)** | 1,641.0 days |
| **99th Percentile ($P_{99}$)** | 1,642.0 days |
| **Maximum** | 1,642.0 days |
| **Standard Deviation** | 268.45 days |

---

## 6. Categorical, Product, and Geographic Profiles

### Shipping Mode Distribution
* **Standard Class:** 6,120 rows (60.03%)
* **Second Class:** 1,979 rows (19.41%)
* **First Class:** 1,548 rows (15.19%)
* **Same Day:** 547 rows (5.37%)

### Product-to-Factory Mapping (100% Coverage)
All 15 products join directly to their production factories as specified in PRD Appendix A:

| Product Name in CSV | Product ID | Factory Name | Rows | Sales (USD) |
|---|---|---|---|---|
| `Wonka Bar - Milk Chocolate` | `CHO-MIL-31000` | Wicked Choccy's | 2,137 | $29,662.75 |
| `Wonka Bar - Triple Dazzle Caramel` | `CHO-TRI-54000` | Wicked Choccy's | 2,015 | $27,882.25 |
| `Wonka Bar - Nutty Crunch Surprise` | `CHO-NUT-13000` | Lot's O' Nuts | 1,810 | $26,380.50 |
| `Wonka Bar -Scrumdiddlyumptious` *(typo)* | `CHO-SCR-58000` | Lot's O' Nuts | 2,064 | $28,944.40 |
| `Wonka Bar - Fudge Mallows` | `CHO-FUD-51000` | Lot's O' Nuts | 1,818 | $25,123.00 |
| `Wonka Gum` | `OTH-GUM-88000` | Secret Factory | 120 | $1,280.00 |
| `Kazookles` | `OTH-KAZ-22000` | The Other Factory | 96 | $950.40 |
| `Lickable Wallpaper` | `OTH-LIC-99000` | Secret Factory | 94 | $985.00 |
| `Fizzy Lifting Drinks` | `SUG-FIZ-11000` | Sugar Shack | 6 | $94.50 |
| `Laffy Taffy` | `SUG-LAF-44000` | Sugar Shack | 10 | $145.00 |
| `SweeTARTS` | `SUG-SWE-77000` | Sugar Shack | 10 | $152.00 |
| `Nerds` | `SUG-NER-33000` | Sugar Shack | 4 | $58.00 |
| `Hair Toffee` | `OTH-HAI-66000` | The Other Factory | 4 | $42.00 |
| `Everlasting Gobstopper` | `OTH-GOB-77000` | Secret Factory | 3 | $32.50 |
| `Fun Dip` | `SUG-FUN-55000` | Sugar Shack | 3 | $49.33 |
| **Total** | | **5 Factories** | **10,194** | **$141,783.63** |

### Geographic and Postal Code Breakdown
* **Countries:** United States (9,994 rows), Canada (200 rows across 10 provinces).
* **Postal Code Cleaning Needs:**
  * **US 4-Digit Codes:** 449 rows (e.g., `1001` instead of `01001` in Massachusetts/New England).
  * **Canadian 3-Character Codes:** 200 rows (e.g., `M5V` instead of full 6-character Canadian FSA/LDU code).
* **Factory $\rightarrow$ State Route Sparsity:**
  * Total state-level routes: **196**
  * Routes with $N \ge 30$ order lines: **54** (Wicked Choccy's: 25, Lot's O' Nuts: 28, Secret Factory: 1)
  * Routes with $N \ge 20$: **69**
  * Routes with $N \ge 10$: **95**
  * Routes with $N < 10$: **101** (51.5% of all routes have severe sample sparsity)

---

## 7. Row Grain and Structural Consistency

The audit validated the internal consistency of order attributes within each `Order ID`:
* `Ship Date`, `Ship Mode`, `Order Date`, `Customer ID`, `State/Province`, and `Country/Region` **never vary within any Order ID** (0 violations across 8,549 distinct Order IDs).
* **Real Customer Shipments:**
  * Defined as: `Customer ID + Order Date + Ship Mode`.
  * Total customer shipments: **5,067**.
  * Multi-factory shipments: **1,702 (33.6%)** contain order lines fulfilled from two or more distinct factories.
  * Multi-Order-ID shipments: **2,240 (44.2%)** group multiple order lines.

---

## 8. Financial Profile and Integrity

```text
Total Revenue (Sales):                  $141,783.63
Total Manufacturing Cost:                $48,340.83
Total Gross Profit:                      $93,442.80
Average Gross Margin:                         65.91%
Equation Check (Sales - Cost == Profit): 10,194 / 10,194 valid (100.0%)
```

* **De-duplicated Financials (9,881 unique rows):** Sales = $138,284.12; Gross Profit = $91,076.41.
* **Cost Semantics:** Unit price and unit cost are fixed per product. The `Cost` field is exclusively manufacturing cost (COGS) and contains zero freight or carriage components.

---

## 9. Data-Quality Risks and Unresolved Assumptions

| # | Data-Quality Risk | Impact / Severity | Current Evidence & Context | Unresolved Assumption |
|---|---|---|---|---|
| **R-1** | Source dates shifted by export script | **Critical** | Raw intervals are 904–1,642 days. Floor offset matches Order-ID year. | Whether order dates were shifted as well as ship dates, or whether this was a synthetic test export. |
| **R-2** | Conflating order lines with shipments | **High** | 33.6% of customer shipments span multiple factories; each Order ID covers one factory. | Treating `Order ID` as an entire customer shipment would hide multi-factory logistics splits. |
| **R-3** | Duplicate rows inflating financial/volume metrics | **Medium** | 313 duplicate copies contribute $3,499.51 (2.5%) in revenue. | Whether duplicates represent legitimate repeat ordering or database extraction re-runs. |
| **R-4** | Small-sample route volatility | **High** | 101 of 196 routes have $< 10$ orders. Sugar Shack has only 33 total order lines. | Calculating route lead times without a minimum sample guardrail produces noisy rankings. |
| **R-5** | Ship-mode confounding in route benchmarking | **High** | Ship mode accounts for 62.3% of lead-time variance; geography adds $< 0.1\%$. | Ranking routes on unadjusted lead times unfairly penalizes routes with high Standard Class usage. |
| **R-6** | Mislabeling COGS as shipping freight cost | **Medium** | `Cost` is fixed per product SKU. | Calculating freight margin or transportation cost from `Cost` is invalid. |
| **R-7** | Postal code formatting breakage | **Low** | 449 US zip codes lost leading zeros; Canadian codes truncated. | Geocoders or mapping libraries failing on 4-digit integers or 3-char strings. |

---

## 10. Architectural Recommendations

Based on these audit findings, the system architecture must implement the following safeguards:

### A. Ingestion and Provenance Architecture (`src/load_data.py`)
1. **Hash Verification:** Compute and store the SHA-256 hash (`6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f`) upon every file read. Throw an exception if the file hash changes.
2. **Read-Only Ingestion:** Ingest `data/original/nassau_candy.csv` strictly as read-only. Store all downstream transformations exclusively in `data/derived/` or `data/synthetic/`.
3. **Data Layer Banners:** Pass an explicit `data_layer` enumeration (`ORIGINAL`, `DERIVED`, `SYNTHETIC`) through all pipeline stages and require every visual component to render a visible layer tag.

### B. Cleaning and Transformation Pipeline (`src/validate_data.py`)
1. **Duplicate Handling:** Flag the 313 duplicate copies with `is_duplicate = True`. Provide an active configuration toggle to exclude duplicates by default while allowing analysts to inspect them.
2. **Text & Postal Formatting:**
   * Pad 4-digit US postal codes to 5-character strings with leading zeros (e.g., `01001`).
   * Flag Canadian postal codes as partial (`is_partial_postal = True`) and exclude from US choropleth mapping.
   * Standardize `Wonka Bar -Scrumdiddlyumptious` to include proper whitespace.
3. **Factory Mapping Attachment:** Join the 15 products with the 5 factories (`Lot's O' Nuts`, `Wicked Choccy's`, `Sugar Shack`, `Secret Factory`, `The Other Factory`) and attach factory latitude/longitude coordinates from `config/factories.csv`.
4. **Order-to-Ship Terminology:** Strictly enforce the label `order-to-ship lead time`; never label this as carrier transit time or delivery time.

### C. Synthetic Generation Engine (`src/generate_synthetic.py`)
1. **Shipment-Grain Generation:** Generate synthetic timing at the `(Customer ID, Order Date, Ship Mode)` grouping level so bundled order lines share uniform dispatch timing.
2. **Neutral Baseline:** Sample directly from the verified empirical per-mode distributions (Appendix D: Same Day 0.38d, First Class 2.55d, Second Class 3.57d, Standard 5.32d).
3. **Injected Scenarios:** Maintain separate, reproducible configurations for *Distance-Sensitive* and *Stress Test* scenarios with fixed seed (42).

### D. Metrics and Ranking Architecture (`src/metrics.py`, `src/route_analysis.py`)
1. **Mode-Adjusted RES (Default):** Center route lead times around their ship-mode means before normalising penalties, ensuring leaderboards reflect route consistency rather than shipping mode mix.
2. **Sample Size Guardrails:** Enforce a default minimum threshold of $N \ge 30$ order lines for Top 10 / Bottom 10 leaderboards. Exclude low-sample routes and display them in a dedicated inspection table. Small factories must be rolled up to regional level (`Factory → Region`).
3. **Dual Financial Reporting:** Report sales and gross margin strictly under the banner of product performance, with prominent disclaimers stating that freight cost is unavailable.
