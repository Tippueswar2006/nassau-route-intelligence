"""
Unit and Integration Tests for Nassau Route Intelligence Release Gate Validation.
Verifies all 5 release gates, CLI execution, error trapping, and zero-Streamlit compliance.
"""

import ast
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from scripts.validate_release_gates import (
    GateResult,
    ValidationReport,
    check_architectural_invariants,
    check_cloud_artifact_loading,
    check_documentation_completeness,
    check_test_suite_pass_rate,
    check_zero_pii_and_surrogates,
    compute_file_sha256,
    main,
    run_all_release_gates,
)
from src.config import BASE_DIR, METADATA_JSON


# ==============================================================================
# Gate 1: Cloud Artifact Loading Tests
# ==============================================================================

def test_gate_1_cloud_artifact_loading_passes():
    """Asserts Gate 1 passes under simulated cloud environment with existing artifacts."""
    result = check_cloud_artifact_loading(simulated_cloud=True)
    assert isinstance(result, GateResult)
    assert result.passed is True
    assert result.status == "PASS"
    assert len(result.errors) == 0
    assert any("Simulated deployment mode verified: cloud" in d for d in result.details)


def test_gate_1_cloud_artifact_loading_missing_artifact(tmp_path):
    """Asserts Gate 1 catches missing production Parquet artifacts."""
    fake_path = tmp_path / "nonexistent.parquet"
    with patch("scripts.validate_release_gates.CLEAN_ORDERS_PARQUET", fake_path):
        result = check_cloud_artifact_loading(simulated_cloud=True)
        assert result.passed is False
        assert result.status == "FAIL"
        assert any("Missing required production artifact" in e for e in result.errors)


# ==============================================================================
# Gate 2: Zero-PII Leak & Surrogate Key Audit Tests
# ==============================================================================

def test_gate_2_zero_pii_and_surrogates_passes():
    """Asserts Gate 2 passes on production artifacts with zero leaks and valid surrogate formats."""
    result = check_zero_pii_and_surrogates()
    assert isinstance(result, GateResult)
    assert result.passed is True
    assert result.status == "PASS"
    assert len(result.errors) == 0
    assert any("valid surrogate Customer IDs" in d for d in result.details)
    assert any("valid surrogate Order IDs" in d for d in result.details)


def test_gate_2_detects_forbidden_column():
    """Asserts Gate 2 fails if a forbidden PII column (City) is present."""
    fake_df = pd.DataFrame({
        "Customer ID": ["CUST-12345678"],
        "Order ID": ["ORD-1234567890"],
        "City": ["San Francisco"],
    })
    with patch("scripts.validate_release_gates.load_prepared_artifacts", return_value={"clean_orders": fake_df}):
        result = check_zero_pii_and_surrogates()
        assert result.passed is False
        assert any("PII leak! Forbidden columns {'City'}" in e for e in result.errors)


def test_gate_2_detects_raw_customer_id():
    """Asserts Gate 2 fails if a raw 6-digit Customer ID is present."""
    fake_df = pd.DataFrame({
        "Customer ID": ["103800"],  # raw 6-digit
        "Order ID": ["ORD-1234567890"],
    })
    with patch("scripts.validate_release_gates.load_prepared_artifacts", return_value={"clean_orders": fake_df}):
        result = check_zero_pii_and_surrogates()
        assert result.passed is False
        assert any("Raw 6-digit Customer ID detected" in e for e in result.errors)


def test_gate_2_detects_invalid_order_id_format():
    """Asserts Gate 2 fails if an Order ID does not match ORD-xxxxxxxxxx format."""
    fake_df = pd.DataFrame({
        "Customer ID": ["CUST-12345678"],
        "Order ID": ["US-2021-103800-CHO-MIL-31000"],  # raw unmasked order id
    })
    with patch("scripts.validate_release_gates.load_prepared_artifacts", return_value={"clean_orders": fake_df}):
        result = check_zero_pii_and_surrogates()
        assert result.passed is False
        assert any("Raw unmasked Order ID detected" in e for e in result.errors)


# ==============================================================================
# Gate 3: Automated Test Suite Tests
# ==============================================================================

def test_gate_3_skip_tests():
    """Asserts Gate 3 correctly handles skip_tests=True."""
    result = check_test_suite_pass_rate(skip_tests=True)
    assert isinstance(result, GateResult)
    assert result.passed is True
    assert result.status == "SKIPPED"
    assert "skipped by user" in result.details[0]


def test_gate_3_subprocess_failure_handling():
    """Asserts Gate 3 catches non-zero exit codes from pytest."""
    mock_proc = subprocess.CompletedProcess(
        args=["pytest"],
        returncode=1,
        stdout="collected 150 items\nFAILED tests/test_foo.py::test_bar - AssertionError\n= 1 failed, 149 passed =",
        stderr="",
    )
    with patch("subprocess.run", return_value=mock_proc):
        result = check_test_suite_pass_rate(skip_tests=False)
        assert result.passed is False
        assert result.status == "FAIL"
        assert any("Pytest exited with non-zero return code 1" in e for e in result.errors)


