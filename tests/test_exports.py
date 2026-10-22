"""
Tests for Provenance-Preserving CSV Export Engine.
Verifies compliance with AD-02, AD-11, and Story 4.5 acceptance criteria.
"""

import pytest
import pandas as pd

from src.config import BASELINE_PARQUET
from src.exports import (
    create_export_csv,
    parse_export_header,
    sanitize_export_dataframe,
    HUMAN_COLUMN_RENAMES,
)
from src.route_analysis import (
    aggregate_routes,
    filter_eligible_routes,
    generate_leaderboards,
)


@pytest.fixture
def sample_export_df() -> pd.DataFrame:
    """Creates a sample route dataframe with internal columns."""
    return pd.DataFrame({
        "Row ID": [101, 102, 103],
        "route_key": ["Lot's O' Nuts -> Texas", "Wicked Choccy's -> Texas", "Lot's O' Nuts -> California"],
        "sample_size": [479, 326, 944],
        "mean_lead_time": [5.2, 5.8, 3.4],
        "res_score": [82.5, 78.1, 91.0],
        "delay_rate": [0.22, 0.23, 0.12],
        "data_layer": ["SYNTHETIC", "SYNTHETIC", "SYNTHETIC"],
    })


def test_create_export_csv_header_elements(sample_export_df: pd.DataFrame):
    """
    Verifies that create_export_csv prepends structured comment lines (#) documenting:
    Data Layer, Active Scenario, Delay Threshold, Timestamp, Active Filters, and Disclaimers.
    """
    metadata = {
        "layer": "SYNTHETIC",
        "scenario": "baseline",
        "delay_threshold": 5.0,
        "filters": {
            "Factory": "All",
            "Region": "Pacific",
            "State": "California",
            "Ship Mode": "Standard Class",
            "Exclude Duplicates": True,
        },
    }

    csv_bytes = create_export_csv(sample_export_df, metadata=metadata, human_headers=True)
    assert isinstance(csv_bytes, bytes)
    text = csv_bytes.decode("utf-8")

    # Check header prefix
    lines = text.splitlines()
    assert lines[0].startswith("# ==================")
    assert any("NASSAU CANDY ROUTE INTELLIGENCE" in l for l in lines)
    assert any("Data Layer: SYNTHETIC" in l for l in lines)
    assert any("Active Scenario: baseline" in l for l in lines)
    assert any("Delay Threshold: 5.0 days" in l for l in lines)
    assert any("Region: Pacific" in l for l in lines)
    assert any("State: California" in l for l in lines)
    assert any("COGS Disclaimer" in l for l in lines)
    assert any("Simulation Notice" in l for l in lines)


def test_parse_export_header_roundtrip(sample_export_df: pd.DataFrame):
    """
    Verifies that parse_export_header accurately reconstructs metadata and data rows.
    """
    metadata = {
        "layer": "DERIVED",
        "scenario": "none",
        "delay_threshold": 6.0,
        "filters": {"Factory": "Lot's O' Nuts"},
    }

    csv_bytes = create_export_csv(sample_export_df, metadata=metadata, human_headers=False)
    extracted_meta, parsed_df = parse_export_header(csv_bytes)

    assert extracted_meta["layer"] == "DERIVED"
    assert "6.0" in extracted_meta["delay_threshold"]
    assert len(parsed_df) == len(sample_export_df)
    assert "route_key" in parsed_df.columns
    assert "Row ID" not in parsed_df.columns  # Row ID was sanitized


def test_human_readable_column_sanitization(sample_export_df: pd.DataFrame):
    """
    Verifies that technical slugs are converted to human-readable headers
    and internal system IDs are stripped.
    """
    sanitized = sanitize_export_dataframe(sample_export_df, human_headers=True)

    assert "Row ID" not in sanitized.columns
    assert "Route Key" in sanitized.columns
    assert "Sample Size (N)" in sanitized.columns
    assert "Mean Lead Time (Days)" in sanitized.columns
    assert "Route Efficiency Score (RES)" in sanitized.columns
    assert "Delay Rate" in sanitized.columns


def test_export_on_actual_route_leaderboard():
    """
    Verifies export generation on actual Top 10 route leaderboard.
    """
    base_df = pd.read_parquet(BASELINE_PARQUET)
    base_df["data_layer"] = "SYNTHETIC"

    agg = aggregate_routes(base_df, level="state", rollup_small_factories=True)
    el, _ = filter_eligible_routes(agg, min_sample=30)
    top_10, _ = generate_leaderboards(el, top_n=10)

    metadata = {
        "layer": "SYNTHETIC",
        "scenario": "baseline",
        "delay_threshold": 5.0,
        "filters": {"min_sample": 30},
    }

    export_bytes = create_export_csv(top_10, metadata=metadata, human_headers=True)
    extracted_meta, parsed_df = parse_export_header(export_bytes)

    assert len(parsed_df) == 10
    assert "Route Key" in parsed_df.columns
    assert extracted_meta["layer"] == "SYNTHETIC"
    assert "5.0" in extracted_meta["delay_threshold"]
