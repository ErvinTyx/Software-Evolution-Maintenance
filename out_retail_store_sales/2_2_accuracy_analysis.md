# Data Profiling Report — Accuracy Analysis
**Dataset:** `retail_store_sales.csv`
**Profiling Role:** Accuracy Analysis
**Records Examined:** 12,575 rows × 11 columns
**Date Range Covered:** 2022-01-01 → 2025-01-18

---

## 1. What Is Accuracy and Why Does It Matter

Accuracy is the degree to which data values correctly represent the real-world facts they are intended to capture. It is the most demanding dimension of data quality — a value can be present (complete), formatted correctly (consistent), and still be wrong.

Accuracy errors fall into three categories:
- **Plausibility violations** — values that are technically valid but outside the range of what could realistically occur (e.g. a quantity of 10,000 units in a single retail transaction)
- **Domain rule violations** — values that break a known business rule (e.g. a negative price, a transaction date before the business opened)
- **Referential accuracy failures** — values that are internally inconsistent with other fields (e.g. an item assigned to the wrong category)

In a retail dataset, accuracy errors directly corrupt revenue reports, distort demand signals, and produce misleading KPIs. A single inaccurate unit price on a high-volume product can misstate that product's contribution to total revenue by thousands of pounds over a reporting period. Accuracy profiling exists to find and document these errors before they reach an analyst's dashboard.

---

## 2. Methodology

The following accuracy checks were applied to the raw, unmodified dataset:

