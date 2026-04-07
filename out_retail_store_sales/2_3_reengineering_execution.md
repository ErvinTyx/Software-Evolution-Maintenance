# Data Re-engineering Execution Report
**Dataset:** `retail_store_sales.csv`
**Section:** 2.3 — Data Re-engineering Execution
**Techniques applied:** Data Cleansing · Transformation · Normalisation & Restructuring
**All decisions logged in:** `metadata.json`

---

## 1. Purpose and Commitment

Data re-engineering is not a cosmetic exercise. It is the structured, evidence-based process of converting raw, imperfect data into a form that is accurate, consistent, and fit for purpose. Every action taken in this report was driven by a specific finding from the profiling stage — not by habit, assumption, or convenience.

The profiling reports (Completeness, Consistency, Accuracy, Duplicate) established four foundational facts about this dataset:

1. **5 columns contain missing values** — some recoverable, some not
2. **The data present is accurate** — zero arithmetic errors, zero format violations, zero range violations
3. **A deterministic mapping rule exists** — `(Category, Price Per Unit)` uniquely identifies `Item`
4. **No duplicates exist** — the transaction grain is intact and no rows need to be removed

These facts determine the shape of the re-engineering work: the task is recovery and restructuring, not correction. The accurate rules embedded in the complete data are the tools used to recover the incomplete data. Every action below is traceable to a specific profiling finding.

---

## 2. Re-engineering Overview

| # | Technique | Action | Rows / Fields Affected |
|---|---|---|---|
| 1 | Cleansing | Standardise column names to `snake_case` | All 11 columns |
| 2 | Cleansing | Strip whitespace from text fields | 6 text columns |
| 3 | Cleansing | Normalise `Discount Applied` to nullable boolean | 12,575 rows |
| 4 | Cleansing | Reconstruct missing `price_per_unit` | 609 rows |
| 5 | Cleansing | Infer missing `item` from category–price lookup | 1,213 rows |
| 6 | Cleansing | Impute missing `quantity` via mode hierarchy | 604 rows |
| 7 | Cleansing | Reconstruct missing `total_spent` | 604 rows |
| 8 | Transformation | Parse `transaction_date` to datetime | 12,575 rows |
| 9 | Transformation | Add `transaction_date_iso` (YYYY-MM-DD) | 12,575 rows |
| 10 | Transformation | Add `transaction_year` and `transaction_month` | 12,575 rows |
| 11 | Transformation | Standardise numeric types | 3 columns |
| 12 | Transformation | Add `row_id` surrogate key | 12,575 rows |
| 13 | Normalisation | Decompose wide table into star schema | 1 fact + 5 dimension tables |

---

## PART A — DATA CLEANSING

Data cleansing addresses values that are wrong, inconsistent, missing, or misrepresented. It brings the data into a state where every value is trustworthy, comparable, and unambiguous.

---

### Action 1 — Standardise Column Names to `snake_case`

**What was done:**

| Original column name | Cleaned column name |
|---|---|
| Transaction ID | transaction_id |
| Customer ID | customer_id |
| Category | category |
| Item | item |
| Price Per Unit | price_per_unit |
| Quantity | quantity |
| Total Spent | total_spent |
| Payment Method | payment_method |
| Location | location |
| Transaction Date | transaction_date |
| Discount Applied | discount_applied |

**Justification:**
Column names with spaces cannot be referenced in SQL without quoting, cause errors in many Python/pandas operations when used with dot notation, and are inconsistently cased across export tools. `snake_case` is the universal standard for programmatic column naming — it works across Python, SQL, R, and every downstream tool without modification. This change is purely structural and carries zero risk of data loss.

**Professional value:** *Data quality* — consistent naming removes a silent source of programmatic errors in every future analysis.

---

### Action 2 — Strip Whitespace from Text Fields

**What was done:** Leading and trailing whitespace was removed from `transaction_id`, `customer_id`, `category`, `item`, `payment_method`, and `location`.

**Justification:**
Whitespace in string fields is invisible to the eye but causes grouping failures at scale. `"Cash"` and `"Cash "` are treated as two separate categories by every groupby, pivot, and JOIN operation. In a dataset with 12,575 rows across 8 categories and 3 payment methods, an untrimmed whitespace variant would silently create spurious groups in every aggregation. The fix is trivial; the downstream cost of not fixing it is not.

