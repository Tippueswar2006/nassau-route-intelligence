# Phase 3: Environment, Dependencies, and Build Validation

**Project:** Nassau Candy Shipping Route Intelligence  
**Audit Date:** 2026-10-25  
**Auditor:** Antigravity Senior Engineering & QA Lead  
**Execution Environment:** Windows 11 x64, PowerShell 5.1  

---

## 1. Runtime Environment Validation

| Runtime / Tool | Expected Version | Detected Active Version | Status | Notes |
|---|---|---|---|---|
| **Python** | `>= 3.10` | `3.10.11 (tags/v3.10.11:7d4cc5a)` | **VALID** | Tested via `.\.venv\Scripts\python.exe --version` |
| **Pytest** | `>= 7.4.0` | `9.1.1` | **VALID** | Tested via `.\.venv\Scripts\pytest.exe --version` |
| **Streamlit** | `>= 1.28.0` | `1.65.0` | **VALID** | Tested via `importlib.metadata.version('streamlit')` |
| **Virtual Environment**| `.venv` (virtualenv) | `C:\Users\preet\OneDrive\Desktop\factory\.venv` | **VALID** | Active virtual environment at project root |

---

## 2. Dependency Manifest Inspection & Package Audit

The project declares dependencies in `requirements.txt` and developer requirements in `requirements-dev.txt`.
Below is the verification comparing declared dependency constraints against currently installed versions:

| Package | Declared in `requirements.txt` | Installed Version | Compatibility Status | License / Notes |
|---|---|---|---|---|
| **pandas** | `>=2.0.0` | `2.3.3` | **COMPATIBLE** | BSD 3-Clause |
| **numpy** | `>=1.24.0` | `2.2.6` | **COMPATIBLE** | BSD 3-Clause |
| **pyarrow** | `>=14.0.0` | `25.0.1` | **COMPATIBLE** | Apache 2.0 |
| **pyyaml** | `>=6.0` | `6.0.3` | **COMPATIBLE** | MIT |
| **matplotlib** | `>=3.8.0` | `3.10.9` | **COMPATIBLE** | PSF-based |
| **seaborn** | `>=0.13.0` | `0.13.2` | **COMPATIBLE** | BSD 3-Clause |
| **streamlit** | `>=1.28.0` | `1.65.0` | **COMPATIBLE** | Apache 2.0 |
| **plotly** | `>=5.18.0` | `7.1.0` | **COMPATIBLE** | MIT |
| **pytest** | `>=7.4.0` (`requirements-dev.txt`) | `9.1.1` | **COMPATIBLE** | MIT |

### Auxiliary Installed Packages:
- `altair` (`6.2.2`), `anyio` (`4.15.1`), `attrs` (`26.1.0`), `click` (`8.5.0`), `jsonschema` (`4.26.0`), `pillow` (`12.3.0`), `pydeck` (`0.9.3`), `uvicorn` (`0.54.0`), `watchdog` (`6.0.0`).

### Package Manager Observation:
- Running `python -m pip` inside `.venv` returns `No module named pip`. The pre-provisioned virtual environment contains all required compiled site-packages and entry points (`pytest.exe`, `streamlit.exe`), but lacks `pip.exe` in its standalone script directory. While runtime and build commands execute without issue, package modifications would require bootstrapping `ensurepip` or using the global Python pip with `--target`.

---

## 3. Environment Configuration & Secret Hygiene

- **Secrets Audit:** An automated scan across all files, commit logs, and configuration tables confirmed that **zero API keys, credentials, database passwords, or personal access tokens are committed or exposed**.
- **External Environment Variables:** The application does not require any external environment variables or `.env` files. Gating between local mode (raw data access) and cloud mode (sanitized Parquet only) is dynamically determined by the presence of `data/original/nassau_candy.csv` via `src/load_data.py:get_deployment_mode()`.
- **Git Hygiene (`.gitignore`):**
  - Excludes `data/original/` (ensuring raw customer records are never pushed to cloud or version control).
  - Excludes `data/derived/surrogate_key_mapping.csv` (ensuring the local token mapping is never published).
  - Excludes `.venv`, Python bytecode caches (`__pycache__`), and pytest caches (`.pytest_cache`).

---

## 4. Build and Compilation Command Validation

### Command 1: Python Bytecode Static Compilation
```powershell
.\.venv\Scripts\python.exe -m compileall -q src pages scripts tests app.py
```
- **Exit Code:** `0`
- **Result:** Successful. Zero syntax errors or indentation defects detected across all 41 Python source and test files.

### Command 2: Data Pipeline Offline Build
```powershell
.\.venv\Scripts\python.exe scripts/build_data.py
```
- **Exit Code:** `0`
- **Execution Time:** 34.09 seconds
- **Output Summary:**
  1. Verified SHA-256 hash of `data/original/nassau_candy.csv` (`6ae9208e77ce410e...`).
  2. Flagged 313 duplicate rows across 307 content groups.
  3. Reconciled 4 core metrics (Rows: $10,194 \rightarrow 9,881$; Units: $38,654 \rightarrow 37,667$; Sales: $\$141,783.63 \rightarrow \$138,284.12$; Profit: $\$93,442.80 \rightarrow \$91,076.41$).
  4. Mapped 15 products to 5 factories with 100% coverage; attached Haversine distances to 59 state/province centroids.
  5. Generated 3 synthetic scenarios (Baseline: 4.29d mean; Distance-Sensitive: 4.30d mean; Stress-Test: 5.04d mean).
  6. Generated 5,044 surrogate Customer IDs and 8,549 surrogate Order IDs; stripped granular geographic PII (`City`, `Postal Code`).
  7. Serialized 5 Parquet artifacts, `transformation_log.json`, and `metadata.json`.

### Command 3: Publication Figure Generation
```powershell
.\.venv\Scripts\python.exe scripts/generate_paper_figures.py
```
- **Exit Code:** `0`
- **Execution Time:** 15.22 seconds
- **Output Summary:**
  - Exported 4 camera-ready publication figures to `docs/figures/` in both 300 DPI PNG and PDF formats (8 files total).

### Command 4: Streamlit Application Headless Startup
```powershell
.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.enableCORS false
```
- **Result:** Successfully initialized Uvicorn ASGI server on port 8501 without uncaught runtime exceptions or startup errors. Cleanly terminated after startup verification.

### Command 5: Release Gate Pre-Deployment Suite
```powershell
.\.venv\Scripts\python.exe scripts/validate_release_gates.py
```
- **Exit Code:** `0`
- **Execution Time:** 157.47 seconds
- **Status:** All 5 release gates PASSED (Simulated Cloud Startup, Zero-PII Audit, Automated Test Suite 100% Pass Rate, Architectural Invariants & Hashes, Documentation Completeness).

---

## 5. Setup Instructions Verification

The instructions provided in `README.md` (Sections 4, 5, 6, 7, and 8) were validated against actual repository behavior:
1. Virtual environment activation and dependency installation (`requirements.txt`) are accurately documented.
2. The command `python scripts/build_data.py` regenerates all Parquet tables and metadata cleanly.
3. The command `pytest` executes the full test suite without requiring extra parameters.
4. The command `python scripts/generate_paper_figures.py` correctly produces all figures in `docs/figures/`.
5. Headless verification flags (`--server.headless true --server.enableCORS false`) operate as described.
