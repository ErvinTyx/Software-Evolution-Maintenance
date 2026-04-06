# Calorie Efficiency Dataset — Data Re-engineering Report
- Generated: 2026-04-06 22:59
- Source file: `calorie_efficiency_dataset.csv`

## 2.1 Data Value Awareness & Dataset Selection (Group)
Dataset selected: `calorie_efficiency_dataset.csv` (local file provided for coursework). It appears to contain fitness and health-related metrics and a categorical outcome label.

Why improving the data is valuable: even small inconsistencies in health/fitness datasets can cause misleading analytics, unfair comparisons between individuals, or incorrect model training labels. Improving consistency and semantics (units, labels, redundant fields) supports responsible reporting and more trustworthy downstream use.

## 2.2 Practical Data Profiling (Individual)
### Completeness & Duplication
**Before**

| Item | Value |
|---|---:|
| Rows | 1000000 |
| Columns | 15 |
| Missing values (total) | 0 |
| Duplicate rows | 0 |
| Constant columns | 1 |

**After**

| Item | Value |
|---|---:|
| Rows | 1000000 |
| Columns | 15 |
| Missing values (total) | 0 |
| Duplicate rows | 0 |
| Constant columns | 0 |

### Consistency & Accuracy Checks
Key observations (before):

- Column 'calories_burned' is constant; likely a placeholder or redundant.
- Column 'body_fat_percentage' appears stored as a fraction (0–1) despite being named as a percentage.
- Column 'efficiency_score' has mixed scale: 24.4% of records are > 1.

Top label values (before):

| Item | Value |
|---|---:|
| Low Efficiency | 938243 |
| Moderate | 34861 |
| High Efficiency | 26896 |

Range-rule violations (before, count of records outside expected bounds):

| Item | Value |
|---|---:|
| age | 0 |
| steps_per_day | 0 |
| active_minutes | 0 |
| calories_burned | 0 |
| sleep_hours | 0 |
| hydration_liters | 0 |
| bmi | 0 |
| workouts_per_week | 0 |
| muscle_mass_ratio | 0 |
| body_fat_percentage | 0 |

## 2.3 Data Re-engineering Execution (Group)
Actions applied:

- Standardized column naming to `snake_case`.
- Standardized `calorie_efficiency` labels to `low` / `moderate` / `high`.
- Converted fractional fields into percentage points (e.g. `body_fat_percentage` → `body_fat_pct`).
- Rounded heart-rate fields to integer BPM.
- Dropped constant columns to reduce redundancy, preserving the constant values in metadata.
- Normalized the wide table into 3 tables (`demographics`, `activity`, `outcomes`) keyed by `record_id`.

Justification highlights:

- **Consistency & integrity**: unit/label standardization reduces misinterpretation risk.
- **Quality & responsibility**: removing redundant placeholders avoids false confidence in metrics.
- **Maintainability**: normalization clarifies ownership of attributes and supports reuse in different analyses.

## 2.4 Validation, Ethics & Quality Review (Individual)
Validation summary:

- Duplicate rows: 0 → 0
- Missing values (total): 0 → 0
- Constant columns detected: 1 → 0

Dropped constant columns (value preserved):

| Item | Value |
|---|---:|
| calories_burned | 1500 |

Ethics reflection prompts (edit for your submission):

- Privacy: dataset contains no direct identifiers; `record_id` is a surrogate key for engineering only.
- Bias/fairness: health-related metrics can encode population bias; avoid overgeneralizing findings.
- Data loss: transformations were documented; avoid deleting records unless clearly justified.

## 2.5 Advocacy & Professional Reflection (Group)
Advocacy artefact: see `advocacy_infographic.png` in the output folder. It summarizes why re-engineering improves trust and decision quality.

Reflection prompt: describe how your attitude toward data quality changed after seeing how small inconsistencies (units, labels, redundant fields) can create downstream risks.
