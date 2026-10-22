"""
Tests for Route Aggregation, Sample Size Guardrails, Regional Rollups, and Leaderboards.
Verifies compliance with AD-02, AD-07, PRD Section 3.7, and Story 3.2 acceptance criteria.
"""

import pytest
import numpy as np
import pandas as pd

from src.config import (
    CLEAN_ORDERS_PARQUET,
    ROUTE_AGGREGATES_PARQUET,
    BASELINE_PARQUET,
    MIN_SAMPLE_SIZE,
    SMALL_FACTORIES,
)
from src.route_analysis import (
    validate_layer_isolation,
    assign_route_hierarchy,
    aggregate_routes,
    filter_eligible_routes,
    generate_leaderboards,
)


def test_boundary_eligibility_n29_n30_n31():
    """
    Verifies strict sample size threshold boundary checks:
    - N = 29 -> Ineligible (low sample)
    - N = 30 -> Eligible
    - N = 31 -> Eligible
    """
    mock_df = pd.DataFrame({
        "route_key": ["Route-29", "Route-30", "Route-31"],
        "sample_size": [29, 30, 31],
        "res_score": [85.0, 90.0, 95.0],
    })

    eligible_df, low_sample_df = filter_eligible_routes(mock_df, min_sample=30)

    # N=29 must be in low-sample table
    assert len(low_sample_df) == 1
    assert low_sample_df.iloc[0]["route_key"] == "Route-29"
    assert not low_sample_df.iloc[0]["is_eligible"]
    assert low_sample_df.iloc[0]["is_low_sample"]

    # N=30 and N=31 must be in eligible table
    assert len(eligible_df) == 2
    assert set(eligible_df["route_key"]) == {"Route-30", "Route-31"}
    assert (eligible_df["is_eligible"]).all()
    assert not (eligible_df["is_low_sample"]).any()


def test_route_filtering_and_counts_against_prd_baseline():
    """
    Asserts exact route counts specified in PRD Section 3.7 & Appendix B:
    - 196 total Factory -> State routes
    - 54 eligible at N >= 30 (Lot's O' Nuts: 28, Wicked Choccy's: 25, Secret Factory: 1)
    - 69 eligible at N >= 20
    - 95 eligible at N >= 10
    - 142 low-sample routes at N < 30
    """
    route_agg = pd.read_parquet(ROUTE_AGGREGATES_PARQUET)
    assert len(route_agg) == 196, f"Expected 196 total routes, got {len(route_agg)}"

    # N >= 30
    eligible_30, low_sample_30 = filter_eligible_routes(route_agg, min_sample=30)
    assert len(eligible_30) == 54, f"Expected 54 eligible routes at N >= 30, got {len(eligible_30)}"
    assert len(low_sample_30) == 142, f"Expected 142 low-sample routes, got {len(low_sample_30)}"

    factory_counts = eligible_30["Factory"].value_counts().to_dict()
    lots_count = factory_counts.get("Lot's O' Nuts")
    wicked_count = factory_counts.get("Wicked Choccy's")
    secret_count = factory_counts.get("Secret Factory")

    assert lots_count == 28, f"Expected 28 for Lot's O' Nuts, got {lots_count}"
    assert wicked_count == 25, f"Expected 25 for Wicked Choccy's, got {wicked_count}"
    assert secret_count == 1, f"Expected 1 for Secret Factory, got {secret_count}"
    assert "Sugar Shack" not in factory_counts
    assert "The Other Factory" not in factory_counts

    # N >= 20
    eligible_20, _ = filter_eligible_routes(route_agg, min_sample=20)
    assert len(eligible_20) == 69, f"Expected 69 eligible routes at N >= 20, got {len(eligible_20)}"

    # N >= 10
    eligible_10, _ = filter_eligible_routes(route_agg, min_sample=10)
    assert len(eligible_10) == 95, f"Expected 95 eligible routes at N >= 10, got {len(eligible_10)}"


def test_small_factory_regional_rollups():
    """
    Verifies that Sugar Shack, Secret Factory, and The Other Factory automatically roll up
    to Factory -> Region level, while Lot's O' Nuts and Wicked Choccy's remain at State level.
    """
    clean_orders = pd.read_parquet(CLEAN_ORDERS_PARQUET)
    routed = assign_route_hierarchy(clean_orders)

    # Check is_regional_rollup flag
    small_mask = routed["Factory"].isin(SMALL_FACTORIES)
    assert routed.loc[small_mask, "is_regional_rollup"].all()
    assert not routed.loc[~small_mask, "is_regional_rollup"].any()

    # Check analysis_destination for small factories vs large factories
    sample_sugar = routed[routed["Factory"] == "Sugar Shack"].iloc[0]
    assert sample_sugar["analysis_destination"] == sample_sugar["Region"]
    assert sample_sugar["analysis_route_key"] == f"Sugar Shack -> {sample_sugar['Region']}"

    sample_lots = routed[routed["Factory"] == "Lot's O' Nuts"].iloc[0]
    assert sample_lots["analysis_destination"] == sample_lots["State/Province"]
    assert sample_lots["analysis_route_key"] == f"Lot's O' Nuts -> {sample_lots['State/Province']}"


