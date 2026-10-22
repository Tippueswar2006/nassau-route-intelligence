"""
Release Gate & Zero-PII Cloud Deployment Validation Suite.
Automated pre-deployment verification for Nassau Route Intelligence on Streamlit Community Cloud.

Gates Enforced:
1. Simulated Cloud Startup & Parquet Artifact Loading (AD-04, AD-08)
2. Zero-PII Leak & Surrogate Key Audit (AD-04, AD-08)
3. Automated Test Suite Execution (pytest 100% pass rate)
4. Architectural Invariants, Checksum Integrity & Streamlit Decoupling (AD-01, AD-02, AD-12)
5. Comprehensive Documentation Suite Completeness

Strictly decoupled from Streamlit (Zero Streamlit imports).
"""

import argparse
import ast
import dataclasses
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd

from src.config import (
    BASE_DIR,
    RAW_DATA_PATH,
    RAW_DATA_SHA256,
    CLEAN_ORDERS_PARQUET,
    ROUTE_AGGREGATES_PARQUET,
    BASELINE_PARQUET,
    DISTANCE_PARQUET,
    STRESS_PARQUET,
    METADATA_JSON,
    SURROGATE_MAPPING_CSV,
)
from src.load_data import (
    get_deployment_mode,
    load_metadata,
    load_prepared_artifacts,
)


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclasses.dataclass
class GateResult:
    gate_name: str
    passed: bool
    status: str  # "PASS", "FAIL", "SKIPPED"
    duration_seconds: float
    details: List[str] = dataclasses.field(default_factory=list)
    errors: List[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "status": self.status,
            "duration_seconds": round(self.duration_seconds, 3),
            "details": self.details,
            "errors": self.errors,
        }


@dataclasses.dataclass
class ValidationReport:
    timestamp_utc: str
    overall_passed: bool
    total_duration_seconds: float
    gates: List[GateResult] = dataclasses.field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_utc": self.timestamp_utc,
            "overall_passed": self.overall_passed,
            "total_duration_seconds": round(self.total_duration_seconds, 3),
            "gates": [g.to_dict() for g in self.gates],
        }


# ==============================================================================
# Helper Utilities
# ==============================================================================

def compute_file_sha256(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file in 64KB blocks."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hash calculation: {file_path}")
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


# ==============================================================================
# Release Gate 1: Simulated Cloud Startup & Parquet Artifact Loading
# ==============================================================================