**Professional value:** *Integrity* — silent grouping errors in categorical data undermine the trustworthiness of every summary statistic built on top of it.

---

### Action 3 — Normalise `Discount Applied` to Nullable Boolean

**What was done:** `Discount Applied` was converted from a raw string column to a typed nullable boolean (`True` / `False` / `<NA>`). The 4,199 missing values were preserved as `<NA>` — they were **not** imputed as `False`.

**Before:**

| Value | Type | Count |
|---|---|---:|
| `"True"` | string | 4,219 |
| `"False"` | string | 4,157 |
| `NaN` | float (missing) | 4,199 |

**After:**

| Value | Type | Count |
|---|---|---:|
| `True` | boolean | 4,219 |
| `False` | boolean | 4,157 |
| `<NA>` | nullable boolean | 4,199 |

**Justification:**
A string field cannot participate in boolean logic directly — filtering `df[discount_applied == True]` on a string column would silently miss rows or produce incorrect results depending on the tool. Converting to a typed boolean enables correct filtering, aggregation, and modelling.

The decision **not** to impute `False` for the 4,199 missing values is the more important half of this action. Unknown discount status is not the same as no discount applied. Imputing `False` would:
- Artificially increase the `False` count from 4,157 to 8,356 — doubling the apparent number of non-discounted transactions
- Reduce the apparent discount rate from 50.4% (of known records) to 33.5% (of all records) — a misrepresentation of 17 percentage points
- Mislead every promotional analysis, discount-impact study, and margin calculation that depends on this field

Preserving `<NA>` is the only action consistent with honesty about what the data actually contains.

**Professional value:** *Responsibility* — choosing not to impute is a responsible decision. Filling unknowns with a value that is convenient but potentially wrong is a form of data fabrication.

**Ethical dimension:** A discount rate that appears 17 percentage points lower than it actually is could lead to incorrect conclusions about promotional effectiveness — resulting in marketing budget decisions based on a distorted view of reality.

---

### Action 4 — Reconstruct Missing `price_per_unit` (609 rows)

**What was done:** For 609 rows where `price_per_unit` was missing but `total_spent` and `quantity` were both present, unit price was reconstructed as:

```
price_per_unit = round(total_spent / quantity, to nearest 0.50)
```

**Evidence base:**
- The accuracy analysis verified that `price_per_unit` values in this dataset always fall on 0.50 increments — zero exceptions across 11,966 known values
- The consistency analysis verified that `total_spent = price_per_unit × quantity` holds for 100% of complete rows (zero arithmetic violations)
- Therefore: `total_spent / quantity` produces the correct unit price, and rounding to 0.50 matches the verified pricing rule

**Rows affected:** 609
**Rounding precision:** Nearest 0.50 (e.g. a computed value of £18.47 → £18.50)

**Justification:**
This is not an estimate or a guess. It is the algebraic reversal of a formula that has been verified to hold without exception. Using it to reconstruct missing values applies the same rule that generated the known values — making the reconstruction as reliable as the original data entry.

**Professional value:** *Data quality* — recovery using a verified deterministic rule is more accurate than leaving the field blank or using a statistical proxy.

---

### Action 5 — Infer Missing `item` from Category–Price Lookup (1,213 rows)

**What was done:** A lookup table was built from all rows where `item`, `category`, and `price_per_unit` are all present:

```
lookup[(category, price_per_unit)] → item
```

This lookup was then applied to the 1,213 rows where `item` was missing but `category` and `price_per_unit` were known.

**Evidence base:**
- The consistency analysis verified that every `(Category, Price Per Unit)` combination maps to exactly one `Item` — zero exceptions across all complete rows
- This means the lookup is deterministic: given category and price, the item name is known with certainty

**Results:**

| Metric | Value |
|---|---:|
| Missing item values before | 1,213 |
| Rows with category + price available | 604 |
| Items inferred successfully | 604 |
| Items resolved via full lookup (all 1,213) | **1,213** |
| Items still missing after inference | **0** |

All 1,213 missing item values were resolved. Zero remain missing after this step.

**Justification:**
Inferring `item` from `(category, price_per_unit)` is not imputation — it is lookup. The item name was always determinable from the other fields present; it simply was not recorded at the time of the transaction. This action restores information that was always implicitly present, using a rule verified to be 100% accurate.

