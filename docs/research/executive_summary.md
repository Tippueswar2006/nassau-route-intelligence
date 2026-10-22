# Executive Research Summary: Nassau Candy Shipping Route Intelligence

**Project:** Nassau Candy Shipping Route Intelligence  
**Role:** Senior Market Research Analyst, Logistics Technology Researcher, Business Analyst, Data Analytics Consultant  
**Date:** October 2026  
**Document Status:** Complete Research Synthesis (Deliverable 1)  

---

## 1. Project Opportunity & Academic Context

The **Nassau Candy Shipping Route Intelligence** project addresses a fundamental challenge in mid-market wholesale distribution: transforming transactional shipping records into actionable, route-level operational intelligence. Utilizing an empirical dataset from Nassau Candy Distributor (spanning multi-factory production, nationwide customer destinations, varied shipping modes, and financial line items), the project develops a lightweight, explainable, and reproducible decision-support dashboard built in **Python, Pandas, NumPy, Plotly, and Streamlit**.

Unlike commercial enterprise software designed for multi-million-dollar transportation budgets, this project is scoped as an **applied academic analytics project** and **decision-support prototype**. Its primary deliverables include:
1. An interactive, multi-page Streamlit analytics dashboard.
2. A formal research paper detailing transportation performance methodologies.
3. An executive summary bridging technical findings with supply chain strategy.
4. Fully documented, reproducible data pipelines with transparent governance.

The strategic opportunity lies in establishing an **explainable, open-source alternative** to black-box commercial Transportation Management Systems (TMS), providing supply chain analysts with transparent visibility into shipping lead times, geographic bottlenecks, and mode-selection trade-offs.

---

## 2. Core Operational & Analytical Problems

Interviews with logistics literature, industry benchmarks, and project documentation identify four core operational problems faced by distributors:

1. **Row-Level Transaction Blindness:** Enterprise Resource Planning (ERP) databases store shipments as isolated row items. Without automated route aggregation ($Factory \to State$), operations teams cannot discern systematic lane degradation from isolated delivery anomalies.
2. **Spreadsheet Analysis Latency & Rigidity:** Most mid-market logistics teams rely on static Microsoft Excel workbooks. Spreadsheets lack native geospatial visualization, cannot dynamically recalculate lead-time distributions across varying delay thresholds, and fail to handle multi-factory network reassignments.
3. **Confounded Mode Comparisons:** Shippers frequently debate the cost-benefit of Standard versus Expedited freight. However, raw comparisons typically suffer from confounding variables (e.g., expedited modes serving longer average distances or distinct product categories), leading to erroneous cost-cutting mandates.
4. **Severe Data Quality Anomaly in Baseline Dataset:** The original Nassau Candy dataset exhibits an extreme chronological anomaly: the elapsed interval between `Order Date` and `Ship Date` ranges from **904 to 1,642 days** across all records (with zero records under 30 days). Blindly computing lead times or delivery delays on this raw data would produce nonsensical, invalid conclusions.

---

## 3. Competitive Landscape & Niche Positioning

A comprehensive market evaluation across commercial and open-source solutions reveals a stark polarization:

```
[Enterprise TMS]            [Real-Time Visibility]         [General BI]           [Proposed Solution]
SAP TM / Oracle OTM         project44 / FourKites          Power BI / Tableau     Nassau Route Intel
-------------------         ---------------------          ------------------     -------------------
* Multi-million $ CapEx     * Telematics/IoT tracking      * General reporting    * Zero software cost
* 6-18 month deployment     * Carrier API network          * Manual data modeling * 100% transparent math
* Complex optimization      * In-transit GPS ETAs          * No native route DSS  * Built-in DQ layer
* Heavy IT overhead         * Enterprise SaaS subscriptions* Black-box DAX/Calcs  * Explicit synthetic layer
```

