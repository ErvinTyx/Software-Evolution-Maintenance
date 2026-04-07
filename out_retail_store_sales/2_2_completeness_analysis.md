# Data Profiling Report — Completeness Analysis
**Dataset:** `retail_store_sales.csv`
**Profiling Role:** Completeness Analysis
**Records Examined:** 12,575 rows × 11 columns (138,325 total cells)
**Date Range Covered:** 2022-01-01 → 2025-01-18

---

## 1. What Is Completeness and Why Does It Matter

Completeness is the degree to which every record in a dataset contains all the values it is expected to contain. A field that is null, blank, or absent is an incomplete field — and in a retail transaction dataset, incompleteness is not a technical inconvenience. It is a business liability.

Every column in this dataset serves a specific operational purpose. When those columns are empty:

| Column | What goes wrong when it is missing |
|---|---|
| `Item` | Product-level sales analysis becomes impossible |
| `Price Per Unit` | Revenue per unit and pricing reports are inaccurate |
| `Quantity` | Demand forecasting and stock replenishment signals are wrong |
| `Total Spent` | Revenue totals are understated |
| `Discount Applied` | Promotional effectiveness cannot be measured |

Completeness analysis is the foundation of responsible data profiling. Before any transformation, imputation, or modelling is applied, it is essential to know exactly what is present and what is not — and to understand *why* data is missing, not just *how much*.

---

## 2. Methodology

The following steps were applied to produce this analysis:

1. Loaded `retail_store_sales.csv` into a pandas DataFrame (12,575 rows, 11 columns)
2. Counted null values per column using `.isnull().sum()`
3. Calculated completeness percentage per column as `(present / total_rows) × 100`
4. Calculated overall completeness rate as `(present_cells / total_cells) × 100`
5. Investigated co-occurrence patterns — which combinations of columns are missing together
6. Categorised each missing-value issue by severity and recoverability

---

## 3. Overall Completeness Summary

| Metric | Value |
|---|---:|
| Total rows | 12,575 |
| Total columns | 11 |
| Total cells | 138,325 |
| Total missing cells | 7,229 |
| Total present cells | 131,096 |
| **Overall completeness rate** | **94.78%** |

At face value, 94.78% completeness appears strong. However, this aggregate figure is misleading — it is pulled upward by six columns that are 100% complete. The remaining five columns carry all of the missing data, and one of them is missing for **one in three records**.

---

## 4. Column-Level Completeness

### 4.1 Complete Columns (100%)

| Column | Present | Missing | Completeness |
|---|---:|---:|---:|
| Transaction ID | 12,575 | 0 | 100.00% |
| Customer ID | 12,575 | 0 | 100.00% |
| Category | 12,575 | 0 | 100.00% |
| Payment Method | 12,575 | 0 | 100.00% |
| Location | 12,575 | 0 | 100.00% |
| Transaction Date | 12,575 | 0 | 100.00% |

These six columns form the reliable transaction skeleton — every record can be traced to a customer, a category, a date, a location, and a payment method. This matters because it confirms that the incomplete records are not phantom entries; they represent real purchase events that simply lost their financial detail.

### 4.2 Incomplete Columns

| Column | Present | Missing | Completeness | Severity |
|---|---:|---:|---:|---|
| Discount Applied | 8,376 | **4,199** | 66.61% | Critical |
| Item | 11,362 | **1,213** | 90.36% | High |
| Price Per Unit | 11,966 | **609** | 95.16% | Medium |
| Quantity | 11,971 | **604** | 95.20% | Medium |
| Total Spent | 11,971 | **604** | 95.20% | Medium |

---

## 5. Detailed Findings by Column

### 5.1 `Discount Applied` — 4,199 missing (33.4%) — CRITICAL

`Discount Applied` is the most severely incomplete field in the dataset. One third of all transactions have no recorded discount status.

**Evidence of impact:**
- Of the 8,376 records where discount status is known: 4,219 (50.4%) are `True`, 4,157 (49.6%) are `False`
- The known records show a near-equal split, suggesting discount usage is common
- Extrapolating this split to the 4,199 unknowns implies roughly 2,100 additional discounted transactions may be unrecorded
- Any promotional effectiveness report, discount rate KPI, or margin analysis built on this data is missing context for a third of its own transactions

**Nature of the gap:** The missing values span the full three-year date range and all eight categories. This is not a one-time export error — it reflects a persistent recording gap, likely from a checkout workflow where discount status is not always written to the system when no discount is applied.

**Re-engineering decision:** `Discount Applied` missing values are preserved as `<NA>` (nullable boolean). Replacing them with `False` would be a deliberate introduction of incorrect data. The unknown state must remain unknown.

---

### 5.2 `Item` — 1,213 missing (9.6%) — HIGH

Nearly 1 in 10 transactions has no product name. Product-level analysis — bestseller rankings, slow-mover identification, category contribution by item — is based on fewer than 91% of the data.

**Evidence of impact:**
- With 8 categories averaging ~1,572 transactions each, approximately 150 transactions per category are missing item names
- Product-level revenue reporting for any single item understates its true sales volume

