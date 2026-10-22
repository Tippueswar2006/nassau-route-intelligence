# Nassau Candy Shipping Route Intelligence

## Product Requirements Document (PRD), Version 1.3 (Final)

| | |
|---|---|
| **Status** | Final, for mentor sign-off |
| **Version** | 1.3 (consolidates v0.2, v1.0, v1.1, v1.2 and a final audit against the brief, the data and the tech stack) |
| **Date** | October 2026 |
| **Project type** | Data analytics, reproducible research, interactive dashboard |
| **Deliverables** | Streamlit dashboard, validated analysis outputs, research paper, executive summary |
| **Stack** | Python, Pandas, NumPy, openpyxl, Plotly, Streamlit, pytest; Matplotlib / Seaborn for paper figures; Git and GitHub; Streamlit Community Cloud |

> **Critical limitation:** This is a decision-support and investigation tool, not a Transportation Management System (TMS), a live-tracking product, or a production route optimizer. Timing results come from a labelled synthetic layer and are not evidence of actual Nassau Candy performance.

### What changed in the final version

| # | Change | Reason |
|---|---|---|
| 1 | **Row grain corrected.** The Order ID contains customer and product codes, so it is an *order line*, not a whole order or shipment | Earlier drafts implied one Order ID was one real shipment. 34% of real customer shipments span two or more factories |
| 2 | **Date anomaly explained.** The raw interval floor depends on the year inside the Order ID (904, 1,269, 1,269 and 1,634 days) | Stronger evidence than a guessed offset. The reconstruction stays a diagnostic and calibration aid, never a fact |
| 3 | **Lead time depends almost only on ship mode** (62% of variance; region adds 0.1%, month 0.3%) | Raw route rankings would mostly reflect ship-mode mix. Added a **mode-adjusted RES** |
| 4 | **Baseline generator recalibrated** to the empirical per-mode distributions; the distance effect and the Nov to Dec peak moved out of the Baseline into named scenarios | The data does not show those effects, so the Baseline must not assume them |
| 5 | **Cleaning list completed:** postal codes, Canadian partial codes, spelling counts, duplicate detail | Verified against the file |
| 6 | **Business insights added** to the Overview (growth, margin, concentration) | They come from valid Original fields |
| 7 | **Audit added** (Appendix E): brief, problem statement, solution, tech stack and v1.1 | Confirms nothing in the brief is missing |

Earlier changes from v1.1 remain: verified data facts, a buildable generator, brief traceability, a descriptive cost-time option, defaults, deployment and appendices.
---

## 1. Executive summary

Nassau Candy Shipping Route Intelligence makes order and shipping records easier to inspect across factories, customer states and regions, and shipping modes. It profiles the source data, documents its quality issues, compares route-level metrics only where timing is valid, and flags routes or locations that may warrant investigation.

The source file has a serious date problem: `Ship Date − Order Date` is 904 to 1,642 days on every row, and no row is under 30 days. This is treated as an unverified anomaly, not as shipping performance. The interval floor depends on the year inside the Order ID, which suggests the dates were shifted during export. Original dates stay unchanged. The mentor has directed that a separate, reproducible synthetic timing dataset be used to demonstrate the timing analytics. Synthetic results are labelled throughout the app, exports and paper.

The data also shows that, even in the reconstructed intervals, lead time is driven almost entirely by ship mode and not by region, factory or month. The product therefore ranks routes on a **mode-adjusted** score by default, and says plainly when differences between routes are small.

The product includes data-quality reporting, route analysis, a transparent Route Efficiency Score (RES), Top 10 and Bottom 10 rankings, a configurable delay threshold, a US state heatmap, ship-mode comparisons, potential-bottleneck flags, drill-down tables with order timelines, business-insight summaries from valid fields, and CSV exports. Correctness and traceability take priority over complex optimisation.
---

## 2. Problem statement

Individual records are difficult to compare across factories, routes, states, regions and shipping modes. Analysis is also at risk from suspicious source dates, ambiguous row grain, thin route samples, and scores that hide their assumptions. The organization cannot tell which routes are consistently efficient, which are often delayed, how performance varies by region, state and mode, or where geographic bottlenecks sit.

The product must make useful patterns discoverable without overstating what the available data proves.

---

## 3. Verified data profile

Computed from the supplied file for this PRD. Recompute whenever the source changes; the app must reproduce every figure on the Data Quality page.

| Fact | Value |
|---|---|
| Rows / distinct Order IDs | 10,194 / 8,549 |
| Exact duplicate rows (all fields except Row ID) | 313 extra copies; 9,881 rows remain after removal |
| Order Date range | 2 Jan 2024 to 31 Dec 2025 (all parse as `dd-mm-yyyy`) |
| Ship Date range (as supplied) | 30 Jun 2026 to 28 Jun 2030 |
| `Ship Date − Order Date` | 904 to 1,642 days; zero rows under 30 days; zero negative |
| Missing values | None in the supplied columns |
| Country | 9,994 United States rows; 200 Canada rows |
| States / provinces | 59 distinct values |
| Product-to-factory mapping | 15 of 15 products matched; 0 unmatched rows |
| Orders (Order IDs) by factory, de-duplicated | Lot's O' Nuts 4,760; Wicked Choccy's 3,445; Secret Factory 213; The Other Factory 98; Sugar Shack 33 |
| Ship mode mix (Order IDs) | Standard 5,142; Second Class 1,653; First Class 1,312; Same Day 442 |
| Sales / gross profit (as supplied) | $141,784 / $93,443 (about 66% margin) |

### 3.1 The date anomaly and what explains it

The Order ID has the form `US-2021-<customer>-<product code>`. Its year runs 2021 to 2024, but every Order Date is in 2024 or 2025, so the order dates were also shifted. The raw interval floor depends on the Order-ID year:

| Year in Order ID | Smallest raw interval | Rows |
|---|---|---|
| 2021 | 904 days | 2,051 |
| 2022 | 1,269 days | 2,130 |
| 2023 | 1,269 days | 2,634 |
| 2024 | 1,634 days | 3,379 |

Subtracting each group's floor puts every row between 0 and 11 days, and the ship modes then separate cleanly:

| Ship mode | Mean (days) | Range |
|---|---|---|
| Same Day | 0.38 | 0 to 2 |
| First Class | 2.55 | 1 to 5 |
| Second Class | 3.57 | 1 to 6 |
| Standard Class | 5.32 | 3 to 11 |

This **reconstruction is a hypothesis**. It is shown on the Data Quality page, sent to the mentor as evidence, and used only to calibrate the synthetic Baseline. It is never used in leaderboards or described as true shipping performance unless the data owner confirms it.

### 3.2 Row grain (corrected)

The Order ID embeds the customer and product codes. So each Order ID holds one product and therefore one factory **by construction**. This does not mean one Order ID is one real shipment.

| Check | Result |
|---|---|
| Ship Date, Ship Mode, order date, customer vary within one Order ID | Never |
| Real customer shipments (customer + order date + ship mode) | 5,067 |
| Customer shipments that contain products from two or more factories | 1,702 (33.6%) |
| Customer shipments that contain more than one Order ID | 2,240 |

**Units of analysis:**
- **Order line** (one Order ID): the unit for lead time, route volume and delay rate. It is one factory-to-customer leg, which is what a route is.
- **Line item** (one row): used for units, sales and profit.
- **Customer shipment** (customer + order date + ship mode): used to show that one customer's order can be split across factories.
- Reports must say "order lines", never "orders", for the 8,549 count, and the glossary must explain why.

### 3.3 Duplicates