1. **Plausibility — `Quantity`:** Verified all values are whole numbers within the range 1–10 (the physically plausible range for a single retail purchase; confirmed as the dataset's business rule)
2. **Plausibility — `Price Per Unit`:** Verified all values are positive and fall on 0.50 increments (the pricing granularity observed across all complete rows)
3. **Plausibility — `Total Spent`:** Verified all values are positive and consistent with `Price × Quantity` within ±0.01
4. **Domain rule — `Transaction Date`:** Verified all dates are parseable, fall within the stated operational period, and contain no future-dated or implausible values
5. **Domain rule — `Transaction ID` and `Customer ID`:** Verified format adherence and uniqueness
6. **Domain rule — `Discount Applied`:** Verified the field contains only valid boolean states
7. **Referential accuracy — `(Category, Price Per Unit) → Item`:** Verified each item is consistently assigned to a single category at a consistent price
8. **Outlier analysis:** Examined `Quantity`, `Price Per Unit`, and `Total Spent` for values that, while within bounds, may represent data entry anomalies
9. **Categorical accuracy:** Verified that all categorical fields contain only expected, legitimate values

Results are reported as counts of violations per check, with the base population (rows in scope) stated for each.

---

## 3. Numeric Field Accuracy

### 3.1 `Quantity`

| Check | Rows in scope | Violations | Violation rate |
|---|---:|---:|---:|
| Non-integer values | 11,971 | **0** | 0.00% |
| Values less than 1 | 11,971 | **0** | 0.00% |
| Values greater than 10 | 11,971 | **0** | 0.00% |
| Negative values | 11,971 | **0** | 0.00% |

**Descriptive statistics (non-null rows):**

| Statistic | Value |
|---|---:|
| Count | 11,971 |
| Mean | 5.54 |
| Standard deviation | 2.86 |
| Minimum | 1 |
| 25th percentile | 3 |
| Median | 6 |
| 75th percentile | 8 |
| Maximum | 10 |

**Finding:** Every recorded quantity is a whole number between 1 and 10. The distribution is approximately uniform across the full range, with a mean of 5.54 and a standard deviation of 2.86. This is consistent with a retail environment where customers purchase between 1 and 10 units of a single item per transaction. No quantity value is implausible — there are no 0-unit transactions (which would indicate a recording error) and no quantities exceeding 10 (which would violate the observed business rule).

**Accuracy verdict: PASS — all 11,971 quantity values are accurate within defined bounds.**

---

### 3.2 `Price Per Unit`

| Check | Rows in scope | Violations | Violation rate |
|---|---:|---:|---:|
| Negative price | 11,966 | **0** | 0.00% |
| Zero price | 11,966 | **0** | 0.00% |
| Not on 0.50 increment | 11,966 | **0** | 0.00% |

**Finding:** Every recorded price is positive and falls precisely on a 0.50 price increment — for example, £7.50, £18.50, £29.00. This is consistent across all eight product categories and all 11,966 non-null price rows. No price is zero (which would suggest a free item recorded in error) and no price is negative (which would suggest a refund mistakenly coded as a transaction).

The consistent use of 0.50 increments indicates that prices are set by a pricing policy, not entered freely. This pricing discipline is an accuracy signal — it means that any reconstructed price value that does not fall on a 0.50 increment should be flagged as potentially inaccurate.

**Accuracy verdict: PASS — all 11,966 price values are accurate within defined rules.**

---

### 3.3 `Total Spent`

| Check | Rows in scope | Violations | Violation rate |
|---|---:|---:|---:|
| Negative total | 11,971 | **0** | 0.00% |
| Zero total | 11,971 | **0** | 0.00% |
| `\|Total − (Price × Qty)\| > 0.01` | 11,366 | **0** | 0.00% |

**Finding:** All recorded `Total Spent` values are positive and agree with the arithmetic product of `Price Per Unit × Quantity` to within ±0.01. There is not a single transaction where the stated total contradicts the unit price and quantity. This confirms that `Total Spent` is not a manually entered field subject to human error — it is computed from the other two fields and recorded correctly every time.

**Accuracy verdict: PASS — all 11,971 total values are arithmetically accurate.**

---

## 4. Date and Identifier Accuracy

### 4.1 `Transaction Date`

| Check | Result |
|---|---|
| Unparseable dates | 0 |
| Dates before 2022-01-01 (stated start) | 0 |
| Dates after 2025-01-18 (last record) | 0 |
| Future-dated transactions | 0 |
| Date range | 2022-01-01 → 2025-01-18 |

**Finding:** All 12,575 transaction dates are valid, parseable, and fall within the operational window of the dataset. The three-year span (January 2022 to January 2025) is internally consistent — there are no transactions dated before the dataset begins and none dated after the most recent record. The absence of future-dated entries rules out a common data entry error where a year is mistyped (e.g. 2025 entered as 2205).

Transaction dates are distributed continuously across the full period with no unexplained gaps, confirming the dataset represents genuine operational history rather than a partial or stitched-together extract.

**Accuracy verdict: PASS — all 12,575 date values are accurate and temporally plausible.**

### 4.2 `Transaction ID`

| Check | Result |
|---|---|
| Format pattern | `TXN_` prefix + 7-digit numeric suffix |
| Rows conforming to pattern | 12,575 (100%) |
| Duplicate values | **0** |
| Missing values | **0** |

**Finding:** Every Transaction ID follows the format `TXN_XXXXXXX` (e.g. `TXN_6867343`). All 12,575 values are unique — confirming that no transaction has been recorded twice and that the ID can serve reliably as a primary key. The consistent format and perfect uniqueness make `Transaction ID` the most accurate field in the dataset.

**Accuracy verdict: PASS — all transaction IDs are correctly formatted, unique, and complete.**

### 4.3 `Customer ID`

| Check | Result |
|---|---|
| Format pattern | `CUST_` prefix + 2-digit numeric suffix |
| Rows conforming to pattern | 12,575 (100%) |
| Missing values | **0** |

**Finding:** All Customer IDs follow the `CUST_XX` format consistently. The 2-digit suffix (e.g. `CUST_09`, `CUST_22`) indicates a bounded set of customer accounts. Every transaction is traceable to a customer, with no ambiguous or malformed IDs.

**Accuracy verdict: PASS — all customer IDs are correctly formatted and complete.**

---

## 5. Categorical Field Accuracy

### 5.1 `Category`

| Value | Count | Legitimate? |
|---|---:|---|
| Electric Household Essentials | 1,591 | Yes |
| Furniture | 1,591 | Yes |
| Food | 1,588 | Yes |
| Milk Products | 1,584 | Yes |
| Butchers | 1,568 | Yes |
| Beverages | 1,567 | Yes |
| Computers & Electric Accessories | 1,558 | Yes |
| Patisserie | 1,528 | Yes |
| **Any other value** | **0** | — |

**Finding:** Exactly 8 distinct, legitimate category values. No misspellings, abbreviations, or unknown categories were found. The balanced distribution (12.2%–12.7% per category) indicates that all categories are actively transacted and that the dataset is not skewed toward a subset of the product range.

**Accuracy verdict: PASS — all 12,575 category values are accurate.**

### 5.2 `Payment Method`

| Value | Count | Legitimate? |
|---|---:|---|
| Cash | 4,310 | Yes |
| Digital Wallet | 4,144 | Yes |
| Credit Card | 4,121 | Yes |
| **Any other value** | **0** | — |

**Finding:** Three valid payment methods, evenly distributed, with no invalid entries. No transactions are recorded with an unrecognised payment method.

**Accuracy verdict: PASS — all 12,575 payment method values are accurate.**

### 5.3 `Location`

| Value | Count | Legitimate? |
|---|---:|---|
| Online | 6,354 | Yes |
| In-store | 6,221 | Yes |
| **Any other value** | **0** | — |

**Finding:** Two valid locations. The near-equal split (50.5% online / 49.5% in-store) is realistic for a modern retail operation with an active e-commerce channel. No ambiguous or hybrid location values exist.

**Accuracy verdict: PASS — all 12,575 location values are accurate.**

### 5.4 `Discount Applied`

| Value | Count | Legitimate? |
|---|---:|---|
| True | 4,219 | Yes |
| False | 4,157 | Yes |
| NaN | 4,199 | Unknown |
| **Any other value** | **0** | — |

**Finding:** The field contains only valid boolean representations. There are no invalid strings, no numeric encodings (`0`/`1`), and no ambiguous values such as `"maybe"` or `"N/A"`. The 4,199 null values are not an accuracy problem in themselves — they are a completeness problem documented separately. From an accuracy standpoint, every recorded value is correct.

**Accuracy verdict: CONDITIONAL PASS — all 8,376 non-null values are accurate. The 4,199 nulls are a completeness issue, not an accuracy error.**

---

## 6. Referential Accuracy

### 6.1 Item–Category Assignment

| Check | Result |
|---|---|
| Items appearing in more than one category | **0** |
| `(Category, Price Per Unit)` groups with more than one item | **0** |
| Items with inconsistent pricing across rows | **0** |

**Finding:** Every item in the dataset belongs to exactly one category and is sold at exactly one price. No item has been mis-categorised (e.g. a beverage recorded under Food in some rows and Beverages in others). No item is sold at different prices in different transactions. The referential structure of the dataset is completely accurate.

This finding has a practical consequence: the `(Category, Price Per Unit) → Item` mapping can be used as a **ground truth lookup** to infer missing item values — because the mapping is accurate and stable across all 12,575 rows.

**Accuracy verdict: PASS — all item–category–price relationships are referentially accurate.**

---

## 7. Accuracy Issues Summary

| Field | Check | Violations | Verdict |
|---|---|---:|---|
| Quantity | Non-integer, out-of-range, negative | 0 | ✅ PASS |
| Price Per Unit | Negative, zero, off-increment | 0 | ✅ PASS |
| Total Spent | Negative, zero, arithmetic mismatch | 0 | ✅ PASS |
| Transaction Date | Unparseable, out-of-range, future-dated | 0 | ✅ PASS |
| Transaction ID | Format, uniqueness | 0 | ✅ PASS |
| Customer ID | Format, completeness | 0 | ✅ PASS |
| Category | Valid values only | 0 | ✅ PASS |
| Payment Method | Valid values only | 0 | ✅ PASS |
| Location | Valid values only | 0 | ✅ PASS |
| Discount Applied | Valid boolean values (non-null) | 0 | ✅ CONDITIONAL PASS |
| Item–Category | Cross-row referential accuracy | 0 | ✅ PASS |

**Zero accuracy violations were found across all checks and all 12,575 records.**

---

## 8. What Accuracy Analysis Reveals About the Missing Data

A critical insight from accuracy profiling is that the missing values in this dataset are not caused by inaccuracy — they are caused by incompleteness. This distinction matters:

- If values were inaccurate (e.g. items recorded in the wrong category), the errors would need to be corrected by overwriting the wrong value with the right one
- Because values are accurate whenever they are present, the re-engineering task is purely about **filling gaps** using the rules that the accurate data has revealed

Specifically:
- The accuracy of `Price Per Unit` (always on 0.50 increments) defines the rounding rule for price reconstruction
- The accuracy of `Total Spent = Price × Quantity` (zero violations) confirms that arithmetic reconstruction is safe
- The referential accuracy of `(Category, Price) → Item` confirms that item inference is deterministic and not a guess

In this dataset, **accuracy is the enabler of re-engineering**. The rules embedded in the accurate data are the tools used to recover the incomplete data.

---

## 9. Justification for Data Re-engineering

| Accuracy Finding | Re-engineering action justified |
|---|---|
| Price always on 0.50 increments | Round all reconstructed prices to nearest 0.50 — any other value would be inaccurate by the dataset's own rule |
| Total = Price × Qty holds 100% | Reconstruct 604 missing totals arithmetically — the rule is verified accurate |
| Item–Category–Price is 1-to-1 | Infer 604 missing items via lookup — the reference data is accurate enough to trust |
| All categorical fields are clean | No category/method/location corrections required — normalisation can proceed safely |
| Transaction IDs are unique and complete | `Transaction ID` can be used as the primary transaction key without modification |

---

## 10. Conclusion

The accuracy analysis of `retail_store_sales.csv` produces a clear and evidence-based finding: **the data that is present is accurate**. Across 10 dimensions and every applicable check, zero accuracy violations were found. Numeric values are plausible and correctly bounded. Dates are valid and temporally coherent. Identifiers follow consistent formats. Categorical fields contain only legitimate values. Referential relationships are perfectly consistent across all rows.

This is a significant result — it means that the dataset's problems are confined entirely to **what is absent**, not to **what is present**. The re-engineering task is not one of correction but of recovery: using the accurate rules embedded in the complete data to fill the gaps left by the incomplete data.

The accuracy findings are not merely reassuring. They are actionable. Every re-engineering decision — rounding reconstructed prices to 0.50, using arithmetic reconstruction for total spent, inferring items from category–price lookups — is directly grounded in an accuracy check that verified the rule holds without exception.

Data that is rigorously profiled for accuracy does not just pass a quality gate. It reveals the structure that makes recovery possible.
