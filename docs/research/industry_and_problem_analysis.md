# Industry and Problem Analysis: Logistics & Shipping Intelligence

**Project:** Nassau Candy Shipping Route Intelligence  
**Role:** Senior Market Research Analyst & Logistics Business Analyst  
**Document Status:** Complete Deliverable 2  

---

## 1. Domain Overview: Logistics & Shipping Route Analytics

Logistics and freight distribution form the operational circulatory system of wholesale commerce. In multi-facility manufacturing and distribution environments—such as confectionery, food, and consumer packaged goods (CPG)—order fulfillment involves complex physical and informational handoffs across supply chain echelons:

```
[Order Placement]      [Order Processing]       [Warehouse Dispatch]       [Carrier Transit]      [Customer Delivery]
      |                        |                         |                         |                       |
      v                        v                         v                         v                       v
ERP Order Entry -------> Batch Allocation ------> Pick, Pack & Stage -------> Carrier Hand-off ------> Final Destination
<---------------------------------------------------------------------------------------------------------------------->
|                       Order-to-Ship Lead Time                         |             Carrier Transit Time             |
|                                                                       |                                              |
<--------------------------------------- Total Order Fulfillment Cycle Time ------------------------------------------->
```

### 1.1 Key Terminology & Conceptual Distinctions
* **Order-to-Ship Lead Time (Fulfillment Latency):** The duration between order creation in the ERP/order system and physical departure from the facility loading dock. This measures internal warehouse efficiency, picking velocity, batching schedules, and inventory availability.
* **Transit Lead Time (Line-Haul Duration):** The elapsed time between carrier pickup and physical arrival at the customer delivery dock. This reflects carrier transit speed, road congestion, routing distance, modal characteristics, and carrier reliability.
* **Total Order Cycle Time:** The complete end-to-end duration from customer order entry to verified delivery.
* **Shipping Route / Lane:** In network modeling, a directed pair from origin node to destination node. In this project, a route is formally aggregated as:
  $$\text{Route} = \text{Factory Location} \to \text{Customer Destination State}$$
* **On-Time Delivery (OTD):** The proportion of shipments delivered on or before the customer's promised delivery date or Service Level Agreement (SLA) window.
* **On-Time In-Full (OTIF):** The proportion of orders that arrive both on time and with 100% complete product quantities, free of damage or partial line-item cancellations.

---

## 2. Core Industry Problems & Decision Space

