---
title: 'Story 2.1: Customer Shipment Grouping & Multi-Scenario Synthetic Lead Time Generator'
type: 'feature'
created: '10-20-2026'
status: 'done'
baseline_commit: 'NO_VCS'
epic: 2
story: 1
story_key: '2-1-customer-shipment-grouping-and-synthetic-lead-time-generator'
context:
  - 'config/generator.yaml'
  - 'src/config.py'
---

# Story 2.1: Customer Shipment Grouping & Multi-Scenario Synthetic Lead Time Generator

## Intent
**Problem:** Raw shipping dates are invalid export artifacts (904–1,642 days). Demonstrating route analytics requires realistic, reproducible, distance-sensitive, and stress-tested synthetic order-to-ship lead times at the true shipment grain `(Customer ID, Order Date, Ship Mode)`.
**Approach:** Implement `src/generate_synthetic.py` grouping order lines into 5,067 customer shipments, applying empirical distributions for Baseline, distance sensitivity ($0.5\text{d} / 1000\text{km}$), and unclipped Stress-Test injections with seed 42.

## User Story
As a simulation modeler,
I want to generate synthetic lead times at the customer-shipment grain `(Customer ID, Order Date, Ship Mode)` across Baseline, Distance-Sensitive, and Stress-Test scenarios using fixed seed 42,
So that all order lines in the same physical shipment share identical lead times while testing network stress conditions without clipping delays.

## Acceptance Criteria
- **Given** the deduplicated mapped dataset,
- **When** `src/generate_synthetic.py` groups lines into customer shipments,
- **Then** exactly 5,067 customer shipments are formed,
- **And** all order lines within each shipment receive the identical simulated lead time,
- **And** **Baseline scenario** samples empirical distributions per mode from `config/generator.yaml` bounded in $[0, 2]$ for Same Day and $[1, 14]$ for others,
- **And** **Distance-Sensitive scenario** applies $0.5 \times (\text{Distance\_km} - \mu_{\text{dist}}) / 1000$ days to Baseline, bounded in $[0, 2]$ for Same Day and $[1, 14]$ for others,
- **And** **Stress-Test scenario** applies base bounds *before* adding injections (+1.0d peak season in Nov/Dec, +1.0d California/New York, +1.5d Lot's O' Nuts -> Texas, +1.5d Wicked Choccy's -> Texas) and enforces expanded bounds ($[0, 6]$ for Same Day, $[1, 20]$ for others) so that injected delays are not clipped,
- **And** synthetic lead times are non-negative and labeled as simulated data.

## Implementation Details & Boundaries
- Target module: `src/generate_synthetic.py`
- Must NOT import Streamlit.
- Must use NumPy random generator with seed 42.
- Functions:
  - `group_into_customer_shipments(df: pd.DataFrame) -> pd.DataFrame`
  - `sample_empirical_lead_times(shipments: pd.DataFrame, rng: np.random.Generator) -> np.ndarray`
  - `generate_baseline_scenario(shipments: pd.DataFrame, seed: int = 42) -> pd.DataFrame`
  - `generate_distance_scenario(baseline_df: pd.DataFrame) -> pd.DataFrame`
  - `generate_stress_scenario(distance_df: pd.DataFrame) -> pd.DataFrame`
  - `generate_all_scenarios(df: pd.DataFrame, seed: int = 42) -> Dict[str, pd.DataFrame]`