- 313 extra copies, in 307 groups (301 pairs and 6 triples); 620 rows are involved.
- They carry $3,499.51 in sales (2.5% of the total) and 987 units: 118 in 2024 and 195 in 2025.
- Only about a third sit next to their twin in the file, so they could be real repeated lines. **Flag them, exclude by default, keep a toggle, and confirm with the mentor.**
- Rows that share an Order ID but are not exact copies (2,398 rows) are split line items, not errors.

### 3.4 Other cleaning issues

| Issue | Rows | Treatment |
|---|---|---|
| US postal codes lost a leading zero (4 digits) | 449 | Pad to 5 digits, stored as text |
| Canadian postal codes cut to 3 characters | 200 | Keep, mark as partial, exclude from the US map |
| Product name `Wonka Bar -Scrumdiddlyumptious` (missing space) | 2,064 | Standardise the name in the Derived layer; Product ID is already consistent |
| No Factory column | All | Add from the supplied mapping |

### 3.5 What passed

Gross Profit equals Sales minus Cost on every row; no zero or negative sales or units; each product has a single fixed unit price and unit cost (so `Cost` is manufacturing cost, not freight); each product has one Product ID and one Division; each state belongs to one region.

### 3.6 What drives lead time (reconstructed intervals)

| Explanatory factor | Variance explained |
|---|---|
| Ship mode alone | 62.3% |
| Ship mode + region | 62.4% (adds 0.1 point) |
| Ship mode + month | 62.6% (adds 0.3 points) |
| Ship mode + state | 64.6% (adds 2.3 points across 59 states, mostly noise) |