Based on established supply chain literature ([Gunasekaran et al., 2001, 2004](https://doi.org/10.1016/j.ijpe.2003.08.003); [Mentzer & Konrad, 1991](https://doi.org/10.1002/j.2158-1592.1991.tb00002.x)) and industry benchmarks, organizations analyze route-level shipping performance to resolve seven fundamental operational problems:

### 2.1 The Seven Core Operational Problems
1. **Unidentified Regional Bottlenecks:** Distribution networks frequently experience localized delivery delays that go undetected because macro-level performance metrics (e.g., "94% overall company OTD") mask severe regional failures (e.g., 68% OTD into congested metropolitan areas).
2. **Suboptimal Factory-to-Customer Sourcing:** In multi-factory networks producing overlapping product lines, orders are often fulfilled from default or legacy production sites rather than the geographically or operationally optimal facility.
3. **Modal Inefficiencies and Uncontrolled Expedited Spend:** Shippers frequently default to expensive expedited shipping modes under the unverified assumption that it guarantees customer satisfaction, without analyzing whether expedited transit actually compresses lead times across short-haul lanes.
4. **Lead-Time Variability & Customer Dissatisfaction:** Academic research demonstrates that lead-time *unpredictability* (variance) is far more detrimental to customer retention and downstream retail replenishment than longer, predictable lead times ([Feo-Valero et al., 2013](https://doi.org/10.1016/j.tre.2012.08.005)).
5. **Static, Non-Contextual Performance Thresholds:** Rigid corporate delay definitions (e.g., "any shipment taking > 5 days is late") fail to account for modal differences, geographic distances, or seasonal demand surges.
6. **Data Silos and ERP Row Blindness:** ERP databases store millions of transactional records. Operations teams lack intuitive visual aggregation tools to convert row-level tables into spatial heatmaps, lane leaderboards, and root-cause timelines.
7. **Severe Data Quality Failures in Legacy Exports:** Enterprise systems frequently suffer from corrupted timestamps, date-epoch shifts, and key-mapping mismatches ([Hazen et al., 2014](https://doi.org/10.1016/j.ijpe.2014.04.018)), leading to misleading analytics if not intercepted by rigorous data profiling.

---

## 3. How Organizations Currently Analyze Shipping Performance

Organizations typically fall into three operational maturity tiers:

| Maturity Tier | Typical Organization | Analytical Tools | Typical Workflow | Critical Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Ad-Hoc / Reactive** | Small to mid-market distributors | Microsoft Excel, CSV exports, manual email queries | Monthly manual spreadsheet dumps; reactive investigation only when a high-value customer complains | Static, formula errors, no geographic visualization, unscalable beyond 20,000 rows, zero automation |
| **Tier 2: Standard BI** | Mid-market to upper-mid enterprise | Microsoft Power BI, Tableau, Looker | Weekly refreshed dashboards; standard KPI scorecards (Total Volume, Revenue by State, Average Lead Time) | Requires dedicated BI engineers, difficult to configure dynamic simulation ("what-if"), lacks automated statistical shrinkage on thin lanes |
| **Tier 3: Enterprise Execution & TMS** | Large multi-national enterprises | SAP TM, Oracle OTM, Blue Yonder, project44 | Real-time telematics, continuous automated re-dispatch, dynamic carrier procurement, IoT milestone tracking | Prohibitive multi-year implementation ($250k–$1M+ TCO), high complexity, black-box algorithms, overkill for mid-market post-hoc route analysis |

---

## 4. Key Metrics in Shipping Route Analytics

To provide rigorous decision support, metrics must be categorized across operational dimensions:

```
                                  LOGISTICS PERFORMANCE METRIC TAXONOMY
                                                    |
        +-----------------------+-------------------+-----------------------+-----------------------+
        |                       |                                           |                       |
        v                       v                                           v                       v
[Throughput / Volume]     [Time & Velocity]                         [Service Reliability]   [Financial & Mode]
- Total Records           - Mean Lead Time ($\mu$)                   - On-Time Delivery Rate - Freight Cost / Order
- Unique Order Count      - Median Lead Time                        - Delay Frequency (%)   - Mode Cost Ratio
- Units Shipped           - Lead-Time Standard Deviation ($\sigma$) - Buffer Penetration    - Expedited Premium %
- Weight / Cube Volume    - Interquartile Range (IQR)               - Bottleneck Priority   - Cost vs. Time Delta
```

### Mathematical Definitions:
1. **Route Lead Time ($LT_i$):**
   $$LT_i = \text{Ship Date}_i - \text{Order Date}_i \quad \text{(Fulfillment Lead Time)}$$
   $$\text{Or: } LT_i = \text{Delivery Date}_i - \text{Ship Date}_i \quad \text{(Transit Lead Time)}$$
2. **Delay Frequency / Late Shipment Rate ($DF_\theta$):**
   $$DF_\theta = \frac{\sum_{i=1}^N \mathbb{I}(LT_i > \theta)}{N} \times 100\%$$
   *Where $\theta$ is the user-configured delay threshold in days, and $\mathbb{I}(\cdot)$ is the indicator function.*
3. **Route Lead-Time Variability Index ($CV$):**
   $$CV = \frac{\sigma_{LT}}{\mu_{LT}} \quad \text{(Coefficient of Variation)}$$
   *Crucial for identifying volatile lanes with unpredictable delivery performance.*

---

## 5. Target Users and User Needs Matrix

To ensure the analytics solution addresses genuine operational workflows, user groups are analyzed below. 

> [!NOTE]
> Primary user interviews were not conducted within the current project phase. The user personas, analytical questions, and pain points documented below represent **empirically informed research hypotheses** derived from standard supply chain literature ([Gunasekaran et al., 2004](https://doi.org/10.1016/j.ijpe.2003.08.003)) and logistics case studies. They require formal validation in subsequent stakeholder reviews.

### Detailed User Group Profiles:

```
+-----------------------------------------------------------------------------------------------------------------------+
| 1. LOGISTICS & TRANSPORTATION MANAGER                                                                                 |
| Role: Oversees outbound shipping operations, carrier contract adherence, and fulfillment SLAs.                       |
| Analytical Questions:                                                                                                 |
| - Which destination states consistently violate our promised delivery windows?                                        |
| - Are our secondary production factories delivering comparable transit velocity to our primary facilities?             |
| - Which lanes exhibit high lead-time volatility, forcing our retail partners to hold excessive safety stock?          |
| Current Workflow: Reviews weekly static Excel reports generated by warehouse clerks; manual pivot tables.             |
| Likely Pain Points: Pivot tables crash with large transaction files; cannot easily see geographic distribution;      |
|                     cannot adjust delay thresholds dynamically to see impact on SLA breach rates.                     |
| Desired Dashboard Features: US choropleth map, Route leaderboard (Top 10 / Bottom 10), delay threshold slider.        |
+-----------------------------------------------------------------------------------------------------------------------+
| 2. SUPPLY CHAIN & OPERATIONS ANALYST                                                                                  |
| Role: Evaluates multi-facility network efficiency, inventory allocation, and cost-to-serve trade-offs.                |
| Analytical Questions:                                                                                                 |
| - What is the volume-performance profile of each factory-to-state corridor?                                           |
| - Are we dispatching orders from distant factories that could be served faster from nearby regional plants?           |
| - Where are the high-volume / high-delay bottleneck lanes that warrant warehouse buffer reallocations?                |
| Current Workflow: SQL queries against ERP databases, exporting to Excel/Power BI; manual chart generation.            |
| Likely Pain Points: Tedious to calculate composite performance scores; difficult to run rapid "what-if" reallocations.|
| Desired Dashboard Features: Bottleneck priority quadrant, What-if factory assignment simulator, CSV export.           |
+-----------------------------------------------------------------------------------------------------------------------+
| 3. DATA ANALYST / BI CONSULTANT                                                                                       |
| Role: Responsible for data pipeline integrity, metric accuracy, reproducible calculations, and reporting governance.   |
| Analytical Questions:                                                                                                 |
| - What percentage of records contain invalid dates, duplicate rows, or missing factory mappings?                      |
| - Are route rankings distorted by thin sample sizes ($N < 30$)?                                                       |
| - How sensitive is the Route Efficiency Score to min-max scaling outliers?                                           |
| Current Workflow: Python/Jupyter scripts, cleaning dirty CSVs, debugging data quality issues.                          |
| Likely Pain Points: Business users taking corrupted raw dates at face value; pressure to present fake accuracy.       |
| Desired Dashboard Features: Dedicated Data Quality page, sample size disclosures, explicit data provenance banners.    |
+-----------------------------------------------------------------------------------------------------------------------+
| 4. EXECUTIVE / BUSINESS STAKEHOLDER (VP of Supply Chain / General Manager)                                            |
| Role: Strategic resource allocation, customer relationship management, high-level logistics budget oversight.         |
| Analytical Questions:                                                                                                 |
| - What is our overall shipping performance trend across quarters?                                                     |
| - Are we over-spending on expedited freight without achieving tangible delivery acceleration?                         |
| - What are the top 3 geographic areas threatening our wholesale retail contracts?                                    |
| Current Workflow: Reviews 1-page executive slide decks or high-level Power BI summaries once a month.                 |
| Likely Pain Points: Overwhelmed by granular tables; lacks clear executive takeaways and actionable recommendations.   |
| Desired Dashboard Features: Executive Overview KPI cards, Standard vs Expedited cost-time trade-off chart.            |
+-----------------------------------------------------------------------------------------------------------------------+
| 5. ACADEMIC EVALUATOR & PROJECT MENTOR                                                                                |
| Role: Reviews academic rigor, statistical validity, transparency of assumptions, and student implementation.          |
| Analytical Questions:                                                                                                 |
| - Did the student protect the original raw dataset from silent alteration?                                           |
| - Are synthetic demonstrations clearly labelled and epistemologically separated from empirical facts?                 |
| - Are the analytical methods (e.g., scoring, ranking, distance) mathematically sound and justified?                   |
| Desired Dashboard Features: Strict layer labeling (Original vs Derived vs Synthetic), transparent generator settings.  |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## 6. What Data is Required for Reliable Shipping Analysis

Reliable logistics route intelligence requires four distinct data domains:

```
[Temporal Milestones]       [Spatial & Network]        [Transactional Profile]    [Operational & Carrier]
--------------------       -------------------        -----------------------    -----------------------
* Order Placement Date      * Origin Facility Lat/Lon  * Order ID & Line Item     * Carrier Identifier
* Order Release Date        * Destination State / Zip  * SKU / Product Hierarchy  * Contracted Service Level
* Warehouse Ship Date       * Route Distance (km)      * Units & Weight/Volume    * Actual Freight Invoiced
* Actual Customer Receipt   * Transit Corridor ID      * Sales & COGS             * Accessorial Surcharges
```

### Critical Gap in Nassau Candy Dataset:
* The original dataset contains `Order Date`, `Ship Date`, `Customer State`, `Customer Region`, `Product Name`, `Sales`, `Units`, `Cost`, and `Gross Profit`.
* **Missing Fields:** Actual Customer Delivery Date, Carrier Name, Package Weight, and Carrier Freight Cost (the existing `Cost` column is COGS).
* **Implication:** The analysis must focus rigorously on **Fulfillment Lead Time (Order Date to Ship Date)** and spatial routing, using the synthetic data layer to illustrate customer delivery and freight trade-offs.

---

## 7. Persistent Industry Challenges in Shipping Analytics

1. **Carrier Visibility "Blind Spots":** Mid-market shippers rarely receive automated EDI/API delivery milestone events from regional LTL carriers, resulting in post-hoc delivery date ambiguity.
2. **Confounding Network Topologies:** Comparing shipping modes across different geographic routes without controlling for distance produces the **Simpson's Paradox** of logistics: expedited shipments appearing slower simply because they are dispatched across transcontinental routes.
3. **The Small Area / Low Volume Dilemma:** Routes with 2 shipments can easily register 100% or 0% delay rates by chance, polluting executive leaderboards unless controlled by statistical shrinkage or threshold filtering.
4. **Data Governance & Migration Artifacts:** Legacy ERP migrations frequently inject corrupt date ranges (such as the 904-to-1,642 day gap observed here), requiring automated data-quality fences before analytical consumption.