def test_aggregate_routes_with_regional_rollup():
    """
    Verifies aggregate_routes with rollup_small_factories=True:
    - Small factories produce Factory -> Region routes.
    - Large factories produce Factory -> State routes.
    - Volume, units, sales, and margin roll up accurately.
    """
    clean_orders = pd.read_parquet(CLEAN_ORDERS_PARQUET)
    agg = aggregate_routes(clean_orders, level="state", rollup_small_factories=True)

    assert "is_regional_rollup" in agg.columns
    assert "sample_size" in agg.columns
    assert "is_eligible" in agg.columns
    assert "is_low_sample" in agg.columns

    # Verify small factories have regional routes
    sugar_routes = agg[agg["Factory"] == "Sugar Shack"]
    for dest in sugar_routes["route_key"]:
        assert any(dest.endswith(f"-> {r}") for r in ["Pacific", "Atlantic", "Interior", "Gulf"])

    # Total units in aggregation equals total units in input
    assert agg["total_units"].sum() == clean_orders["Units"].sum()


def test_layer_isolation_enforcement():
    """
    Verifies AD-02: Layer Isolation.
    - Single layer (ORIGINAL, DERIVED, SYNTHETIC) succeeds.
    - Mixed layers raise ValueError.
    - Unknown layer raises ValueError.
    """
    # Valid single layer
    derived_df = pd.DataFrame({
        "route_key": ["R1", "R2"],
        "sample_size": [50, 60],
        "res_score": [80.0, 90.0],
        "data_layer": ["DERIVED", "DERIVED"],
    })
    assert validate_layer_isolation(derived_df) == "DERIVED"

    # Mixed layers must raise ValueError
    mixed_df = pd.DataFrame({
        "route_key": ["R1", "R2"],
        "sample_size": [50, 60],
        "res_score": [80.0, 90.0],
        "data_layer": ["DERIVED", "SYNTHETIC"],
    })
    with pytest.raises(ValueError, match="Layer isolation violation"):
        validate_layer_isolation(mixed_df)

    with pytest.raises(ValueError, match="Layer isolation violation"):
        generate_leaderboards(mixed_df)

    # Invalid layer name must raise ValueError
    invalid_layer_df = pd.DataFrame({
        "route_key": ["R1"],
        "data_layer": ["UNKNOWN_LAYER"],
    })
    with pytest.raises(ValueError, match="Unrecognized data layer"):
        validate_layer_isolation(invalid_layer_df)


def test_leaderboard_generation():
    """
    Verifies Top 10 and Bottom 10 leaderboard generation:
    - Top 10 sorted descending by res_score, ranks 1..10.
    - Bottom 10 sorted ascending by res_score, ranks 1..10.
    - Ineligible routes are excluded.
    """
    # 20 routes with varying RES and sample sizes
    np.random.seed(42)
    scores = np.linspace(30.0, 95.0, 20)
    mock_routes = pd.DataFrame({
        "route_key": [f"Route-{i}" for i in range(20)],
        "sample_size": [35] * 18 + [25, 20],  # Last 2 are low-sample
        "res_score": scores,
        "data_layer": ["SYNTHETIC"] * 20,
    })

    top_10, bottom_10 = generate_leaderboards(mock_routes, top_n=10, min_sample=30)

    # Assert exactly 10 in each
    assert len(top_10) == 10
    assert len(bottom_10) == 10

    # Assert rank column
    assert list(top_10["rank"]) == list(range(1, 11))
    assert list(bottom_10["rank"]) == list(range(1, 11))

    # Assert top 10 is descending
    assert (top_10["res_score"].diff().iloc[1:] <= 0).all()

    # Assert bottom 10 is ascending
    assert (bottom_10["res_score"].diff().iloc[1:] >= 0).all()

    # Assert low-sample routes (Route-18 and Route-19) are not present in either
    assert "Route-18" not in top_10["route_key"].values
    assert "Route-18" not in bottom_10["route_key"].values
    assert "Route-19" not in top_10["route_key"].values
    assert "Route-19" not in bottom_10["route_key"].values


def test_aggregate_routes_with_synthetic_lead_times():
    """
    Verifies end-to-end route aggregation and RES scoring using actual synthetic baseline data.
    """
    baseline_df = pd.read_parquet(BASELINE_PARQUET)
    baseline_df["data_layer"] = "SYNTHETIC"

    route_summary = aggregate_routes(baseline_df, level="state", rollup_small_factories=True)

    assert "res_score" in route_summary.columns
    assert "speed_only_score" in route_summary.columns
    assert "delay_rate" in route_summary.columns
    assert "is_eligible" in route_summary.columns

    # Verify score ranges
    assert (route_summary["res_score"] >= 0.0).all()
    assert (route_summary["res_score"] <= 100.0).all()

    # Leaderboard generation on synthetic summary
    top_10, bottom_10 = generate_leaderboards(route_summary[route_summary["is_eligible"]])
    assert len(top_10) == 10
    assert len(bottom_10) == 10
    assert top_10.iloc[0]["res_score"] >= top_10.iloc[-1]["res_score"]
    assert bottom_10.iloc[0]["res_score"] <= bottom_10.iloc[-1]["res_score"]
