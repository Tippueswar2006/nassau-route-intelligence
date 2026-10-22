"""
Automated Test Suite for Publication Figure Generation Script.
Verifies compliance with Story 6.2, FR-15, and AD-02:
- Standalone CLI execution (`scripts/generate_paper_figures.py`)
- High-resolution (300 DPI) output in `docs/figures/`
- Existence of lead-time distributions, RES quadrant scatter, scenario comparison bars, and sensitivity trade-offs
- Support for dual formats (PNG and PDF)
- Non-empty byte sizes and valid image metadata
- Decoupled backend architecture (zero Streamlit imports)
"""

import ast
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import warnings

# Suppress upstream Seaborn/Matplotlib categorical pending deprecations
warnings.filterwarnings("ignore", category=PendingDeprecationWarning, module="seaborn")

from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import pytest

from src.config import (
    BASE_DIR,
    BASELINE_PARQUET,
    DEFAULT_DELAY_THRESHOLD,
    DISTANCE_PARQUET,
    STRESS_PARQUET,
)
from src.route_analysis import aggregate_routes
from scripts.generate_paper_figures import (
    DEFAULT_OUTPUT_DIR,
    generate_all_figures,
    generate_fig1_lead_time_distributions,
    generate_fig2_res_quadrant_scatter,
    generate_fig3_scenario_comparison_bars,
    generate_fig4_weight_sensitivity_and_thresholds,
)


SCRIPT_PATH = BASE_DIR / "scripts" / "generate_paper_figures.py"


# ==============================================================================
# 1. Architecture & Code Invariants
# ==============================================================================

def test_no_streamlit_imports_in_figure_script():
    """Asserts that scripts/generate_paper_figures.py has zero Streamlit imports."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    parsed = ast.parse(content, filename=str(SCRIPT_PATH))

    violations = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "streamlit" in alias.name:
                    violations.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and "streamlit" in node.module:
                violations.append(node.module)

    assert not violations, f"Streamlit imports forbidden in figure generation script: {violations}"


# ==============================================================================
# 2. Individual Figure Generator Functions
# ==============================================================================

def test_individual_figure_generators(tmp_path):
    """
    Verifies that all 4 individual figure generator functions execute cleanly,
    return valid Matplotlib Figure objects, and export files to disk.
    """
    base_df = pd.read_parquet(BASELINE_PARQUET)
    dist_df = pd.read_parquet(DISTANCE_PARQUET)
    stress_df = pd.read_parquet(STRESS_PARQUET)
    base_agg = aggregate_routes(base_df, level="state", rollup_small_factories=False)

    # 1. Figure 1
    fig1, paths1 = generate_fig1_lead_time_distributions(
        base_df, dist_df, stress_df, output_dir=tmp_path, dpi=100, formats=["png", "pdf"]
    )
    assert isinstance(fig1, plt.Figure)
    assert len(paths1) == 2
    for p in paths1:
        assert p.exists()
        assert p.stat().st_size > 1000
    plt.close(fig1)

    # 2. Figure 2
    fig2, paths2 = generate_fig2_res_quadrant_scatter(
        base_agg, output_dir=tmp_path, dpi=100, formats=["png", "pdf"]
    )
    assert isinstance(fig2, plt.Figure)
    assert len(paths2) == 2
    for p in paths2:
        assert p.exists()
        assert p.stat().st_size > 1000
    plt.close(fig2)

    # 3. Figure 3
    fig3, paths3 = generate_fig3_scenario_comparison_bars(
        base_df, dist_df, stress_df, output_dir=tmp_path, dpi=100, formats=["png", "pdf"]
    )
    assert isinstance(fig3, plt.Figure)
    assert len(paths3) == 2
    for p in paths3:
        assert p.exists()
        assert p.stat().st_size > 1000
    plt.close(fig3)

    # 4. Figure 4
    fig4, paths4 = generate_fig4_weight_sensitivity_and_thresholds(
        base_agg, output_dir=tmp_path, dpi=100, formats=["png", "pdf"]
    )
    assert isinstance(fig4, plt.Figure)
    assert len(paths4) == 2
    for p in paths4:
        assert p.exists()
        assert p.stat().st_size > 1000
    plt.close(fig4)


# ==============================================================================
# 3. Master Generation & 300 DPI Verification
# ==============================================================================

def test_generate_all_figures_master_call(tmp_path):
    """
    Verifies that generate_all_figures produces all 4 publication figures
    in both PNG and PDF formats at 300 DPI resolution.
    """
    results = generate_all_figures(
        output_dir=tmp_path,
        dpi=300,
        formats=["png", "pdf"],
    )

    assert len(results) == 4
    for key in ["fig1", "fig2", "fig3", "fig4"]:
        assert key in results
        paths = results[key]
        assert len(paths) == 2

        # Check extensions
        exts = {p.suffix.lower() for p in paths}
        assert exts == {".png", ".pdf"}

        for p in paths:
            assert p.exists(), f"File does not exist: {p}"
            # Substantial file size > 20 KB
            assert p.stat().st_size > 20_000, f"File unexpectedly small ({p.stat().st_size} bytes): {p}"

            # Verify PNG 300 DPI metadata
            if p.suffix.lower() == ".png":
                with Image.open(p) as img:
                    dpi = img.info.get("dpi")
                    assert dpi is not None, f"PNG missing DPI metadata: {p}"
                    assert round(dpi[0]) == 300, f"Expected 300 DPI X, got {dpi[0]}"
                    assert round(dpi[1]) == 300, f"Expected 300 DPI Y, got {dpi[1]}"
                    assert img.size[0] >= 2000, f"Expected high resolution width >= 2000, got {img.size[0]}"


# ==============================================================================
# 4. CLI Execution
# ==============================================================================

def test_generate_paper_figures_cli(tmp_path):
    """Verifies executing scripts/generate_paper_figures.py via command line."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--output-dir",
        str(tmp_path),
        "--dpi",
        "150",
        "--formats",
        "png,pdf",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"CLI command failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "Done: 4 figures (8 files) successfully exported" in proc.stdout

    # Verify all 8 files were written
    files = list(tmp_path.glob("*.*"))
    assert len(files) == 8