def check_cloud_artifact_loading(simulated_cloud: bool = True) -> GateResult:
    """
    Gate 1: Verifies production Parquet artifacts and metadata can be loaded
    in a simulated cloud environment where data/original/ is absent.
    """
    start_time = time.time()
    details: List[str] = []
    errors: List[str] = []

    # 1. Verify file presence on disk
    required_artifacts = [
        ("Clean Orders Parquet", CLEAN_ORDERS_PARQUET),
        ("Route Aggregates Parquet", ROUTE_AGGREGATES_PARQUET),
        ("Baseline Parquet", BASELINE_PARQUET),
        ("Distance Sensitive Parquet", DISTANCE_PARQUET),
        ("Stress Test Parquet", STRESS_PARQUET),
        ("Metadata JSON", METADATA_JSON),
    ]

    for name, path in required_artifacts:
        if not path.exists():
            errors.append(f"Missing required production artifact: {name} ({path.name})")
        elif path.stat().st_size == 0:
            errors.append(f"Empty production artifact: {name} ({path.name})")
        else:
            size_kb = path.stat().st_size / 1024
            details.append(f"Found {name} ({path.name}): {size_kb:.1f} KB")

    # 2. Test simulated cloud deployment mode and artifact loader
    try:
        def simulated_exists(p_self):
            if simulated_cloud and (str(p_self) == str(RAW_DATA_PATH) or getattr(p_self, "name", "") == "nassau_candy.csv"):
                return False
            return Path.is_file(p_self) or Path.is_dir(p_self)

        with patch.object(Path, "exists", autospec=True, side_effect=simulated_exists):
            mode = get_deployment_mode()
            if simulated_cloud and mode != "cloud":
                errors.append(f"Simulated cloud deployment mode check failed: expected 'cloud', got '{mode}'")
            else:
                details.append(f"Simulated deployment mode verified: {mode}")

            # Test loading artifacts while inside the simulated cloud context
            artifacts = load_prepared_artifacts()

        expected_keys = {"clean_orders", "route_aggregates", "baseline", "distance_sensitive", "stress_test"}
        missing_keys = expected_keys - set(artifacts.keys())
        if missing_keys:
            errors.append(f"load_prepared_artifacts() missing expected table keys: {missing_keys}")
        else:
            for k in expected_keys:
                df = artifacts[k]
                details.append(f"Loaded '{k}': {len(df):,} rows, {len(df.columns)} columns")
                if len(df) == 0:
                    errors.append(f"Loaded artifact '{k}' has 0 rows")

        # Test metadata loading
        meta = load_metadata()
        if not meta or "scenarios" not in meta:
            errors.append("load_metadata() failed or returned invalid metadata structure")
        else:
            details.append(f"Loaded metadata.json: {len(meta.get('scenarios', []))} scenarios, build seed {meta.get('build_seed')}")

    except Exception as exc:
        errors.append(f"Exception during cloud artifact loading: {str(exc)}")

    duration = time.time() - start_time
    passed = len(errors) == 0
    return GateResult(
        gate_name="Gate 1: Simulated Cloud Startup & Parquet Artifact Loading",
        passed=passed,
        status="PASS" if passed else "FAIL",
        duration_seconds=duration,
        details=details,
        errors=errors,
    )


# ==============================================================================
# Release Gate 2: Zero-PII Leak & Surrogate Key Audit
# ==============================================================================

