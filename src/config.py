"""
Centralized Configuration and Path Management for Nassau Route Intelligence.
Strictly decoupled from UI libraries (Zero Streamlit imports).
"""

from pathlib import Path
from typing import Dict, List

# Base workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Config directory and paths
CONFIG_DIR = BASE_DIR / "config"
FACTORIES_CSV = CONFIG_DIR / "factories.csv"
PRODUCT_FACTORY_CSV = CONFIG_DIR / "product_factory.csv"
GEOGRAPHIC_CENTROIDS_CSV = CONFIG_DIR / "geographic_centroids.csv"
GENERATOR_YAML = CONFIG_DIR / "generator.yaml"

# Data directories
DATA_DIR = BASE_DIR / "data"
ORIGINAL_DATA_DIR = DATA_DIR / "original"
DERIVED_DATA_DIR = DATA_DIR / "derived"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"

# Raw dataset specification
RAW_DATA_PATH = ORIGINAL_DATA_DIR / "nassau_candy.csv"
RAW_DATA_SHA256 = "6ae9208e77ce410e90073b19813d29f89853ce9f3cce43d41f9643781696e94f"

# Derived artifacts
CLEAN_ORDERS_PARQUET = DERIVED_DATA_DIR / "clean_orders.parquet"
ROUTE_AGGREGATES_PARQUET = DERIVED_DATA_DIR / "route_aggregates.parquet"
SURROGATE_MAPPING_CSV = DERIVED_DATA_DIR / "surrogate_key_mapping.csv"
TRANSFORMATION_LOG_JSON = DERIVED_DATA_DIR / "transformation_log.json"

# Synthetic artifacts
BASELINE_PARQUET = SYNTHETIC_DATA_DIR / "baseline.parquet"
DISTANCE_PARQUET = SYNTHETIC_DATA_DIR / "distance_sensitive.parquet"
STRESS_PARQUET = SYNTHETIC_DATA_DIR / "stress_test.parquet"
METADATA_JSON = SYNTHETIC_DATA_DIR / "metadata.json"

# Core business parameters
DEFAULT_SEED = 42
ROBUSTNESS_SEEDS = [42, 101, 202, 303, 404]
MIN_SAMPLE_SIZE = 30
SMALL_FACTORIES: List[str] = ["Sugar Shack", "Secret Factory", "The Other Factory"]
DEFAULT_DELAY_THRESHOLD = 5.0
DEFAULT_RES_WEIGHT_SPEED = 0.70
DEFAULT_RES_WEIGHT_VARIABILITY = 0.30

# Approved unit and financial reconciliation baselines (AD-12)
RECONCILIATION_TARGETS: Dict[str, Dict[str, float]] = {
    "rows": {"raw": 10194, "clean": 9881, "delta": -313},
    "units": {"raw": 38654, "clean": 37667, "delta": -987},
    "sales": {"raw": 141783.63, "clean": 138284.12, "delta": -3499.51},
    "profit": {"raw": 93442.80, "clean": 91076.41, "delta": -2366.39},
}

# Order grains
ORDER_LINE_COUNT = 8549
CUSTOMER_SHIPMENT_COUNT = 5067
MULTI_FACTORY_SHIPMENTS = 1702
MULTI_ORDER_LINE_SHIPMENTS = 2240

# US State name to 2-letter postal abbreviation mapping for Plotly Choropleths
US_STATE_TO_CODE: Dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

# Shipping modes
SHIPPING_MODES: List[str] = [
    "Same Day",
    "First Class",
    "Second Class",
    "Standard Class",
]

EXPEDITED_MODES: List[str] = [
    "Same Day",
    "First Class",
    "Second Class",
]

STANDARD_MODES: List[str] = [
    "Standard Class",
]

# Distance bands (FR-10, Section 12)
DISTANCE_BAND_BINS: List[float] = [0.0, 500.0, 1500.0, 3000.0, float("inf")]
DISTANCE_BAND_LABELS: List[str] = [
    "0–500 km",
    "500–1,500 km",
    "1,500–3,000 km",
    "3,000+ km",
]

# Raw dataset column names
RAW_COLUMNS = [
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Country/Region",
    "City",
    "State/Province",
    "Postal Code",
    "Division",
    "Region",
    "Product ID",
    "Product Name",
    "Sales",
    "Units",
    "Gross Profit",
    "Cost",
]
