#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


RAW_EXPECTED_COLUMNS: Tuple[str, ...] = (
    "age",
    "steps_per_day",
    "active_minutes",
    "calories_burned",
    "sleep_hours",
    "hydration_liters",
    "bmi",
    "workouts_per_week",
    "muscle_mass_ratio",
    "body_fat_percentage",
    "heart_rate_resting",
    "heart_rate_avg",
    "continuous_exercise_days",
    "efficiency_score",
    "calorie_efficiency",
)


RANGE_RULES = {
    "age": (0, 120),
    "steps_per_day": (0, 100_000),
    "active_minutes": (0, 24 * 60),
    "calories_burned": (0, 20_000),
    "sleep_hours": (0, 24),
    "hydration_liters": (0, 20),
    "bmi": (0, 100),
    "workouts_per_week": (0, 21),
    "muscle_mass_ratio": (0, 1),
    "body_fat_percentage": (0, 1),
    "muscle_mass_pct": (0, 100),
    "body_fat_pct": (0, 100),
    "heart_rate_resting": (20, 200),
    "heart_rate_avg": (20, 240),
    "continuous_exercise_days": (0, 3650),
    "efficiency_score": (0, 10),
}


LABEL_MAP = {
    "low efficiency": "low",
    "moderate": "moderate",
    "high efficiency": "high",
}


@dataclass(frozen=True)
class Profile:
    n_rows: int
    n_cols: int
    missing_by_col: Dict[str, int]
    missing_total: int
    duplicate_rows: int
    constant_cols: Dict[str, Any]
    label_values: Dict[str, int]
    range_violations: Dict[str, int]
    notes: List[str]


def _snake_case(name: str) -> str:
    """
    Convert a string to snake_case: lowercase, spaces to underscores, and strip whitespace.
    """
    return name.strip().lower().replace(" ", "_")


