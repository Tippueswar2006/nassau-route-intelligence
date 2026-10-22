"""
Tests for Factory Mapping, Geographic Centroids, and Haversine Distance Engine.
Verifies compliance with AD-04, AD-10, and PRD Appendix A.
"""

import pytest
import numpy as np
import pandas as pd

from src.config import (
    FACTORIES_CSV,
    PRODUCT_FACTORY_CSV,
    GEOGRAPHIC_CENTROIDS_CSV,
    ORDER_LINE_COUNT,
    CUSTOMER_SHIPMENT_COUNT,
    MULTI_FACTORY_SHIPMENTS,
    MULTI_ORDER_LINE_SHIPMENTS,
)
from src.map_factories import (
    load_factory_configs,
    assign_factories,
    compute_route_distances,
    generate_route_keys,
    haversine_vectorized,
)


def test_factory_and_product_configs():
    """Validates configuration files structure and reference integrity."""
    factories_df, product_factory_df, centroids_df = load_factory_configs()

    # 5 production facilities
    assert len(factories_df) == 5, f"Expected 5 factories, got {len(factories_df)}"
    expected_factories = {
        "Lot's O' Nuts",
        "Wicked Choccy's",
        "Sugar Shack",
        "Secret Factory",
        "The Other Factory",
    }
    assert set(factories_df["Factory"]) == expected_factories

    # 59 destination centroids (49 US + 10 Canadian)
    assert len(centroids_df) == 59, f"Expected 59 centroids, got {len(centroids_df)}"
    assert (centroids_df["Country/Region"] == "Canada").sum() == 10
    assert (centroids_df["Country/Region"] == "United States").sum() == 49


def test_product_mapping_coverage(deduplicated_df: pd.DataFrame):
    """Asserts that 100% of products are mapped to the 5 factories with zero unmapped lines."""
    mapped = assign_factories(deduplicated_df)
    assert mapped["Factory"].notna().all(), "Encountered unmapped products"
    assert set(mapped["Factory"].unique()) == {
        "Lot's O' Nuts",
        "Wicked Choccy's",
        "Sugar Shack",
        "Secret Factory",
        "The Other Factory",
    }


def test_order_line_single_factory_invariant(deduplicated_df: pd.DataFrame):
    """
    Asserts that every Order ID maps to exactly 1 factory across all 8,549 clean order lines.
    This guarantees that the Order ID represents a single factory-to-customer order leg.
    """
    mapped = assign_factories(deduplicated_df)
    order_factory_counts = mapped.groupby("Order ID")["Factory"].nunique()

    assert len(order_factory_counts) == ORDER_LINE_COUNT, (
        f"Expected {ORDER_LINE_COUNT} unique Order IDs, got {len(order_factory_counts)}"
    )
    assert (order_factory_counts == 1).all(), (
        "Order-line grain violation! Some Order IDs map to multiple factories."
    )


def test_customer_shipment_grains(deduplicated_df: pd.DataFrame):
    """
    Verifies the customer shipment grain (Customer ID + Order Date + Ship Mode):
    - 5,067 distinct shipments
    - 1,702 multi-factory shipments (33.6%)
    - 2,240 multi-order-line shipments
    """
    mapped = assign_factories(deduplicated_df)
    shipment_group = mapped.groupby(["Customer ID", "Order Date", "Ship Mode"])

    assert len(shipment_group) == CUSTOMER_SHIPMENT_COUNT, (
        f"Expected {CUSTOMER_SHIPMENT_COUNT} customer shipments, got {len(shipment_group)}"
    )

    multi_factory = (shipment_group["Factory"].nunique() > 1).sum()
    assert multi_factory == MULTI_FACTORY_SHIPMENTS, (
        f"Expected {MULTI_FACTORY_SHIPMENTS} multi-factory shipments, got {multi_factory}"
    )

    multi_order = (shipment_group["Order ID"].nunique() > 1).sum()
    assert multi_order == MULTI_ORDER_LINE_SHIPMENTS, (
        f"Expected {MULTI_ORDER_LINE_SHIPMENTS} multi-order-line shipments, got {multi_order}"
    )


def test_haversine_distance_math():
    """Tests Haversine formula calculation against known great-circle distances."""
    # Boston (42.3601, -71.0589) to Chicago (41.8781, -87.6298) is ~1,368 km
    dist = haversine_vectorized(
        np.array([42.3601]),
        np.array([-71.0589]),
        np.array([41.8781]),
        np.array([-87.6298]),
    )
    assert 1360.0 <= dist[0] <= 1380.0, f"Haversine calculation deviation: {dist[0]} km"


def test_distance_computation_and_centroids(mapped_df: pd.DataFrame):
    """
    Asserts that:
    - Distance is computed for every record without any NaN values.
    - No distance is <= 0 km.
    - Canadian records have explicit non-zero distance from assigned factories.
    """
    assert mapped_df["distance_km"].notna().all(), "NaN values found in distance_km"
    assert (mapped_df["distance_km"] > 0).all(), "Zero or negative distance found"

    # Verify Canadian records specifically
    ca_records = mapped_df[mapped_df["is_canadian"]]
    assert len(ca_records) == 194  # 200 raw minus 6 duplicates = 194 clean records
    assert (ca_records["distance_km"] > 0).all(), "Canadian distances must not be zero"
    assert ca_records["distance_km"].mean() > 500, "Canadian distances should reflect real geography"


def test_route_keys(mapped_df: pd.DataFrame):
    """Verifies generation of standard route keys."""
    assert "route_key" in mapped_df.columns
    assert "route_key_region" in mapped_df.columns

    sample_route = mapped_df["route_key"].iloc[0]
    assert " -> " in sample_route, f"Invalid route key format: {sample_route}"

    sample_region = mapped_df["route_key_region"].iloc[0]
    assert " -> " in sample_region, f"Invalid route region format: {sample_region}"