* **Enterprise TMS (SAP TM, Oracle OTM, Blue Yonder, Descartes):** Offer robust automated dispatch and multi-echelon optimization, but require prohibitive capital investment ($100,000 to $600,000+ annually), complex integration, and extensive training.
* **Real-Time Visibility Platforms (project44, FourKites):** Excel at active in-transit telematics and predictive GPS ETAs, but are execution-monitoring platforms rather than post-hoc route diagnostic tools.
* **General-Purpose BI (Microsoft Power BI, Tableau):** Powerful visualizers, but require extensive custom data modeling (DAX, M, calculated fields) and lack domain-specific logistics guardrails (e.g., statistical shrinkage for low-volume lanes, multi-layer data provenance).

**Defensible Niche:** Nassau Candy Shipping Route Intelligence provides a **transparent, accessible, zero-infrastructure analytical workbench**. It bridges the gap between static spreadsheets and cost-prohibitive TMS platforms, delivering clear route scoring, dynamic delay thresholds, and interactive spatial bottleneck detection.

---

## 4. Key Academic & Methodological Findings

The research evaluated 18+ peer-reviewed studies across transportation logistics, visual analytics, and data quality. Four foundational findings govern the technical architecture:

1. **Variability Outweighs Central Tendency:** Logistics performance research demonstrates that *lead-time variance* ($\sigma$) impacts customer service satisfaction and inventory holding costs significantly more than *mean lead time* ($\mu$) ([Feo-Valero et al., 2013](https://doi.org/10.1016/j.tre.2012.08.005); [Hsu et al., 2013](https://doi.org/10.1080/09720510.2013.777568)). Route scoring must penalize unpredictability, not just duration.
2. **Small-Sample Distortion in Route Rankings:** Ranking routes purely on sample mean lead times introduces extreme bias on thin lanes ($N < 30$). Top/Bottom leaderboards will be dominated by random noise from low-volume routes unless protected by hard sample thresholds ($N \ge 30$) or Empirical Bayes shrinkage estimators ([Laird & Louis, 1989](https://doi.org/10.3102/10769986014001029)).
3. **Composite Scoring Rigor:** Composite indices (such as the Route Efficiency Score) must adhere to established index construction frameworks ([OECD / JRC, 2008](https://doi.org/10.1787/9789264043466-en)). Relative min-max scaling is valid for internal cohort benchmarking, but must avoid arbitrary weightings and explicitly communicate non-compensatory trade-offs.
4. **Data Provenance & Synthetic Benchmarking:** In the presence of corrupted historical dates, data provenance frameworks ([Hazen et al., 2014](https://doi.org/10.1016/j.ijpe.2014.04.018); [Wang & Strong, 1996](https://doi.org/10.1080/07421222.1996.11518099)) require strict separation of source facts from simulated models. Recent supply chain synthetic data research ([Long et al., 2024](https://doi.org/10.1080/00207543.2024.2447927)) demonstrates that hybrid synthetic generation preserves empirical order topology while enabling valid algorithm demonstration.

---

## 5. The Critical Data Constraint & 3-Layer Solution

To resolve the 904-to-1,642 day date gap without falsifying records or compromising academic integrity, the project adopts a **Strict Three-Layer Data Architecture**:

```
+---------------------------------------------------------------------------------------+
| LAYER 1: ORIGINAL (Read-Only)                                                         |
| - Exact source records: Order ID, original dates, customer state/region, products     |
| - Financials: Sales, Units, Cost (COGS), Gross Profit                                 |
| - Usage: Data Quality Profiling, volume distribution, sales summaries                 |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| LAYER 2: DERIVED (Deterministic Mapping)                                              |
| - Product-to-Factory mapping (5 production facilities)                                |
| - Geocoding: Factory coordinates (Lat/Lon), Customer State centroids                  |
| - Route Key: Factory -> Customer State (e.g., "Factory_A -> NY")                      |
| - Anomaly & Duplicate Flags (identifies 313 exact duplicate rows)                     |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
| LAYER 3: SYNTHETIC (Time-Dependent Demonstration)                                     |
| - Preserves empirical orders, locations, products, and financial totals               |
| - Replaces corrupted dates with a reproducible lead-time generator:                   |
|   Lead_Time = Base_Mode + Dist_Effect(km) + Congestion + Seasonality + Noise(seed=42) |
| - Generates: Promised_Delivery_Date, Synthetic_Ship_Date, Lead_Time_Days             |
| - Usage: Dynamic threshold sliders, route scores, heatmaps, bottleneck prioritization |
+---------------------------------------------------------------------------------------+
```

### Strict Governance Mandates:
* **Banner Transparency:** Every dashboard page and CSV export must carry an unambiguous visual banner indicating whether displayed metrics originate from *Original*, *Derived*, or *Synthetic* data.
* **Non-Conflation of Financials:** The existing `Cost` column represents *Cost of Goods Sold (COGS)*, not shipping/freight expense. Carrier freight rates must not be inferred from `Cost`.
* **Zero Real-World Performance Claims:** Findings generated from the synthetic layer must be framed strictly as methodological demonstrations, not empirical evaluations of Nassau Candy's actual logistics operations.

---

## 6. Feature Prioritization (MoSCoW Summary)

Features are prioritized based on analytical validity, user value, implementation effort, and academic suitability:

* **Must Have (P0 - Core Prototype):**
  1. Multi-file ingestion and automated data schema validation.
  2. Data Quality & Profiling Engine (date interval distribution, missing values, duplicate detection).
  3. Product-to-Factory Mapping Engine with coverage reporting.
  4. Lane-level volume and geographic order distribution KPIs.
  5. Route Efficiency Leaderboard with a minimum sample size filter ($N \ge 30$).
  6. Interactive Delay Threshold Slider with dynamic KPI recalculation.
  7. Data Provenance Banner and filtered CSV export engine.
* **Should Have (P1 - Advanced Analytics):**
  1. Interactive US State Choropleth Heatmap (Plotly).
  2. Standard vs. Expedited Shipping Mode Performance & Confounder Analysis.
  3. Multi-Criteria Bottleneck Priority Matrix (Volume $\times$ Delay Rate $\times$ Variability).
  4. Order-Level Shipment Timeline Drill-Down.
  5. Monthly Seasonality & Shipping Volume Trends.
  6. Illustrative "What-If" Factory Reallocation Simulation (centroid distance model).
* **Future Scope / Not Recommended for v1 (P2):**
  1. Machine Learning Delay Prediction (deferred until verified ground-truth delivery labels exist).
  2. Real-Time Carrier Telematics & Live Weather Integration (out of scope for an offline academic prototype).

---

## 7. Major Strategic & Methodological Risks

| Risk Identified | Operational / Academic Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Synthetic Misattribution** | Evaluators mistake synthetic lead times for real company performance. | Permanent UI badges, red disclaimer banners, explicit methodology chapter in research paper. |
| **Factory Volume Skew** | 3 of 5 factories account for only ~350 total orders combined, distorting route rankings. | Enforce minimum sample threshold ($N \ge 30$), flag low-sample lanes, isolate primary factories (A & B) in benchmark cohorts. |
| **Cost Conflation** | User interprets COGS as carrier transportation cost. | Clearly label financial metrics as "Product Gross Profit / COGS"; separate synthetic shipping cost if modeled. |
| **Ecological Fallacy / Confounding** | Concluding Expedited shipping is "slower" because it was dispatched across longer lanes. | Stratify mode comparisons by distance buckets and regional corridors. |

---

## 8. Open Questions for Mentor / Data Owner

1. **Root Cause of Date Anomaly:** Was the 904–1,642 day gap caused by an ERP database migration epoch shift (e.g., Year 2000 / Julian conversion), mismatched order/ship export tables, or masking? Will corrected historical dates be released?
2. **Promised Service Level Agreements (SLAs):** What are the official contractual delivery day commitments for each shipping mode (Same Day, First Class, Second Class, Standard Class)?
3. **Financial Scope:** Should freight cost be excluded entirely, or modeled synthetically using industry mileage/weight rate tables?
4. **Order Multi-Line Span:** Does each row represent a distinct shipment package or an order line-item? Should volume KPIs count rows or `Distinct Order IDs`?
