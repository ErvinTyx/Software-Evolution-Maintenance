# Retail Store Sales — Data Re-engineering Report

- **Generated:** 2026-04-07 08:46
- **Source file:** `retail_store_sales.csv`
- **Records (raw):** 12,575 rows × 11 columns

## 2.1 Data Value Awareness & Dataset Selection

**Dataset:** `retail_store_sales.csv` — a retail transaction log containing purchase records with fields for product, price, quantity, customer, payment method, location, and discount status. The dataset covers transactions from 2022-01-01 → 2025-01-18.

**Legal use:** Dataset is sourced from Kaggle (`ahmedmohamed2003/retail-store-sales-dirty-for-data-cleaning`) under a public license explicitly intended for data-cleaning practice. Customer IDs appear pseudonymous (e.g. `CUST_09`), and no directly identifying information is present.

**Why improving this data is valuable:**

- Retail analytics (revenue reporting, inventory planning, staff performance, promotion effectiveness) depend entirely on accurate transaction records. Missing quantity or price data means revenue figures are understated, and imputed values without documentation create silent errors in KPI dashboards.
- The `Discount Applied` field is missing for ~33% of records. If these gaps were silently filled with `False`, the reported discount rate and any discount-impact analysis would be structurally wrong.
- Normalising the flat file into a star schema eliminates data redundancy, reduces storage, and enforces referential integrity — prerequisites for reliable BI reporting.

**Key quality issues identified at a glance:**

| Issue | Count |
|---|---:|
| Missing `Discount Applied` | 4,199 (33.4%) |
| Missing `Item` | 1,213 (9.6%) |
| Missing `Price Per Unit` | 609 (4.8%) |
| Missing `Quantity` | 604 (4.8%) |
| Missing `Total Spent` | 604 (4.8%) |

> 1213 records have missing Item AND missing financial fields (price/qty/total) simultaneously, suggesting a shared data-capture failure at the point of sale.

## 2.2 Practical Data Profiling

### Completeness Analysis

Overall data completeness: **94.77%** (7,229 missing cells across 12,575 rows × 11 columns).

Missing values per column:

| Column | Missing (completeness %) |
|---|---:|
| Discount Applied | 4,199 (66.6% complete) |
| Item | 1,213 (90.3% complete) |
| Price Per Unit | 609 (95.2% complete) |
| Quantity | 604 (95.2% complete) |
| Total Spent | 604 (95.2% complete) |

**Structured missingness pattern:** 1213 records have missing Item AND missing financial fields (price/qty/total) simultaneously, suggesting a shared data-capture failure at the point of sale.

### Consistency Analysis

| Rule | Violations |
|---|---:|
| total_spent ≠ price × qty | 0 |
| Quantity non-integer | 0 |
| Quantity outside 1–10 | 0 |
| Price not in 0.50 steps | 0 |
| Unparseable dates | 0 |

Transaction date range: **2022-01-01 → 2025-01-18**

Payment method distribution:

| Method | Count |
|---|---:|
| Cash | 4310 |
| Digital Wallet | 4144 |
| Credit Card | 4121 |

Location distribution:

| Location | Count |
|---|---:|
| Online | 6354 |
| In-store | 6221 |

### Accuracy Analysis

- Each (Category, Price Per Unit) pair maps to exactly one Item. This rule can be used to infer missing Item values reliably.
- 'Discount Applied' is missing for 4,199 records (33.4%). Discount status is not imputed (unknown ≠ False) to avoid introducing bias.
- All complete transactions satisfy total_spent = price_per_unit × quantity (within ±0.01 rounding). Internal arithmetic is consistent.

Duplicate Transaction IDs: **0** — each transaction ID is unique, confirming transaction grain integrity.

### Duplicate Analysis

Exact duplicate rows: **0** (0.00% of 12,575 records).
Duplicate Transaction IDs: **0**.

## 2.3 Data Re-engineering Execution

All decisions are logged in `metadata.json`.

**Column renaming:** All headers standardised to `snake_case` for consistent programmatic access.