# ==============================================================================
# 5. Error Handling & Edge Cases
# ==============================================================================

def test_generate_all_figures_missing_artifact_error(tmp_path):
    """Verifies that FileNotFoundError is raised when required synthetic artifact is missing."""
    with patch("scripts.generate_paper_figures.BASELINE_PARQUET", tmp_path / "nonexistent.parquet"):
        with pytest.raises(FileNotFoundError, match="Required synthetic artifact not found"):
            generate_all_figures(output_dir=tmp_path)


def test_empty_dataframe_handling(tmp_path):
    """Verifies that individual figure generators handle empty DataFrames gracefully without crashing."""
    empty_df = pd.DataFrame()

    fig1, p1 = generate_fig1_lead_time_distributions(empty_df, empty_df, empty_df, output_dir=tmp_path)
    assert len(p1) == 2
    plt.close(fig1)

    fig2, p2 = generate_fig2_res_quadrant_scatter(empty_df, output_dir=tmp_path)
    assert len(p2) == 2
    plt.close(fig2)

    fig3, p3 = generate_fig3_scenario_comparison_bars(empty_df, empty_df, empty_df, output_dir=tmp_path)
    assert len(p3) == 2
    plt.close(fig3)

    fig4, p4 = generate_fig4_weight_sensitivity_and_thresholds(empty_df, output_dir=tmp_path)
    assert len(p4) == 2
    plt.close(fig4)


def test_unsupported_format_error(tmp_path):
    """Verifies that requesting an unsupported file extension raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported figure format 'xyz'"):
        generate_all_figures(output_dir=tmp_path, formats=["xyz"])


def test_custom_single_format_cli(tmp_path):
    """Verifies that specifying a single format (e.g. svg) exports only that format."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--output-dir",
        str(tmp_path),
        "--dpi",
        "100",
        "--formats",
        "svg",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    files = list(tmp_path.glob("*.svg"))
    assert len(files) == 4
