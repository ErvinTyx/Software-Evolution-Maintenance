# Calorie Efficiency Dataset — Data Re-engineering Report

- **Generated:** 2026-04-07 08:47
- **Source file:** `calorie_efficiency_dataset.csv`
- **Records (raw):** 1,000,000 rows × 15 columns

## 2.1 Data Value Awareness & Dataset Selection

**Dataset:** `calorie_efficiency_dataset.csv` — a synthetic fitness and health metrics dataset containing individual-level physical activity and biometric measurements with a categorical calorie-efficiency outcome label (`low`, `moderate`, `high`).

**Legal use:** The dataset is a synthetically generated public-domain file provided for educational use. It contains no real personal identifiers; individual records are indistinguishable from one another without the surrogate key added during re-engineering.

**Why improving this data is valuable:**

- Health and fitness data directly informs clinical recommendations, personal training plans, and population-health research. Inconsistent units (e.g. body fat stored as a fraction rather than a percentage) or a mixed-scale outcome score can silently skew any downstream analysis or model.
- The constant `calories_burned` column (all values = 1,500) is a data-generation artefact that, if left in, gives machine-learning models a spurious 'perfect' feature with no real predictive meaning.
- Standardising class labels (`Low Efficiency` → `low`) removes case and whitespace ambiguity, which is a common source of silent grouping errors in analytics pipelines.

**Key quality issues identified at a glance:**

| Issue | Detail |
|---|---|
| Constant column | `calories_burned` = 1,500 for all 1,000,000 rows |
| Unit inconsistency | `body_fat_percentage` and `muscle_mass_ratio` stored as fractions (0–1) |
| Mixed-scale numeric | `efficiency_score`: 24.4% of records > 1.0 |
| Inconsistent labels | `calorie_efficiency` uses mixed casing / verbose forms |
| Class imbalance | `Low Efficiency` = 938,243 records (93.8%) |

## 2.2 Practical Data Profiling

### Completeness Analysis

Overall data completeness: **100.00%** (0 missing cells across 1,000,000 rows × 15 columns).

No missing values were found in any column. While completeness is 100%, this does not exclude other quality issues such as constant, inconsistent, or out-of-range values.

### Consistency Analysis

**Label consistency (`calorie_efficiency`):**

| Raw label | Count |
|---|---:|
| low efficiency | 938243 |
| moderate | 34861 |
| high efficiency | 26896 |

The labels use verbose, mixed-case forms (`Low Efficiency`, `High Efficiency`) and an inconsistent short form (`Moderate`). These must be standardised before any grouping or modelling step.

**Unit / scale consistency:**

- `body_fat_percentage`: maximum observed value = 0.50 (stored as fraction; should be expressed as 0–100%).
- `muscle_mass_ratio`: maximum observed value ≤ 1 (stored as fraction; renamed to `muscle_mass_pct` and scaled ×100).
- `efficiency_score`: 24.4% of records have a value > 1.0 while the majority are ≤ 1.0, indicating a mixed measurement scale.

**Constant columns (same value for every row):**

| Column | Constant value |
|---|---:|
| calories_burned | 1500 |

### Accuracy Analysis

Range-rule violations (records outside physically plausible bounds):

| Column | Violations |
|---|---:|
| efficiency_score | 244137 |

Accuracy observations:

- 'calories_burned' is a constant column (value: 1500). Likely a placeholder — drop it.
- 'body_fat_percentage' appears stored as a fraction (0–1) despite its name implying a percentage. Multiply by 100.
- 'muscle_mass_ratio' values are all ≤ 1. Renamed to 'muscle_mass_pct' and scaled ×100 for clarity.
- 'efficiency_score': 24.4% of records exceed 1.0, while the majority are ≤ 1.0 — indicating a mixed scale. Values > 1 are divided by 10 to standardise to 0–1.
- 'calorie_efficiency' label is highly imbalanced: 'Low Efficiency' accounts for 93.8% of records. Downstream models should account for this class imbalance.

### Duplicate Analysis

Duplicate rows: **0** (0.00% of 1,000,000 records).

No exact duplicate rows were found. The dataset appears to have been generated without row-level duplication, though near-duplicates (same person, different timestamp) cannot be ruled out without a unique identifier.

