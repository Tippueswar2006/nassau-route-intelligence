# Technical Method Evaluation & Algorithm Comparison

**Project:** Nassau Candy Shipping Route Intelligence  
**Role:** Data Analytics Consultant & Technical Research Specialist  
**Document Status:** Complete Deliverable 5  

---

## 1. Technical Evaluation Scope

This document provides a rigorous, method-by-method evaluation of the **14 core analytical tasks** required for the Nassau Candy Shipping Route Intelligence solution. Each task is analyzed across twelve technical dimensions: business question, required inputs, recommended method, mathematical formulation, assumptions, strengths, weaknesses, data prerequisites, validation approach, visualization, implementation feasibility in the specified stack (Python, Pandas, NumPy, Plotly, Streamlit), and release priority.

---

## 2. Evaluation of the 14 Analytical Tasks

### Task 1: Factory-to-State Route Aggregation
* **Business Question:** What are the active transportation corridors connecting Nassau Candy's manufacturing facilities to customer geographic destinations?
* **Required Input Fields:** `Factory` (from product-factory mapping), `Customer State` (or `State/Province`).
* **Recommended Method:** Categorical composite key generation and multi-index group aggregation in Pandas.
* **Formula / Algorithm:**
  $$\text{Route\_Key} = \text{Factory} \mathbin{\Vert} \text{" \(\to\) "} \mathbin{\Vert} \text{Customer\_State}$$
  $$\text{Groupby}(\text{Route\_Key}).\text{agg}(\{\text{Order\_ID}: \text{nunique}, \text{Units}: \text{sum}, \dots\})$$
* **Assumptions:** Each product maps unambiguously to a single primary production factory; customer states are standardized two-letter FIPS codes.
* **Strengths:** Intuitive, computationally trivial ($O(N)$ hash-table grouping), forms the atomic unit for all downstream route metrics.
* **Weaknesses:** Masks intra-state geographic dispersion (e.g., shipping to Buffalo vs. NYC within New York State).
* **Data Requirements:** Clean factory lookup table, valid customer state column.
* **Validation Method:** Check that the sum of route order volumes reconciles exactly to total unique orders in the filtered dataset.
* **Suitable Visualization:** Interactive Plotly data table with search and column sorting.
* **Stack Feasibility:** Fully supported in Pandas and Streamlit.
* **Version Priority:** **Must Have (P0)**.

---

### Task 2: Shipment Volume Measurement
* **Business Question:** How much physical demand and transaction volume flows through each facility, state, and route?
* **Required Input Fields:** `Order ID`, `Units`, `Sales`, `Row Index`.
* **Recommended Method:** Dual-metric measurement: Distinct Order Count ($N_{\text{orders}} = |\text{unique}(\text{Order ID})|$) alongside Total Units Shipped ($\sum \text{Units}$).
* **Formula / Algorithm:**
  $$\text{Order\_Volume} = \text{len}(\text{df}[\text{'Order ID'}].\text{unique}())$$
  $$\text{Physical\_Volume} = \sum_{i=1}^n \text{Units}_i$$
* **Assumptions:** Single orders spanning multiple product lines share the same Order ID; duplicate rows are filtered prior to counting.
* **Strengths:** Distinguishes transaction velocity (number of shipments) from physical payload volume (units handled).
* **Weaknesses:** Lacks volumetric weight (cube) or pallet counts, which are the true physical drivers of freight capacity.
* **Data Requirements:** Order ID, Units.
* **Validation Method:** Assert that sum of units grouped by factory equals total dataset units.
* **Suitable Visualization:** Plotly horizontal bar charts (Top 15 volume states/routes), Streamlit KPI metric cards.
* **Stack Feasibility:** Fully supported in Pandas/Plotly/Streamlit.
* **Version Priority:** **Must Have (P0)**.

---

### Task 3: Lead-Time Calculation
* **Business Question:** How long does it take for an order to move from customer order placement to warehouse dispatch (and customer delivery)?
* **Required Input Fields:** `Order Date`, `Ship Date` (Original and Synthetic), `Delivery Date` (Synthetic).
* **Recommended Method:** Datetime difference conversion to integer days:
  $$LT_{\text{fulfillment}} = (\text{Ship Date} - \text{Order Date}).\text{dt.days}$$
  $$LT_{\text{transit}} = (\text{Delivery Date} - \text{Ship Date}).\text{dt.days}$$
