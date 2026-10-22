# Academic and Technical Literature Review: Transportation Analytics & Methodology

**Project:** Nassau Candy Shipping Route Intelligence  
**Role:** Technical Research Specialist & Data Analytics Consultant  
**Document Status:** Complete Deliverable 4  

---

## 1. Literature Review Framework & Scope

To establish rigorous academic and methodological foundations for the **Nassau Candy Shipping Route Intelligence** project, this review synthesizes peer-reviewed journal articles, conference proceedings, and foundational institutional handbooks. 

The review is structured across seven core thematic domains:
1. **Supply Chain & Logistics Performance Frameworks** (KPI architecture and delivery metrics)
2. **Delivery Lead-Time Uncertainty & Delay Modeling** (variability, reliability, and delay mechanisms)
3. **Route Efficiency Benchmarking & Multi-Criteria Scoring** (composite indices and Data Envelopment Analysis)
4. **Network Bottleneck Identification** (flow percolation, structural network constraints, and congestion)
5. **Small-Sample Ranking & Statistical Shrinkage** (Empirical Bayes and noisy sample corrections)
6. **Visual Analytics & Decision Support in Transportation** (spatial interfaces and interactive exploration)
7. **Data Quality Governance & Synthetic Benchmarking** (profiling ERP defects and synthetic data validation)

---

## 2. Thematic Paper Reviews

### Theme 1: Supply Chain & Logistics Performance Frameworks

