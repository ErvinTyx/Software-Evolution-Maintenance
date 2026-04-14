# Quality Review Report

**Dataset:** `transaction.csv` → `data_normalise.csv`  
**Purpose:** Assess the overall data quality of the raw dataset, evaluate the effectiveness of re-engineering, and identify residual quality concerns that require ongoing attention.

---

## 1. Quality Review Framework

Data quality is assessed across five standard dimensions:

| Dimension | Definition |
|-----------|------------|
| **Completeness** | Are all expected values present? |
| **Consistency** | Do values conform to a defined, uniform standard? |
| **Accuracy** | Do values correctly represent the real-world facts they describe? |
| **Uniqueness** | Are records free of duplication? |
| **Validity** | Do values fall within expected domains, formats, and ranges? |

Each dimension is scored on a 0–100 scale for the raw dataset and the normalised dataset.

---

## 2. Column-Level Quality Assessment

### 2.1 `status`

| Metric | Raw | Normalised |
|--------|-----|-----------|
| NULL count | 0 | 0 |
| Distinct values | 6 | 2 |
| Non-canonical rows | 2,135 (21.13%) | 0 (0.00%) |
| Domain compliance | 78.87% | 100% |

**Raw quality issues:**
- 6 distinct values for a binary field: `fail`, `failed`, `FAIL`, `success`, `Success`, `succeed`
- Case inconsistency and synonym variants prevent reliable grouping

**Post-engineering quality:**
- Fully resolved. 100% of rows map to exactly one of two canonical values: `failed` (5,421) or `success` (4,682)
- Domain compliance: 100%

**Quality score:** Raw: 55/100 | Normalised: 100/100

---

### 2.2 `time`

| Metric | Raw | Normalised |
|--------|-----|-----------|
| NULL count | 8 | 23 |
| Valid datetimes | 10,076 (99.73%) | 10,080 (99.77%) |
| Impossible values | 14 | 0 |
| Format conformance | Mixed (5 patterns) | 100% (`YYYY-MM-DD` + `HH:MM:SS`) |

**Raw quality issues:**
- Two competing datetime formats in active use
- 14 physically impossible datetimes (hour > 23, month > 12)
- 5 non-standard format strings (`3pm 2025/09/11`, `03-00-2025 09-11`)
- 8 NULL values

**Post-engineering quality:**
- All valid datetimes parsed and split into `date` (YYYY-MM-DD) and `time` (HH:MM:SS)
- Impossible values correctly nulled (23 total NULLs)
- 99.77% of rows have a valid, parseable, consistently-formatted timestamp

**Residual concern:** 23 rows (0.23%) have no usable timestamp. These cannot be placed in time-series analysis without additional source data.

**Quality score:** Raw: 62/100 | Normalised: 91/100

---

### 2.3 `card_type`

| Metric | Raw | Normalised |
|--------|-----|-----------|
| NULL count | 314 | 314 |
| Distinct values | 11 | 4 |
| Non-canonical rows | 3,007 (29.77%) | 0 (0.00%) |
| Domain compliance (non-null rows) | 70.23% | 100% |

**Raw quality issues:**
- 11 distinct values representing only 4 card brands
- Typos: `MastCard` (1,010 rows), `Vsa` (810 rows)
- Format variants: `Master-Card`, `Master Card`, `MasterCard`
- Case variants: `Visa`, `visa`, `VISA`
- 314 NULL values (3.11%)

**Post-engineering quality:**
- All 10 non-null variants correctly mapped to 4 canonical brands
- Domain compliance for non-null rows: 100%
- NULL count unchanged — unknown card types not guessed

**Residual concern:** 314 rows (3.11%) have no card type. These cannot be attributed to a brand in any brand-level analysis.

**Quality score:** Raw: 42/100 | Normalised: 90/100

---

### 2.4 `city`

| Metric | Raw | Normalised |
|--------|-----|-----------|
| NULL count | 117 | 117 |
| Distinct values | 14 | 8 |
| Non-canonical rows | 1,636 (16.19%) | 0 (0.00%) |
| Domain compliance (non-null rows) | 83.81% | 100% |

**Raw quality issues:**
- 14 distinct values for 8 known cities
- IATA code used in place of city name: `THR` (414 rows)
- Typo: `tehr@n` (335 rows) — `@` substituted for `a`
- Case variants: `TEHRAN`, `karaj`, `ThRan`
- 117 NULL values (1.16%)

**Post-engineering quality:**
- All 13 non-null variants correctly mapped to 8 canonical cities via lookup table
- Domain compliance for non-null rows: 100%
- NULL count unchanged

**Residual concern:** 117 rows (1.16%) have no city. Geographic analysis excludes these rows.

**Quality score:** Raw: 52/100 | Normalised: 90/100

---

### 2.5 `amount`

| Metric | Raw | Normalised |
|--------|-----|-----------|
| NULL count | 2 | 301 |
| Negative values | 1,217 (12.05%) | 0 |
| Non-numeric values | 1 | 0 |
| Outliers (IQR) | 299 | 0 (nulled) |
| Type consistency | Mixed (int + decimal + text) | Uniform `double` |
| Valid non-null rows | 8,883 (87.92%) | 9,802 (97.02%) |

**Raw quality issues:**
- 1,217 negative amounts — violate the business rule that transaction amounts must be positive
- 1 non-numeric value: `"one hundred"` (should be `100`)
- Mixed types: 96.91% integer, 3.06% decimal, 0.01% text
- 299 extreme outlier values (e.g. `9,999,999,999`) — identified as sentinel/placeholder values
- 2 NULL values

