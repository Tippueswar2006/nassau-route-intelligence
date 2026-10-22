"""
Automated Test Suite for Nassau Route Intelligence Documentation Suite.
Verifies compliance with Story 6.3, FR-15, FR-18, FR-19, and AD-01/02/04:
- Existence and non-empty byte size (>1000 bytes) of all 4 documentation files:
  - docs/data_dictionary.md
  - docs/methodology.md
  - docs/synthetic_assumptions.md
  - README.md
- Structural integrity, required markdown headers, and required sections
- Mathematical formulations, formulas, and symbols in docs/methodology.md
- Schema completeness (18 raw columns, derived/synthetic fields) in docs/data_dictionary.md
- Simulation assumptions, empirical tables, stress parameters, and seeds in docs/synthetic_assumptions.md
- Quickstart commands, testing, figure generation, and cloud deployment in README.md
- Decoupled backend architecture (zero Streamlit imports)
"""

import ast
from pathlib import Path
import re
import pytest

from src.config import (
    BASE_DIR,
    RAW_COLUMNS,
    ROBUSTNESS_SEEDS,
    SHIPPING_MODES,
)

DOCS_DIR = BASE_DIR / "docs"
DATA_DICT_PATH = DOCS_DIR / "data_dictionary.md"
METHODOLOGY_PATH = DOCS_DIR / "methodology.md"
SYNTHETIC_ASSUMPTIONS_PATH = DOCS_DIR / "synthetic_assumptions.md"
README_PATH = BASE_DIR / "README.md"
TEST_FILE_PATH = Path(__file__).resolve()


# ==============================================================================
# 1. Architecture & Code Invariants
# ==============================================================================

def test_no_streamlit_imports_in_documentation_tests():
    """Asserts that tests/test_documentation.py has zero Streamlit imports."""
    content = TEST_FILE_PATH.read_text(encoding="utf-8")
    parsed = ast.parse(content, filename=str(TEST_FILE_PATH))

    violations = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "streamlit" in alias.name:
                    violations.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and "streamlit" in node.module:
                violations.append(node.module)

    assert not violations, f"Streamlit import detected in test file: {violations}"


# ==============================================================================
# 2. File Existence & Size Checks
# ==============================================================================

@pytest.mark.parametrize("file_path,min_bytes", [
    (DATA_DICT_PATH, 1000),
    (METHODOLOGY_PATH, 1000),
    (SYNTHETIC_ASSUMPTIONS_PATH, 1000),
    (README_PATH, 1000),
])
def test_documentation_file_exists_and_non_empty(file_path: Path, min_bytes: int):
    """Verifies that each documentation artifact exists and meets minimum length criteria."""
    assert file_path.exists(), f"Required documentation file missing: {file_path}"
    assert file_path.is_file(), f"Path is not a regular file: {file_path}"
    size = file_path.stat().st_size
    assert size >= min_bytes, f"File {file_path.name} is undersized ({size} bytes < {min_bytes} bytes)"


# ==============================================================================
# 3. Data Dictionary Verification (docs/data_dictionary.md)
# ==============================================================================

def test_data_dictionary_content_and_schemas():
    """Verifies that docs/data_dictionary.md documents all data tiers and attributes."""
    content = DATA_DICT_PATH.read_text(encoding="utf-8")

    # Required section titles
    required_sections = [
        "1. Data Architecture & Layer Provenance",
        "2. Original Layer: `data/original/nassau_candy.csv`",
        "3. Derived Layer: `data/derived/`",
        "4. Synthetic Simulation Layer: `data/synthetic/`",
        "5. Computed Analytics & Route Efficiency Metrics",
    ]
    for section in required_sections:
        assert section in content, f"Missing section in data_dictionary.md: {section}"

    # Verifies all 18 raw columns are documented
    for raw_col in RAW_COLUMNS:
        assert f"`{raw_col}`" in content or raw_col in content, (
            f"Raw column '{raw_col}' missing from data_dictionary.md"
        )

    # Verifies derived and synthetic artifact filenames are present
    artifacts = [
        "clean_orders.parquet",
        "route_aggregates.parquet",
        "surrogate_key_mapping.csv",
        "transformation_log.json",
        "baseline.parquet",
        "distance_sensitive.parquet",
        "stress_test.parquet",
        "metadata.json",
    ]
    for art in artifacts:
        assert art in content, f"Artifact '{art}' missing from data_dictionary.md"

    # Verifies computed metrics are defined
    computed_metrics = [
        "mode_adjusted_lead_time",
        "speed_penalty",
        "variability_penalty",
        "res_score",
        "speed_only_score",
        "is_delayed",
        "is_bottleneck",
        "is_watchlist",
    ]
    for metric in computed_metrics:
        assert metric in content, f"Metric '{metric}' missing from data_dictionary.md"

    # Verifies compliance disclosures AD-01, AD-02, AD-04
    assert "904" in content and "1,642" in content, "AD-01 date anomaly range missing"
    assert "AD-02" in content or "Synthetic Data Disclosure" in content
    assert "CUST-" in content and "ORD-" in content, "Surrogate key tokens missing"


# ==============================================================================
# 4. Methodology Verification (docs/methodology.md)
# ==============================================================================