Mean reconstructed lead time barely moves by factory (Lot's O' Nuts and Wicked Choccy's differ by about 0.02 day within a mode) or by month (4.0 to 4.5 days). **Consequence:** differences between routes are small and mostly reflect ship-mode mix. The product must say so, and must offer mode-adjusted comparisons.

### 3.7 Route sample reality

There are 196 Factory → State routes. 54 have at least 30 order lines, 69 at least 20, and 95 at least 10. The 54 eligible routes are Lot's O' Nuts (28), Wicked Choccy's (25) and Secret Factory (1). Top 10 and Bottom 10 are feasible but come almost entirely from the two large factories. Sugar Shack, Secret Factory and The Other Factory are handled through Factory → Region rollups with low-sample warnings.

### 3.8 Observed business patterns (Original layer, valid fields)

- Sales grew about 44.6% from 2024 ($57,956) to 2025 ($83,827); Q4 is the strongest quarter each year.
- Order volumes peak in September (1,177), November (1,237) and December (1,227), about double the roughly 600 baseline in other months, consistent with industry reports that around 62 to 64% of US candy sales fall in four holiday seasons.
- The five Wonka bars are about 93% of sales; the two large factories are about 93%; California alone is about 20%.
- Kazookles has a margin of about 7.7%; the Wonka bars sit at 65 to 71%.
- Ship mode mix is about 60% Standard in every region, and average order value is similar across modes.
---

## 4. Objectives and success criteria

### Objectives

- Profile the original dataset without overwriting or silently correcting it.
- Document missing values, duplicates, date anomalies and mapping gaps.
- Map products to factories only through the supplied mapping table.
- Define routes as **Factory → Customer State** and **Factory → Customer Region**.
- Summarise volume and valid timing by route, geography, factory and ship mode.
- Calculate a transparent RES and provide ranked route tables.
- Make the delay threshold adjustable and visible.
- Compare Standard and Expedited shipping descriptively, not causally.
- Flag potential bottlenecks using disclosed rules, at state and route level.
- Produce reproducible outputs for the research paper and executive summary.

### Measurable success criteria

| ID | Criterion | Target | Check |
|---|---|---|---|
| SC-1 | Source integrity | Source file hash identical before and after any run | Automated test |
| SC-2 | Provenance coverage | 100% of pages, charts, tables and exports show the data layer | Checklist plus export test |
| SC-3 | Date anomaly handling | 100% of rows with interval over 30 days flagged; none silently changed | Automated test |
| SC-4 | Row reconciliation | 10,194 = 9,881 + 313 | Automated test |
| SC-5 | Leaderboard integrity | No route below the minimum sample in Top 10 or Bottom 10 | Automated test |
| SC-6 | Reproducibility | Same seed and settings give an identical synthetic file | Hash test |
| SC-7 | Responsiveness | Initial load and slider updates measured on a student laptop; target under 5 seconds and under 1 second | Recorded measurement |
| SC-8 | Auditability | A reviewer can recompute one route's RES by hand and match the app | Reviewer test |
| SC-9 | Brief coverage | Every brief item maps to a delivered feature (Section 6) | Traceability table |
| SC-10 | Traceability | Every research number links to code and data | Evidence log |
| SC-11 | Mix control | Leaderboards offer a mode-adjusted score beside the raw one, with rank changes shown | Automated test |

---

## 5. Users

| User | Need | Key pages |
|---|---|---|
| Data analyst / project team | Validate data, reproduce calculations, inspect route patterns | Data Quality, Route Efficiency |
| Logistics / operations reviewer | Identify routes or locations for further investigation | Overview, Map, Bottlenecks |
| Faculty / mentor / research evaluator | Understand evidence, assumptions, methodology, limitations | Data Quality and Method |
| Business stakeholder | Read clear summaries without inspecting raw rows | Overview, executive summary |

---

## 6. Scope, priorities and traceability to the brief

### In scope for v1

Dataset validation and data-quality report; Original, Derived and Synthetic layer separation; factory mapping coverage; route aggregation by Factory → State and Factory → Region; lead-time summaries for a selected valid layer; RES, Top 10 / Bottom 10 and configurable delay threshold; US heatmap, ship-mode comparison and bottleneck analysis; route/state drill-down with order timelines; filtered CSV exports; reproducible synthetic generation and validation; research methodology, limitations and reference audit.

### Out of scope

Live carrier / GPS tracking; real-time traffic or weather; confirmed root-cause analysis without operational data; automatic changes to real shipping assignments; vehicle-routing optimisation or ML delay prediction; any freight-cost figure derived from the `Cost` field; presenting synthetic results as actual company performance.

### Priority

- **P0, must ship:** source integrity and hash, layer labels, data-quality report, mapping report, overview, route summaries, RES, Top / Bottom 10, threshold slider, filters, exports, methodology page, core tests, deployment.
- **P1, should ship:** heatmap, ship-mode comparison (including Standard vs Expedited), bottleneck quadrant, drill-down with timeline, trends.
- **P2, stretch (start only after P0 passes):** what-if factory reallocation, alternative-score UI, extra uncertainty analysis, business-day lead times.

### Traceability: assignment brief to requirements

| Brief requirement | Covered by | Priority |
|---|---|---|
| Validate date formats; handle invalid lead times; handle missing records; standardize geography | FR-02, FR-03 | P0 |
| Shipping lead time; categorize routes by Factory → Region and Factory → State; group by ship mode | FR-05, FR-06 | P0 |
| Route aggregation: shipments, average lead time, variability | FR-06 | P0 |
| Rank fastest to slowest; Top 10 / Bottom 10; compare across ship modes | FR-07, FR-10 | P0 / P1 |
| Geographic bottlenecks: high lead time; high volume plus poor performance | FR-09, FR-11 | P1 |
| Ship mode analysis: Standard vs Expedited; descriptive cost-time tradeoff | FR-10 (Section 11) | P1 |
| KPIs: lead time, average lead time, route volume, delay frequency, efficiency score | Section 12 | P0 |
| Dashboard: route overview and leaderboard | FR-06, FR-07 | P0 |
| Dashboard: US heatmap and regional bottleneck view | FR-09, FR-11 | P1 |
| Dashboard: ship-mode comparison | FR-10 | P1 |
| Dashboard: state-level insights and order-level timelines | FR-12 | P1 |
| Filters: date range, region / state, ship mode, lead-time threshold slider | FR-08, FR-13 | P0 |
| Deliverables: research paper, dashboard, executive summary | Section 21 | P0 |

---

## 7. Data governance and provenance

Every chart, table, metric and download must identify its data layer.

| Layer | Definition | Permitted use | Required label |
|---|---|---|---|
| **Original** | Supplied source file, unchanged | Source profiling, safe counts and non-timing summaries, date-quality report, order-volume trends | `ORIGINAL — SOURCE DATA` |
| **Derived** | Calculated fields and mapping joins; original values retained | Route construction, mapping coverage, duplicate flags, raw date diagnostics, distance | `DERIVED — CALCULATED FROM SOURCE` |
| **Synthetic** | Separate demonstration data with generated timing and documented assumptions | Timing demos, delay threshold, RES, scenario tests | `SYNTHETIC — NOT ACTUAL PERFORMANCE` |

Requirements:

- Never overwrite the source file; keep generated outputs separate.
- Record source filename, row and column count, run timestamp and SHA-256 hash.
- Keep a data dictionary and a transformation log.
- Do not silently drop duplicates; flag them and document the analysis treatment (default: excluded, with a toggle).
- Every CSV export includes `data_layer` and, where relevant, `scenario_name`.
- **Publication rule:** the public deployed app uses only the Synthetic layer, with `Customer ID` removed or hashed. Original source data and customer identifiers are not published unless permission is confirmed.

### Date policy

Preserve source `Order Date` and `Ship Date` exactly as supplied. Calculate a diagnostic interval but mark it **unverified**. Do not subtract a guessed offset and call the result true. (The interval floor depends on the year inside the Order ID, which suggests the dates were shifted during export; see Section 3.1. This is a hypothesis to report to the mentor, not a rule to apply.) Use separate synthetic timing for the prototype and recalculate the diagnostic range whenever the source file changes.

---

## 8. Definitions

### Route and mapping

- State-level route: `Factory → Customer State`. Region-level route: `Factory → Customer Region`.
- Factory comes only from the supplied product-to-factory table. Unmatched products stay unmatched and are counted.
- Missing or invalid geography is labelled and excluded from geographic plotting. Canada rows (200) stay in tables but are excluded from the US map, with a visible note.

### Units of analysis

- **Order line:** one distinct Order ID (customer + product + year code). One factory per order line by construction. Counted as "order lines" in the app.
- **Line item:** one source row; used for units, sales and profit.
- **Customer shipment:** customer + order date + ship mode; shown only to explain that real orders can span factories.

### Timing terminology

- **Shipping lead time (order-to-ship):** `Ship Date − Order Date` in calendar days. This follows the brief's KPI definition. It is **not** carrier transit time or customer delivery time.
- **Transit time:** needs pickup and delivery timestamps; not available.
- **Delivery performance:** needs a delivery date plus a promised date; not supported by known fields.
- **Synthetic lead time:** generated interval used only to demonstrate the analysis.
- **Mode-adjusted lead time:** `lead_time_days − mean lead time of that ship mode` in the selected layer and scenario (fixed reference means, so values do not shift when filters change). It removes the effect of ship-mode mix when comparing routes.
- **Delay flag:** `lead_time_days > analysis_threshold_days` (strict). The threshold is a user-defined analysis setting, not a contractual SLA.
- **Delay rate (delay frequency):** delayed eligible order lines / eligible order lines × 100. Missing or invalid timing is excluded from the denominator and reported separately.
- **Reference service days (optional view):** assumed days per mode (Same Day 1, First Class 2, Second Class 3, Standard 5), clearly labelled as assumptions pending mentor confirmation. Off by default.

### Financial fields

`Cost` is treated as product manufacturing COGS unless the owner confirms otherwise. It is never called freight or shipping cost. `Sales`, `Cost` and `Gross Profit` are shown as supplied with caveats.

### Distance

Factory-to-state-centroid distance is **estimated geographic distance**, not road mileage. Any distance-to-time effect in synthetic data is a generator assumption.

---

## 9. Data quality requirements

The quality page must show:

- Row and column counts, and distinct Order IDs.
- Missing values by column.
- Exact duplicate rows and repeated order IDs, separately (repeated Order IDs are multi-line orders, not errors).
- Invalid or unparseable dates, `Ship Date < Order Date`, and suspiciously large intervals (histogram of the 904 to 1,642 range).
- Missing or unknown state and region values; non-US rows.
- Factory-mapping coverage and unmatched products.
- Invalid numeric types, unexpected negatives or impossible values where documented rules support the check.
- Counts before and after any analysis-only exclusion (10,194 → 9,881).
- Postal-code format: US codes shorter than 5 digits (449 rows) padded; non-US partial codes (200 rows) marked partial.
- Order ID anatomy: check that the customer segment matches `Customer ID` and the product segment matches `Product ID`; show how many real customer shipments span two or more factories.
- Order-ID year versus Order Date year mismatch, and the interval floor by Order-ID year (Section 3.1), labelled "reconstruction hypothesis".
- Text standardisation applied (for example, `"Wonka Bar -Scrumdiddlyumptious"` spacing), logged in the transformation log.

Classify findings as **observed issue**, **documented rule violation**, **review flag** or **resolved issue**. Mark an issue resolved only when a recorded, approved rule supports the change.

---

## 10. Synthetic data design and validation

### Purpose

Create a reproducible demonstration dataset because source dates are unverified. It must not be used to infer actual company performance.

### Generator rules

- Keep source product, geography, and financial fields. For cloud artifacts, replace BOTH Customer ID and Order ID with a randomized surrogate assignment reproducible for a given build seed (strictly avoiding sequential or predictable key schemes); drop `City` and `Postal Code`; keep the original-to-surrogate mapping strictly local-only and git-ignored.
- Generate timing separately; never replace source dates. Keep them as `Order_Date_Original` and `Ship_Date_Original`.
- **Generation unit: the customer shipment** (customer + order date + ship mode). All lines in it share one lead time, matching the source, where ship date never varies inside an Order ID.
- Bounded values; no negative lead times.
- Fixed default seed (42). Record seed, settings, generator version and software versions in the file metadata.
- Include `scenario_name` and `is_synthetic` fields.
- Never generate synthetic freight cost from source `Cost`.

### Scenarios

| Scenario | Model | Use |
|---|---|---|
| **Baseline** (default) | For each shipment, draw a lead time from the **empirical per-mode distribution** (Appendix D). No distance, region, month or route effects | Method behaviour on neutral data. Mirrors the unverified reconstruction, so route differences are expected to be small |
| **Distance-sensitive** | Baseline plus `0.5 × (Distance_km − mean distance) / 1000` days, rounded, bounded in [0, 2] for Same Day and [1, 14] for other modes | Tests whether the product detects a distance effect that the real data does not show. Centred so per-mode means are preserved |
| **Stress test** | Distance-sensitive foundation plus calibrated delay injections: `+1.0 day` for orders in November and December (peak season), `+1.0 day` in California and New York (high-volume destination states), and `+1.5 days` on two high-volume routes into Texas (*Lot's O' Nuts → Texas* and *Wicked Choccy's → Texas*). Route matching is configurable in `config/generator.yaml` and validated at build time | Proves the detection rules recover known injected patterns. Called "injected stress-test patterns", never discoveries |

### Calibration targets (Baseline)

| Check | Target |
|---|---|
| Mean lead time by mode | Same Day 0.38; First Class 2.55; Second Class 3.57; Standard 5.32, each within ±0.10 |
| Per-mode distribution | Each day-value within ±3 percentage points of Appendix D |
| Overall mean | 4.29 days within ±0.15 |
| Extra variance explained by region or month beyond ship mode | 1 percentage point or less |
| Same seed run twice | Identical file |

These are generator checks, not findings. The Baseline is "calibrated to an unverified reconstruction".

### Validation & Order of Operations

- **Order of Operations for Bounds:** Bounds $[0, 2]$ for Same Day and $[1, 14]$ for other modes are applied to the Distance-Sensitive foundation *before* delay injections are added. To prevent clipping injected delays (e.g., Same Day shipments receiving $+1.0$d or $+1.5$d), the Stress-Test scenario uses expanded bounds: $[0, 6]$ for Same Day and $[1, 20]$ for other modes.
- Mode ordering confirmed only because it is intentionally enforced.
- **Bottleneck Recovery Test Across 5 Seeds:** Tested across five deterministic seeds (`[42, 101, 202, 303, 404]`). Passes if the injected Texas route bottlenecks (enforcing minimum sample $N \ge 30$) are recovered in at least 4 of the 5 seeds ($\ge 4/5$, i.e. $\ge 80\%$) under the standard screening rule ($\text{Volume} \ge P_{75}$ and $\text{Delay Rate} \ge P_{75}$ at 5-day threshold, or watchlist with $\text{Delay Rate} > \text{Median}$) with a Stress-Test delay rate strictly greater than their Baseline delay rate.
- Distributions, route sample sizes and tiny groups checked.
- Publish generator assumptions with every result based on synthetic timing.
- Carrier transit guides are a plausibility reference only, because they measure pickup to delivery, not order to ship.
---

## 11. Descriptive cost-time view (brief requirement)

The brief asks for a descriptive cost-time tradeoff. `Cost` is COGS, so freight cost does not exist in the source. Options, in order of preference:

1. **Margin by mode (default, uses source fields only):** gross margin %, sales and units by ship mode, labelled "Product margin, not shipping cost", shown beside lead time by mode.
2. **Synthetic shipping cost (only if mentor approves, scenario `cost_demo`):** `Shipping_Cost = rate_per_km × Distance_km + mode_markup`, generated from distance and mode only, labelled Synthetic.

State on the page that no real freight cost data is available and that no causal claim is made.

---

## 12. Metric definitions

### Route summary

For each route report `n_order_lines`, `n_line_items`, mean and median lead time, standard deviation, interquartile range, 90th percentile, delay count and rate, invalid or missing timing count, data layer and scenario.

### Eligibility

Default **minimum sample is 30 order lines per route** (configurable, 10 to 100). This is a project guardrail, not a statistical law. Low-sample routes can be inspected and are labelled "low sample".

### Route Efficiency Score (RES)

RES is a **project-defined relative ranking index**, not an industry-standard metric. Calculate only for valid timing in one selected layer and scenario.

- `SpeedPenalty = min_max_normalize(route_mean_lead_time)`, using the selected **lead-time basis**: **mode-adjusted (default)** or raw
- `VariabilityPenalty = min_max_normalize(route_sd_lead_time)` on the same basis
- `RES = 100 × [1 − (0.70 × SpeedPenalty + 0.30 × VariabilityPenalty)]`

Rules:

- Normalise across eligible routes in the currently selected comparison population.
- Lower mean and lower variability give a higher score.
- The 70/30 weights are project assumptions. Show a **speed-only score** (weights 100/0) beside it, because the brief defines the score as normalized lead-time performance.
- Show comparison scope and active filters; scores change when the population changes.
- If a component's max equals its min, its penalty is 0 for every route, with a note.
- If only one eligible route exists, show "insufficient comparison set".
- Exclude invalid-timing and below-minimum routes from the ranked leaderboard.
- Never mix Original unverified timing and Synthetic timing in one leaderboard.

**Why mode-adjusted by default:** Section 3.6 shows lead time is driven by ship mode. A raw ranking would mostly reward routes that happen to use more Same Day and First Class orders. The raw score stays available beside it, and the app shows how many routes change rank between the two. This follows the brief's "normalized lead-time performance" while preventing a misleading leaderboard.

**Sensitivity:** compare 50/50, 70/30 and 90/10 weights and report ranking changes.

### Top 10 and Bottom 10

Rank eligible routes by RES, highest first. Show count, mean, median, variability, delay rate, layer and scenario beside each score. If fewer than 10 qualify, show those available and explain. Tie-break: RES, then order count, then route name.

### Potential bottlenecks (state and route level)

A flag is a screening signal, not proof of cause. Configurable default:

- **Flag:** volume at or above the 75th percentile **and** delay rate at or above the 75th percentile of the eligible comparison set.
- **Watch list:** volume at or above the 75th percentile and delay rate above the median.
- Show which rules were met, sample size, low-sample warnings, and the filters and population used.
- Apply at State level (all factories combined) and Factory → State route level.

### Ship-mode comparison

Report volume, mean and median lead time, variability and delay rate by individual mode and by group (**Expedited** = Same Day, First Class, Second Class; **Standard** = Standard Class). Add a distance-band view (0 to 500, 500 to 1,500, 1,500 to 3,000, 3,000+ km) that hides cells under 30 orders. Use descriptive wording ("associated with"), never "caused by".

---

## 13. Functional requirements

| ID | Requirement | Acceptance criteria | Priority |
|---|---|---|---|
| FR-01 | Safe data loading | Detects CSV or Excel; reports rows and columns; validates required columns; never overwrites source; records hash | P0 |
| FR-02 | Quality report | Missingness, duplicates, date issues, invalid values, geography and mapping issues; flagged rows exportable | P0 |
| FR-03 | Factory mapping | Uses supplied mapping only; coverage and unmatched shown; no invented factories; factory coordinates attached | P0 |
| FR-04 | Layer separation | Layer label on pages, charts, tables and exports; no silent blending | P0 |
| FR-05 | Overview | KPI definitions visible; order lines and line items separate; metrics respond to filters | P0 |
| FR-06 | Route analysis | State and region routes show volume, timing stats, delay rate, sample size; low-sample routes listed separately; Factory → Region rollup for small factories | P0 |
| FR-07 | RES and leaderboard | Formula, population, weights shown (70/30 fixed on Pages 1–7; sensitivity analysis on Page 8 only); constant-value handling; speed-only score; Top and Bottom 10; low-sample notes | P0 |
| FR-08 | Delay threshold | Slider 1 to 15 days (default 5), always visible; delay counts and rates update consistently on every page; label "analysis threshold" | P0 |
| FR-09 | Geographic view | State metric selector (mean lead time, delay rate, RES, volume); legend and units; missing and non-US rows disclosed | P1 |
| FR-10 | Ship-mode comparison | Individual modes and Standard vs Expedited; distance bands; margin-by-mode (Section 11); no causal language | P1 |
| FR-11 | Bottleneck flags | Configurable rules; reasons, counts and warnings visible; labelled "potential"; state and route level | P1 |
| FR-12 | Drill-down | Route or state summary and order list; order-level timeline (order date, ship date, threshold marker); order-to-ship never labelled transit time | P1 |
| FR-13 | Filters | Layer, scenario (Synthetic only), factory, state, region, ship mode, valid date range, minimum sample, duplicate toggle; reset control; empty-state messages | P0 |
| FR-14 | Exports | Filtered CSV with readable headers, layer, scenario, threshold, score settings, applied filters | P0 |
| FR-15 | Research traceability | Figures regenerate by script; methodology, generator settings, software versions recorded | P0 |
| FR-16 | Error handling | Missing columns, malformed dates, empty results, unsupported files give clear messages | P0 |
| FR-17 | Trends | Monthly order volume (Original layer, valid order dates) and monthly mean lead time (Synthetic) | P1 |
| FR-18 | Deployment | Public link uses Synthetic layer only; local run documented as backup | P0 |
| FR-19 | Lead-time basis switch | Toggle between mode-adjusted (default) and raw lead time for RES, rankings and the map; both shown side by side with rank changes; mode reference means calculated on full scenario dataset before user filters | P0 |
| FR-20 | Business insights | Overview shows sales, margin and growth by year, product, factory and state from valid Original fields; each card labelled Original | P1 |
| FR-21 | Cleaning outputs | Derived layer applies postal-code padding, product-name standardisation and the duplicate flag; each change counted in the transformation log | P0 |

---

## 14. Dashboard information architecture

Eight pages; keep the PRD, README, app, screenshots and paper consistent.

1. **Executive Overview:** layer banner, order lines and line items, mapping coverage, timing validity, route summary, business insights (sales, margin, growth by year and product).
2. **Data Quality and Method:** missingness, duplicates, date anomaly, mapping issues, definitions, assumptions, generator settings, limitations.
3. **Route Efficiency:** RES, route table, mean, median, variability, counts, Top and Bottom 10, low-sample list.
4. **Geographic Analysis:** US state heatmap with a named metric and consistent legend.
5. **Ship-Mode Comparison:** descriptive comparison, distance bands, margin by mode.
6. **Potential Bottlenecks:** volume versus performance quadrant, criteria, reasons.
7. **Route Drill-Down:** selected factory, state or region; supporting orders; timelines.
8. **Trends and Scenarios:** order-volume trends (valid dates), Baseline versus Stress scenarios.

**Build order:** Data Quality and Method → Overview → Route Efficiency → exports → remaining pages. Do not sacrifice core correctness to finish all pages.

---

## 15. Filters, defaults and interaction rules

| Setting | Default | Range |
|---|---|---|
| Data layer | Synthetic for timing pages; Original for volume pages | Required selection |
| Scenario | Baseline | Baseline, Distance-sensitive, Stress test (Synthetic only) |
| Analysis threshold | 5 days | 1 to 15 |
| Minimum sample | 30 orders | 10 to 100 |
| Duplicates | Excluded | Toggle |
| Lead-time basis | Mode-adjusted | Mode-adjusted or raw |
| RES weights | 70 / 30 | Fixed 70/30 on Pages 1–7; sensitivity analysis on Page 8 only |

- Calculate shipping-mode reference means using the full applicable scenario dataset before user filters are applied. User filters must not change the reference means used for RES calculations.
- Display active filters and the comparison population near RES.
- Provide reset and helpful empty states.
- Label the slider "analysis threshold", not SLA.
- All charts and tables on a page use consistent filters and denominators.
- If filters change the normalisation population, recompute RES and state that scores may change.

---

## 16. Non-functional requirements

- **Usability:** clear labels, metric tooltips, accessible colour scales, glossary, units on axes.
- **Performance:** around 10,000 records should feel responsive; cache loading and aggregation; record measured load and update times.
- **Reliability:** malformed inputs and empty selections produce actionable messages.
- **Reproducibility:** fixed seed, versioned settings, pinned dependencies, repeatable scripts.
- **Maintainability:** separate loading and validation, transformations, metrics, generator, charts and UI.
- **Traceability:** every score and chart traces to a definition and source layer.
- **Privacy and security:** follow the publication rule in Section 7; load only trusted files; avoid unsafe deserialisation.

---

## 17. Technical architecture

### Stack (from the tech stack analysis)

| Layer | Choice |
|---|---|
| Language | Python 3.11 or 3.12 |
| Data | Pandas, NumPy, openpyxl, PyYAML, pyarrow |
| App | Streamlit (multi-page, presentation-only with caching in app layer) |
| Charts and map | Plotly, including US state choropleth; Matplotlib and Seaborn for paper figures |
| Tests | pytest (targeted tests on critical paths) |
| Storage | Apache Parquet (via pyarrow) for derived and synthetic datasets; CSV for audited exports |
| Version control | Git and GitHub (with `.gitignore` excluding raw data) |
| Deployment | Streamlit Community Cloud (cloud artifacts only, no raw source data, no authentication); local run as backup |

Pin exact versions in `requirements.txt`. The `.gitignore` file strictly excludes `data/original/` and raw `.csv` files. Pre-computation is executed offline via `scripts/build_data.py` before application startup; the Streamlit application strictly loads and caches prepared Parquet artifacts via `@st.cache_data` in the application presentation layer (`app.py`), keeping `src/` modules completely free of Streamlit imports.

### Structure

```text
factory/
├── .gitignore                      # Excludes data/original/, cache, local secrets
├── README.md                       # Project overview, quickstart, methodology, run instructions
├── config/
│   ├── factories.csv               # Factory coordinates (lat/long) and addresses
│   ├── product_factory.csv         # 15-product to 5-factory mapping
│   ├── geographic_centroids.csv    # US state and Canadian province centroids for distance calc
│   └── generator.yaml              # Synthetic calibration params, seed 42, Texas route injections
├── data/
│   ├── original/
│   │   └── nassau_candy.csv        # Local-only immutable source file (SHA-256 verified; GIT-IGNORED)
│   ├── derived/
│   │   ├── clean_orders.parquet    # Cleaned, mapped, postal-padded dataset (via pyarrow)
│   │   ├── route_aggregates.parquet# Pre-aggregated Factory -> State & Region tables
│   │   └── transformation_log.json # Auditable step-by-step cleaning and deduplication log
│   └── synthetic/
│       ├── baseline.parquet        # Baseline scenario synthetic dataset
│       ├── distance_sensitive.parquet # Distance-sensitive scenario with Haversine distance
│       ├── stress_test.parquet     # Stress-test scenario (Distance-sensitive + injected delays)
│       └── metadata.json           # Build timestamp, seed 42, scenario hashes, reconciliation metrics
├── docs/
│   ├── Nassau_Route_Intelligence_PRD_v1.3_FINAL.md # Approved PRD
│   ├── DATA_AUDIT.md               # Source dataset audit report
│   ├── ARCHITECTURE.md             # Technical Architecture Specification (v1.1)
│   ├── data_dictionary.md          # Formal column definitions and semantic units
│   ├── methodology.md              # Research paper methodology and formulas
│   └── synthetic_assumptions.md    # Disclosed generator rules and bounds
├── scripts/
│   └── build_data.py               # Pre-computes, validates, and serializes all Parquet artifacts
├── src/
│   ├── __init__.py
│   ├── config.py                   # Centralized configuration, paths, defaults, weights
│   ├── load_data.py                # Pure Python dual-mode loader (no Streamlit imports)
│   ├── validate_data.py            # 4-metric reconciliation, duplicate flags, postal padding
│   ├── map_factories.py            # Product-to-factory joins, coordinate attachment, haversine
│   ├── generate_synthetic.py       # Shipment-grain synthetic timing generator (Seed 42)
│   ├── metrics.py                  # Lead time, mode-adjusted residuals, RES math, delay rates
│   ├── route_analysis.py           # Route aggregation, N >= 30 filtering, safe metrics, rankings
│   ├── bottleneck_rules.py         # 75th percentile screening flags and watch list quadrant
│   └── exports.py                  # Filtered CSV generator with embedded metadata header
├── tests/
│   ├── conftest.py                 # Pytest fixtures and sample dataframes
│   ├── test_data_quality.py        # Tests for hash, duplicates, 4-metric reconciliation, zip, Canada
│   ├── test_mapping.py             # Tests for 15/15 product coverage, 1 factory/order, distances
│   ├── test_synthetic.py           # Tests for seed 42, bounds, calibration, stress injections unclipped
│   ├── test_metrics.py             # Tests for RES math [0, 100], safe metrics, mode-adjustment
│   ├── test_route_analysis.py      # Tests for N >= 30 boundaries (29, 30, 31), layer isolation
│   ├── test_bottlenecks.py         # Tests for 5-seed bottleneck recovery (>= 4/5)
│   ├── test_privacy.py             # Asserts zero real Customer IDs or unmasked Order IDs in cloud artifacts
│   ├── test_architecture.py        # Asserts zero Streamlit imports in src/
│   └── test_exports.py             # Tests for export metadata, headers, layer tagging
├── app.py                          # Streamlit application entrypoint, sidebar filters, @st.cache_data
├── pages/
├── pyproject.toml                  # Python build & dependency metadata (with pyarrow, PyYAML, seaborn)
└── requirements.txt                # Pinned production dependencies
```

### Data flow

1. **Offline Preparation Flow (`scripts/build_data.py`):**
   Original raw file (`data/original/nassau_candy.csv`, local-only, SHA-256 verified) → quality validation (313 duplicates flagged, units reconciled $38,654 \rightarrow 37,667$) → geographic mapping (US states + Canadian province centroids from `geographic_centroids.csv`) → shipment-grain generation (5,067 shipments, seed 42) → scenario calculation (Baseline, Distance-Sensitive, Stress-Test with Texas route injections) → serialization of Parquet artifacts, `metadata.json`, and `transformation_log.json`.
2. **Runtime Application Flow (`app.py`):**
   Streamlit app loads cached Parquet artifacts via `@st.cache_data` in `app.py` → applies pre-computed mode reference means and filter logic in memory → displays interactive pages, leaderboards, and maps without re-running simulations.

---

## 18. Testing and quality gates

### Required automated tests (Targeted tests on critical paths)

- Required columns present; missing-column error.
- Empty dataset and empty filter results.
- Missing or unparseable dates; `Ship Date < Order Date`.
- Suspiciously large source intervals flagged without modification.
- Exact duplicates and repeated order IDs treated separately; 10,194 = 9,881 + 313.
- Four-metric reconciliation: rows ($10,194 \rightarrow 9,881$), units ($38,654 \rightarrow 37,667$), sales ($\$141,783.63 \rightarrow \$138,284.12$), and gross profit ($\$93,442.80 \rightarrow \$91,076.41$).
- Unmatched product-to-factory mapping (15/15 products covered).
- Order-line grain: every Order ID maps to exactly one factory across all 8,549 Order IDs.
- Distance calculation: Canadian province centroids and US state centroids present; no missing distance interpreted as zero.
- Privacy in cloud artifacts (`test_privacy.py`): assert zero raw Customer IDs appear in cloud Parquet files or metadata; assert Order ID surrogate keys cannot reveal original Customer IDs; assert City and Postal Code are dropped from cloud artifacts.
- Streamlit separation (`test_architecture.py`): assert zero Streamlit imports (`import streamlit`, `from streamlit`) in any file under `src/`.
- Route samples at exact boundary cases: $N=29$ (ineligible), $N=30$ (eligible), and $N=31$ (eligible).
- Safe metric handling: zero-variance and constant-value routes assign penalty = 0 without error; single-route comparisons display insufficient comparison set.
- Layer isolation: assert leaderboards strictly prohibit mixing ORIGINAL, DERIVED, and SYNTHETIC rows in the same ranked table.
- RES stays within 0 to 100 for valid multi-route comparison sets; hand-calculation check for one route.
- Delay boundary: `lead_time_days == threshold` is not delayed (strict `>`).
- Deterministic reproducibility: same seed (42) and settings reproduce identical synthetic DataFrame hash.
- Calibration targets in Section 10 hold on Baseline.
- Stress-test injection survival: assert injected delays (+1.0d peak season, +1.0d CA/NY, +1.5d for Texas routes *Lot's O' Nuts → Texas* and *Wicked Choccy's → Texas*) survive without being clipped on any mode, including Same Day.
- Bottleneck recovery test across 5 seeds (`test_bottlenecks.py`): recovery succeeds in at least 4 of 5 seeds ($\ge 4/5$, i.e. $\ge 80\%$) at 5-day threshold under the $P_{75}$ volume and delay rule (or watchlist with $\text{Delay Rate} > \text{Median}$), enforcing minimum sample $N \ge 30$ and requiring Stress-Test delay rate strictly greater than Baseline delay rate.
- Exports contain layer, scenario, threshold, and settings in prepended metadata header.
- Source hash unchanged: assert SHA-256 of raw file remains identical before and after pipeline execution.
- Slider change updates delay rate on every page.
- Mode-adjusted lead time reference means pre-computed on full scenario dataset before user filters and invariant to filter changes.
- Postal codes: 449 four-digit US codes padded; 200 Canadian codes flagged as partial and international.
- Reconstruction check: per-mode means from the Order-ID-year floors match Section 3.1 within 0.01.

### Release gates

Do not call the dashboard research-ready until core calculations pass tests, the mentor is informed of the date anomaly, synthetic assumptions are documented, score sensitivity is checked, charts show units, denominators and layer, figures regenerate from scripts, and key references are verified.

---

## 19. Research plan and evidence standards

### Research questions

1. What problem is addressed and why are route-level summaries useful?
2. What are the dataset's grain, coverage and quality?
3. How are route, lead time, delay, variability, RES and potential bottleneck defined?
4. How does the method behave on Baseline and Stress-test scenarios?
5. How sensitive are rankings to score weights, minimum sample and random seed?
6. Which conclusions are supported, and which remain unverified?

### Required experiments

| Experiment | Scope |
|---|---|
| Data-quality audit | Actual counts and date statistics from source (Section 3) |
| Baseline scenario | Generated timing distributions and route ranking behaviour |
| Stress test | Are the injected patterns flagged? |
| RES sensitivity | 50/50, 70/30, 90/10 weights |
| Sample-threshold sensitivity | 10, 20, 30, 50, 100 |
| Seed robustness | At least 5 seeds; ranking stability |
| Limitations | Scenarios do not establish actual company performance |

### Evidence rules

- Never invent experimental results before running code.
- Separate dataset facts, literature findings, project assumptions and synthetic results.
- Verify each academic paper's title, authors, venue, year, DOI or URL and claim alignment.
- Verify competitor capabilities and pricing from current official sources; label unavailable prices "not publicly verified".
- Keep `research_evidence_log.md` with claim, source, date, evidence summary, verification status and intended use.
- Exclude unverified references from key claims.
- Do not claim novelty because the project combines dashboards, route ranking or synthetic data; state the specific contribution and compare fairly with verified prior work.

### Starter evidence log

| Claim | Source type | Status | Allowed use |
|---|---|---|---|
| Date interval 904 to 1,642 days on all rows | Dataset | Verified by profiling | Fact |
| Interval floor depends on Order-ID year (904 / 1,269 / 1,269 / 1,634) | Dataset | Verified by profiling | Fact about the file |
| Subtracting the floors gives 0 to 11 days that separate by ship mode | Dataset | Verified, but the reconstruction is unconfirmed | Hypothesis; calibration of Baseline only |
| Order ID embeds customer and product; 34% of customer shipments span 2+ factories | Dataset | Verified by profiling | Fact (explains the unit of analysis) |
| Ship mode explains 62% of reconstructed lead-time variance; region adds 0.1 point | Dataset (reconstruction) | Verified, conditional on the hypothesis | Rationale for mode-adjusted RES |
| 313 exact duplicate rows, $3,499.51 sales | Dataset | Verified by profiling | Fact |
| About 62 to 64% of US candy sales fall in four holiday seasons | National Confectioners Association reports via trade press | Secondary source; verify against NCA | Context for seasonality |
| US ground carriers quote about 1 to 5 business days, rising with distance | Carrier-guide summaries | Secondary; transit is not order-to-ship time | Plausibility check only, not calibration |
| Consistency matters more than average speed | Feo-Valero et al. (2013) | Verify DOI and claim | Rationale for variability in RES |
| Small-group rankings are noisy | Laird and Louis (1989) | Verify DOI and claim | Rationale for minimum sample |
| Composite indicator practice | OECD / JRC handbook (2008) | Verify | Score design |
| Training on self-generated data is circular for ML | Müller et al. (2025) | Verify | ML exclusion |

---

## 20. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Source dates invalid | Preserve dates, flag anomaly, use separate synthetic timing until confirmed |
| Synthetic pattern mistaken for discovery | Baseline default; Distance-sensitive and Stress-test scenarios named and labelled; published assumptions |
| Findings only mirror generator settings | Disclose all assumptions; sensitivity and seed checks; frame as method demonstration |
| Order-to-ship time mistaken for transit or delivery time | Use "order-to-ship lead time" everywhere; definitions page |
| Incomplete mapping | Report coverage; never invent factories (currently 0 unmatched) |
| Row grain misunderstood | Grain documented (Section 3.2); order lines and line items counted separately |
| Duplicates are real repeated lines | Flag, default exclude, toggle, ask mentor |
| Three small factories have almost no eligible routes | Region rollup, low-sample warnings, focus on two large factories |
| RES changes with filters | Show population; recompute transparently; sensitivity checks |
| Arbitrary score weights | Fixed 70/30 on Pages 1–7; sensitivity analysis on Page 8 only; speed-only score (100/0) shown beside it |
| COGS mistaken for freight cost | Define `Cost`; margin-only default; synthetic cost labelled |
| Estimated distance mistaken for mileage | Label as geographic estimate |
| Correlation mistaken for causation | Descriptive wording only |
| Canada rows break the US map | Exclude from map with a note |
| Weak citations | Verify bibliography; keep evidence log |
| Scope creep | P0 first; stretch features only after P0 passes |
| Source data published without permission | Public cloud app uses sanitized Parquet artifacts with surrogate keys for Customer ID and Order ID; City and Postal Code dropped; mapping local-only |
| Route differences are small and mostly reflect ship-mode mix | Mode-adjusted RES by default; raw shown beside it; plain statement that differences are small |
| "Order" count mistaken for real orders or shipments | Say "order lines"; explain the grain in the glossary and on the Data Quality page |
| Reconstruction treated as fact | Hypothesis label; used for calibration only; mentor confirmation recorded |
| Streamlit slow on each interaction | Cache loading and aggregation |

---

## 21. Delivery plan and deliverables

### Five-week plan (adjust to the real deadline)

| Week | Work | Exit criteria |
|---|---|---|
| 1 | Source hash, data profile, grain note, quality report, mapping, mentor notification; repository and config files | Audit reviewed; 10,194 = 9,881 + 313; no silent source changes |
| 2 | Derived layer, route aggregation, distance, unit tests; generator and Baseline scenario | Mapping and route tables reproducible; calibration targets pass |
| 3 | Stress scenario; RES, leaderboards, filters, threshold, exports; Overview and Route pages | P0 pages pass tests and show labels |
| 4 | Heatmap, ship-mode, bottlenecks, drill-down, trends (P1); deployment | Live link works; local backup documented |
| 5 | Sensitivity experiments, paper, executive summary, QA, demo rehearsal | Figures regenerate; citations verified |

If time is short, finish P0 reliably before attempting all eight pages.

### Final deliverables

1. Streamlit dashboard with isolated, labelled data layers and a public link (Synthetic layer only).
2. Source data-quality report covering date anomaly, mapping, duplicates, missingness and grain.
3. Derived route tables and data dictionary.
4. Synthetic Baseline and Stress-test datasets with generator code, seed, settings and notes.
5. Metric implementation and tests for RES, delay rates, sample rules and edge cases.
6. Research paper: verified literature, experiments, sensitivity analysis, results and limitations.
7. Executive summary in plain language (suitable for non-technical and government stakeholders), separating source facts from synthetic demonstrations.
8. README and methodology docs aligned with the implemented app.

---

## 22. Definition of done

- [ ] Original source unchanged and hash recorded.
- [ ] Data grain and duplicate treatment documented.
- [ ] Date anomaly visible and not silently corrected.
- [ ] Original, Derived and Synthetic layers isolated and labelled.
- [ ] Mapping coverage and unmatched records reported.
- [ ] Lead time labelled "order-to-ship"; never called transit or delivery time.
- [ ] `Cost` not described as freight cost without confirmation.
- [ ] RES formula, population, weights and edge cases documented; speed-only score shown.
- [ ] Sample threshold configurable and sensitivity-tested.
- [ ] Baseline and Stress scenarios reproducible; assumptions documented.
- [ ] Filters, threshold, heatmap, ranking and exports tested.
- [ ] Research results reproducible and citations verified.
- [ ] README, PRD, app and paper use consistent page names and definitions.
- [ ] Mentor notified of date anomaly; publication permission checked; public app uses Synthetic layer only.

---

## 23. Open decisions for the mentor

| # | Decision | Proposed default |
|---|---|---|
| 1 | Confirm synthetic timing, with original order, customer, product and money fields kept | Yes (already directed) |
| 2 | Is the Order-ID-year reconstruction correct (floors 904, 1,269, 1,269, 1,634, then 0 to 11 days)? Were order dates shifted too? | Present as evidence; keep as a diagnostic. If confirmed, the reconstructed intervals could be offered as a real-timing option |
| 3 | Treat an Order ID as one factory-to-customer leg ("order line")? | Yes, backed by the Order ID structure |
| 4 | Remove or keep the 313 duplicates? | Flag and exclude by default, with a toggle |
| 5 | Reference service days per mode (optional view) | Same Day 1, First Class 2, Second Class 3, Standard 5, labelled assumed |
| 6 | Synthetic shipping cost scenario wanted? | Margin-only by default; synthetic cost only if approved |
| 7 | Which states and routes carry the Stress-test injections? | Approved: California and New York (+1.0d); Lot's O' Nuts -> Texas (+1.5d); Wicked Choccy's -> Texas (+1.5d); Nov/Dec peak season (+1.0d). Configurable and validated in generator.yaml |
| 8 | Rank routes on mode-adjusted lead time by default? | Yes, with raw shown beside it |
| 9 | Permission to publish source data or customer IDs? | No; public cloud app uses sanitized Parquet artifacts with surrogate keys for Customer ID and Order ID; City and Postal Code dropped; mapping local-only |
---

## Appendix A. Factories, coordinates and products

| Factory | Latitude | Longitude | Products | Order lines (de-duplicated) |
|---|---|---|---|---|
| Lot's O' Nuts | 32.881893 | -111.768036 | Wonka Bar: Nutty Crunch Surprise, Fudge Mallows, Scrumdiddlyumptious | 4,760 |
| Wicked Choccy's | 32.076176 | -81.088371 | Wonka Bar: Milk Chocolate, Triple Dazzle Caramel | 3,445 |
| Sugar Shack | 48.11914 | -96.18115 | Laffy Taffy, SweeTARTS, Nerds, Fun Dip, Fizzy Lifting Drinks | 33 |
| Secret Factory | 41.446333 | -90.565487 | Everlasting Gobstopper, Lickable Wallpaper, Wonka Gum | 213 |
| The Other Factory | 35.1175 | -89.971107 | Hair Toffee, Kazookles | 98 |

## Appendix B. Data profile snapshot

| Item | Value |
|---|---|
| Regions (rows) | Pacific 3,253; Atlantic 2,986; Interior 2,335; Gulf 1,620 |
| Top states by orders | California 1,686; New York 942; Texas 833; Pennsylvania 487; Illinois 433; Washington 432; Ohio 392; Florida 319 |
| Orders per month (both years combined) | Jan 324; Feb 263; Mar 611; Apr 567; May 644; Jun 609; Jul 588; Aug 592; Sep 1,177; Oct 710; Nov 1,237; Dec 1,227 |
| Eligible Factory → State routes (order lines) | 54 at N ≥ 30 (28 Lot's O' Nuts, 25 Wicked Choccy's, 1 Secret Factory); 69 at N ≥ 20; 95 at N ≥ 10; 196 total |
| Product division (rows) | Chocolate 9,844; Other 310; Sugar 40 |
| Units per line | Mean 3.8; maximum 14 |
| Postal-code formats | 449 four-digit US codes; 200 three-character Canadian codes |
| Sales by year | 2024: $57,956; 2025: $83,827 (+44.6%) |

## Appendix C. Glossary

| Term | Meaning |
|---|---|
| Route | A factory to customer state (or region) pair |
| Order line | One distinct Order ID; contains customer and product codes, so it is one factory-to-customer leg |
| Customer shipment | Customer + order date + ship mode (5,067 shipments; 1,702 [33.6%] multi-factory; 2,240 multi-order-line); distinct from order-line count (8,549) |
| Mode-adjusted lead time | Lead time minus the mean of its ship mode |
| Order-to-ship lead time | Days from order date to ship date |
| Delay rate | Share of eligible orders with lead time above the analysis threshold |
| RES | Route Efficiency Score, a 0 to 100 relative index |
| Eligible route | A route with at least the minimum number of orders |
| Layer | Original, Derived or Synthetic data set |
| Scenario | A named synthetic configuration (Baseline, Stress test) |
| COGS | Cost of goods sold (the file's `Cost` column) |

## Appendix D. Empirical per-mode lead-time distributions (Baseline calibration)

Derived from the unverified reconstruction in Section 3.1. Share of order lines at each day value. A handful of Standard Class rows sit at 11 days.

| Ship mode | 0 d | 1 d | 2 d | 3 d | 4 d | 5 d | 6 d | 7 d | 8 d | Mean | Std dev |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Same Day | 64.0% | 33.6% | 2.4% | | | | | | | 0.38 | 0.53 |
| First Class | | 12.3% | 35.3% | 37.8% | 14.5% | 0.1% | | | | 2.55 | 0.89 |
| Second Class | | 0.1% | 26.7% | 24.5% | 20.9% | 20.4% | 7.5% | | | 3.57 | 1.28 |
| Standard Class | | | | 0.2% | 27.6% | 33.4% | 21.7% | 13.5% | 3.6% | 5.32 | 1.13 |

The generator samples these distributions directly; store them in `generator.yaml` and recompute them if the source or the reconstruction rule changes.

## Appendix E. Final audit: brief, problem statement, solution and tech stack

### Problem statement (four questions in the brief)

| Question | Where answered | Status |
|---|---|---|
| Which routes are consistently efficient? | Route Efficiency page: RES, Top 10 | Covered |
| Which routes are frequently delayed? | Delay frequency, Bottom 10, bottleneck flags | Covered |
| How performance varies by region, state and ship mode | Map, route tables, ship-mode comparison, mode-adjusted view | Covered |
| Where geographic bottlenecks exist | Quadrant and flags at state and route level | Covered |

### Methodology steps in the brief

| Brief step | In v1.1 | In v1.3 |
|---|---|---|
| Data cleaning: validate dates, handle invalid lead times, handle missing, standardise geography | Partly (no postal-code or Canada handling) | Covered (Sections 3.4, 9) |
| Feature engineering: lead time, routes by region and state, group by ship mode | Covered | Covered, plus order-line grain |
| Route aggregation: shipments, average, variability | Covered | Covered, with order-line counting |
| Benchmarking: rank, Top 10 / Bottom 10, compare ship modes | Covered | Covered, plus mode-adjusted ranking |
| Geographic bottlenecks: high lead time, high volume plus poor performance, congestion-prone states | Routes only | State and route level |
| Ship mode analysis: Standard vs Expedited; descriptive cost-time tradeoff | Cost-time prohibited; no clear grouping | Grouping defined; margin-by-mode default; labelled synthetic cost optional |
| Five KPIs | Covered | Covered with formulas |

### Dashboard and users

| Brief item | In v1.1 | In v1.3 |
|---|---|---|
| Route Efficiency Overview and leaderboard | Covered | Covered |
| US heatmap and regional bottleneck view | Covered | Covered (Canada excluded with a note) |
| Ship Mode Comparison | Covered | Covered |
| Route Drill-Down: state insights, order-level timelines | Partly | Covered (FR-12) |
| Date range, region / state, ship mode filters, threshold slider | Covered | Covered, with defaults |

### Deliverables and data inputs

| Item | In v1.1 | In v1.3 |
|---|---|---|
| Research paper, dashboard, executive summary | Covered; no audience note | Covered; summary suitable for non-technical and government stakeholders |
| Factory coordinates and product-factory table | Referred to, not included | Appendix A and `config/` files |
| Verified data facts, grain, duplicates | Missing | Section 3 |
| Generator values and calibration | Missing | Section 10, Appendix D |

### Tech stack

| Component | Brief / stack analysis | In v1.1 | In v1.3 |
|---|---|---|---|
| Python, Pandas, NumPy | Required | Yes | Yes |
| Streamlit, Plotly | Required | Yes | Yes (including the state choropleth) |
| openpyxl | Reads the Excel input | No | Yes |
| PyYAML, pyarrow | Config parsing and Parquet storage | No | Yes |
| pytest | Recommended | Yes | Yes, with targeted tests on critical paths |
| Matplotlib / Seaborn | Paper figures | No | Yes |
| Git and GitHub | Version control, deployment | No | Yes |
| Deployment (Streamlit Community Cloud, local backup) | Brief asks for live analytics | No | Yes; public cloud app loads Synthetic/Derived artifacts only (no original data or auth required) |
| Config files (factories, mapping, centroids, generator) | Reproducibility | Partly | Yes |

No item in the brief or the tech stack analysis is missing from v1.3. Remaining items need mentor input (Section 23) and verification of references before submission.

## References

Official technical documentation for implementation details only; it does not validate logistics assumptions or prove research claims.

- Streamlit caching overview: https://docs.streamlit.io/develop/concepts/architecture/caching
- Streamlit app tutorial: https://docs.streamlit.io/get-started/tutorials/create-an-app
- Streamlit download button API: https://docs.streamlit.io/develop/api-reference/widgets/st.download_button

**Research integrity note:** treat the existing research package as a starting point, not a verified literature review. Before final submission, audit every reference, DOI or URL, competitor claim, publication date and claim-to-source match. Do not present synthetic outputs as empirical company findings.