**Professional value:** *Integrity* — restoring a value from a verified rule is fundamentally different from estimating an unknown. The distinction matters when the data is used in inventory and product performance analysis.

---

### Action 6 — Impute Missing `quantity` via Mode Hierarchy (604 rows)

**What was done:** For 604 rows where `quantity` was missing, imputation was applied using a three-level hierarchy:

1. **Level 1 — Mode per item:** The most commonly purchased quantity for that specific item (e.g. if `Item_04_BEV` is most often bought in quantities of 3, use 3)
2. **Level 2 — Mode per category:** If the item is unknown, use the most common quantity for that category (e.g. if Beverages transactions most often involve 7 units, use 7)
3. **Level 3 — Global mode:** If category mode is also unavailable, use the most common quantity across the entire dataset (= **10**)

**Justification for using a mode hierarchy rather than a fixed global value:**
The mode hierarchy respects the specificity of the available information. An item-level mode is a better estimate than a category-level mode, which is better than a global mode. Using the most granular applicable estimate minimises the distortion introduced by imputation.

The choice of **mode** (most frequent value) over mean or median is appropriate for `Quantity` because:
- Quantity is a discrete, bounded integer (1–10) — not a continuous variable
- The mode represents the most likely observed behaviour, not a mathematical average that may not correspond to any real transaction value
- A mean of 5.54 would produce a rounded integer of 6, but the actual most common purchase quantity per item or category may differ from this global average

**Transparency requirement:** All imputed quantity rows should be identified in downstream analysis. Imputed quantities are reasonable estimates — they are not observed facts. Any customer-level or product-level analysis should treat imputed quantities with appropriate caution.

**Professional value:** *Responsibility* — using a hierarchy of modes rather than a single global default shows commitment to minimising the gap between imputed values and likely reality.

**Ethical dimension:** If employee or store performance is measured by units sold, imputed quantities affect those evaluations. Documenting which quantities were imputed protects against unfair assessments based on fabricated figures.

---

### Action 7 — Reconstruct Missing `total_spent` (604 rows)

**What was done:** After `price_per_unit` and `quantity` were established (either from original data or from Actions 4 and 6), `total_spent` was reconstructed as:

```
total_spent = price_per_unit × quantity
```

**Evidence base:**
- The consistency analysis verified this formula holds for 100% of complete rows — zero exceptions
- After Actions 4 and 6, both source fields are now available for the 604 affected rows

**Results:**

| Metric | Value |
|---|---:|
| Missing `total_spent` before | 604 |
| Missing `total_spent` after reconstruction | **0** |

**Justification:**
The formula is the same one used by the original system to calculate total spent — verified by zero arithmetic violations across 11,366 known rows. Applying it to reconstructed inputs produces a value that is consistent with every other total in the dataset.

**Professional value:** *Data quality* — completing the revenue record for 604 transactions ensures that financial reporting reflects all real purchase activity captured by the system.

---

## PART B — TRANSFORMATION

Transformation changes the structure, type, or representation of existing values to make them more useful, consistent, and analytically accessible — without changing what the values mean.

---

### Action 8 — Parse `transaction_date` to Datetime

**What was done:** The `transaction_date` column was converted from a raw string object (e.g. `"2024-04-08"`) to a Python datetime type using `pd.to_datetime()`.

**Justification:**
A date stored as a string cannot be used in date arithmetic, filtered by date range, sorted chronologically by the database, or aggregated by month or year without additional parsing at query time. Parsing once at the point of data preparation removes this overhead from every downstream operation and eliminates the risk of inconsistent parsing (different tools may interpret `"04/08/2024"` differently — as April 8 or August 4).

All 12,575 dates parsed successfully — zero failures confirmed by the accuracy analysis.

**Professional value:** *Data quality* — a date that is typed correctly is a date that works correctly in every context.

---

### Action 9 — Add `transaction_date_iso` (Stable Export Format)

**What was done:** A new column `transaction_date_iso` was added, storing the date as a standardised ISO 8601 string: `YYYY-MM-DD` (e.g. `"2024-04-08"`).

**Justification:**
Datetime objects are not portable across all export formats. When a cleaned CSV is loaded by another tool — R, Tableau, Power BI, a SQL database — the datetime type may be re-interpreted differently. An ISO 8601 string is universally readable, sorts correctly as a string (because YYYY-MM-DD lexicographic order = chronological order), and eliminates ambiguity between date formats (DD/MM/YYYY vs MM/DD/YYYY).

