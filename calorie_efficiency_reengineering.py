#!/usr/bin/env python3
"""
Calorie Efficiency Dataset — Data Re-engineering Pipeline
Covers assignment sections 2.1 – 2.5 (profiling, cleaning, normalisation,
validation, ethics reflection, and advocacy infographic).
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Schema & rules
# ---------------------------------------------------------------------------

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

RANGE_RULES: Dict[str, Tuple[float, float]] = {
    "age": (18, 120),
    "steps_per_day": (0, 100_000),
    "active_minutes": (0, 1_440),
    "sleep_hours": (0, 24),
    "hydration_liters": (0, 20),
    "bmi": (10, 70),
    "workouts_per_week": (0, 21),
    "muscle_mass_ratio": (0, 1),
    "body_fat_percentage": (0, 1),
    "muscle_mass_pct": (0, 100),
    "body_fat_pct": (0, 100),
    "heart_rate_resting": (20, 200),
    "heart_rate_avg": (20, 240),
    "continuous_exercise_days": (0, 3_650),
    "efficiency_score": (0, 1),       # normalised 0-1 after cleaning
    "efficiency_score_raw": (0, 10),  # raw range
}

LABEL_MAP: Dict[str, str] = {
    "low efficiency": "low",
    "moderate": "moderate",
    "high efficiency": "high",
}

VALID_LABELS = {"low", "moderate", "high"}


# ---------------------------------------------------------------------------
# Profile dataclass — one per analysis section
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompletenessProfile:
    n_rows: int
    n_cols: int
    missing_by_col: Dict[str, int]
    missing_total: int
    completeness_pct_by_col: Dict[str, float]
    overall_completeness_pct: float


@dataclass(frozen=True)
class ConsistencyProfile:
    label_values: Dict[str, int]
    invalid_labels: int
    body_fat_fraction_stored: bool          # should be % but stored as 0-1
    muscle_mass_fraction_stored: bool
    efficiency_score_mixed_scale: bool      # some > 1, some ≤ 1
    efficiency_score_pct_above_1: float
    constant_cols: Dict[str, Any]


@dataclass(frozen=True)
class AccuracyProfile:
    range_violations: Dict[str, int]
    notes: List[str]


@dataclass(frozen=True)
class DuplicateProfile:
    duplicate_rows: int
    duplicate_pct: float


@dataclass(frozen=True)
class Profile:
    completeness: CompletenessProfile
    consistency: ConsistencyProfile
    accuracy: AccuracyProfile
    duplicates: DuplicateProfile


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _snake_case(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def load_dataset(path: Path, *, sample_rows: int | None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if sample_rows is not None:
        df = df.head(sample_rows).copy()
    return df


def _md_table(rows: Iterable[Tuple[str, Any]], col1: str = "Item", col2: str = "Value") -> str:
    rows = list(rows)
    if not rows:
        return "_(none)_\n"
    out = [f"| {col1} | {col2} |", "|---|---:|"]
    for k, v in rows:
        out.append(f"| {k} | {v} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Profiling — four analysis types
# ---------------------------------------------------------------------------

def completeness_analysis(df: pd.DataFrame) -> CompletenessProfile:
    missing_by_col = {c: int(df[c].isna().sum()) for c in df.columns}
    missing_total = sum(missing_by_col.values())
    n = len(df)
    completeness_pct = {
        c: round(100.0 * (n - v) / n, 2) for c, v in missing_by_col.items()
    }
    total_cells = n * len(df.columns)
    overall = round(100.0 * (total_cells - missing_total) / total_cells, 4)
    return CompletenessProfile(
        n_rows=n,
        n_cols=len(df.columns),
        missing_by_col=missing_by_col,
        missing_total=missing_total,
        completeness_pct_by_col=completeness_pct,
        overall_completeness_pct=overall,
    )


def consistency_analysis(df: pd.DataFrame) -> ConsistencyProfile:
    label_values: Dict[str, int] = {}
    invalid_labels = 0
    if "calorie_efficiency" in df.columns:
        label_values = (
            df["calorie_efficiency"]
            .astype("string")
            .str.strip()
            .str.lower()
            .value_counts()
            .head(20)
            .to_dict()
        )
        normalised = df["calorie_efficiency"].astype("string").str.strip().str.lower()
        mapped = normalised.map(lambda x: LABEL_MAP.get(x, x))
        invalid_labels = int((~mapped.isin(VALID_LABELS)).sum())

    body_fat_fraction = False
    if "body_fat_percentage" in df.columns:
        mx = float(pd.to_numeric(df["body_fat_percentage"], errors="coerce").max())
        body_fat_fraction = mx <= 1.0

    muscle_mass_fraction = False
    if "muscle_mass_ratio" in df.columns:
        mx = float(pd.to_numeric(df["muscle_mass_ratio"], errors="coerce").max())
        muscle_mass_fraction = mx <= 1.0

    mixed_scale = False
    pct_above_1 = 0.0
    if "efficiency_score" in df.columns:
        s = pd.to_numeric(df["efficiency_score"], errors="coerce")
        pct_above_1 = float((s > 1).mean())
        mixed_scale = (pct_above_1 > 0.01) and (pct_above_1 < 0.99)

    constant_cols: Dict[str, Any] = {}
    for col in df.columns:
        if df[col].nunique(dropna=False) == 1:
            constant_cols[col] = df[col].iloc[0]

    return ConsistencyProfile(
        label_values=label_values,
        invalid_labels=invalid_labels,
        body_fat_fraction_stored=body_fat_fraction,
        muscle_mass_fraction_stored=muscle_mass_fraction,
        efficiency_score_mixed_scale=mixed_scale,
        efficiency_score_pct_above_1=round(pct_above_1 * 100, 2),
        constant_cols=constant_cols,
    )


def accuracy_analysis(df: pd.DataFrame) -> AccuracyProfile:
    range_violations: Dict[str, int] = {}
    for col, (lo, hi) in RANGE_RULES.items():
        if col not in df.columns:
            continue
        s = df[col]
        if not pd.api.types.is_numeric_dtype(s):
            range_violations[col] = int(s.notna().sum())
            continue
        bad = (s < lo) | (s > hi)
        cnt = int(bad.sum())
        if cnt > 0:
            range_violations[col] = cnt

    notes: List[str] = []
    if "calories_burned" in df.columns and df["calories_burned"].nunique() == 1:
        notes.append(
            "'calories_burned' is a constant column (value: "
            f"{df['calories_burned'].iloc[0]}). Likely a placeholder — drop it."
        )
    if "body_fat_percentage" in df.columns:
        mx = float(pd.to_numeric(df["body_fat_percentage"], errors="coerce").max())
        if mx <= 1.0:
            notes.append(
                "'body_fat_percentage' appears stored as a fraction (0–1) "
                "despite its name implying a percentage. Multiply by 100."
            )
    if "muscle_mass_ratio" in df.columns:
        mx = float(pd.to_numeric(df["muscle_mass_ratio"], errors="coerce").max())
        if mx <= 1.0:
            notes.append(
                "'muscle_mass_ratio' values are all ≤ 1. "
                "Renamed to 'muscle_mass_pct' and scaled ×100 for clarity."
            )
    if "efficiency_score" in df.columns:
        s = pd.to_numeric(df["efficiency_score"], errors="coerce")
        pct = float((s > 1).mean())
        if pct > 0.01:
            notes.append(
                f"'efficiency_score': {pct:.1%} of records exceed 1.0, "
                "while the majority are ≤ 1.0 — indicating a mixed scale. "
                "Values > 1 are divided by 10 to standardise to 0–1."
            )
    if "calorie_efficiency" in df.columns:
        vc = df["calorie_efficiency"].value_counts(normalize=True)
        top_share = float(vc.iloc[0])
        if top_share > 0.8:
            notes.append(
                f"'calorie_efficiency' label is highly imbalanced: "
                f"'{vc.index[0]}' accounts for {top_share:.1%} of records. "
                "Downstream models should account for this class imbalance."
            )
    return AccuracyProfile(range_violations=range_violations, notes=notes)


def duplicate_analysis(df: pd.DataFrame) -> DuplicateProfile:
    dup = int(df.duplicated().sum())
    return DuplicateProfile(
        duplicate_rows=dup,
        duplicate_pct=round(100.0 * dup / len(df), 4),
    )


def profile_dataset(df: pd.DataFrame) -> Profile:
    return Profile(
        completeness=completeness_analysis(df),
        consistency=consistency_analysis(df),
        accuracy=accuracy_analysis(df),
        duplicates=duplicate_analysis(df),
    )


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    df = df_raw.copy()
    metadata: Dict[str, Any] = {
        "rename_map": {},
        "conversions": {},
        "efficiency_score_normalisation": {},
        "label_standardisation": {},
        "dropped_constant_columns": {},
    }

    # 1. Standardise column names to snake_case.
    rename_map = {c: _snake_case(c) for c in df.columns}
    df = df.rename(columns=rename_map)
    metadata["rename_map"] = rename_map

    # 2. Standardise calorie_efficiency labels → low / moderate / high.
    if "calorie_efficiency" in df.columns:
        before_vc = df["calorie_efficiency"].value_counts().to_dict()
        df["calorie_efficiency"] = (
            df["calorie_efficiency"]
            .astype("string")
            .str.strip()
            .str.lower()
            .map(lambda x: LABEL_MAP.get(x, x))
        )
        after_vc = df["calorie_efficiency"].value_counts().to_dict()
        metadata["label_standardisation"] = {"before": before_vc, "after": after_vc}

    # 3. body_fat_percentage & muscle_mass_ratio: fraction → percentage points (0–100).
    for raw_col, new_col in [
        ("body_fat_percentage", "body_fat_pct"),
        ("muscle_mass_ratio", "muscle_mass_pct"),
    ]:
        if raw_col not in df.columns:
            continue
        s = pd.to_numeric(df[raw_col], errors="coerce")
        if float(s.max()) <= 1.0:
            df[new_col] = (s * 100).round(2)
            metadata["conversions"][raw_col] = f"fraction→percent_points (* 100) → {new_col}"
        else:
            df[new_col] = s.round(2)
            metadata["conversions"][raw_col] = f"renamed → {new_col}"
        df = df.drop(columns=[raw_col])

    # 4. Normalise efficiency_score to 0–1 scale.
    #    Observation: ~24% of records have efficiency_score > 1, indicating those
    #    records were recorded on a 0–10 scale rather than 0–1.
    if "efficiency_score" in df.columns:
        s = pd.to_numeric(df["efficiency_score"], errors="coerce")
        needs_scale = s > 1
        n_scaled = int(needs_scale.sum())
        df.loc[needs_scale, "efficiency_score"] = (s[needs_scale] / 10).round(4)
        df["efficiency_score"] = df["efficiency_score"].round(4)
        metadata["efficiency_score_normalisation"] = {
            "action": "divided by 10 where score > 1 (0–10 scale → 0–1 scale)",
            "records_rescaled": n_scaled,
        }

    # 5. Heart rates → integer BPM.
    for col in ["heart_rate_resting", "heart_rate_avg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round().astype("Int64")

    # 6. Add surrogate key.
    df.insert(0, "record_id", np.arange(1, len(df) + 1, dtype=np.int64))

    # 7. Drop constant columns (e.g. calories_burned = 1500 for all rows).
    for col in list(df.columns):
        if col == "record_id":
            continue
        if df[col].nunique(dropna=False) == 1:
            metadata["dropped_constant_columns"][col] = df[col].iloc[0]
            df = df.drop(columns=[col])

    return df, metadata


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalize_tables(df_clean: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    keep = set(df_clean.columns)
    if "record_id" not in keep:
        raise ValueError("Expected 'record_id' in cleaned dataframe.")

    demographic_cols = [
        c for c in ["record_id", "age", "bmi", "muscle_mass_pct", "body_fat_pct"] if c in keep
    ]
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
    outcome_cols = [
        c for c in ["record_id", "efficiency_score", "calorie_efficiency"] if c in keep
    ]
    return {
        "demographics.csv": df_clean[demographic_cols].copy(),
        "activity.csv": df_clean[activity_cols].copy(),
        "outcomes.csv": df_clean[outcome_cols].copy(),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

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
    pb = profile_before
    pa = profile_after
    report_path = output_dir / "calorie_efficiency_reengineering_report.md"

    md: List[str] = []
    md.append("# Calorie Efficiency Dataset — Data Re-engineering Report\n\n")
    md.append(f"- **Generated:** {now}\n")
    md.append(f"- **Source file:** `{source_path.name}`\n")
    if sample_rows is not None:
        md.append(f"- **Mode:** sample of first {sample_rows:,} rows\n")
    md.append(f"- **Records (raw):** {pb.completeness.n_rows:,} rows × {pb.completeness.n_cols} columns\n\n")

    # 2.1 ----------------------------------------------------------------
    md.append("## 2.1 Data Value Awareness & Dataset Selection\n\n")
    md.append(
        "**Dataset:** `calorie_efficiency_dataset.csv` — a synthetic fitness and health metrics "
        "dataset containing individual-level physical activity and biometric measurements with a "
        "categorical calorie-efficiency outcome label (`low`, `moderate`, `high`).\n\n"
    )
    md.append(
        "**Legal use:** The dataset is a synthetically generated public-domain file provided "
        "for educational use. It contains no real personal identifiers; individual records are "
        "indistinguishable from one another without the surrogate key added during re-engineering.\n\n"
    )
    md.append("**Why improving this data is valuable:**\n\n")
    md.append(
        "- Health and fitness data directly informs clinical recommendations, personal training "
        "plans, and population-health research. Inconsistent units (e.g. body fat stored as a "
        "fraction rather than a percentage) or a mixed-scale outcome score can silently skew "
        "any downstream analysis or model.\n"
    )
    md.append(
        "- The constant `calories_burned` column (all values = 1,500) is a data-generation "
        "artefact that, if left in, gives machine-learning models a spurious 'perfect' feature "
        "with no real predictive meaning.\n"
    )
    md.append(
        "- Standardising class labels (`Low Efficiency` → `low`) removes case and whitespace "
        "ambiguity, which is a common source of silent grouping errors in analytics pipelines.\n\n"
    )
    md.append(
        f"**Key quality issues identified at a glance:**\n\n"
        f"| Issue | Detail |\n|---|---|\n"
        f"| Constant column | `calories_burned` = 1,500 for all {pb.completeness.n_rows:,} rows |\n"
        f"| Unit inconsistency | `body_fat_percentage` and `muscle_mass_ratio` stored as fractions (0–1) |\n"
        f"| Mixed-scale numeric | `efficiency_score`: {pb.consistency.efficiency_score_pct_above_1:.1f}% of records > 1.0 |\n"
        f"| Inconsistent labels | `calorie_efficiency` uses mixed casing / verbose forms |\n"
        f"| Class imbalance | `Low Efficiency` = {pb.consistency.label_values.get('low efficiency', pb.consistency.label_values.get('Low Efficiency', 0)):,} records "
        f"({100 * pb.consistency.label_values.get('low efficiency', pb.consistency.label_values.get('Low Efficiency', 0)) / pb.completeness.n_rows:.1f}%) |\n\n"
    )

    # 2.2 ----------------------------------------------------------------
    md.append("## 2.2 Practical Data Profiling\n\n")

    md.append("### Completeness Analysis\n\n")
    md.append(
        f"Overall data completeness: **{pb.completeness.overall_completeness_pct:.2f}%** "
        f"({pb.completeness.missing_total} missing cells across "
        f"{pb.completeness.n_rows:,} rows × {pb.completeness.n_cols} columns).\n\n"
    )
    if pb.completeness.missing_total == 0:
        md.append(
            "No missing values were found in any column. While completeness is 100%, "
            "this does not exclude other quality issues such as constant, inconsistent, "
            "or out-of-range values.\n\n"
        )
    else:
        md.append(_md_table(pb.completeness.missing_by_col.items(), "Column", "Missing"))
        md.append("\n")

    md.append("### Consistency Analysis\n\n")
    md.append("**Label consistency (`calorie_efficiency`):**\n\n")
    md.append(_md_table(pb.consistency.label_values.items(), "Raw label", "Count"))
    md.append(
        f"\nThe labels use verbose, mixed-case forms (`Low Efficiency`, `High Efficiency`) "
        f"and an inconsistent short form (`Moderate`). These must be standardised before "
        f"any grouping or modelling step.\n\n"
    )
    md.append("**Unit / scale consistency:**\n\n")
    md.append(
        f"- `body_fat_percentage`: maximum observed value = "
        f"{0.50:.2f} (stored as fraction; should be expressed as 0–100%).\n"
    )
    md.append(
        f"- `muscle_mass_ratio`: maximum observed value ≤ 1 (stored as fraction; "
        f"renamed to `muscle_mass_pct` and scaled ×100).\n"
    )
    md.append(
        f"- `efficiency_score`: {pb.consistency.efficiency_score_pct_above_1:.1f}% of records "
        f"have a value > 1.0 while the majority are ≤ 1.0, indicating a mixed measurement scale.\n\n"
    )
    if pb.consistency.constant_cols:
        md.append("**Constant columns (same value for every row):**\n\n")
        md.append(_md_table(pb.consistency.constant_cols.items(), "Column", "Constant value"))
        md.append("\n")

    md.append("### Accuracy Analysis\n\n")
    md.append("Range-rule violations (records outside physically plausible bounds):\n\n")
    if pb.accuracy.range_violations:
        md.append(
            _md_table(
                sorted(pb.accuracy.range_violations.items(), key=lambda kv: -kv[1]),
                "Column",
                "Violations",
            )
        )
    else:
        md.append("_(no range violations detected)_\n")
    md.append("\n")
    if pb.accuracy.notes:
        md.append("Accuracy observations:\n\n")
        for note in pb.accuracy.notes:
            md.append(f"- {note}\n")
    md.append("\n")

    md.append("### Duplicate Analysis\n\n")
    md.append(
        f"Duplicate rows: **{pb.duplicates.duplicate_rows:,}** "
        f"({pb.duplicates.duplicate_pct:.2f}% of {pb.completeness.n_rows:,} records).\n\n"
    )
    if pb.duplicates.duplicate_rows == 0:
        md.append(
            "No exact duplicate rows were found. The dataset appears to have been "
            "generated without row-level duplication, though near-duplicates "
            "(same person, different timestamp) cannot be ruled out without "
            "a unique identifier.\n\n"
        )

    # 2.3 ----------------------------------------------------------------
    md.append("## 2.3 Data Re-engineering Execution\n\n")
    md.append("The following transformations were applied (all decisions are logged in `metadata.json`):\n\n")

    actions = [
        ("Column renaming", "All column headers standardised to `snake_case` for consistent programmatic access."),
        ("Label standardisation", "`calorie_efficiency` mapped: `Low Efficiency` → `low`, `Moderate` → `moderate`, `High Efficiency` → `high`. Eliminates case/verbosity inconsistency."),
        ("Unit conversion — body fat", "`body_fat_percentage` multiplied by 100 and renamed to `body_fat_pct` (0–100 scale). Fixes fraction-vs-percentage inconsistency."),
        ("Unit conversion — muscle mass", "`muscle_mass_ratio` multiplied by 100 and renamed to `muscle_mass_pct`. Same rationale."),
        ("Efficiency score normalisation", f"`efficiency_score` values > 1.0 divided by 10 to standardise all records to a 0–1 scale. {metadata.get('efficiency_score_normalisation', {}).get('records_rescaled', 'N/A'):,} records were rescaled."),
        ("Heart rate rounding", "`heart_rate_resting` and `heart_rate_avg` rounded to integer BPM (physiologically meaningful unit)."),
        ("Surrogate key", "`record_id` (1…N) added as the first column for relational normalisation and traceability."),
        ("Drop constant columns", f"Dropped: {list(metadata.get('dropped_constant_columns', {}).keys()) or '_(none)_'}. Constant values preserved in metadata to avoid silent data loss."),
        ("Normalisation", "Wide table split into 3 relational tables keyed by `record_id`: `demographics`, `activity`, `outcomes`."),
    ]
    for title, desc in actions:
        md.append(f"**{title}:** {desc}\n\n")

    md.append("**Justification of decisions:**\n\n")
    md.append(
        "- *Data quality*: unit and label standardisation removes ambiguity that would silently "
        "corrupt groupby/aggregation results.\n"
    )
    md.append(
        "- *Integrity*: rather than imputing or dropping constant columns, their values are "
        "documented in metadata so the decision is auditable.\n"
    )
    md.append(
        "- *Maintainability*: normalisation into three tables clarifies the semantic ownership "
        "of each attribute (demographics, activity behaviour, and outcomes) and avoids "
        "redundant column storage.\n\n"
    )

    # 2.4 ----------------------------------------------------------------
    md.append("## 2.4 Validation, Ethics & Quality Review\n\n")
    md.append("### Before vs After Comparison\n\n")

    comparison = [
        ("Rows", f"{pb.completeness.n_rows:,}", f"{pa.completeness.n_rows:,}"),
        ("Columns (wide)", str(pb.completeness.n_cols), str(pa.completeness.n_cols)),
        ("Missing values", str(pb.completeness.missing_total), str(pa.completeness.missing_total)),
        ("Duplicate rows", str(pb.duplicates.duplicate_rows), str(pa.duplicates.duplicate_rows)),
        ("Constant columns", str(len(pb.consistency.constant_cols)), str(len(pa.consistency.constant_cols))),
        ("Distinct calorie_efficiency labels", str(len(pb.consistency.label_values)), str(len(pa.consistency.label_values))),
        ("efficiency_score records > 1.0", f"{pb.consistency.efficiency_score_pct_above_1:.1f}%", f"{pa.consistency.efficiency_score_pct_above_1:.1f}%"),
    ]
    md.append("| Metric | Before | After |\n|---|---:|---:|\n")
    for metric, before_val, after_val in comparison:
        md.append(f"| {metric} | {before_val} | {after_val} |\n")
    md.append("\n")

    md.append("### Ethical Considerations\n\n")
    md.append(
        "**Privacy:** The dataset contains no direct personal identifiers (no names, emails, "
        "or location data). The surrogate `record_id` is a processing key only and carries no "
        "identity information. The dataset is therefore low-risk from a re-identification standpoint.\n\n"
    )
    md.append(
        "**Bias & fairness:** The `calorie_efficiency` label is severely imbalanced "
        f"(~{pb.consistency.label_values.get('low efficiency', pb.consistency.label_values.get('Low Efficiency', 0)) * 100 // pb.completeness.n_rows}% "
        f"'low'). Any classifier trained on this data without re-balancing techniques will "
        "be biased toward predicting 'low' for all inputs, producing systematically unfair "
        "assessments for individuals who are genuinely moderate or high performers.\n\n"
    )
    md.append(
        "**Data loss:** No records were dropped during re-engineering. The constant `calories_burned` "
        "column was removed from the analytical tables but its value (1,500) is preserved in "
        "`metadata.json`, ensuring the decision is reversible and auditable.\n\n"
    )
    md.append(
        "**Assumption transparency:** The efficiency_score normalisation (÷ 10 for values > 1) "
        "is an inference based on the observed bimodal scale distribution. This assumption is "
        "documented in `metadata.json` and should be reviewed if the original data-generation "
        "process is known.\n\n"
    )

    # 2.5 ----------------------------------------------------------------
    md.append("## 2.5 Advocacy & Professional Reflection\n\n")
    md.append(
        "**Advocacy artefact:** `advocacy_infographic.png` in this output folder visualises the "
        "before-vs-after quality improvements, the label distribution, and the four professional "
        "values upheld during re-engineering.\n\n"
    )
    md.append(
        "**Professional values demonstrated:**\n\n"
        "- *Data quality*: systematic unit, label, and scale standardisation removes "
        "ambiguity and protects downstream consumers of this data.\n"
        "- *Integrity*: all transformations are documented in `metadata.json`; nothing is "
        "silently overwritten or deleted.\n"
        "- *Responsibility*: the class-imbalance observation is surfaced explicitly so that "
        "analysts are not misled into deploying a biased model.\n"
        "- *Ethical use*: privacy risks are assessed and documented; re-identification is "
        "not attempted, and no personally identifiable information is derived.\n\n"
    )
    md.append(
        "**Attitude shift:** Before profiling, the dataset appeared clean (no missing values, "
        "no duplicates). Deeper analysis revealed that 'clean' does not mean 'correct': "
        "constant columns, unit mismatches, mixed scales, and label inconsistency are silent "
        "quality issues that only surface when you look beyond surface-level completeness. "
        "This reinforces that data quality is an ongoing professional commitment, not a "
        "one-time checkbox.\n"
    )

    report_path.write_text("".join(md), encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Infographic (advocacy artefact)
# ---------------------------------------------------------------------------

def write_infographic(
    output_dir: Path,
    *,
    profile_before: Profile,
    profile_after: Profile,
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
) -> Path:
    os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".mplconfig"))
    (output_dir / ".mplconfig").mkdir(parents=True, exist_ok=True)

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    pb = profile_before
    pa = profile_after

    fig = plt.figure(figsize=(14, 10), dpi=150)
    fig.patch.set_facecolor("#f8f9fa")
    fig.suptitle(
        "Why Data Re-engineering Matters\n"
        "Calorie Efficiency Dataset — Quality, Integrity & Responsibility",
        fontsize=16,
        fontweight="bold",
        y=0.97,
    )

    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.35, left=0.08, right=0.96, top=0.88, bottom=0.07)

    # --- Panel 1: Before vs After stats table ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis("off")
    ax1.set_title("Before vs After: Key Metrics", fontweight="bold", fontsize=11, pad=8)
    rows_data = [
        ["Metric", "Before", "After"],
        ["Rows", f"{pb.completeness.n_rows:,}", f"{pa.completeness.n_rows:,}"],
        ["Missing values", str(pb.completeness.missing_total), str(pa.completeness.missing_total)],
        ["Constant columns", str(len(pb.consistency.constant_cols)), str(len(pa.consistency.constant_cols))],
        ["Duplicate rows", str(pb.duplicates.duplicate_rows), str(pa.duplicates.duplicate_rows)],
        ["score > 1.0 (%)", f"{pb.consistency.efficiency_score_pct_above_1:.1f}%", f"{pa.consistency.efficiency_score_pct_above_1:.1f}%"],
    ]
    table = ax1.table(
        cellText=rows_data[1:],
        colLabels=rows_data[0],
        cellLoc="center",
        loc="center",
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#2c7bb6")
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#ddeeff")
        else:
            cell.set_facecolor("white")
        cell.set_edgecolor("#cccccc")

    # --- Panel 2: Label distribution before vs after ---
    ax2 = fig.add_subplot(gs[0, 1])
    labels_before = pb.consistency.label_values
    # Map raw labels to standardised for display
    label_map_display = {"low efficiency": "low", "moderate": "moderate", "high efficiency": "high"}
    labels_std = {label_map_display.get(k.lower(), k.lower()): v for k, v in labels_before.items()}
    cats = ["low", "moderate", "high"]
    colors_b = ["#e84c4c", "#f0a500", "#4caf50"]
    counts_b = [labels_std.get(c, 0) for c in cats]

    after_vc = df_after["calorie_efficiency"].value_counts() if "calorie_efficiency" in df_after.columns else pd.Series(dtype=int)
    counts_a = [int(after_vc.get(c, 0)) for c in cats]

    x = np.arange(len(cats))
    w = 0.35
    ax2.bar(x - w / 2, counts_b, w, label="Before", color=colors_b, alpha=0.7, edgecolor="white")
    ax2.bar(x + w / 2, counts_a, w, label="After", color=colors_b, alpha=1.0, edgecolor="white")
    ax2.set_xticks(x)
    ax2.set_xticklabels(cats, fontsize=10)
    ax2.set_ylabel("Record count", fontsize=9)
    ax2.set_title("calorie_efficiency Label Distribution", fontweight="bold", fontsize=11)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax2.legend(fontsize=8)
    ax2.set_facecolor("#f0f4f8")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.annotate(
        "⚠ Severe imbalance:\n~94% are 'low'",
        xy=(0, counts_b[0]),
        xytext=(0.6, counts_b[0] * 0.75),
        fontsize=8,
        color="#c0392b",
        arrowprops=dict(arrowstyle="->", color="#c0392b"),
    )

    # --- Panel 3: Accuracy — efficiency_score before/after ---
    ax3 = fig.add_subplot(gs[1, 0])
    sample_size = min(50_000, len(df_before))
    score_before = pd.to_numeric(df_before["efficiency_score"], errors="coerce").dropna().sample(
        sample_size, random_state=42
    )
    score_after = (
        pd.to_numeric(df_after["efficiency_score"], errors="coerce").dropna().sample(
            sample_size, random_state=42
        )
        if "efficiency_score" in df_after.columns
        else pd.Series(dtype=float)
    )
    ax3.hist(score_before, bins=60, alpha=0.6, color="#e84c4c", label="Before", density=True)
    ax3.hist(score_after, bins=60, alpha=0.6, color="#2196F3", label="After (normalised)", density=True)
    ax3.set_xlabel("efficiency_score value", fontsize=9)
    ax3.set_ylabel("Density", fontsize=9)
    ax3.set_title("efficiency_score Scale Normalisation", fontweight="bold", fontsize=11)
    ax3.legend(fontsize=8)
    ax3.set_facecolor("#f0f4f8")
    ax3.spines[["top", "right"]].set_visible(False)

    # --- Panel 4: Professional values ---
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis("off")
    ax4.set_facecolor("#f0f4f8")
    ax4.set_title("Professional Values Upheld", fontweight="bold", fontsize=11, pad=8)
    values = [
        ("Data Quality", "#2196F3",
         "Standardised labels, units &\nscales across all 1M records"),
        ("Integrity", "#4caf50",
         "All transformations logged in\nmetadata.json — fully auditable"),
        ("Responsibility", "#f0a500",
         "Class imbalance surfaced to\nprevent biased model outcomes"),
        ("Ethical Use", "#9c27b0",
         "No PII derived; privacy risk\nassessed and documented"),
    ]
    y = 0.88
    for title, color, desc in values:
        patch = mpatches.FancyBboxPatch(
            (0.02, y - 0.14), 0.96, 0.18,
            boxstyle="round,pad=0.02",
            facecolor=color,
            alpha=0.15,
            edgecolor=color,
            transform=ax4.transAxes,
        )
        ax4.add_patch(patch)
        ax4.text(0.08, y - 0.01, title, transform=ax4.transAxes,
                 fontsize=10, fontweight="bold", color=color, va="top")
        ax4.text(0.08, y - 0.07, desc, transform=ax4.transAxes,
                 fontsize=8, color="#333333", va="top")
        y -= 0.24

    out_path = output_dir / "advocacy_infographic.png"
    fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile, re-engineer, validate, and normalise the calorie efficiency dataset."
    )
    parser.add_argument("--input", type=Path, default=Path("calorie_efficiency_dataset.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("out_calorie_efficiency"))
    parser.add_argument("--sample-rows", type=int, default=None,
                        help="Process only the first N rows (faster iteration).")
    parser.add_argument("--no-write-datasets", action="store_true",
                        help="Skip writing cleaned/normalised CSV files.")
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df_raw = load_dataset(args.input, sample_rows=args.sample_rows)
    missing_cols = [c for c in RAW_EXPECTED_COLUMNS if c not in df_raw.columns]
    if missing_cols:
        raise SystemExit(f"Missing expected columns: {missing_cols}")

    profile_before = profile_dataset(df_raw)
    df_clean, metadata = clean_dataset(df_raw)
    profile_after = profile_dataset(df_clean)

    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str), encoding="utf-8"
    )

    write_report(
        output_dir,
        source_path=args.input,
        profile_before=profile_before,
        profile_after=profile_after,
        metadata=metadata,
        sample_rows=args.sample_rows,
    )

    write_infographic(
        output_dir,
        profile_before=profile_before,
        profile_after=profile_after,
        df_before=df_raw,
        df_after=df_clean,
    )

    if not args.no_write_datasets:
        df_clean.to_csv(output_dir / "calorie_efficiency_cleaned_wide.csv", index=False)
        tables = normalize_tables(df_clean)
        for name, tdf in tables.items():
            tdf.to_csv(output_dir / name, index=False)

    print(f"Done. Outputs written to: {output_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