## 2.3 Data Re-engineering Execution

The following transformations were applied (all decisions are logged in `metadata.json`):

**Column renaming:** All column headers standardised to `snake_case` for consistent programmatic access.

**Label standardisation:** `calorie_efficiency` mapped: `Low Efficiency` → `low`, `Moderate` → `moderate`, `High Efficiency` → `high`. Eliminates case/verbosity inconsistency.

**Unit conversion — body fat:** `body_fat_percentage` multiplied by 100 and renamed to `body_fat_pct` (0–100 scale). Fixes fraction-vs-percentage inconsistency.

**Unit conversion — muscle mass:** `muscle_mass_ratio` multiplied by 100 and renamed to `muscle_mass_pct`. Same rationale.

**Efficiency score normalisation:** `efficiency_score` values > 1.0 divided by 10 to standardise all records to a 0–1 scale. 244,137 records were rescaled.

**Heart rate rounding:** `heart_rate_resting` and `heart_rate_avg` rounded to integer BPM (physiologically meaningful unit).

**Surrogate key:** `record_id` (1…N) added as the first column for relational normalisation and traceability.

**Drop constant columns:** Dropped: ['calories_burned']. Constant values preserved in metadata to avoid silent data loss.

**Normalisation:** Wide table split into 3 relational tables keyed by `record_id`: `demographics`, `activity`, `outcomes`.

**Justification of decisions:**

- *Data quality*: unit and label standardisation removes ambiguity that would silently corrupt groupby/aggregation results.
- *Integrity*: rather than imputing or dropping constant columns, their values are documented in metadata so the decision is auditable.
- *Maintainability*: normalisation into three tables clarifies the semantic ownership of each attribute (demographics, activity behaviour, and outcomes) and avoids redundant column storage.

## 2.4 Validation, Ethics & Quality Review

### Before vs After Comparison

| Metric | Before | After |
|---|---:|---:|
| Rows | 1,000,000 | 1,000,000 |
| Columns (wide) | 15 | 15 |
| Missing values | 0 | 0 |
| Duplicate rows | 0 | 0 |
| Constant columns | 1 | 0 |
| Distinct calorie_efficiency labels | 3 | 3 |
| efficiency_score records > 1.0 | 24.4% | 0.0% |

### Ethical Considerations

**Privacy:** The dataset contains no direct personal identifiers (no names, emails, or location data). The surrogate `record_id` is a processing key only and carries no identity information. The dataset is therefore low-risk from a re-identification standpoint.

**Bias & fairness:** The `calorie_efficiency` label is severely imbalanced (~93% 'low'). Any classifier trained on this data without re-balancing techniques will be biased toward predicting 'low' for all inputs, producing systematically unfair assessments for individuals who are genuinely moderate or high performers.

**Data loss:** No records were dropped during re-engineering. The constant `calories_burned` column was removed from the analytical tables but its value (1,500) is preserved in `metadata.json`, ensuring the decision is reversible and auditable.

**Assumption transparency:** The efficiency_score normalisation (÷ 10 for values > 1) is an inference based on the observed bimodal scale distribution. This assumption is documented in `metadata.json` and should be reviewed if the original data-generation process is known.

## 2.5 Advocacy & Professional Reflection

**Advocacy artefact:** `advocacy_infographic.png` in this output folder visualises the before-vs-after quality improvements, the label distribution, and the four professional values upheld during re-engineering.

**Professional values demonstrated:**

- *Data quality*: systematic unit, label, and scale standardisation removes ambiguity and protects downstream consumers of this data.
- *Integrity*: all transformations are documented in `metadata.json`; nothing is silently overwritten or deleted.
- *Responsibility*: the class-imbalance observation is surfaced explicitly so that analysts are not misled into deploying a biased model.
- *Ethical use*: privacy risks are assessed and documented; re-identification is not attempted, and no personally identifiable information is derived.

**Attitude shift:** Before profiling, the dataset appeared clean (no missing values, no duplicates). Deeper analysis revealed that 'clean' does not mean 'correct': constant columns, unit mismatches, mixed scales, and label inconsistency are silent quality issues that only surface when you look beyond surface-level completeness. This reinforces that data quality is an ongoing professional commitment, not a one-time checkbox.