* **Assumptions:** Order Date occurs on or before Ship Date ($LT \ge 0$). In the original dataset, this assumption holds chronologically, but the magnitude (904–1,642 days) is an operational impossibility.
* **Strengths:** Direct, interpretable measurement in calendar days.
* **Weaknesses:** Does not account for warehouse working days versus weekends/holidays unless paired with a custom business-day calendar (`numpy.busday_count`).
* **Data Requirements:** Valid ISO datetime timestamps.
* **Validation Method:** Assert $\min(LT) \ge 0$. Profile original data to expose the 904–1,642 day defect; validate synthetic data adheres to realistic 1–10 day bounds.
* **Suitable Visualization:** Plotly histogram / KDE distribution plot with vertical mean and median markers.
* **Stack Feasibility:** Vectorized in Pandas/NumPy.
* **Version Priority:** **Must Have (P0)**.

---

### Task 4: Delay-Rate Calculation
* **Business Question:** What percentage of shipments on a given route fail to meet promised delivery schedules or operational thresholds?
* **Required Input Fields:** `Lead Time Days`, `Promised Delivery Date` (or user threshold $\theta$).
* **Recommended Method:** Indicator step function aggregated over route volume:
  $$\text{Delay Rate}_r(\theta) = \frac{1}{N_r} \sum_{i=1}^{N_r} \mathbb{I}(LT_i > \theta) \times 100\%$$
* **Alternative Method:** SLA-based delay calculation: $\mathbb{I}(\text{Actual Delivery Date}_i > \text{Promised Date}_i)$.
* **Comparison & Rationale:** The slider-based threshold ($\theta$) is superior for exploratory analytics because contractual promised dates are missing from the raw file and vary across modes.
* **Assumptions:** All orders within a route cohort are evaluated against the active threshold.
* **Strengths:** Highly sensitive to operational bottlenecks; directly intuitive to business executives.
* **Weaknesses:** A route taking 6 days against a 5-day threshold receives the same binary penalty as a route taking 20 days.
* **Data Requirements:** Computed lead-time field, user threshold parameter.
* **Validation Method:** Verify $0\% \le \text{Delay Rate} \le 100\%$.
* **Suitable Visualization:** Plotly gauge charts, color-coded table cells, bar charts.
* **Stack Feasibility:** Vectorized in Pandas; fully reactive in Streamlit.
* **Version Priority:** **Must Have (P0)**.

---

### Task 5: Route Efficiency Scoring
* **Business Question:** How can multiple route attributes (speed, reliability, volume) be aggregated into a single, standardized benchmark score to compare lanes objectively?
* **Required Input Fields:** Average Lead Time ($\mu_r$), Lead Time Standard Deviation ($\sigma_r$), Delay Rate ($DR_r$), Sample Size ($N_r$).
* **Method Comparison:**
  1. *Option A: Simple Min-Max Lead-Time Scaling (PRD v0.2 Baseline):*
     $$\text{Score}_r = 100 \times \left(1 - \frac{\mu_r - \min(\mu)}{\max(\mu) - \min(\mu)}\right)$$
  2. *Option B: Z-Score Standardization:*
     $$Z_r = -\frac{\mu_r - \bar{\mu}}{\sigma_\mu}$$
  3. *Option C: Multi-Attribute Composite Index (Recommended by OECD 2008 Framework):*
     $$\text{RES}_r = 100 \times \left[ w_1 \cdot \left(1 - \frac{\mu_r - \mu_{\min}}{\mu_{\max} - \mu_{\min}}\right) + w_2 \cdot \left(1 - \frac{\sigma_r - \sigma_{\min}}{\sigma_{\max} - \sigma_{\min}}\right) + w_3 \cdot (1 - DR_r) \right]$$
     *Recommended Weights:* $w_1 = 0.50$ (Lead Time), $w_2 = 0.30$ (Variability), $w_3 = 0.20$ (Delay Rate).
  4. *Option D: Data Envelopment Analysis (DEA):* Non-parametric frontier optimization.