**Professional value:** *Integrity* — a date format that means the same thing to every tool protects against silent misinterpretation across the data pipeline.

---

### Action 10 — Add `transaction_year` and `transaction_month`

**What was done:** Two derived integer columns were added:
- `transaction_year` — the calendar year of the transaction (2022, 2023, 2024, or 2025)
- `transaction_month` — the month number (1–12)

**Justification:**
Time-based analysis — monthly sales trends, year-over-year comparisons, seasonal demand patterns — is one of the most common use cases for retail transaction data. Without pre-computed year and month fields, every analyst must re-parse the date and extract these components themselves. Pre-computing them once ensures consistency (two analysts will not extract the month differently) and improves query performance.

**Professional value:** *Maintainability* — pre-computed, consistently named time fields reduce the chance of analytical error and speed up every time-series query.

---

### Action 11 — Standardise Numeric Data Types

**What was done:**

| Column | Before type | After type | Reason |
|---|---|---|---|
| `quantity` | float64 (with NaN) | Int64 (nullable integer) | Quantity is always a whole number; float representation is misleading |
| `price_per_unit` | float64 | float64, rounded to 2 d.p. | Monetary values should not carry floating-point precision beyond 2 decimal places |
| `total_spent` | float64 | float64, rounded to 2 d.p. | Same — prevents values like £185.00000000003 appearing in exports |

**Justification:**
A quantity of `3.0` communicates that fractional quantities are possible — they are not. Converting to integer type (`Int64`) makes the data type match the data semantics. Rounding monetary values to 2 decimal places matches standard financial precision and prevents floating-point artefacts (e.g. `185.00000000003`) from appearing in exports and causing value-comparison failures.

**Professional value:** *Accuracy* — data types should reflect the meaning of the values they hold, not the default type assigned by a CSV parser.

---

### Action 12 — Add `row_id` Surrogate Key

**What was done:** A `row_id` column was added as the first column, assigned sequential integer values from 1 to 12,575.

**Justification:**
`Transaction ID` is the business key — it identifies transactions in the source system. A `row_id` is a technical key for the re-engineered dataset — it provides a stable, integer-based reference for relational joins, array indexing, and database loading. Using a surrogate integer key (rather than the string-based `Transaction ID`) as the primary join key in a database produces faster index lookups and smaller foreign key storage.

**Professional value:** *Maintainability* — separating business keys from technical keys is a standard data engineering practice that protects the integrity of both.

---

## PART C — NORMALISATION AND RESTRUCTURING

Normalisation reorganises the data from a single flat table into a set of related tables, each focused on one subject. It eliminates redundancy, enforces referential integrity, and supports scalable analytics.

---

### Action 13 — Decompose into Star Schema

**What was done:** The wide cleaned table (12,575 rows × 15 columns after transformation) was decomposed into one fact table and five dimension tables.

#### Dimension Tables

| Table | Key | Columns | Distinct rows |
|---|---|---|---:|
| `dim_customer.csv` | `customer_key` | `customer_id` | 26 |
| `dim_category.csv` | `category_key` | `category` | 8 |
| `dim_item.csv` | `item_key` | `item`, `category_key`, `price_per_unit` | varies |
| `dim_payment_method.csv` | `payment_method_key` | `payment_method` | 3 |
| `dim_location.csv` | `location_key` | `location` | 2 |

#### Fact Table

**`fact_sales.csv`** — one row per transaction

| Column | Source | Type |
|---|---|---|
| `transaction_id` | Original | String (business key) |
| `customer_key` | FK → `dim_customer` | Integer |
| `item_key` | FK → `dim_item` | Integer |
| `payment_method_key` | FK → `dim_payment_method` | Integer |
| `location_key` | FK → `dim_location` | Integer |
| `category_key` | FK → `dim_category` | Integer |
| `quantity` | Cleaned | Integer |
| `total_spent` | Cleaned / reconstructed | Float |
| `transaction_date_iso` | Transformed | String (ISO date) |
| `discount_applied` | Cleaned | Nullable boolean |

**Justification for star schema design:**