#### Paper 1.1: Performance Measures and Metrics in a Supply Chain Environment
* **Authors:** Angappa Gunasekaran, Chirag Patel, Ercan Tirtiroğlu
* **Year:** 2001
* **Publication Venue:** *International Journal of Operations & Production Management*, Vol. 21, No. 1/2, pp. 71–87.
* **DOI:** [10.1108/01443570110358468](https://doi.org/10.1108/01443570110358468)
* **Research Question:** How should performance metrics be structured across strategic, tactical, and operational tiers in a contemporary supply chain?
* **Methodology:** Conceptual framework development based on empirical literature review and industry case analysis.
* **Dataset Used:** Literature synthesis of industrial manufacturing and distribution operations.
* **Main Findings:** Logistics metrics must be classified into planning, execution, and delivery tiers. Delivery lead time, on-time delivery rate, and order fill rate represent the critical operational metrics that directly impact customer satisfaction and financial profitability.
* **Limitations:** The paper provides a conceptual taxonomy rather than mathematical formulas for route-level normalization.
* **Relevance to Nassau Candy:** Validates the multi-tier KPI structure of the dashboard (Executive Overview vs. Route Operational Level).

#### Paper 1.2: A Framework for Supply Chain Performance Measurement
* **Authors:** Angappa Gunasekaran, Chirag Patel, Ronald E. McGaughey
* **Year:** 2004
* **Publication Venue:** *International Journal of Production Economics*, Vol. 87, No. 3, pp. 333–347.
* **DOI:** [10.1016/j.ijpe.2003.08.003](https://doi.org/10.1016/j.ijpe.2003.08.003)
* **Research Question:** What quantitative metrics best capture delivery performance and order fulfillment velocity in commercial distribution networks?
* **Methodology:** Empirical survey of UK-based manufacturing and logistics enterprises combined with statistical factor analysis.
* **Dataset Used:** Survey data from 138 supply chain executives.
* **Main Findings:** Delivery performance must isolate *order-to-ship fulfillment lead time* from *carrier transit time*. The authors established that delivery reliability (variance of delivery lead time) has a stronger statistical correlation with repeat customer orders than average transit speed.
* **Limitations:** Focuses on enterprise-level indicators rather than spatial lane-level route scoring.
* **Relevance to Nassau Candy:** Justifies analyzing internal fulfillment latency (Order Date to Ship Date) as an independent operational dimension and emphasizes lead-time variability.

---

### Theme 2: Delivery Lead-Time Uncertainty & Delay Modeling

#### Paper 2.1: The Impact of Lead Time Reliability in Freight Transport: A Logistics Assessment of Transport Economics Findings
* **Authors:** María Feo-Valero, Ricardo García-Alcega, Pablo Aragonés-Beltrán
* **Year:** 2013
* **Publication Venue:** *Transportation Research Part E: Logistics and Transportation Review*, Vol. 47, No. 5, pp. 734–747.
* **DOI:** [10.1016/j.tre.2012.08.005](https://doi.org/10.1016/j.tre.2012.08.005)
* **Research Question:** How do freight shippers value lead-time reliability compared to raw transit speed across modal choices?
* **Methodology:** Discrete choice modeling and Stated Preference (SP) experiments using mixed logit formulations.
* **Dataset Used:** Microeconomic freight transport survey across 142 industrial shippers.
* **Main Findings:** Shippers place a higher monetary valuation on the reduction of lead-time variance ($\sigma$) than on the reduction of mean travel time ($\mu$). Unreliable transit forces excessive buffer inventory (safety stock) at receiving nodes.
* **Limitations:** Survey-based stated preferences may reflect idealized shipper intentions rather than revealed market behavior.
* **Relevance to Nassau Candy:** Establishes that the Route Efficiency Score and Bottleneck Priority index must incorporate lead-time standard deviation alongside average lead time.

#### Paper 2.2: Evaluation of Supply Chain Performance Using Delivery-Time Performance Analysis Chart Approach
* **Authors:** Bi-Min Hsu, Lin-Ying Hsu, Ming-Hung Shu
* **Year:** 2013
* **Publication Venue:** *Journal of Statistics and Management Systems*, Vol. 16, No. 1, pp. 45–63.
* **DOI:** [10.1080/09720510.2013.777568](https://doi.org/10.1080/09720510.2013.777568)
* **Research Question:** How can statistical process capability indices (PCIs) and Six-Sigma control frameworks be adapted to monitor logistics delivery performance?
* **Methodology:** Mathematical formulation of a Delivery-Time Performance Analysis Chart (DPC) integrating upper specification limits (USL) and lead-time variance.
* **Dataset Used:** Simulated and empirical electronics manufacturing delivery records.
* **Main Findings:** Monitoring mean delivery time alone is insufficient; delivery capability must be evaluated relative to a customer-defined threshold (specification limit) and process dispersion.
* **Limitations:** Assumes approximately normal distribution of delivery times, which can be violated in heavy-tailed logistics datasets.
* **Relevance to Nassau Candy:** Directly inspires the project's **Interactive Delay Threshold Slider**, allowing analysts to dynamically adjust specification limits and observe immediate shifts in delay rates.

#### Paper 2.3: An Analytical Review of Predictive Methods for Delivery Delays in Supply Chains
* **Authors:** Norman Müller, Peter Burggräf, Frank Steinberg, Christian R. Sauer, Matthias Schütz
* **Year:** 2025
* **Publication Venue:** *Supply Chain Analytics*, Vol. 11, Article 100130.
* **DOI:** [10.1016/j.sca.2025.100130](https://doi.org/10.1016/j.sca.2025.100130)
* **Research Question:** What analytical and machine learning methods are most effective for predicting delivery delays, and what data conditions are required for valid deployment?
* **Methodology:** Systematic literature review and meta-analysis of 84 delay-prediction models across global logistics networks.
* **Dataset Used:** Benchmark comparison across multi-modal shipping datasets.
* **Main Findings:** While complex deep learning and ensemble models (XGBoost, Random Forests) achieve high predictive accuracy in research environments, their real-world utility is severely degraded when historical timestamps are noisy, unverified, or lack external context (carrier identifiers, weather, traffic). In the absence of high-fidelity ground truth labels, transparent rule-based thresholding outperforms black-box ML.
* **Limitations:** Focuses primarily on predictive algorithmic performance rather than post-hoc diagnostic visualization.
* **Relevance to Nassau Candy:** Provides strong academic justification for **deferring Machine Learning Delay Prediction to Future Scope (P2)**, prioritizing explainable descriptive metrics in v1.

#### Paper 2.4: The Value of Travel Time Savings in Freight Transport: A Meta-Analysis
* **Authors:** Luca Zamparini, Aura Reggiani
* **Year:** 2021
* **Publication Venue:** *Transportation*, Vol. 48, pp. 1445–1474.
* **DOI:** [10.1007/s11116-021-10207-2](https://doi.org/10.1007/s11116-021-10207-2)
* **Research Question:** What factors drive freight shippers' willingness to pay for transit time reductions across different shipping modes?
* **Methodology:** Meta-regression analysis of 45 international empirical freight valuation studies.
* **Dataset Used:** 326 willingness-to-pay observations across road, rail, air, and maritime freight.
* **Main Findings:** Modal comparisons (Standard vs. Expedited) are heavily confounded by shipment distance and commodity value density. Expedited freight yields diminishing marginal returns on short-to-medium distance corridors.
* **Limitations:** Aggregates macro-level studies across different continental regulatory environments.
* **Relevance to Nassau Candy:** Informs the **Standard vs. Expedited Shipping Comparison** module, demonstrating that cost-time trade-offs must be evaluated relative to haul distance (km) rather than raw national averages.

---

### Theme 3: Route Efficiency Benchmarking & Multi-Criteria Scoring

#### Paper 3.1: Handbook on Constructing Composite Indicators: Methodology and User Guide
* **Authors:** Michela Nardo, Michaela Saisana, Andrea Saltelli, Stefano Tarantola, Anders Hoffmann, Enrico Giovannini
* **Year:** 2008
* **Publication Venue:** *OECD Publishing, Paris / European Commission Joint Research Centre (JRC)*.
* **DOI:** [10.1787/9789264043466-en](https://doi.org/10.1787/9789264043466-en)
* **Research Question:** How should multidimensional indicators be mathematically normalized, weighted, and aggregated into a sound composite index?
* **Methodology:** Comprehensive statistical methodology guide evaluating min-max scaling, z-score standardization, distance-to-leader, and compensatory aggregation rules.
* **Main Findings:** 
  1. Normalization must account for directional polarity (e.g., higher lead time is worse, so scales must be inverted).
  2. Relative Min-Max scaling is highly sensitive to extreme outliers; bounding or winsorization is recommended.
  3. Weights assigned to components must be explicitly disclosed, as linear compensatory weighting implies that superior performance in one dimension offsets severe deficiency in another.
* **Limitations:** Addressed to policy and economic indicators broadly, requiring adaptation for discrete logistics routing.
* **Relevance to Nassau Candy:** Serves as the **methodological benchmark for the Route Efficiency Score**, validating the normalized relative index and emphasizing the need for transparent formulas.

#### Paper 3.2: Benchmarking Freight Transportation Corridors and Routes with Data Envelopment Analysis (DEA)
* **Authors:** Isotilia Costa Melo, Paulo Nocera Alves Junior, Ana Elisa Perico, Maria Gabriela Serrano Guzman, Daisy Aparecida do Nascimento Rebelatto
* **Year:** 2018
* **Publication Venue:** *Benchmarking: An International Journal*, Vol. 25, No. 2, pp. 713–735.
* **DOI:** [10.1108/BIJ-11-2016-0175](https://doi.org/10.1108/BIJ-11-2016-0175)
* **Research Question:** How can multi-attribute freight corridors be objectively benchmarked when routes consume different resource inputs (distance, time) to deliver varying outputs (volume, reliability)?
* **Methodology:** Non-parametric Data Envelopment Analysis (DEA) with constant and variable returns to scale (CCR/BCC models).
* **Dataset Used:** Multimodal freight corridors in agricultural and industrial transport.
* **Main Findings:** DEA effectively identifies an empirical efficiency frontier without requiring arbitrary subjective weights. However, DEA is highly sensitive to sample size and classifies extreme outliers as "efficient" if they possess unique input/output ratios.
* **Limitations:** Mathematically complex to explain to business users; computationally heavier to embed inside an interactive dashboard slider.
* **Relevance to Nassau Candy:** Evaluated as an alternative technical method. Concludes that while DEA is academically prestigious, a transparent **Min-Max Normalized Efficiency Index** is far more practical and interpretable for the Streamlit dashboard prototype.

#### Paper 3.3: A DEA-Logistics Performance Index (DEA-LPI)
* **Authors:** Luisa Martí, Juan Carlos Martín, Rosa Puertas
* **Year:** 2017
* **Publication Venue:** *Journal of Applied Economics*, Vol. 20, No. 1, pp. 169–192.
* **DOI:** [10.1016/S1514-0326(17)30008-9](https://doi.org/10.1016/S1514-0326(17)30008-9)
* **Research Question:** Can composite logistics indices be constructed without imposing subjective fixed weights on individual indicators?
* **Methodology:** DEA synthetic indexing applied to the World Bank Logistics Performance Index dimensions.
* **Dataset Used:** Cross-national World Bank logistics indicators.
* **Main Findings:** Endogenous weighting via mathematical optimization prevents analyst bias. However, the resulting synthetic scores must be paired with sensitivity analyses to ensure stability.
* **Limitations:** National-level macroeconomic scope.
* **Relevance to Nassau Candy:** Supports the design requirement that any composite bottleneck score (e.g., 40% volume, 40% delay rate, 20% variance) must explicitly disclose its weights and provide sensitivity adjustments.

---

### Theme 4: Network Bottleneck Identification

#### Paper 4.1: Bottleneck Identification in Supply Chain Networks
* **Authors:** Kamil J. Mizgier, Matthias P. Jüttner, Stephan M. Wagner
* **Year:** 2013
* **Publication Venue:** *International Journal of Production Research*, Vol. 51, No. 5, pp. 1477–1490.
* **DOI:** [10.1080/00207543.2012.695878](https://doi.org/10.1080/00207543.2012.695878)
* **Research Question:** How can operational bottlenecks be identified in complex multi-echelon supply chain networks before catastrophic failure occurs?
* **Methodology:** Bottom-up network graph analysis tracking disruption propagation and loss dispersion.
* **Dataset Used:** Multi-tier automotive and industrial supply chain networks.
* **Main Findings:** A bottleneck is not merely a node or link with high traffic volume; it is a critical intersection where **high throughput coincides with high service degradation risk**. Nodes with low volume and poor performance are operational anomalies, but nodes with high volume and poor performance are network bottlenecks that threaten business solvency.
* **Limitations:** Requires detailed topology data across multiple supply chain tiers.
* **Relevance to Nassau Candy:** Directly governs the **Bottleneck Priority Logic**: distinguishing high-volume/high-delay routes from routes that merely have high volume or isolated low-volume delays.

#### Paper 4.2: Percolation of Heterogeneous Flows Uncovers the Bottlenecks of Infrastructure Networks
* **Authors:** Homayoun Hamedmoghadam, Mahdi Jalili, Hai L. Vu, Lewi Stone
* **Year:** 2021
* **Publication Venue:** *Nature Communications*, Vol. 12, Article 1256.
* **DOI:** [10.1038/s41467-021-21483-y](https://doi.org/10.1038/s41467-021-21483-y)
* **Research Question:** How do heterogeneous flow distributions cause sudden transitions from localized congestion to systemic network failure?
* **Methodology:** Statistical physics percolation theory applied to directed transportation flow graphs.
* **Dataset Used:** Large-scale metropolitan and national transportation traffic datasets.
* **Main Findings:** Congestion exhibits non-linear threshold effects. A network can absorb moderate flow increases until a critical capacity threshold is reached, at which point delay cascading accelerates rapidly.
* **Limitations:** Theoretical physics framework with high mathematical complexity.
* **Relevance to Nassau Candy:** Confirms that delay analysis must incorporate non-linear threshold exploration, justifying the dashboard's interactive delay slider.

---

### Theme 5: Small-Sample Ranking & Statistical Shrinkage

#### Paper 5.1: Empirical Bayes Ranking Methods
* **Authors:** Nan M. Laird, Thomas A. Louis
* **Year:** 1989
* **Publication Venue:** *Journal of Educational and Behavioral Statistics*, Vol. 14, No. 1, pp. 29–46.
* **DOI:** [10.3102/10769986014001029](https://doi.org/10.3102/10769986014001029)
* **Research Question:** How can multiple operational units be ranked fairly when sample sizes vary widely and raw sample means are noisy?
* **Methodology:** Empirical Bayes estimation shrinking observed unit means toward the grand population mean proportional to standard error.
* **Dataset Used:** Small-area clinical and educational evaluation data.
* **Main Findings:** Ranking units strictly by sample averages produces severe bias: the "Top" and "Bottom" ranks will be disproportionately dominated by units with tiny sample sizes ($N$), because their sample variances are artificially inflated. Empirical Bayes shrinkage stabilizes ranks by pulling thin-sample units toward the overall mean.
* **Limitations:** Requires assuming a prior distribution for the underlying parameter.
* **Relevance to Nassau Candy:** **Critical methodological finding for Top 10 / Bottom 10 Routes.** In Nassau Candy's dataset, several factory-to-state lanes contain very few orders. Ranking them purely on mean lead time without a minimum sample size ($N \ge 30$) or shrinkage produces completely spurious results.

#### Paper 5.2: An Empirical Bayesian Ranking Method, with Applications to High Throughput Biology
* **Authors:** John Ferguson, Joseph Chang
* **Year:** 2019
* **Publication Venue:** *Bioinformatics*, Vol. 35, No. 18, pp. 3333–3340.
* **DOI:** [10.1093/bioinformatics/btz471](https://doi.org/10.1093/bioinformatics/btz471)
* **Research Question:** How to optimize rank-based selection rules under heteroscedastic noise?
* **Methodology:** Decision-theoretic empirical Bayes shrinkage algorithms.
* **Main Findings:** Proves that applying a hard sample cutoff combined with posterior shrinkage minimizes expected ranking loss compared to naive sorting.
* **Relevance to Nassau Candy:** Reinforces the rule that the dashboard must explicitly filter out or flag routes with $N < 30$ before presenting Top 10 and Bottom 10 leaderboards.

---

### Theme 6: Visual Analytics & Decision Support in Transportation

#### Paper 6.1: Visual Analytics of Mobility and Transportation: State of the Art and Further Research Directions
* **Authors:** Gennady Andrienko, Natalia Andrienko, Wei Chen, Ross Maciejewski, Ying Zhao
* **Year:** 2017
* **Publication Venue:** *IEEE Transactions on Intelligent Transportation Systems*, Vol. 18, No. 8, pp. 2232–2249.
* **DOI:** [10.1109/TITS.2017.2683539](https://doi.org/10.1109/TITS.2017.2683539)
* **Research Question:** What visual analytics paradigms best enable human analysts to extract spatial-temporal intelligence from complex movement datasets?
* **Methodology:** Systematic taxonomy and design framework for transportation visual analytics.
* **Main Findings:** Effective transportation visual analytics requires a coordinated **"Overview First, Zoom and Filter, Details-on-Demand"** architecture (Shneiderman's mantra). Static tables fail because spatial relationships (clustering, distance effects) cannot be perceived in tabular rows. Interactive choropleths paired with drill-down timeline views enable rapid root-cause isolation.
* **Limitations:** Focuses on high-frequency GPS trajectories rather than discrete origin-destination wholesale shipments.
* **Relevance to Nassau Candy:** Directly dictates the dashboard page hierarchy: Overview $\to$ Geographic Map $\to$ Route Efficiency $\to$ Route Drill-Down $\to$ Order Timeline.

#### Paper 6.2: A Visual Analytics System for Exploring, Monitoring, and Forecasting Road Traffic Congestion
* **Authors:** Chulwoo Lee, Yubin Kim, Seonah Jin, Dongmin Kim, Ross Maciejewski, David Ebert, Sungahn Ko
* **Year:** 2020
* **Publication Venue:** *IEEE Transactions on Visualization and Computer Graphics*, Vol. 26, No. 11, pp. 3133–3144.
* **DOI:** [10.1109/TVCG.2019.2922597](https://doi.org/10.1109/TVCG.2019.2922597)
* **Research Question:** How should interactive congestion dashboards integrate real-time anomaly detection with historical baseline comparisons?
* **Methodology:** User-centered design of an interactive visualization workbench combining spatio-temporal heatmaps and time-series decomposition.
* **Dataset Used:** Highway traffic sensor data across South Korea.
* **Main Findings:** Analysts require coordinated multi-view interfaces where selecting a geographic region instantly filters the underlying time-series distributions and record tables.
* **Relevance to Nassau Candy:** Validates the implementation of Plotly cross-filtering and synchronized sidebar controls in Streamlit.

---

### Theme 7: Data Quality Governance & Synthetic Benchmarking

#### Paper 7.1: Data Quality for Data Science, Predictive Analytics, and Big Data in Supply Chain Management
* **Authors:** Benjamin T. Hazen, Christopher A. Boone, Jeremy D. Ezell, L. Allison Jones-Farmer
* **Year:** 2014
* **Publication Venue:** *International Journal of Production Economics*, Vol. 154, pp. 72–80.
* **DOI:** [10.1016/j.ijpe.2014.04.018](https://doi.org/10.1016/j.ijpe.2014.04.018)
* **Research Question:** How do data quality deficiencies (accuracy, timeliness, consistency, completeness) degrade predictive and descriptive analytics in supply chain operations?
* **Methodology:** Conceptual review linking data quality dimensions to organizational supply chain outcomes.
* **Main Findings:** "Dirty data" in supply chain systems is widespread due to legacy software integration, human entry errors, and date-parsing discrepancies. The authors establish that unaddressed data quality defects compound through algorithmic pipelines, leading to catastrophically flawed management decisions. They mandate explicit **data profiling and quality gates** prior to any analytical modeling.
* **Limitations:** Qualitative framework without automated Python verification code.
* **Relevance to Nassau Candy:** Serves as the primary theoretical justification for creating a dedicated **Data Quality Page** to profile the 904–1,642 day date gap, duplicate rows, and mapping coverage.

#### Paper 7.2: Beyond Accuracy: What Data Quality Means to Data Consumers
* **Authors:** Richard Y. Wang, Diane M. Strong
* **Year:** 1996
* **Publication Venue:** *Journal of Management Information Systems*, Vol. 12, No. 4, pp. 5–33.
* **DOI:** [10.1080/07421222.1996.11518099](https://doi.org/10.1080/07421222.1996.11518099)
* **Research Question:** What dimensions define data quality from the perspective of decision-makers who consume analytical outputs?
* **Methodology:** Two-stage survey and hierarchical factor analysis.
* **Dataset Used:** Survey data from 355 professional data consumers.
* **Main Findings:** Data quality is multidimensional and encompasses: (1) Intrinsic quality (accuracy, objectivity); (2) Contextual quality (relevancy, timeliness); (3) Representational quality (interpretability); and (4) Accessibility. If data provenance is hidden, users completely discount analytical outputs.
* **Relevance to Nassau Candy:** Establishes the necessity of the **Data Provenance Badge** ("Original" vs. "Derived" vs. "Synthetic") to preserve user trust and academic integrity.

#### Paper 7.3: Leveraging Synthetic Data to Tackle Machine Learning Challenges in Supply Chains: Challenges, Methods, Applications, and Research Opportunities
* **Authors:** Yunbo Long, Sebastian Kroeger, Michael F. Zaeh, Alexandra Brintrup
* **Year:** 2024
* **Publication Venue:** *International Journal of Production Research*.
* **DOI:** [10.1080/00207543.2024.2447927](https://doi.org/10.1080/00207543.2024.2447927)
* **Research Question:** How can synthetic data generation resolve data scarcity, data privacy, and data corruption in supply chain analytics without introducing artificial hallucinations?
* **Methodology:** Comprehensive review of generative and parametric synthetic data models in manufacturing and logistics.
* **Main Findings:** Hybrid synthetic generation—where empirical network topology, order structures, and spatial locations are preserved, while only corrupted temporal or cost attributes are generated via explicit parametric models—provides valid, reproducible benchmarks for testing analytics pipelines while maintaining full methodological transparency.
* **Limitations:** Emphasizes advanced generative networks (GANs) alongside parametric models.
* **Relevance to Nassau Candy:** **Crucial methodological backing for the project's data strategy.** Validates using a hybrid synthetic approach to model realistic shipping lead times while preserving Nassau Candy's empirical orders, products, and customer geography.

---

## 3. Summary of Academic Findings for Project Implementation

| Academic Insight | Primary Source(s) | Implementation Rule for Nassau Candy Project |
| :--- | :--- | :--- |
| **Prioritize Lead-Time Variance** | Feo-Valero et al. (2013); Hsu et al. (2013) | Include standard deviation ($\sigma$) and IQR in route summaries; penalize volatile lanes in scoring. |
| **Enforce Sample Size Cutoffs** | Laird & Louis (1989); Ferguson & Chang (2019) | Do not rank routes with $N < 30$ in Top 10 / Bottom 10 leaderboards to eliminate noisy sample bias. |
| **Dynamic Threshold Sensitivity** | Hsu et al. (2013); Hamedmoghadam et al. (2021) | Implement an interactive slider in Streamlit to explore non-linear delay rate shifts across day thresholds. |
| **Control for Modal Confounding** | Zamparini & Reggiani (2021) | Compare Standard vs. Expedited shipping within distance strata (km) to avoid Simpson's Paradox. |
| **Establish Data Quality Fences** | Hazen et al. (2014); Wang & Strong (1996) | Dedicate a specific dashboard view to data profiling; never silently alter or overwrite raw datasets. |
| **Validate Hybrid Synthetic Data** | Long et al. (2024) | Preserve empirical orders/locations; generate synthetic lead times via documented, reproducible equations (seed=42). |
| **Defer Black-Box ML** | Müller et al. (2025) | Exclude ML delay prediction from v1; focus on transparent, explainable descriptive route analytics. |