def load_dataset(path: Path, *, sample_rows: int | None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if sample_rows is not None:
        df = df.head(sample_rows).copy()
    return df


def profile_dataset(df: pd.DataFrame) -> Profile:
    """
    The function performs several operations on the DataFrame to gather information about the dataset:

    It calculates the number of missing values for each column in the DataFrame and stores them in a dictionary missing_by_col.
    It calculates the total number of missing values in the DataFrame and stores it in a variable missing_total.
    It calculates the number of duplicate rows in the DataFrame and stores it in a variable duplicate_rows.
    It identifies columns that have only one unique value (constant columns) and stores them in a dictionary constant_cols.
    It counts the number of occurrences of each unique value in the column "calorie_efficiency" and stores them in a dictionary label_values.
    It checks if the values in each column are within the specified range defined in the RANGE_RULES dictionary and stores the number of violations in a dictionary range_violations.
    It checks for specific notes related to the dataset and stores them in a list notes.
    Finally, it creates a 
    Profile
    object with the gathered information and returns it.
    The 
    Profile
    object contains the following attributes:

    n_rows: the number of rows in the DataFrame
    n_cols: the number of columns in the DataFrame
    missing_by_col: a dictionary of missing values for each column
    missing_total: the total number of missing values in the DataFrame
    duplicate_rows: the number of duplicate rows in the DataFrame
    constant_cols: a dictionary of constant columns and their values
    label_values: a dictionary of unique values in the "calorie_efficiency" column and their counts
    range_violations: a dictionary of columns and the number of violations
    notes: a list of additional notes about the dataset
    """
    missing_by_col = df.isna().sum().to_dict()
    missing_total = int(sum(missing_by_col.values()))
    duplicate_rows = int(df.duplicated().sum())

    constant_cols: Dict[str, Any] = {}
    for col in df.columns:
        # Use dropna=False so "all missing" would count as constant too
        uniques = df[col].nunique(dropna=False)
        if uniques == 1:
            constant_cols[col] = df[col].iloc[0]

    label_values: Dict[str, int] = {}
    if "calorie_efficiency" in df.columns:
        label_values = (
            df["calorie_efficiency"]
            .astype("string")
            .fillna("<missing>")
            .str.strip()
            .value_counts()
            .head(20)
            .to_dict()
        )

    range_violations: Dict[str, int] = {}
    for col, (lo, hi) in RANGE_RULES.items():
        if col not in df.columns:
            continue
        s = df[col]
        if not pd.api.types.is_numeric_dtype(s):
            range_violations[col] = int(s.notna().sum())
            continue
        bad = (s < lo) | (s > hi)
        range_violations[col] = int(bad.sum())

    notes: List[str] = []
    if "calories_burned" in constant_cols:
        notes.append(
            "Column 'calories_burned' is constant; likely a placeholder or redundant."
        )
    if "body_fat_percentage" in df.columns:
        mx = float(pd.to_numeric(df["body_fat_percentage"], errors="coerce").max())
        if mx <= 1.0:
            notes.append(
                "Column 'body_fat_percentage' appears stored as a fraction (0–1) despite being named as a percentage."
            )
    if "efficiency_score" in df.columns:
        score = pd.to_numeric(df["efficiency_score"], errors="coerce")
        pct_gt_1 = float((score > 1).mean())
        if pct_gt_1 > 0.05:
            notes.append(
                f"Column 'efficiency_score' has mixed scale: {pct_gt_1:.1%} of records are > 1."
            )

    return Profile(
        n_rows=int(df.shape[0]),
        n_cols=int(df.shape[1]),
        missing_by_col={k: int(v) for k, v in missing_by_col.items()},
        missing_total=missing_total,
        duplicate_rows=duplicate_rows,
        constant_cols=constant_cols,
        label_values={str(k): int(v) for k, v in label_values.items()},
        range_violations={k: int(v) for k, v in range_violations.items()},
        notes=notes,
    )


def clean_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    df = df_raw.copy()

    rename_map = {c: _snake_case(c) for c in df.columns}
    df = df.rename(columns=rename_map)

    # Standardize label values (consistency).
    if "calorie_efficiency" in df.columns:
        df["calorie_efficiency"] = (
            df["calorie_efficiency"]
            .astype("string")
            .str.strip()
            .str.lower()
            .map(lambda x: LABEL_MAP.get(x, x))
        )

    # Convert fractional "percentage" fields into percentage points (0–100).
    conversions: Dict[str, str] = {}
    for col, new_col in [
        ("body_fat_percentage", "body_fat_pct"),
        ("muscle_mass_ratio", "muscle_mass_pct"),
    ]:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        if float(s.max()) <= 1.0:
            df[new_col] = (s * 100).round(2)
            conversions[col] = f"scaled_to_percent_points -> {new_col}"
            df = df.drop(columns=[col])
        else:
            # Keep original if already in 0–100; just rename for clarity.
            df[new_col] = s.round(2)
            conversions[col] = f"renamed -> {new_col}"
            df = df.drop(columns=[col])

    # Heart rates should be integers in BPM.
    for col in ["heart_rate_resting", "heart_rate_avg"]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            df[col] = s.round().astype("Int64")

    # Add surrogate key for normalization.
    df.insert(0, "record_id", np.arange(1, len(df) + 1, dtype=np.int64))

    # Drop constant columns (keep them in metadata so the decision is explicit).
    constant_cols: Dict[str, Any] = {}
    for col in list(df.columns):
        if col == "record_id":
            continue
        if df[col].nunique(dropna=False) == 1:
            constant_cols[col] = df[col].iloc[0]
            df = df.drop(columns=[col])

    metadata = {
        "rename_map": rename_map,
        "conversions": conversions,
        "dropped_constant_columns": constant_cols,
    }
    return df, metadata


def normalize_tables(df_clean: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    keep = set(df_clean.columns)
    if "record_id" not in keep:
        raise ValueError("Expected 'record_id' in cleaned dataframe.")

    demographic_cols = [c for c in ["record_id", "age", "bmi", "muscle_mass_pct", "body_fat_pct"] if c in keep]
    activity_cols = [
        c
        for c in [
            "record_id",
            "steps_per_day",
            "active_minutes",
            "workouts_per_week",
            "continuous_exercise_days",
            "sleep_hours",
            "hydration_liters",
            "heart_rate_resting",
            "heart_rate_avg",
        ]
        if c in keep
    ]
    outcome_cols = [c for c in ["record_id", "efficiency_score", "calorie_efficiency"] if c in keep]

    return {
        "demographics.csv": df_clean[demographic_cols].copy(),
        "activity.csv": df_clean[activity_cols].copy(),
        "outcomes.csv": df_clean[outcome_cols].copy(),
    }


def _md_table(rows: Iterable[Tuple[str, Any]]) -> str:
    rows = list(rows)
    if not rows:
        return "_(none)_\n"
    out = ["| Item | Value |", "|---|---:|"]
    for k, v in rows:
        out.append(f"| {k} | {v} |")
    return "\n".join(out) + "\n"


def write_report(
    output_dir: Path,
    *,
    source_path: Path,
    profile_before: Profile,
    profile_after: Profile,
    metadata: Dict[str, Any],
    sample_rows: int | None,
) -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_path = output_dir / "calorie_efficiency_reengineering_report.md"

    pct = lambda n, d: (100.0 * n / d) if d else 0.0

    issues_before = [
        ("Rows", profile_before.n_rows),
        ("Columns", profile_before.n_cols),
        ("Missing values (total)", profile_before.missing_total),
        ("Duplicate rows", profile_before.duplicate_rows),
        ("Constant columns", len(profile_before.constant_cols)),
    ]
    issues_after = [
        ("Rows", profile_after.n_rows),
        ("Columns", profile_after.n_cols),
        ("Missing values (total)", profile_after.missing_total),
        ("Duplicate rows", profile_after.duplicate_rows),
        ("Constant columns", len(profile_after.constant_cols)),
    ]

    dropped_constants = metadata.get("dropped_constant_columns") or {}

    md = []
    md.append("# Calorie Efficiency Dataset — Data Re-engineering Report\n")
    md.append(f"- Generated: {now}\n")
    md.append(f"- Source file: `{source_path.name}`\n")
    if sample_rows is not None:
        md.append(f"- Mode: sample of first {sample_rows:,} rows\n")
    md.append("\n")

    md.append("## 2.1 Data Value Awareness & Dataset Selection (Group)\n")
    md.append(
        "Dataset selected: `calorie_efficiency_dataset.csv` (local file provided for coursework). "
        "It appears to contain fitness and health-related metrics and a categorical outcome label.\n\n"
        "Why improving the data is valuable: even small inconsistencies in health/fitness datasets can "
        "cause misleading analytics, unfair comparisons between individuals, or incorrect model training labels. "
        "Improving consistency and semantics (units, labels, redundant fields) supports responsible reporting and "
        "more trustworthy downstream use.\n\n"
    )

    md.append("## 2.2 Practical Data Profiling (Individual)\n")
    md.append("### Completeness & Duplication\n")
    md.append("**Before**\n\n")
    md.append(_md_table(issues_before))
    md.append("\n**After**\n\n")
    md.append(_md_table(issues_after))
    md.append("\n")

    md.append("### Consistency & Accuracy Checks\n")
    if profile_before.notes:
        md.append("Key observations (before):\n\n")
        for note in profile_before.notes:
            md.append(f"- {note}\n")
        md.append("\n")

    md.append("Top label values (before):\n\n")
    md.append(_md_table(profile_before.label_values.items()))
    md.append("\n")

    md.append("Range-rule violations (before, count of records outside expected bounds):\n\n")
    worst = sorted(profile_before.range_violations.items(), key=lambda kv: -kv[1])[:10]
    md.append(_md_table(worst))
    md.append("\n")

    md.append("## 2.3 Data Re-engineering Execution (Group)\n")
    md.append("Actions applied:\n\n")
    md.append("- Standardized column naming to `snake_case`.\n")
    md.append("- Standardized `calorie_efficiency` labels to `low` / `moderate` / `high`.\n")
    md.append(
        "- Converted fractional fields into percentage points (e.g. `body_fat_percentage` → `body_fat_pct`).\n"
    )
    md.append("- Rounded heart-rate fields to integer BPM.\n")
    if dropped_constants:
        md.append(
            "- Dropped constant columns to reduce redundancy, preserving the constant values in metadata.\n"
        )
    md.append(
        "- Normalized the wide table into 3 tables (`demographics`, `activity`, `outcomes`) keyed by `record_id`.\n\n"
    )
    md.append("Justification highlights:\n\n")
    md.append(
        "- **Consistency & integrity**: unit/label standardization reduces misinterpretation risk.\n"
    )
    md.append(
        "- **Quality & responsibility**: removing redundant placeholders avoids false confidence in metrics.\n"
    )
    md.append(
        "- **Maintainability**: normalization clarifies ownership of attributes and supports reuse in different analyses.\n\n"
    )

    md.append("## 2.4 Validation, Ethics & Quality Review (Individual)\n")
    md.append("Validation summary:\n\n")
    md.append(
        f"- Duplicate rows: {profile_before.duplicate_rows:,} → {profile_after.duplicate_rows:,}\n"
    )
    md.append(
        f"- Missing values (total): {profile_before.missing_total:,} → {profile_after.missing_total:,}\n"
    )
    md.append(
        f"- Constant columns detected: {len(profile_before.constant_cols)} → {len(profile_after.constant_cols)}\n"
    )
    if dropped_constants:
        md.append("\nDropped constant columns (value preserved):\n\n")
        md.append(_md_table(dropped_constants.items()))
    md.append("\nEthics reflection prompts (edit for your submission):\n\n")
    md.append(
        "- Privacy: dataset contains no direct identifiers; `record_id` is a surrogate key for engineering only.\n"
    )
    md.append(
        "- Bias/fairness: health-related metrics can encode population bias; avoid overgeneralizing findings.\n"
    )
    md.append(
        "- Data loss: transformations were documented; avoid deleting records unless clearly justified.\n\n"
    )

    md.append("## 2.5 Advocacy & Professional Reflection (Group)\n")
    md.append(
        "Advocacy artefact: see `advocacy_infographic.png` in the output folder. It summarizes why "
        "re-engineering improves trust and decision quality.\n\n"
    )
    md.append(
        "Reflection prompt: describe how your attitude toward data quality changed after seeing how small "
        "inconsistencies (units, labels, redundant fields) can create downstream risks.\n"
    )

    report_path.write_text("".join(md), encoding="utf-8")
    return report_path


def write_infographic(output_dir: Path, *, profile_before: Profile, profile_after: Profile) -> Path:
    os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".mplconfig"))
    (output_dir / ".mplconfig").mkdir(parents=True, exist_ok=True)

    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 6), dpi=200)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    title = "Why Data Re-engineering Matters"
    subtitle = "Calorie efficiency dataset: quality, integrity, responsibility"
    ax.text(0.05, 0.92, title, fontsize=22, fontweight="bold")
    ax.text(0.05, 0.875, subtitle, fontsize=12, color="#333333")

    before = {
        "Rows": profile_before.n_rows,
        "Columns": profile_before.n_cols,
        "Missing": profile_before.missing_total,
        "Duplicates": profile_before.duplicate_rows,
        "Constant cols": len(profile_before.constant_cols),
    }
    after = {
        "Rows": profile_after.n_rows,
        "Columns": profile_after.n_cols,
        "Missing": profile_after.missing_total,
        "Duplicates": profile_after.duplicate_rows,
        "Constant cols": len(profile_after.constant_cols),
    }

    ax.text(0.05, 0.78, "Before vs After (high-level)", fontsize=14, fontweight="bold")
    y = 0.73
    for k in before.keys():
        ax.text(0.06, y, k, fontsize=12)
        ax.text(0.32, y, f"{before[k]:,}", fontsize=12, family="monospace")
        ax.text(0.48, y, "→", fontsize=12)
        ax.text(0.52, y, f"{after[k]:,}", fontsize=12, family="monospace")
        y -= 0.055

    ax.text(0.05, 0.40, "Professional values supported", fontsize=14, fontweight="bold")
    bullets = [
        "Data quality: clear units, consistent labels",
        "Integrity: documented transformations and decisions",
        "Responsibility: reduce misleading analytics risk",
        "Ethics: privacy-aware handling; avoid unfair conclusions",
    ]
    y = 0.35
    for b in bullets:
        ax.text(0.06, y, f"• {b}", fontsize=12, color="#222222")
        y -= 0.055

    out_path = output_dir / "advocacy_infographic.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile, re-engineer, validate, and normalize the calorie efficiency dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("calorie_efficiency_dataset.csv"),
        help="Path to raw CSV dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("out_calorie_efficiency"),
        help="Directory for outputs (reports, cleaned data).",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=None,
        help="If set, only process the first N rows (faster iteration).",
    )
    parser.add_argument(
        "--no-write-datasets",
        action="store_true",
        help="Only write report/infographic/metadata (skip writing cleaned CSV outputs).",
    )
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df_raw = load_dataset(args.input, sample_rows=args.sample_rows)
    missing_cols = [c for c in RAW_EXPECTED_COLUMNS if c not in df_raw.columns]
    if missing_cols:
        raise SystemExit(f"Missing expected columns: {missing_cols}")

    before = profile_dataset(df_raw)
    df_clean, metadata = clean_dataset(df_raw)
    after = profile_dataset(df_clean)

    # Write outputs
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str), encoding="utf-8"
    )
    write_report(
        output_dir,
        source_path=args.input,
        profile_before=before,
        profile_after=after,
        metadata=metadata,
        sample_rows=args.sample_rows,
    )
    write_infographic(output_dir, profile_before=before, profile_after=after)

    if not args.no_write_datasets:
        df_clean.to_csv(output_dir / "calorie_efficiency_cleaned_wide.csv", index=False)
        tables = normalize_tables(df_clean)
        for name, tdf in tables.items():
            tdf.to_csv(output_dir / name, index=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