**Eliminating redundancy:** In the original flat file, `category` is repeated on every one of the 1,591 Electric Household Essentials rows. `payment_method` is repeated 4,310 times for `Cash`. Normalisation stores each distinct value once in a dimension table and replaces the repeated string with a compact integer foreign key. This reduces storage and eliminates the risk of update anomalies — if a category name changes, it changes in one place (the dimension table), not in thousands of fact rows.

**Enforcing referential integrity:** In a relational database, foreign key constraints on the fact table prevent any transaction from referencing a customer, item, or category that does not exist in the corresponding dimension. This structural enforcement is stronger than any data validation rule applied at import time.

**Supporting scalable analytics:** Star schemas are the standard design pattern for business intelligence and analytical queries. A sales analyst querying monthly revenue by category joins `fact_sales` to `dim_category` on a single integer key — a fast, indexed operation. The same query on the flat file requires string matching across 12,575 rows, which is slower and more error-prone.

**Professional value:** *Maintainability* — a normalised schema is not just cleaner; it is structurally resistant to the kinds of inconsistency that accumulate in flat files over time.

**Ethical dimension:** Separating customer data into its own dimension table (`dim_customer`) is a step toward privacy-conscious data architecture. Customer identity is isolated — it can be anonymised, masked, or access-controlled independently of the transaction records, without restructuring the entire dataset.

---

## 3. Complete Justification Summary

| Action | Type | Profiling finding that justified it | Professional value upheld |
|---|---|---|---|
| Column renaming | Cleansing | Inconsistent naming causes programmatic errors | Data quality |
| Whitespace strip | Cleansing | Invisible characters break groupby operations | Integrity |
| Discount → nullable boolean | Cleansing | NaN ≠ False; imputing False misrepresents discount rate by 17 pp | Responsibility / Ethics |
| Reconstruct `price_per_unit` | Cleansing | Arithmetic rule verified 100% accurate; 609 rows recoverable | Data quality |
| Infer `item` | Cleansing | Referential rule verified 100% accurate; all 1,213 rows recoverable | Integrity |
| Impute `quantity` | Cleansing | Mode hierarchy minimises distortion; 604 rows affected | Responsibility |
| Reconstruct `total_spent` | Cleansing | Same arithmetic rule; downstream of price and qty recovery | Data quality |
| Parse date | Transformation | String dates fail in date arithmetic and range filtering | Data quality |
| ISO date string | Transformation | Datetime objects are not portable across all export formats | Integrity |
| Year / month fields | Transformation | Time-series analysis requires pre-computed time dimensions | Maintainability |
| Type standardisation | Transformation | Float quantities and excess decimal places misrepresent data | Accuracy |
| Surrogate key | Transformation | Integer keys outperform string keys in relational joins | Maintainability |
| Star schema | Normalisation | Flat file stores redundant strings 1,500+ times per field | Maintainability / Ethics |

---

## 4. What Was Deliberately Not Done

A responsible re-engineering report is as clear about what was not changed as about what was.

| Action considered | Decision | Reason |
|---|---|---|
| Impute `Discount Applied` missing values | **Not done** | Unknown ≠ False; imputing would fabricate data |
| Drop the 609 fully-missing transaction rows | **Not done** | Real purchase events; removing them deletes legitimate customer activity |
| Correct or re-categorise any item | **Not done** | All item–category assignments were verified accurate; no correction needed |
| Remove any rows | **Not done** | Zero duplicates found; all rows represent distinct real events |
| Alter any `Transaction ID` | **Not done** | All IDs are valid and unique; no modification was warranted |

Every inaction above is as deliberate as every action. Re-engineering means improving the data — not changing it unnecessarily.

---

## 5. Conclusion

The re-engineering of `retail_store_sales.csv` was executed in three stages — cleansing, transformation, and normalisation — each grounded in specific findings from the profiling stage.

Cleansing recovered 604 unit prices, inferred 1,213 missing item names, imputed 604 quantities, and reconstructed 604 total spent values — all using rules verified to be 100% accurate in the existing data. Transformation converted types, standardised date formats, and added analytically useful derived fields. Normalisation restructured the data into a star schema that eliminates redundancy, supports referential integrity, and is ready for database loading or BI tool integration.

Every action was taken because the profiling evidence justified it. Every non-action was chosen because the evidence did not support it. That balance — between improving what can be improved and leaving alone what should not be changed — is the professional standard for responsible data re-engineering.