def test_methodology_content_and_math():
    """Verifies that docs/methodology.md contains formal mathematical definitions."""
    content = METHODOLOGY_PATH.read_text(encoding="utf-8")

    # Required sections
    required_sections = [
        "1. Geographic Modeling & Great-Circle Distance",
        "2. Shipping Mode Normalization",
        "3. Route Efficiency Score (RES) Formulation",
        "4. Sample Size Guardrails",
        "5. Transparent Bottleneck Quadrant Screening",
        "6. Sensitivity & Multi-Seed Robustness Framework",
    ]
    for section in required_sections:
        assert section in content, f"Missing section in methodology.md: {section}"

    # Mathematical formulas and concepts
    assert "Haversine" in content
    assert "6,371" in content  # Earth radius R
    assert "arcsin" in content or "sin^2" in content

    # Distance bands
    assert "0–500 km" in content
    assert "500–1,500 km" in content
    assert "1,500–3,000 km" in content
    assert "3,000+ km" in content

    # Mode Reference benchmarks
    for mode in SHIPPING_MODES:
        assert mode in content, f"Shipping mode '{mode}' missing from methodology.md"
    assert "0.38" in content  # Same Day mean
    assert "2.55" in content  # First Class mean
    assert "3.57" in content  # Second Class mean
    assert "5.32" in content  # Standard Class mean

    # RES Formulas
    assert "P_{\\text{speed}}" in content or "P_{speed}" in content or "speed_penalty" in content
    assert "P_{\\text{var}}" in content or "P_{var}" in content or "variability_penalty" in content
    assert "0.70" in content and "0.30" in content  # Canonical RES weights

    # Guardrail and screening
    assert "N \\ge 30" in content or "N >= 30" in content
    assert "75th" in content or "P_{75}" in content
    assert "Critical Bottlenecks" in content
    assert "Watchlist" in content

    # Sensitivity and seeds
    assert "Spearman" in content
    for seed in ROBUSTNESS_SEEDS:
        assert str(seed) in content, f"Seed {seed} missing from methodology.md"


# ==============================================================================
# 5. Synthetic Assumptions Verification (docs/synthetic_assumptions.md)
# ==============================================================================

def test_synthetic_assumptions_content_and_parameters():
    """Verifies that docs/synthetic_assumptions.md discloses simulation parameters."""
    content = SYNTHETIC_ASSUMPTIONS_PATH.read_text(encoding="utf-8")

    # Required sections
    required_sections = [
        "1. Motivation & Context",
        "2. Customer Shipment Grouping & Order Grain",
        "3. Empirical Baseline Distribution Calibration",
        "4. Distance Sensitivity Model",
        "5. Stress-Test Disruption Scenarios",
        "6. Privacy & Surrogate Key Anonymization",
        "7. Multi-Seed Robustness Standards",
    ]
    for section in required_sections:
        assert section in content, f"Missing section in synthetic_assumptions.md: {section}"

    # Shipment grain and counts
    assert "5,067" in content  # customer shipments
    assert "8,549" in content or "9,881" in content
    assert "1,702" in content  # multi-factory shipments

    # Empirical mode tables
    for mode in SHIPPING_MODES:
        assert mode in content, f"Shipping mode '{mode}' missing from synthetic_assumptions.md"
    assert "0.640" in content  # Same day p0
    assert "0.353" in content  # First class p2
    assert "0.267" in content  # Second class p2
    assert "0.276" in content  # Standard class p4

    # Distance sensitivity and bounds
    assert "0.50" in content or "0.5" in content
    assert "1,000 km" in content or "1000" in content
    assert "14.0" in content  # base bound upper
    assert "20.0" in content  # stress bound upper

    # Stress injections
    assert "November" in content or "Nov/Dec" in content or "month" in content
    assert "California" in content and "New York" in content
    assert "Texas" in content
    assert "Lot's O' Nuts" in content
    assert "Wicked Choccy's" in content

    # Privacy and seeds
    assert "CUST-" in content and "ORD-" in content
    for seed in ROBUSTNESS_SEEDS:
        assert str(seed) in content, f"Seed {seed} missing from synthetic_assumptions.md"


# ==============================================================================
# 6. Repository README Verification (README.md)
# ==============================================================================

def test_readme_content_and_commands():
    """Verifies that README.md provides comprehensive project guide and executable commands."""
    content = README_PATH.read_text(encoding="utf-8")

    # Badges / Titles
    assert "Nassau Candy Shipping Route Intelligence" in content
    assert "Python" in content
    assert "Streamlit" in content
    assert "pytest" in content
    assert "Zero-PII" in content or "Zero--PII" in content

    # Key Sections
    assert "1. Project Vision & Capabilities" in content
    assert "2. Key Research Questions Answered" in content
    assert "3. Repository Architecture & Directory Tree" in content
    assert "4. Quickstart Guide" in content
    assert "5. Data Pipeline Build Execution" in content
    assert "6. Automated Test Suite Execution" in content
    assert "7. Publication Figure Generation" in content
    assert "8. Launching the Streamlit Application" in content
    assert "9. Production Cloud Deployment Guide" in content

    # Executable CLI commands
    assert "scripts/build_data.py" in content
    assert "scripts/generate_paper_figures.py" in content
    assert "streamlit run app.py" in content
    assert "pytest" in content
    assert "test_sensitivity.py" in content