def check_zero_pii_and_surrogates() -> GateResult:
    """
    Gate 2: Rigorous audit of Parquet files and metadata for zero raw Customer IDs,
    surrogate token formats (CUST-xxxxxxxx, ORD-xxxxxxxxxx), absence of PII columns,
    and gitignore privacy exclusions.
    """
    start_time = time.time()
    details: List[str] = []
    errors: List[str] = []

    # 1. Dropped granular PII columns check
    forbidden_cols = {
        "City",
        "Postal Code",
        "Postal Code Cleaned",
        "Customer Name",
        "Contact Name",
        "Address",
        "Phone",
        "Email",
    }
    try:
        artifacts = load_prepared_artifacts()
    except Exception as e:
        return GateResult(
            gate_name="Gate 2: Zero-PII Leak & Surrogate Key Audit",
            passed=False,
            status="FAIL",
            duration_seconds=time.time() - start_time,
            details=[],
            errors=[f"Failed to load artifacts for PII audit: {e}"],
        )

    for name, df in artifacts.items():
        present_forbidden = forbidden_cols.intersection(set(df.columns))
        if present_forbidden:
            errors.append(f"PII leak! Forbidden columns {present_forbidden} detected in '{name}'")
        else:
            details.append(f"Verified '{name}': 0 forbidden geographic/identity PII columns")

    # 2. Surrogate formatting and zero 6-digit Customer IDs
    cust_regex = re.compile(r"^CUST-[0-9a-f]{8}$")
    order_regex = re.compile(r"^ORD-[0-9a-f]{10}$")
    raw_cust_regex = re.compile(r"^\d{6}$")

    for name in ["clean_orders", "baseline", "distance_sensitive", "stress_test"]:
        if name not in artifacts:
            continue
        df = artifacts[name]

        # Audit Customer ID presence and format
        if "Customer ID" in df.columns:
            cust_series = df["Customer ID"].dropna().astype(str)
            raw_cust_matches = cust_series[cust_series.str.match(raw_cust_regex)]
            if not raw_cust_matches.empty:
                errors.append(f"Raw 6-digit Customer ID detected in '{name}': {raw_cust_matches.iloc[0]}")
            else:
                invalid_surrogates = cust_series[~cust_series.str.match(cust_regex)]
                if not invalid_surrogates.empty:
                    errors.append(f"Invalid surrogate Customer ID format in '{name}': {invalid_surrogates.iloc[0]}")
                else:
                    details.append(f"Verified '{name}': {cust_series.nunique():,} valid surrogate Customer IDs (CUST-xxxxxxxx)")
        else:
            errors.append(f"Mandatory 'Customer ID' column missing in '{name}'")

        # Audit Order ID presence and format
        if "Order ID" in df.columns:
            order_series = df["Order ID"].dropna().astype(str)
            raw_order_matches = order_series[order_series.str.contains(r"^US-\d{4}-\d{6}", regex=True)]
            if not raw_order_matches.empty:
                errors.append(f"Raw unmasked Order ID detected in '{name}': {raw_order_matches.iloc[0]}")
            else:
                invalid_order_surrogates = order_series[~order_series.str.match(order_regex)]
                if not invalid_order_surrogates.empty:
                    errors.append(f"Invalid surrogate Order ID format in '{name}': {invalid_order_surrogates.iloc[0]}")
                else:
                    details.append(f"Verified '{name}': {order_series.nunique():,} valid surrogate Order IDs (ORD-xxxxxxxxxx)")
        else:
            errors.append(f"Mandatory 'Order ID' column missing in '{name}'")

    # 3. Check metadata.json content for raw Customer IDs
    if METADATA_JSON.exists():
        with open(METADATA_JSON, "r", encoding="utf-8") as f:
            meta_text = f.read()
        raw_cust_in_meta = re.findall(r"\b\d{6}\b", meta_text)
        if raw_cust_in_meta:
            if RAW_DATA_PATH.exists():
                try:
                    raw_df = pd.read_csv(RAW_DATA_PATH, usecols=["Customer ID"])
                    raw_cids = set(raw_df["Customer ID"].dropna().astype(str))
                    leaked = set(raw_cust_in_meta).intersection(raw_cids)
                    if leaked:
                        errors.append(f"Raw Customer IDs leaked into metadata.json: {list(leaked)[:3]}")
                except Exception as ex:
                    errors.append(f"Failed to cross-reference metadata IDs against raw data: {ex}")
            else:
                errors.append(f"Found {len(raw_cust_in_meta)} unverified 6-digit candidate numbers in metadata.json")
        details.append("Verified metadata.json: zero Customer ID leaks")

    # 4. Check .gitignore for privacy exclusions
    gitignore_path = BASE_DIR / ".gitignore"
    if not gitignore_path.exists():
        errors.append(".gitignore file is missing at project root")
    else:
        gi_text = gitignore_path.read_text(encoding="utf-8")
        gi_lines = [
            line.strip().lstrip("/")
            for line in gi_text.splitlines()
            if line.strip() and not line.startswith("#")
        ]
        if not any("data/original" in line for line in gi_lines):
            errors.append(".gitignore missing 'data/original/' exclusion")
        else:
            details.append("Verified .gitignore excludes 'data/original/'")

        if not any("surrogate_key_mapping.csv" in line for line in gi_lines):
            errors.append(f".gitignore missing '{SURROGATE_MAPPING_CSV.name}' exclusion")
        else:
            details.append(f"Verified .gitignore excludes '{SURROGATE_MAPPING_CSV.name}'")

    # 5. Check surrogate mapping file not in cloud data/synthetic directory
    if (BASE_DIR / "data" / "synthetic" / "surrogate_key_mapping.csv").exists():
        errors.append("Privacy violation: surrogate_key_mapping.csv present in data/synthetic/!")

    duration = time.time() - start_time
    passed = len(errors) == 0
    return GateResult(
        gate_name="Gate 2: Zero-PII Leak & Surrogate Key Audit",
        passed=passed,
        status="PASS" if passed else "FAIL",
        duration_seconds=duration,
        details=details,
        errors=errors,
    )


