"""
Audited CSV Export Engine for Nassau Route Intelligence.
Generates provenance-preserving CSV files with prepended metadata comment headers
documenting Data Layer, Scenario, Threshold, active filters, and generation timestamp.
Pure Python backend decoupled from UI libraries (Zero Streamlit imports).
"""

from datetime import datetime, timezone
import io
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd


HUMAN_COLUMN_RENAMES = {
    "route_key": "Route Key",
    "route_key_region": "Regional Route Key",
    "sample_size": "Sample Size (N)",
    "order_line_count": "Order Lines",
    "line_item_count": "Line Items",
    "total_units": "Total Units",
    "total_sales": "Gross Revenue ($)",
    "total_gross_profit": "Gross Profit ($)",
    "distance_km": "Distance (km)",
    "mean_lead_time": "Mean Lead Time (Days)",
    "median_lead_time": "Median Lead Time (Days)",
    "std_lead_time": "Lead Time Std Dev (Days)",
    "p75_lead_time": "P75 Lead Time (Days)",
    "p90_lead_time": "P90 Lead Time (Days)",
    "min_lead_time": "Min Lead Time (Days)",
    "max_lead_time": "Max Lead Time (Days)",
    "delay_rate": "Delay Rate",
    "delayed_count": "Delayed Orders",
    "res_score": "Route Efficiency Score (RES)",
    "res_mode_adj": "Mode-Adjusted RES",
    "res_raw": "Raw Lead Time RES",
    "speed_only_score": "Speed-Only Score (100/0)",
    "speed_penalty": "Speed Penalty",
    "variability_penalty": "Variability Penalty",
    "rank_delta": "Rank Delta (Raw - ModeAdj)",
    "is_eligible": "Eligible (N >= 30)",
    "is_low_sample": "Low Sample (N < 30)",
    "is_bottleneck": "Critical Bottleneck",
    "is_watchlist": "Watchlist",
    "quadrant_category": "Quadrant Category",
    "lead_time_days": "Lead Time (Days)",
    "mode_adjusted_lead_time": "Mode-Adjusted Lead Time (Days)",
    "is_delayed": "Delayed",
}


def sanitize_export_dataframe(df: pd.DataFrame, human_headers: bool = True) -> pd.DataFrame:
    """
    Cleans DataFrame for public/audited export:
    - Drops raw system identifiers (e.g. Row ID).
    - Renames internal column slugs to human-readable headers if requested.
    """
    df = df.copy()

    # Drop internal technical columns
    drop_cols = [c for c in ["Row ID", "analysis_route_key", "analysis_destination"] if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    if human_headers:
        rename_map = {c: HUMAN_COLUMN_RENAMES[c] for c in df.columns if c in HUMAN_COLUMN_RENAMES}
        df = df.rename(columns=rename_map)

    return df


def create_export_csv(
    df: pd.DataFrame,
    metadata: Optional[Dict[str, Any]] = None,
    human_headers: bool = True,
) -> bytes:
    """
    Generates an audited CSV file with prepended commented metadata header lines (prefixed with #).

    Parameters:
      - df: Tabular dataset to export
      - metadata: Dictionary containing:
          - layer: Data Layer (ORIGINAL, DERIVED, SYNTHETIC)
          - scenario: Active scenario name (e.g. baseline, distance_sensitive, stress_test)
          - delay_threshold: Delay threshold used (e.g. 5.0)
          - filters: Dictionary of active user filter settings
          - timestamp_utc: Optional ISO timestamp (defaults to current UTC time)
      - human_headers: If True, renames internal slugs to human-readable column headers

    Returns:
      UTF-8 encoded bytes containing the complete commented header and CSV data.
    """
    if metadata is None:
        metadata = {}

    layer = str(metadata.get("layer", df.get("data_layer", pd.Series(["UNSPECIFIED"])).iloc[0] if "data_layer" in df.columns and len(df) > 0 else "UNSPECIFIED")).upper()
    scenario = metadata.get("scenario", "none")
    threshold = metadata.get("delay_threshold", 5.0)
    filters = metadata.get("filters", {})
    ts = metadata.get("timestamp_utc", datetime.now(timezone.utc).isoformat())

    # Build prepended comment header
    header_lines = [
        "# ==============================================================================",
        "# NASSAU CANDY ROUTE INTELLIGENCE — AUDITED DATA EXPORT",
        f"# Export Timestamp UTC: {ts}",
        f"# Data Layer: {layer}",
    ]

    if layer == "SYNTHETIC":
        header_lines.append(f"# Active Scenario: {scenario}")
        header_lines.append("# Simulation Notice: Lead times are synthetic calibrated values (Seed 42). Not actual carrier stamps.")
    elif layer == "ORIGINAL":
        header_lines.append("# Source Notice: Direct raw distributor records (Local development layer).")
    else:
        header_lines.append("# Derived Notice: Cleaned, deduplicated, and mapped historical distributor records.")

    header_lines.append(f"# Delay Threshold: {threshold} days (Strict inequality: Lead Time > Threshold)")
    header_lines.append("# COGS Disclaimer: Cost reflects manufacturing COGS only; freight shipping costs are not present.")

    # Filter details
    if filters:
        header_lines.append("# Active Global Filters:")
        for k, v in filters.items():
            if v:
                header_lines.append(f"#   - {k}: {v}")
            else:
                header_lines.append(f"#   - {k}: All")
    else:
        header_lines.append("# Active Global Filters: None (Unfiltered Population)")

    header_lines.append("# ==============================================================================")
    header_text = "\n".join(header_lines) + "\n"

    # Format data
    export_df = sanitize_export_dataframe(df, human_headers=human_headers)
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    full_output = header_text + csv_data
    return full_output.encode("utf-8")


def parse_export_header(csv_content: Union[str, bytes]) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Parses an audited CSV export:
      - Extracts metadata attributes from prepended # comment lines.
      - Loads the underlying tabular rows into a pandas DataFrame.

    Returns:
      (metadata_dict, data_df)
    """
    if isinstance(csv_content, bytes):
        text = csv_content.decode("utf-8")
    else:
        text = csv_content

    lines = text.splitlines()
    header_lines = []
    data_lines = []

    for line in lines:
        if line.startswith("#"):
            header_lines.append(line)
        else:
            data_lines.append(line)

    meta: Dict[str, Any] = {}
    for line in header_lines:
        clean = line.lstrip("#").strip()
        if clean.startswith("Export Timestamp UTC:"):
            meta["timestamp_utc"] = clean.split(":", 1)[1].strip()
        elif clean.startswith("Data Layer:"):
            meta["layer"] = clean.split(":", 1)[1].strip()
        elif clean.startswith("Active Scenario:"):
            meta["scenario"] = clean.split(":", 1)[1].strip()
        elif clean.startswith("Delay Threshold:"):
            meta["delay_threshold"] = clean.split(":", 1)[1].strip()

    # Read CSV data lines into DataFrame
    data_text = "\n".join(data_lines)
    data_df = pd.read_csv(io.StringIO(data_text)) if data_lines else pd.DataFrame()

    return meta, data_df