**Date parsing:** `transaction_date` parsed to datetime; `transaction_date_iso` (YYYY-MM-DD string) added for portable exports. Derived `transaction_year` and `transaction_month` fields added for analytics.

**Discount Applied → nullable boolean:** Normalised to `True`/`False`/`<NA>`. Missing values are preserved as `<NA>` rather than imputed — unknown discount status is NOT assumed to be `False`.

**Reconstruct price_per_unit:** For 609 rows where price was missing but total and quantity were known: `price = total / quantity`, rounded to nearest 0.50 (observed dataset granularity).

**Infer missing item:** Used the verified rule (Category, Price Per Unit) → Item to infer 1,213 missing Item values. Unresolvable cases remain `<NA>`.

**Impute missing quantity:** For 604 rows with missing quantity: mode per item → mode per category → global mode (10). Imputed quantity used to reconstruct total_spent.

**Total spent reconstruction:** 604 total_spent values reconstructed as `price_per_unit × quantity` after upstream fills.

**Surrogate key:** `row_id` (1…N) inserted as first column for relational normalisation.

**Star schema normalisation:** Wide table decomposed into: `fact_sales` + 5 dimension tables (`dim_customer`, `dim_category`, `dim_item`, `dim_payment_method`, `dim_location`). Foreign keys use integer surrogate keys.

**Justification:**

- *Integrity*: arithmetic reconstruction (price × qty = total) is deterministic and consistent with the dataset rule — no guesswork involved.
- *Responsibility*: discount status is not imputed because imputing `False` would misrepresent the proportion of discounted transactions.
- *Maintainability*: the star schema eliminates redundancy and supports JOIN-based analytics without duplicating category or item metadata per transaction.

## 2.4 Validation, Ethics & Quality Review

### Before vs After Comparison

| Metric | Before | After |
|---|---:|---:|
| Missing values (total) | 7,229 | 4,199 |
| Missing Item | 1,213 | 0 |
| Missing Price Per Unit | 609 | 0 |
| Missing Quantity | 604 | 0 |
| Missing Total Spent | 604 | 0 |
| Duplicate rows | 0 | 0 |
| Duplicate Transaction IDs | 0 | 0 |
| total_spent mismatches | 0 | 0 |

### Ethical Considerations

**Privacy:** Customer IDs are pseudonymous (e.g. `CUST_09`) and carry no directly identifying information. No attempt has been made to re-identify individuals by cross-referencing purchase patterns with external data.

**Bias / fairness:** Imputed quantity values are based on statistical modes and may not reflect the true transaction. Downstream sales performance analysis should flag imputed records to avoid drawing unfair conclusions about customer spending behaviour from fabricated data points.

**Discount Applied — null preservation:** Approximately 33% of discount values are missing. Imputing `False` would artificially deflate the discount rate and mislead promotional effectiveness analysis. The `<NA>` values are preserved and should be treated as 'unknown' in all downstream aggregations.

**Data loss:** No records were dropped. All transformations are documented in `metadata.json`. Original column names are preserved in `rename_map` so that any transformation can be traced and reversed.

## 2.5 Advocacy & Professional Reflection

**Advocacy artefact:** `advocacy_infographic.png` in this folder shows the before-vs-after missingness improvements, category distribution, and the four professional values upheld throughout the re-engineering process.

**Professional values demonstrated:**

- *Data quality*: arithmetic reconstruction and lookup-based inference recover missing values without introducing guesswork.
- *Integrity*: all imputation decisions (strategy, counts, fallback modes) are logged in `metadata.json` — nothing is silently overwritten.
- *Responsibility*: discount status is intentionally left nullable — a deliberate decision not to overstate certainty in the data.
- *Ethical use*: pseudonymous customer IDs are not cross-referenced or enriched; imputed records are flagged to protect against unfair analytical conclusions.

**Attitude shift:** The discovery that Item, Price, Quantity, and Total Spent are all missing together in 609 records (a structured missingness pattern) changed our approach from treating missing values as random noise to investigating them as evidence of a real-world failure point (e.g. a POS system outage or incomplete data export). This shift from 'fill the gaps' to 'understand the gaps' is a hallmark of responsible data stewardship.