# ==============================================================================
# Release Gate 3: Automated Test Suite 100% Pass Rate
# ==============================================================================

def check_test_suite_pass_rate(
    skip_tests: bool = False, timeout_seconds: int = 180
) -> GateResult:
    """
    Gate 3: Executes pytest across the entire test suite and asserts 100% pass rate.
    Can be bypassed via skip_tests=True for rapid dry-runs.
    """
    start_time = time.time()
    details: List[str] = []
    errors: List[str] = []

    if skip_tests:
        return GateResult(
            gate_name="Gate 3: Automated Test Suite 100% Pass Rate",
            passed=True,
            status="SKIPPED",
            duration_seconds=0.0,
            details=["Test suite execution skipped by user (--skip-tests flag)."],
            errors=[],
        )

    cmd = [sys.executable, "-m", "pytest"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        summary_line = "No summary found"
        for line in reversed(stdout.splitlines()):
            if "passed" in line or "failed" in line or "error" in line:
                summary_line = line.strip("= ")
                break

        if proc.returncode != 0:
            errors.append(f"Pytest exited with non-zero return code {proc.returncode}")
            errors.append(f"Summary: {summary_line}")
            tail_lines = (stdout if stdout else stderr).splitlines()[-10:]
            errors.extend([f"  {line}" for line in tail_lines])
            if stderr and stdout:
                errors.append(f"  STDERR: {stderr[:300]}")
        else:
            details.append(f"Test suite passed 100%: {summary_line}")

    except subprocess.TimeoutExpired:
        errors.append(f"Pytest execution timed out after {timeout_seconds} seconds")
    except Exception as exc:
        errors.append(f"Failed to execute pytest: {str(exc)}")

    duration = time.time() - start_time
    passed = len(errors) == 0
    return GateResult(
        gate_name="Gate 3: Automated Test Suite 100% Pass Rate",
        passed=passed,
        status="PASS" if passed else "FAIL",
        duration_seconds=duration,
        details=details,
        errors=errors,
    )


# ==============================================================================
# Release Gate 4: Architectural Invariants & Hash Consistency
# ==============================================================================

def check_architectural_invariants() -> GateResult:
    """
    Gate 4: Validates Parquet SHA-256 disk checksums against metadata.json,
    verifies source immutability if raw data is present, and scans AST
    for zero Streamlit imports across src/ and all scripts/*.py.
    """
    start_time = time.time()
    details: List[str] = []
    errors: List[str] = []

    # 1. Parquet Checksums against metadata.json
    if not METADATA_JSON.exists():
        errors.append(f"metadata.json not found at {METADATA_JSON}")
    else:
        try:
            with open(METADATA_JSON, "r", encoding="utf-8") as f:
                meta = json.load(f)

            checksum_map = meta.get("artifact_checksums", {}) if isinstance(meta, dict) else {}
            canonical_artifacts = {
                "clean_orders.parquet": CLEAN_ORDERS_PARQUET,
                "route_aggregates.parquet": ROUTE_AGGREGATES_PARQUET,
                "baseline.parquet": BASELINE_PARQUET,
                "distance_sensitive.parquet": DISTANCE_PARQUET,
                "stress_test.parquet": STRESS_PARQUET,
            }

            for fname, expected_path in canonical_artifacts.items():
                if fname not in checksum_map:
                    errors.append(f"metadata.json missing checksum entry for '{fname}'")
                    continue

                expected_hash = checksum_map[fname]
                if not expected_path.exists():
                    errors.append(f"Artifact {fname} missing at {expected_path}")
                    continue

                actual_hash = compute_file_sha256(expected_path)
                if actual_hash != expected_hash:
                    errors.append(
                        f"Checksum mismatch on {fname}! Expected: {expected_hash}, Actual: {actual_hash}"
                    )
                else:
                    details.append(f"Verified SHA-256 for {fname}: {actual_hash[:16]}... (matches metadata.json)")
        except Exception as e:
            errors.append(f"Failed to read or parse metadata.json checksums: {e}")

    # 2. Source Data Immutability (AD-01) if present
    if RAW_DATA_PATH.exists():
        raw_hash = compute_file_sha256(RAW_DATA_PATH)
        if raw_hash != RAW_DATA_SHA256:
            errors.append(
                f"Source immutability violation! Expected SHA-256: {RAW_DATA_SHA256}, Got: {raw_hash}"
            )
        else:
            details.append(f"Verified source immutability (AD-01): {raw_hash[:16]}... (SHA-256 verified)")

    # 3. Zero Streamlit imports in src/ and all scripts/*.py (AD-12)
    py_files_to_scan = list((BASE_DIR / "src").glob("**/*.py"))
    py_files_to_scan.extend((BASE_DIR / "scripts").glob("*.py"))

    streamlit_violations: List[str] = []
    for fpath in py_files_to_scan:
        try:
            content = fpath.read_text(encoding="utf-8")
            parsed = ast.parse(content, filename=str(fpath))
            for node in ast.walk(parsed):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "streamlit" or alias.name.startswith("streamlit."):
                            streamlit_violations.append(f"{fpath.name}:{node.lineno}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == "streamlit" or node.module.startswith("streamlit.")):
                        streamlit_violations.append(f"{fpath.name}:{node.lineno}: from {node.module} import ...")
        except Exception as e:
            errors.append(f"Failed to parse AST for {fpath.name}: {e}")

    if streamlit_violations:
        errors.append(f"Strict decoupling violation! Streamlit imports found:\n  " + "\n  ".join(streamlit_violations))
    else:
        details.append(f"Verified zero Streamlit imports across {len(py_files_to_scan)} backend files in src/ and scripts/ (AD-12)")

    # 4. Invariant layer separation & provenance compliance (AD-02)
    app_py_path = BASE_DIR / "app.py"
    if app_py_path.exists():
        app_text = app_py_path.read_text(encoding="utf-8")
        if 'data_layer' in app_text and 'SYNTHETIC' in app_text and 'DERIVED' in app_text:
            details.append("Verified AD-02 layer provenance separation in application shell (app.py)")
        else:
            errors.append("app.py missing explicit AD-02 three-tier layer separation logic")
    else:
        errors.append("app.py application shell not found at project root")

    duration = time.time() - start_time
    passed = len(errors) == 0
    return GateResult(
        gate_name="Gate 4: Architectural Invariants & Hash Consistency",
        passed=passed,
        status="PASS" if passed else "FAIL",
        duration_seconds=duration,
        details=details,
        errors=errors,
    )


# ==============================================================================
# Release Gate 5: Comprehensive Documentation Suite Completeness
# ==============================================================================

def check_documentation_completeness() -> GateResult:
    """
    Gate 5: Verifies presence, non-empty status, and absence of unresolved placeholders
    in the 4 required publication documentation artifacts.
    """
    start_time = time.time()
    details: List[str] = []
    errors: List[str] = []

    doc_files = [
        ("Data Dictionary", BASE_DIR / "docs" / "data_dictionary.md", 5000),
        ("Methodology Specification", BASE_DIR / "docs" / "methodology.md", 5000),
        ("Synthetic Assumptions Disclosure", BASE_DIR / "docs" / "synthetic_assumptions.md", 5000),
        ("Project README", BASE_DIR / "README.md", 3000),
    ]

    placeholder_pattern = re.compile(r"\[(TODO|TBD|PLACEHOLDER|REPLACE_ME)\]", re.IGNORECASE)

    for title, doc_path, min_bytes in doc_files:
        if not doc_path.exists():
            errors.append(f"Missing documentation artifact: {title} ({doc_path.name})")
        else:
            size_bytes = doc_path.stat().st_size
            if size_bytes < min_bytes:
                errors.append(f"Documentation file {doc_path.name} is unexpectedly small: {size_bytes} bytes (min {min_bytes})")
            else:
                text = doc_path.read_text(encoding="utf-8")
                placeholders = placeholder_pattern.findall(text)
                if placeholders:
                    errors.append(f"Unresolved placeholders {set(placeholders)} detected in {doc_path.name}")
                else:
                    details.append(f"Verified {title} ({doc_path.name}): {size_bytes / 1024:.1f} KB, 0 placeholders")

    duration = time.time() - start_time
    passed = len(errors) == 0
    return GateResult(
        gate_name="Gate 5: Documentation Suite Completeness",
        passed=passed,
        status="PASS" if passed else "FAIL",
        duration_seconds=duration,
        details=details,
        errors=errors,
    )


# ==============================================================================
# Orchestration & Reporting
# ==============================================================================

def run_all_release_gates(
    skip_tests: bool = False,
    verbose: bool = False,
) -> ValidationReport:
    """Executes all 5 release gates and aggregates findings into a ValidationReport."""
    total_start = time.time()
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    gates: List[GateResult] = [
        check_cloud_artifact_loading(simulated_cloud=True),
        check_zero_pii_and_surrogates(),
        check_test_suite_pass_rate(skip_tests=skip_tests),
        check_architectural_invariants(),
        check_documentation_completeness(),
    ]

    overall_passed = all(g.passed for g in gates)
    total_duration = time.time() - total_start

    return ValidationReport(
        timestamp_utc=timestamp,
        overall_passed=overall_passed,
        total_duration_seconds=total_duration,
        gates=gates,
    )


def print_summary_table(report: ValidationReport, verbose: bool = False) -> None:
    """Prints a structured status table of gate results with ASCII-safe formatting."""
    print("\n" + "=" * 80)
    print(" NASSAU ROUTE INTELLIGENCE - CLOUD RELEASE GATE VERIFICATION")
    print("=" * 80)
    print(f" Timestamp (UTC): {report.timestamp_utc}")
    print(f" Total Duration : {report.total_duration_seconds:.2f} seconds")
    print("-" * 80)
    print(f" {'GATE':<56} | {'STATUS':<7} | {'TIME':<7}")
    print("-" * 80)

    for g in report.gates:
        if g.status == "PASS":
            status_symbol = "[PASS]"
        elif g.status == "SKIPPED":
            status_symbol = "[SKIP]"
        else:
            status_symbol = "[FAIL]"

        print(f" {g.gate_name:<56} | {status_symbol:<7} | {g.duration_seconds:>5.2f}s")
        if verbose or not g.passed:
            for detail in g.details:
                print(f"    +-- {detail}")
            for error in g.errors:
                print(f"    x-- [ERROR] {error}")

    print("=" * 80)
    if report.overall_passed:
        print(" RESULT: ALL RELEASE GATES PASSED (PRODUCTION READY FOR CLOUD DEPLOYMENT)")
    else:
        print(" RESULT: RELEASE GATES FAILED (HALTED PRE-DEPLOYMENT)")
    print("=" * 80 + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entrypoint for release gate validation."""
    parser = argparse.ArgumentParser(
        description="Verify release gates and zero-PII compliance for Nassau Route Intelligence."
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running the pytest test suite (useful for fast gate dry-runs).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display detailed diagnostic output for each check.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional path to output JSON validation report.",
    )

    args = parser.parse_args(argv)

    report = run_all_release_gates(
        skip_tests=args.skip_tests,
        verbose=args.verbose,
    )

    print_summary_table(report, verbose=args.verbose)

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"Validation report saved to: {out_path}")

    return 0 if report.overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
