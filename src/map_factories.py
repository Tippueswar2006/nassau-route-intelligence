"""
Factory Mapping, Geographic Coordinate Join, and Haversine Distance Engine.
Pure backend module decoupled from UI libraries (Zero Streamlit imports).
"""

from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd

from src.config import (
    FACTORIES_CSV,
    PRODUCT_FACTORY_CSV,
    GEOGRAPHIC_CENTROIDS_CSV,
)

EARTH_RADIUS_KM = 6371.0088


def load_factory_configs() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads reference configuration tables for factories, products, and centroids.
    """
    factories_df = pd.read_csv(FACTORIES_CSV)
    product_factory_df = pd.read_csv(PRODUCT_FACTORY_CSV)
    centroids_df = pd.read_csv(GEOGRAPHIC_CENTROIDS_CSV)

    return factories_df, product_factory_df, centroids_df


def assign_factories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps products to production facilities based on config/product_factory.csv.
    Enforces that 100% of products are mapped and validates that each Order ID
    maps to exactly one factory across all records.
    """
    df = df.copy()
    _, product_factory_df, _ = load_factory_configs()

    # Build mapping dictionary supporting both exact and normalized product names
    mapping = dict(zip(product_factory_df["Product Name"], product_factory_df["Factory"]))

    # Normalize whitespace for robust matching
    df["Factory"] = df["Product Name"].map(mapping)

    # Secondary lookup by Product ID if Product Name was unmapped
    if df["Factory"].isna().any():
        id_mapping = dict(zip(product_factory_df["Product ID"], product_factory_df["Factory"]))
        df["Factory"] = df["Factory"].fillna(df["Product ID"].map(id_mapping))

    unmapped = df[df["Factory"].isna()]
    if not unmapped.empty:
        unmapped_names = unmapped["Product Name"].unique().tolist()
        raise ValueError(f"Unmapped products encountered in pipeline: {unmapped_names}")

    # Verify order-line grain: each Order ID must map to exactly one factory
    order_factories = df.groupby("Order ID")["Factory"].nunique()
    multi_factory_orders = order_factories[order_factories > 1]
    if not multi_factory_orders.empty:
        raise ValueError(
            f"Encountered {len(multi_factory_orders)} Order IDs spanning multiple factories! "
            "Order lines must strictly map to 1 factory."
        )

    return df


def haversine_vectorized(
    lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray
) -> np.ndarray:
    """
    Computes great-circle distances in kilometers between two coordinate pairs
    using the vectorized Haversine formula.
    """
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )
    # Clip to avoid domain errors in arcsin / sqrt due to floating point precision
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))

    distance_km = EARTH_RADIUS_KM * c
    return distance_km


def compute_route_distances(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attaches factory coordinates and destination state/province centroids
    (including Canadian provinces), then calculates Haversine distance in kilometers.
    Fails if any destination lacks a centroid or is silently assigned zero distance.
    """
    df = df.copy()
    factories_df, _, centroids_df = load_factory_configs()

    # Merge factory coordinates
    factory_coords = factories_df[["Factory", "Latitude", "Longitude"]].rename(
        columns={"Latitude": "factory_lat", "Longitude": "factory_lon"}
    )
    df = df.merge(factory_coords, on="Factory", how="left")

    if df["factory_lat"].isna().any():
        missing_factories = df[df["factory_lat"].isna()]["Factory"].unique().tolist()
        raise ValueError(f"Missing coordinates for factories: {missing_factories}")

    # Merge destination centroids
    dest_coords = centroids_df[
        ["Country/Region", "State/Province", "Latitude", "Longitude"]
    ].rename(columns={"Latitude": "dest_lat", "Longitude": "dest_lon"})

    df = df.merge(dest_coords, on=["Country/Region", "State/Province"], how="left")

    if df["dest_lat"].isna().any():
        missing_dests = (
            df[df["dest_lat"].isna()][["Country/Region", "State/Province"]]
            .drop_duplicates()
            .to_dict(orient="records")
        )
        raise ValueError(
            f"Missing centroids for destinations (Canadian or US): {missing_dests}. "
            "Never silently treat missing distance as zero."
        )

    # Vectorized Haversine distance
    df["distance_km"] = haversine_vectorized(
        df["factory_lat"].values,
        df["factory_lon"].values,
        df["dest_lat"].values,
        df["dest_lon"].values,
    )

    if (df["distance_km"] <= 0).any():
        zero_routes = df[df["distance_km"] <= 0][["Factory", "State/Province"]].drop_duplicates()
        raise ValueError(f"Found zero or negative distance for routes:\n{zero_routes}")

    return df


def generate_route_keys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates standard route keys for state-level and regional analysis:
    - route_key: Factory -> State/Province (e.g. Lot's O' Nuts -> Texas)
    - route_key_region: Factory -> Region (e.g. Lot's O' Nuts -> Gulf)
    """
    df = df.copy()
    df["route_key"] = df["Factory"] + " -> " + df["State/Province"]
    df["route_key_region"] = df["Factory"] + " -> " + df["Region"]
    return df


def process_mapping_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Executes full mapping pipeline: factory assignment, coordinate joins,
    distance computation, and route key generation.
    """
    df = assign_factories(df)
    df = compute_route_distances(df)
    df = generate_route_keys(df)
    return df