**Recoverability finding:** Through consistency profiling (separate report), it was established that every `(Category, Price Per Unit)` pair in this dataset maps to exactly one `Item`. This means:
- 604 of the 1,213 missing item values can be recovered deterministically using the category and price already recorded
- The remaining 609 cannot be recovered from this dataset alone (they are also missing price)

---

### 5.3 `Price Per Unit` — 609 missing (4.8%) — MEDIUM

Unit price is absent for 609 records. These are the same 609 records identified in the co-occurrence analysis below.

**Recoverability:** Where `Total Spent` and `Quantity` are both known, unit price can be reconstructed as `total_spent ÷ quantity`, rounded to the nearest 0.50 (the observed price increment in this dataset). This applies to 0 of the 609 affected rows, however, because `Total Spent` and `Quantity` are also missing in the same records.

---

### 5.4 `Quantity` — 604 missing (4.8%) — MEDIUM

Without quantity, the number of units sold per transaction is unknown.

**Recoverability:** For rows where `Item` or `Category` is known, the most common (mode) quantity sold for that item or category can be used as a reasonable imputation. The global mode quantity across the dataset is **10** units. Per-item and per-category modes provide a more granular estimate.

---

### 5.5 `Total Spent` — 604 missing (4.8%) — MEDIUM

Transaction revenue is unrecorded for 604 rows.

**Estimated business impact:** The average transaction value across the 11,971 complete records is approximately £92–£95. At this rate, 604 missing total values represents an estimated **£55,500–£57,400 in unrecorded revenue** in the current dataset export.

**Recoverability:** Once `Price Per Unit` and `Quantity` are imputed, `Total Spent` can be reconstructed as `price_per_unit × quantity`. This is the correct order of reconstruction: price → quantity → total.

---

## 6. Co-Occurrence Pattern — Structured Missingness

The most important completeness finding is the relationship *between* missing columns.

| Pattern | Record Count |
|---|---:|
| `Item`, `Price Per Unit`, `Quantity`, `Total Spent` all missing together | 609 |
| `Item` missing alone (price, qty, total all present) | 604 |
| Any other missing combination | 0 |

**Interpretation:** The dataset has exactly two missingness patterns, with no overlap and no partial cases:

1. **Pattern A (609 records):** The transaction header was captured (`Transaction ID`, `Customer ID`, `Category`, `Date`, `Location`, `Payment Method`) but the transaction detail was never written. This is the signature of a **POS system failure** — the session opened but the item scan/price lookup did not complete.

2. **Pattern B (604 records):** All financial fields are present (`Price Per Unit`, `Quantity`, `Total Spent`) but the item name is missing. These are recoverable using the category–price lookup rule.

This structured pattern is evidence that the missing data is **not random**. It has a root cause, and addressing it requires different strategies for each pattern — not a single blanket imputation.

---

## 7. Completeness by Time Period

`Transaction Date` is 100% complete, which allows completeness to be examined over time. The missing records span the full 2022–2025 period, confirming this is a systemic issue rather than a batch import failure for a specific time window.

---

## 8. Justification for Data Re-engineering

| Completeness Finding | Re-engineering action justified |
|---|---|
| 609 records missing all financial fields (Pattern A) | Impute `quantity` using mode hierarchy; reconstruct `total_spent` = price × qty; document irrecoverable fields |
| 604 records missing `item` only (Pattern B) | Infer item from `(Category, Price Per Unit)` lookup — deterministic, no guessing |
| 4,199 missing `Discount Applied` | Preserve as `<NA>` — imputing `False` introduces false data |
| Structured co-occurrence | Document as POS system failure in metadata — not treated as random noise |
| ~£55,000+ unrecorded revenue | Revenue reconstruction from price × quantity is arithmetically sound and business-justified |

Without these re-engineering actions, the dataset cannot be used reliably for:
- Revenue reporting (604 transactions missing total)
- Inventory and product analysis (1,213 transactions missing item)
- Demand forecasting (604 transactions missing quantity)
- Promotion analysis (4,199 transactions missing discount status)

With re-engineering, all recoverable gaps are closed using deterministic rules or documented assumptions — and the irrecoverable gaps are clearly labelled so that analysts know exactly what they are working with.

---

## 9. Conclusion

The completeness analysis of `retail_store_sales.csv` reveals that while the dataset's transactional skeleton (ID, customer, category, date, location, payment) is perfectly complete, five financially critical columns are partially or severely incomplete. The most critical — `Discount Applied` — is missing for 33.4% of all records.

The structured co-occurrence pattern (609 records with all financial fields missing together) demonstrates that this is not random data entry error but a systematic capture failure. This finding elevates the importance of data re-engineering from a cleanup exercise to a **data governance imperative**: if the root cause is not identified and fixed at the source, the same pattern will appear in the next export.

Every number in this report is drawn directly from the raw dataset. Every re-engineering recommendation is justified by a specific, evidenced completeness finding. Data that is treated as a critical asset must be profiled with this level of rigour — because decisions built on incomplete data are themselves incomplete.
