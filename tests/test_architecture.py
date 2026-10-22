"""
Architectural Invariant and Compliance Tests for Nassau Route Intelligence.
Enforces decoupling from Streamlit in src/, .gitignore data hygiene, and config integrity.
"""

import ast
from pathlib import Path
import pytest

from src.config import (
    BASE_DIR,
    FACTORIES_CSV,
    PRODUCT_FACTORY_CSV,
    GEOGRAPHIC_CENTROIDS_CSV,
    GENERATOR_YAML,
)


def test_zero_streamlit_in_src():
    """
    Asserts that NO file under src/ imports Streamlit.
    Core business logic, ingestion, metrics, and models must remain 100% headless.
    """
    src_dir = BASE_DIR / "src"
    py_files = list(src_dir.glob("**/*.py"))
    assert len(py_files) > 0, "No python files found in src/"

    violations = []

    for file_path in py_files:
        content = file_path.read_text(encoding="utf-8")
        parsed = ast.parse(content, filename=str(file_path))

        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "streamlit" or alias.name.startswith("streamlit."):
                        violations.append((file_path.name, node.lineno, f"import {alias.name}"))
            elif isinstance(node, ast.ImportFrom):
                if node.module and (node.module == "streamlit" or node.module.startswith("streamlit.")):
                    violations.append((file_path.name, node.lineno, f"from {node.module} import ..."))

    assert not violations, f"Streamlit imports detected in src/ (strictly prohibited):\n{violations}"


def test_gitignore_data_separation():
    """
    Verifies that .gitignore properly excludes:
    - data/original/ (never committed or deployed to cloud)
    - data/derived/surrogate_key_mapping.csv (local-only key mapping)
    """
    gitignore_path = BASE_DIR / ".gitignore"
    assert gitignore_path.exists(), ".gitignore file must exist at project root"

    content = gitignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    assert "data/original/" in lines or "data/original" in lines, (
        "data/original/ must be excluded in .gitignore"
    )
    assert "data/derived/surrogate_key_mapping.csv" in lines, (
        "data/derived/surrogate_key_mapping.csv must be excluded in .gitignore"
    )


def test_config_files_present_and_valid():
    """Verifies that all required configuration files exist and are populated."""
    for cfg in [FACTORIES_CSV, PRODUCT_FACTORY_CSV, GEOGRAPHIC_CENTROIDS_CSV, GENERATOR_YAML]:
        assert cfg.exists(), f"Missing config file: {cfg.name}"
        assert cfg.stat().st_size > 0, f"Config file is empty: {cfg.name}"
