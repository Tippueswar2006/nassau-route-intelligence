# Recommended Next Steps and Research-Based Roadmap

**Project:** Nassau Candy Shipping Route Intelligence  
**Role:** Senior Data Analytics Consultant & Logistics Researcher  
**Document Status:** Complete Deliverable 10  

---

## 1. Research-to-Product Transition Roadmap

Having completed the rigorous market, competitor, academic, technical, and data quality research phases, the project is now prepared to transition from **Exploratory Research** to **Product Specification & Implementation**.

The recommended execution plan spans six focused milestones across a 5-week implementation lifecycle:

```
+--------------------------------------------------------------------------------------------------+
| MILESTONE 1: DATA ARCHITECTURE & GOVERNANCE FREEZE (Week 1)                                      |
| - Build raw data ingestion and schema validation script                                          |
| - Implement Data Quality profiling module (date anomaly bounds, duplicate counter)               |
| - Code product-to-factory mapping logic and verify coverage rate (>95%)                          |
| - Output: src/data_quality.py and cleaned Derived Dataset                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| MILESTONE 2: STAKEHOLDER & MENTOR ALIGNMENT GATEWAY (Week 1.5)                                   |
| - Present Data Quality findings and formalize mentor responses to 4 critical questions            |
| - Freeze synthetic lead-time generator parameters and random seed (seed=42)                      |
| - Formalize PRD v1.0 signing off on scope boundaries                                             |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| MILESTONE 3: SYNTHETIC ENGINE IMPLEMENTATION & VERIFICATION (Week 2)                             |
| - Programmatically generate synthetic lead times via documented formula                          |
| - Validate synthetic output distributions (realistic 1–10 day bounds, distance correlation)      |
| - Assert strict isolation: attach Data_Source='Synthetic' flag to every record                   |
| - Output: src/synthetic_generator.py and data/synthetic/nassau_synthetic.csv                     |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| MILESTONE 4: CORE DASHBOARD BUILD (P0 CAPABILITIES) (Week 3)                                     |
| - Implement Route Efficiency Score (RES) calculation with N >= 30 filter                         |
| - Build Overview KPI page and Route Leaderboard (Top 10 / Bottom 10)                             |
| - Embed interactive Delay Threshold Slider with dynamic Streamlit reactivity                     |
| - Enforce persistent UI Data Provenance Badges across all pages                                  |
| - Output: Working P0 Streamlit prototype                                                         |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| MILESTONE 5: ADVANCED VISUAL ANALYTICS BUILD (P1 CAPABILITIES) (Week 4)                          |
| - Develop interactive US State Choropleth Heatmap (Plotly Express)                               |
| - Build Multi-Criteria Bottleneck Priority Quadrant Scatter Plot                                 |
| - Implement Distance-Stratified Standard vs. Expedited Modal Comparison                          |
| - Construct Order-Level Shipment Milestone Drill-Down                                            |
| - Code Illustrative "What-If" Factory Reallocation Simulator                                     |
| - Output: Feature-complete Streamlit web application                                             |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| MILESTONE 6: RESEARCH PAPER, EXECUTIVE SUMMARY & ACADEMIC DEFENSE (Week 5)                       |
| - Author formal Academic Research Paper detailing methodology and findings                       |
| - Draft 1-Page Plain-Language Executive Summary                                                  |
| - Extract reproducible high-resolution figures and CSV benchmark tables                          |
| - Final academic packaging and GitHub repository release                                         |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Immediate Validation Tasks: What to Validate First

Prior to writing Streamlit user interface code, three foundational validations must be executed:
1. **Validate Factory Mapping Match Rate:** Run a test join between the Nassau Candy transactional dataset and the `product-factory` mapping table. Confirm that unmatched SKUs account for $< 5\%$ of total order volume. Document any unmatched SKUs explicitly.
2. **Validate Factory Concentration Skew:** Quantify the exact order distribution across all five factories. If Facilities C, D, and E account for $< 5\%$ of volume, hardcode low-sample warnings on those facility views.
3. **Validate Exact Duplicate Row Distribution:** Confirm that the 313 duplicate rows are exact replicas across all fields (Order ID, SKU, Date, Financials) and determine whether they represent repeat batch line-items or accidental double-exports.

---

## 3. Formal Inquiries for Mentor / Data Owner

The following four questions should be formally submitted to the academic mentor or data provider to resolve critical unknowns:

```
+-------------------------------------------------------------------------------------------------------+
| QUESTION 1: ROOT CAUSE OF THE DATE INTERVAL DEFECT                                                    |
| "The raw export demonstrates an order-to-ship interval ranging from 904 to 1,642 days across 100% of  |
| rows. Is this a known epoch/migration offset (e.g., Year 2000 Julian shift, mismatched join tables),  |
| or synthetic masking? Will a corrected historical date export be provided during the semester?"      |
+-------------------------------------------------------------------------------------------------------+
| QUESTION 2: PROMISED SERVICE LEVEL AGREEMENTS (SLAs) BY MODE                                          |
| "To ensure our delay threshold slider is anchored in commercial reality, what are Nassau Candy's      |
| contractual delivery commitments for each mode? (e.g., Same Day = 1 day, First Class = 2 days,       |
| Second Class = 3 days, Standard Class = 5 days)?"                                                     |
+-------------------------------------------------------------------------------------------------------+
| QUESTION 3: FINANCIAL SCOPE & FREIGHT SPEND                                                           |
| "The financial column 'Cost' reconciles to Cost of Goods Sold (COGS). Should our route intelligence  |
| focus purely on transit velocity and volume, or would you prefer us to generate a synthetic freight   |
| shipping cost (based on distance and weight rate tables) to demonstrate freight cost-to-serve?"       |
+-------------------------------------------------------------------------------------------------------+
| QUESTION 4: GRANULARITY OF ORDER ID AND MULTI-LINE SHIPMENTS                                          |
| "Does each row in the file represent an individual freight package, or a line-item within an order?   |
| If an order spans multiple rows with differing products, should route volume count unique Order IDs   |
| or physical rows?"                                                                                    |
+-------------------------------------------------------------------------------------------------------+
```

---

## 4. Technical Decisions: Frozen vs. Requiring Further Evidence

### 4.1 Technical Decisions Frozen by This Research
* $\checkmark$ **Core Technology Stack:** Python, Pandas, NumPy, Plotly, Streamlit, Git/GitHub. (Confirmed ideal for lightweight, reproducible, zero-cost decision support).
* $\checkmark$ **Three-Layer Data Governance Architecture:** Original (read-only) $\to$ Derived (spatial & mapping) $\to$ Synthetic (parametric timing demo).
* $\checkmark$ **Sample-Size Guardrails:** Leaderboards (Top 10 / Bottom 10) and Route Efficiency Scores are strictly constrained to routes with $N \ge 30$ orders to prevent small-sample noise domination.
* $\checkmark$ **Exclusion of ML Delay Prediction from v1:** Deferred to Future Scope (P2) to avoid circular training on synthetic data and preserve academic credibility.
* $\checkmark$ **Financial Disambiguation:** The existing `Cost` column will be labelled exclusively as "Product Manufacturing Cost / COGS"; carrier freight spend will not be inferred from it.
* $\checkmark$ **Distance Calculation Method:** Vectorized Haversine formula mapping factory coordinates to destination state population centroids.

### 4.2 Decisions Requiring Further Stakeholder Evidence
* $?$ **Synthetic Freight Cost Generation:** Whether to introduce a synthetic carrier freight cost column (e.g., $\$0.15/\text{km} + \text{modal markup}$) to enable a cost-time trade-off curve, pending mentor feedback on Question 3.
* $?$ **Handling of 313 Duplicate Rows:** Whether to drop duplicates globally in the Derived layer or provide an interactive UI toggle allowing users to compare results with and without duplicates.
* $?$ **Factory Production Cross-Compatibility:** Whether the "What-If" factory reallocation simulator should restrict reassignments based on product categories or allow unconstrained geographic reassignments.

---

## 5. Action Items for Next Working Session

1. **Create Project Directory Structure:**
   ```bash
   mkdir data/original data/derived data/synthetic
   mkdir src docs/paper tests
   ```
2. **Draft PRD v1.0:** Update the baseline PRD v0.2 using the findings from Deliverable 7 (Feature Prioritization) and Deliverable 8 (Data Requirements).
3. **Implement Baseline Data Quality Script:** Write `src/data_quality.py` to profile the raw file, verify the 313 duplicate rows, and generate the date interval histogram.
4. **Author Synthetic Generator:** Write `src/synthetic_generator.py` implementing the parametric lead-time model with `seed=42`.