# ==============================================================================
# Gate 4: Architectural Invariants & Hash Consistency Tests
# ==============================================================================

def test_gate_4_architectural_invariants_passes():
    """Asserts Gate 4 passes on valid checksums, source immutability, and zero Streamlit imports."""
    result = check_architectural_invariants()
    assert isinstance(result, GateResult)
    assert result.passed is True
    assert result.status == "PASS"
    assert len(result.errors) == 0
    assert any("Verified SHA-256 for clean_orders.parquet" in d for d in result.details)
    assert any("Verified zero Streamlit imports" in d for d in result.details)


def test_gate_4_checksum_mismatch_detected():
    """Asserts Gate 4 flags checksum discrepancies cleanly without false positive immutability errors."""
    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        real_meta = json.load(f)
    tampered_meta = json.loads(json.dumps(real_meta))
    tampered_meta["artifact_checksums"]["clean_orders.parquet"] = (
        "bad000000000000000000000000000000000000000000000000000000000dead"
    )

    with patch("json.load", return_value=tampered_meta):
        result = check_architectural_invariants()
        assert result.passed is False
        assert any("Checksum mismatch on clean_orders.parquet" in e for e in result.errors)


# ==============================================================================
# Gate 5: Documentation Completeness Tests
# ==============================================================================

def test_gate_5_documentation_completeness_passes():
    """Asserts Gate 5 passes when all 4 documentation files exist and meet size thresholds."""
    result = check_documentation_completeness()
    assert isinstance(result, GateResult)
    assert result.passed is True
    assert result.status == "PASS"
    assert len(result.errors) == 0
    assert any("Data Dictionary" in d for d in result.details)
    assert any("Methodology Specification" in d for d in result.details)
    assert any("Synthetic Assumptions Disclosure" in d for d in result.details)
    assert any("Project README" in d for d in result.details)


def test_gate_5_documentation_missing_file(tmp_path):
    """Asserts Gate 5 flags missing documentation files by executing against an empty directory."""
    with patch("scripts.validate_release_gates.BASE_DIR", tmp_path):
        result = check_documentation_completeness()
        assert result.passed is False
        assert result.status == "FAIL"
        assert any("Missing documentation artifact: Data Dictionary" in e for e in result.errors)
        assert any("Missing documentation artifact: Project README" in e for e in result.errors)


def test_gate_5_documentation_placeholder_detected(tmp_path):
    """Asserts Gate 5 flags placeholder tokens like [TODO] or [TBD] in publication docs."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    # Write files with sufficient size, but one contains [TODO]
    (docs_dir / "data_dictionary.md").write_text("A" * 6000 + "\nContains [TODO]: fix later", encoding="utf-8")
    (docs_dir / "methodology.md").write_text("B" * 6000, encoding="utf-8")
    (docs_dir / "synthetic_assumptions.md").write_text("C" * 6000, encoding="utf-8")
    (tmp_path / "README.md").write_text("D" * 4000, encoding="utf-8")

    with patch("scripts.validate_release_gates.BASE_DIR", tmp_path):
        result = check_documentation_completeness()
        assert result.passed is False
        assert any("Unresolved placeholders {'TODO'} detected in data_dictionary.md" in e for e in result.errors)


# ==============================================================================
# CLI and Orchestration Tests
# ==============================================================================

def test_cli_execution_with_skip_tests(tmp_path):
    """Asserts CLI entrypoint executes cleanly and writes report when requested."""
    report_file = tmp_path / "reports" / "cli_report.json"
    exit_code = main(["--skip-tests", "--output", str(report_file)])
    assert exit_code == 0
    assert report_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["overall_passed"] is True
    assert len(data["gates"]) == 5
    assert data["gates"][2]["status"] == "SKIPPED"


def test_cli_execution_failure_exit_code():
    """Asserts main CLI exits with return code 1 when any release gate fails."""
    mock_failed_report = ValidationReport(
        timestamp_utc="2026-10-22T00:00:00Z",
        overall_passed=False,
        total_duration_seconds=0.1,
        gates=[
            GateResult(
                gate_name="Gate 1: Simulated Cloud Startup & Parquet Artifact Loading",
                passed=False,
                status="FAIL",
                duration_seconds=0.05,
                details=[],
                errors=["Simulated cloud missing artifact failure"],
            )
        ],
    )
    with patch("scripts.validate_release_gates.run_all_release_gates", return_value=mock_failed_report):
        exit_code = main(["--skip-tests"])
        assert exit_code == 1


def test_zero_streamlit_in_release_gate_script_and_test():
    """Asserts zero Streamlit imports in scripts/validate_release_gates.py and this test file."""
    for script_path in [
        BASE_DIR / "scripts" / "validate_release_gates.py",
        Path(__file__).resolve(),
    ]:
        content = script_path.read_text(encoding="utf-8")
        parsed = ast.parse(content, filename=str(script_path))
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "streamlit" and not alias.name.startswith("streamlit."), (
                        f"Streamlit import found in {script_path.name}: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert node.module != "streamlit" and not node.module.startswith("streamlit."), (
                        f"Streamlit from-import found in {script_path.name}: {node.module}"
                    )