**Post-engineering quality:**
- All negatives converted to absolute values
- `"one hundred"` → `100.0`
- All amounts typed as `double`
- 299 outliers nulled — no longer distort mean/sum calculations
- Valid non-null rows increased from 8,883 to 9,802 (+919, owing to negative→positive and text→numeric conversions)

**Residual concern:** 301 rows (2.98%) have NULL amount. Revenue and volume calculations will exclude these rows. The 299 outlier-nulled amounts require human review to determine whether any represent legitimate large transactions.

**Quality score:** Raw: 38/100 | Normalised: 85/100

---

### 2.6 `id` / `transaction_id`

| Metric | Raw `id` | Normalised `transaction_id` |
|--------|----------|---------------------------|
| NULL count | 0 | 0 |
| Distinct values | 99 | 10,103 |
| Duplication rate | 100% | 0% |
| Uniqueness | 0.98% (99/10,103) | 100% |

**Raw quality issues:**
- 99 distinct values across 10,103 rows — 100% duplication rate
- The `id` column cannot serve as a primary key

**Post-engineering quality:**
- Surrogate key `transaction_id` assigned: `TRX_00001` through `TRX_10103`
- 100% unique — every row individually addressable
- Original `id` preserved for reference in `data_clean.csv`

**Quality score:** Raw: 1/100 | Normalised: 100/100

---

## 3. Overall Quality Scorecard

| Dimension | Raw Score | Normalised Score | Improvement |
|-----------|----------:|-----------------:|-------------|
| Completeness | 85/100 | 83/100 | −2 (correct nulling of false-valid values) |
| Consistency | 38/100 | 100/100 | +62 |
| Accuracy | 55/100 | 90/100 | +35 |
| Uniqueness | 1/100 | 100/100 | +99 |
| Validity | 44/100 | 88/100 | +44 |
| **Overall** | **45/100** | **92/100** | **+47** |

> Note: Completeness score decreased slightly by design. The raw dataset contained 14 impossible datetimes and 299 extreme sentinel amounts that appeared complete but were not usable. Correctly nulling these reduces the apparent completeness while improving true usability.

---

## 4. Residual Quality Concerns

Despite the improvements, the following quality gaps remain after re-engineering and should be acknowledged in any downstream use:

| Issue | Rows Affected | % | Risk |
|-------|-------------:|---|------|
| Unknown `card_type` (NULL) | 314 | 3.11% | Card brand analysis is incomplete |
| Unknown `city` (NULL) | 117 | 1.16% | Geographic analysis excludes these rows |
| NULL `date` / `time` | 23 | 0.23% | Time-series analysis excludes these rows |
| NULL `amount` (post-outlier nulling) | 301 | 2.98% | Revenue/volume calculations are understated |
| `succeed` mapped to `success` (unconfirmed) | 221 | 2.19% | If `succeed` had a distinct meaning, success rate is overstated |

These residual gaps cannot be resolved through re-engineering alone — they require either source data correction or explicit acknowledgement in reports and dashboards.

---

## 5. Quality Improvement Summary

| Column | Key Improvement | Before | After |
|--------|----------------|--------|-------|
| `status` | Synonyms and case variants unified | 6 values | 2 values |
| `time` | Mixed formats standardised; impossible values removed | 5 formats, 14 invalid | 1 format, 0 invalid |
| `card_type` | Typos and variants mapped to 4 brands | 11 values | 4 values |
| `city` | Abbreviations and typos resolved; IATA code fixed | 14 values | 8 values |
| `amount` | Negatives fixed, text converted, outliers quarantined, typed as `double` | 4 types, 12% negative | 1 type, 0 negative |
| `id` | Surrogate key guarantees uniqueness | 100% duplicate | 100% unique |

---

## 6. Recommendations for Ongoing Quality Management

1. **Input validation at source:** The re-engineering pipeline fixed 10,103 rows of legacy data, but the root cause — absence of input validation when data is entered — remains. Enforce constraints at the point of entry: status must be `success` or `failed`, city must be from an approved list, amounts must be positive numeric values.

2. **Monitor NULL rates over time:** The 314 unknown card types and 117 unknown cities represent a 3.11% and 1.16% data gap respectively. These rates should be tracked over time. An increasing NULL rate signals a deteriorating data pipeline.

3. **Review the 299 nulled amounts:** These rows should be reviewed by a business analyst to determine whether any represent legitimate large transactions that were incorrectly flagged by the IQR method. If so, the IQR threshold should be adjusted or a business-rule-based threshold used instead.

4. **Confirm `succeed` semantics:** The business owner should confirm whether `succeed` was intended as a synonym for `success` or as a distinct transaction state. This affects 221 rows (2.19%) and the reported success rate.

5. **Establish a data quality baseline:** The overall quality score of 92/100 post-re-engineering should serve as a baseline. Future datasets should be profiled against this standard before use.

---

## 7. Conclusion

The raw `transaction.csv` dataset had a measured overall quality score of 45/100 — below the threshold for reliable use in business analysis. The re-engineering pipeline raised this to 92/100, resolving all consistency violations and the uniqueness failure, improving accuracy, and correctly quarantining unusable values. The five residual quality gaps (unknown card types, unknown cities, null timestamps, null amounts, and the unconfirmed `succeed` mapping) are explicitly documented and manageable. The dataset is now fit for purpose, with known and bounded limitations.