* **Method Rationale & Trade-offs:** Option A ignores variability. Option D is black-box and unstable on small samples. Option C (Multi-Attribute Composite Index) is recommended because logistics research ([Feo-Valero et al., 2013](https://doi.org/10.1016/j.tre.2012.08.005)) proves that variability ($\sigma$) is vital to customer service.
* **Assumptions:** Linear compensatory trade-off between speed and variability; cohort minimum sample filter ($N_r \ge 30$) applied first.
* **Strengths:** Produces an intuitive 0–100 score; rewards both fast and predictable lanes.
* **Weaknesses:** Relative cohort score shifts if underlying filters change; weights must be transparently disclosed.
* **Data Requirements:** Route-aggregated statistics.
* **Validation Method:** Confirm best-performing route receives score near 100, worst near 0.
* **Suitable Visualization:** Ranked leaderboard bar chart with color gradient (Green to Red).
* **Stack Feasibility:** Vectorized in NumPy/Pandas.
* **Version Priority:** **Must Have (P0)**.

---

### Task 6: Top 10 and Bottom 10 Route Ranking
* **Business Question:** Which shipping routes are the top performers, and which are the most severely degraded lanes requiring executive intervention?
* **Required Input Fields:** Route Efficiency Score, Route Order Volume ($N_r$).
* **Recommended Method:** Constrained Sorting with Hard Minimum Sample Cutoff ($N \ge 30$):
  $$\text{Eligible Routes} = \{r \in \mathcal{R} \mid N_r \ge 30\}$$
  $$\text{Top 10} = \text{sort\_descending}(\text{RES}_r)[:10], \quad \text{Bottom 10} = \text{sort\_ascending}(\text{RES}_r)[:10]$$
* **Statistical Rigor (Handling Small Samples):** Ranking unconstrained routes causes the **Small Area Problem** ([Laird & Louis, 1989](https://doi.org/10.3102/10769986014001029)), where lanes with 2 or 3 orders register extreme averages (1.0 days or 15.0 days) purely due to random variance. Filtering by $N \ge 30$ eliminates spurious noise.
* **Assumptions:** 30 orders provides sufficient statistical stability under the Central Limit Theorem.
* **Strengths:** Protects executive attention from chasing statistical phantoms.
* **Weaknesses:** Excludes low-volume emerging routes from the leaderboard (must be viewed in a separate "Low-Volume Audit" tab).
* **Data Requirements:** Grouped route dataframe.
* **Validation Method:** Ensure no route in Top 10 or Bottom 10 has $N < 30$.
* **Suitable Visualization:** Split side-by-side horizontal bar charts in Streamlit (`st.columns(2)`).
* **Stack Feasibility:** Pandas `nlargest()` / `nsmallest()`.
* **Version Priority:** **Must Have (P0)**.

---

### Task 7: Configurable Delay Thresholds
* **Business Question:** How does the organization's SLA compliance rate change if the delivery standard is tightened or relaxed?
* **Required Input Fields:** Lead Time series, Streamlit slider value $\theta \in [1, 15]$.
* **Recommended Method:** Reactive dynamic thresholding in memory.
* **Formula:**
  $$\text{Late Flag}_i = \text{Lead Time}_i > \theta$$
* **Assumptions:** In-memory recalculation is fast enough for 10,000 records to provide instant UI responsiveness (<100 ms).
* **Strengths:** Empowers non-technical managers to conduct sensitivity analysis without editing code.
* **Weaknesses:** Threshold is uniform across modes unless stratified by mode.
* **Data Requirements:** Numeric lead time column.
* **Validation Method:** Verify that as $\theta \to \infty$, Delay Rate $\to 0\%$; as $\theta \to 0$, Delay Rate $\to 100\%$.
* **Suitable Visualization:** Streamlit `st.slider` in sidebar, linked to KPI delta cards and histogram threshold vertical line.
* **Stack Feasibility:** Native Streamlit reactive state.
* **Version Priority:** **Must Have (P0)**.

---

### Task 8: Geographic Heatmaps
* **Business Question:** How does shipping performance and volume vary across the United States geographically?
* **Required Input Fields:** `Customer State` (2-letter postal code), Metric to plot (e.g., Delay Rate %, Volume, Average Lead Time).
* **Recommended Method:** Plotly Express Choropleth Map using US State boundaries (`locationmode='USA-states'`).
* **Formula / Configuration:**
  ```python
  fig = px.choropleth(
      state_df,
      locations="State_Code",
      locationmode="USA-states",
      color="Delay_Rate",
      scope="usa",
      color_continuous_scale="Reds",
  )
```
* **Handling Non-Contiguous States:** Alaska (AK) and Hawaii (HI) have longer maritime/air transit lead times; choropleth displays them in standard inset boxes.
* **Assumptions:** State-level aggregation is representative of delivery conditions across the state.
* **Strengths:** Instant spatial pattern recognition (e.g., identifying Pacific Northwest or Midwest congestion clusters).
* **Weaknesses:** Choropleth maps suffer from area bias (large geographic states like Montana dominate visually despite low population/volume).
* **Data Requirements:** Clean 2-letter state abbreviations.
* **Validation Method:** Check that all 50 states + DC map properly without unrecognized location errors.
* **Suitable Visualization:** Interactive Plotly Choropleth with hover tooltips showing State Name, Volume, Lead Time, and Delay Rate.
* **Stack Feasibility:** Plotly Express / Streamlit `st.plotly_chart`.
* **Version Priority:** **Should Have (P1)**.

---

### Task 9: Standard vs. Expedited Shipping Comparisons
* **Business Question:** Does paying for expedited shipping actually deliver faster and more reliable delivery, or is freight spend being wasted?
* **Required Input Fields:** `Ship Mode`, `Lead Time Days`, `Distance km`, `Shipping Cost` (Synthetic).
* **Methodological Challenge (Confounder Control):** Directly comparing mean lead times between Standard and Expedited modes is vulnerable to **Simpson's Paradox**. If Expedited shipping is disproportionately chosen for transcontinental shipments (e.g., NY to California, 4,000 km), raw lead times may appear equal to or slower than Standard shipping used for local regional deliveries (e.g., NY to NJ, 150 km).
* **Recommended Method:** Stratified Modal Comparison controlling for Haversine Distance:
  $$\text{Distance Buckets} = [0\text{–}500\text{ km}], [500\text{–}1500\text{ km}], [1500\text{–}3000\text{ km}], [3000+\text{ km}]$$
  $$\Delta LT_b = \mu_{LT}(\text{Standard}, b) - \mu_{LT}(\text{Expedited}, b)$$
* **Assumptions:** Shipping mode definitions are consistent; synthetic cost data reflects realistic modal surcharges.
* **Strengths:** Prevents false management conclusions regarding carrier performance.
* **Weaknesses:** Requires geographic coordinates to compute lane distances.
* **Data Requirements:** Ship Mode, Lead Time, Factory/Customer coordinates.
* **Validation Method:** Ensure stratified comparisons show $\Delta LT_b > 0$ across all distance strata.
* **Suitable Visualization:** Plotly grouped box plot (Lead Time distribution by Mode) and scatter plot (Lead Time vs. Distance colored by Mode).
* **Stack Feasibility:** Pandas/Plotly/Streamlit.
* **Version Priority:** **Should Have (P1)**.

---

### Task 10: Bottleneck Prioritization
* **Business Question:** Which specific factory-to-state lanes represent the greatest operational threat to company service levels?
* **Required Input Fields:** Route Volume ($N_r$), Delay Rate ($DR_r$), Lead-Time Standard Deviation ($\sigma_r$).
* **Recommended Method:** Multi-Criteria Bottleneck Priority Quadrant & Composite Rank:
  $$\text{BPI}_r = 0.40 \times \text{Norm}(N_r) + 0.40 \times \text{Norm}(DR_r) + 0.20 \times \text{Norm}(\sigma_r)$$
  $$\text{Where: } \text{Norm}(X) = \frac{X - X_{\min}}{X_{\max} - X_{\min}}$$
* **Quadrant Logic:**
  * *Quadrant I (High Volume, High Delay):* **CRITICAL BOTTLENECK** (Immediate operational intervention required).
  * *Quadrant II (Low Volume, High Delay):* **Operational Anomaly** (Monitor; investigate specific carrier or weather).
  * *Quadrant III (Low Volume, Low Delay):* **Low Priority** (Stable niche lane).
  * *Quadrant IV (High Volume, Low Delay):* **Core Star Corridor** (Benchmark lane; model practices elsewhere).
* **Assumptions:** Volume weighting ensures executive resources focus where customer impact is highest.
* **Strengths:** Explicitly separates high-volume bottlenecks from isolated anomalies ([Mizgier et al., 2013](https://doi.org/10.1080/00207543.2012.695878)).
* **Weaknesses:** Linear weights are subjective and require documentation.
* **Data Requirements:** Clean aggregated route dataframe ($N \ge 30$).
* **Validation Method:** Verify that top-flagged bottleneck lanes have both above-average volume and above-average delay rates.
* **Suitable Visualization:** Plotly interactive scatter plot (X = Volume, Y = Delay Rate %, Bubble Size = Lead Time Variance, colored by Quadrant) with quadrant reference lines.
* **Stack Feasibility:** Plotly/Streamlit.
* **Version Priority:** **Should Have (P1)**.

---

### Task 11: Order-Level Shipment Timeline Drill-Down
* **Business Question:** What happened during the lifecycle of an individual delayed order, and why was it flagged?
* **Required Input Fields:** `Order ID`, `Order Date`, `Ship Date`, `Promised Date`, `Customer State`, `Product Name`, `Sales`.
* **Recommended Method:** Filtered master-detail drill-down view with interactive timeline bar/scatter.
* **Assumptions:** Order ID uniquely identifies order records.
* **Strengths:** Provides auditability, bridging high-level executive summaries with micro-level operational records.
* **Weaknesses:** Displaying 10,000 individual timeline bars would crash browser DOM; requires pre-filtering by State/Route first.
* **Data Requirements:** Order-level transactional table.
* **Validation Method:** Selected order details match raw source row exactly.
* **Suitable Visualization:** Expandable Streamlit container (`st.expander`), Plotly milestone timeline (Gantt-style), formatted data table.
* **Stack Feasibility:** Streamlit dataframe with pagination.
* **Version Priority:** **Should Have (P1)**.

---

### Task 12: Monthly Trend Analysis & Seasonality
* **Business Question:** Are shipping volumes, lead times, and delay rates improving over time, and do fourth-quarter holiday surges create seasonal bottlenecks?
* **Required Input Fields:** `Order Date` (Year-Month period), `Lead Time Days`, `Order Volume`.
* **Recommended Method:** Resampled monthly time-series aggregation:
  $$\text{df}.\text{groupby}(\text{df}[\text{'Order Date'}].\text{dt.to\_period}(\text{'M'})).\text{agg}(\{\dots\})$$
* **Assumptions:** Date ranges span at least 12–24 continuous months.
* **Strengths:** Identifies macro seasonality (e.g., confectionery demand peaks in October–December for Halloween/Christmas).
* **Weaknesses:** If original dates are distorted, monthly trends in the raw file reflect export batching artifacts rather than real seasonal demand.
* **Data Requirements:** Validated monthly datetime index.
* **Validation Method:** Ensure monthly volume sums equal annual totals.
* **Suitable Visualization:** Plotly dual-axis line/bar chart (Bars = Monthly Volume, Line = Average Lead Time / Delay Rate).
* **Stack Feasibility:** Pandas time-series / Plotly.
* **Version Priority:** **Should Have (P1)**.

---

### Task 13: What-If Factory Assignment Simulation
* **Business Question:** What would happen to lead times and transportation distance if customer orders in a delayed state were fulfilled from an alternate factory?
* **Required Input Fields:** Factory coordinates, Customer state centroids, Haversine distance function, Lead-time model.
* **Recommended Method:** Centroid Distance Reallocation Simulation:
  1. User selects Customer State (e.g., "Texas") and Alternate Factory (e.g., "Factory B" instead of "Factory A").
  2. Compute new Haversine distance:
     $$d = 2R \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)} \right)$$
  3. Recompute simulated lead time using distance coefficient ($\beta \approx +0.5\text{ days} / 1000\text{ km}$).
  4. Compare baseline lead time versus simulated lead time.
* **Methodological Disclaimer:** Must be prominently labelled as an **Illustrative Centroid Heuristic Simulation**, NOT an operational optimization model, because it does not model factory machine capacities, inventory stockouts, or production line constraints.
* **Assumptions:** Alternate factory has inventory availability and physical capacity to produce the required SKUs.
* **Strengths:** Highly engaging decision-support demonstration for academic evaluation.
* **Weaknesses:** Simplified heuristic; ignores production capacity constraints.
* **Data Requirements:** Factory Lat/Lon, State Centroid Lat/Lon, Haversine formula.
* **Validation Method:** If alternate factory is closer, distance and simulated lead time must decrease monotonically.
* **Suitable Visualization:** Before/After Plotly metric delta cards, comparative bar chart.
* **Stack Feasibility:** Vectorized NumPy math in Streamlit.
* **Version Priority:** **Should Have (P1)**.

---

### Task 14: Data Quality Monitoring & Profiling
* **Business Question:** What data integrity risks, date anomalies, duplicates, and unmapped records exist in the source dataset?
* **Required Input Fields:** All columns in the raw uploaded file, Product-to-Factory mapping table.
* **Recommended Method:** Automated multi-check data profiling pipeline:
  1. *Schema Validation:* Check presence of required columns and expected dtypes.
  2. *Duplicate Profiling:* Identify exact row duplicates ($\text{df}.\text{duplicated}()$).
  3. *Date Interval Anomaly Profiling:* Compute $\Delta T = \text{Ship Date} - \text{Order Date}$; flag rows where $\Delta T < 0$ or $\Delta T > 30\text{ days}$.
  4. *Mapping Coverage:* Left-join products against factory mapping table; compute unmatched product percentage:
     $$\text{Coverage Rate} = \frac{|\text{Mapped Products}|}{|\text{Total Distinct Products}|} \times 100\%$$
* **Assumptions:** Data quality rules are deterministic and run on file upload.
* **Strengths:** Establishes complete methodological honesty; prevents garbage-in, garbage-out analytics.
* **Weaknesses:** None; foundational to academic integrity.
* **Data Requirements:** Raw uncleaned dataset.
* **Validation Method:** Unit tests verifying known duplicate count (313 rows) and date anomaly bounds (904–1,642 days).
* **Suitable Visualization:** Streamlit metric tiles, alert banners (`st.error`, `st.warning`), downloadable CSV of flagged records.
* **Stack Feasibility:** Pure Python / Pandas.
* **Version Priority:** **Must Have (P0)**.

---

## 3. Summary Priority Matrix across All 14 Tasks

| Task ID | Analytical Task Name | Recommended Algorithm | Stack Support | Initial Version Priority |
| :---: | :--- | :--- | :---: | :---: |
| **01** | Factory-to-State Aggregation | Multi-index composite key hash grouping | Pandas | **Must Have (P0)** |
| **02** | Shipment Volume Measurement | Unique order count + physical units sum | Pandas | **Must Have (P0)** |
| **03** | Lead-Time Calculation | Datetime difference in calendar days | Pandas/NumPy | **Must Have (P0)** |
| **04** | Delay-Rate Calculation | Step indicator against threshold $\theta$ | Pandas/NumPy | **Must Have (P0)** |
| **05** | Route Efficiency Scoring | Multi-attribute min-max normalized index | NumPy | **Must Have (P0)** |
| **06** | Top 10 & Bottom 10 Ranking | Sample-size constrained sorting ($N \ge 30$) | Pandas | **Must Have (P0)** |
| **07** | Configurable Delay Thresholds | Reactive slider with dynamic recalculation | Streamlit | **Must Have (P0)** |
| **08** | Geographic Heatmaps | US State Choropleth (`locationmode='USA-states'`) | Plotly | **Should Have (P1)** |
| **09** | Standard vs. Expedited Analysis | Distance-stratified box plots (anti-Simpson's) | Plotly | **Should Have (P1)** |
| **10** | Bottleneck Prioritization | Multi-criteria priority score & 4-quadrant scatter | Plotly | **Should Have (P1)** |
| **11** | Order-Level Drill-Down | Filtered master-detail timeline / table drawer | Streamlit | **Should Have (P1)** |
| **12** | Monthly Trend & Seasonality | Resampled monthly time series decomposition | Pandas/Plotly | **Should Have (P1)** |
| **13** | What-If Factory Simulation | Haversine centroid distance reallocation | NumPy | **Should Have (P1)** |
| **14** | Data Quality Profiling | Automated anomaly, duplicate, and mapping gates | Pandas | **Must Have (P0)** |
