"""
Pytest configuration and shared fixtures for Nassau Route Intelligence test suite.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.config import RAW_DATA_PATH
from src.load_data import load_raw_data
from src.validate_data import clean_dataset
from src.map_factories import process_mapping_pipeline


@pytest.fixture(scope="session")
def raw_df() -> pd.DataFrame:
    """Loads the raw Nassau Candy dataset with hash verification."""
    if not RAW_DATA_PATH.exists():
        pytest.skip(f"Raw data file not present at {RAW_DATA_PATH} (cloud environment)")
    return load_raw_data(RAW_DATA_PATH, verify_hash=True)


@pytest.fixture(scope="session")
def cleaned_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Returns the cleaned dataset with duplicate flags and normalized fields."""
    return clean_dataset(raw_df)


@pytest.fixture(scope="session")
def deduplicated_df(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """Returns the deduplicated clean dataset (is_duplicate == False)."""
    return cleaned_df[~cleaned_df["is_duplicate"]].copy()


@pytest.fixture(scope="session")
def mapped_df(deduplicated_df: pd.DataFrame) -> pd.DataFrame:
    """Returns the deduplicated dataset with factories and distances mapped."""
    return process_mapping_pipeline(deduplicated_df)
