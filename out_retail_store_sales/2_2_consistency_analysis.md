# Data Profiling Report — Consistency Analysis
**Dataset:** `retail_store_sales.csv`
**Profiling Role:** Consistency Analysis
**Records Examined:** 12,575 rows × 11 columns
**Date Range Covered:** 2022-01-01 → 2025-01-18

---

## 1. What Is Consistency and Why Does It Matter

Consistency is the degree to which data conforms to expected rules, formats, relationships, and logical constraints — both within a single record and across the dataset as a whole. A dataset can be 100% complete and still be entirely inconsistent: values can be present but wrong, formatted differently across rows, or contradict each other within the same record.

In a retail transaction dataset, inconsistency is particularly dangerous because it is often invisible. A `Total Spent` field that silently disagrees with `Price Per Unit × Quantity` will not trigger an error — it will simply produce incorrect revenue figures. A `Discount Applied` field that mixes `"True"`, `"true"`, and `"1"` will silently split what should be a single group into three. These errors compound every time the data is aggregated, filtered, or modelled.

Consistency analysis examines five dimensions:
1. **Arithmetic consistency** — do calculated fields agree with their source fields?
2. **Format consistency** — do values follow a uniform, parseable format?
3. **Range consistency** — do values fall within physically and logically plausible bounds?
4. **Referential consistency** — do related fields agree with each other across rows?
5. **Categorical consistency** — are categorical fields restricted to a valid set of values?

---

## 2. Methodology

The following checks were applied systematically across all 12,575 records:

1. **Arithmetic:** Verified `Total Spent = Price Per Unit × Quantity` within a ±0.01 tolerance (to account for floating-point rounding) for all rows where all three fields are present
2. **Format — dates:** Applied `pd.to_datetime()` to `Transaction Date`; counted unparseable values
3. **Format — IDs:** Inspected `Transaction ID` and `Customer ID` for pattern adherence
4. **Range — quantity:** Checked all `Quantity` values are whole numbers within 1–10
5. **Range — price:** Verified `Price Per Unit` values fall on 0.50 increments (dataset rule discovered during profiling)
6. **Referential:** Grouped complete rows by `(Category, Price Per Unit)` and counted distinct `Item` values per group — to verify the categorical mapping rule
7. **Categorical:** Enumerated all distinct values in `Category`, `Payment Method`, `Location`, and `Discount Applied`
8. **Cross-field:** Checked whether `Discount Applied` states are represented consistently across all categories, payment methods, and locations

All checks were applied to the raw, unmodified dataset. Counts and percentages are based on the total number of rows where the relevant fields are present and non-null.

---

## 3. Arithmetic Consistency

### 3.1 `Total Spent = Price Per Unit × Quantity`

This is the most critical internal consistency rule in the dataset. If a transaction records a unit price and a quantity, the total should equal their product.

| Check | Rows in scope | Violations | Violation rate |
|---|---:|---:|---:|
| `\|Total Spent − (Price × Qty)\| > 0.01` | 11,366 | **0** | **0.00%** |

**Finding:** Every complete transaction satisfies the arithmetic rule exactly (within ±0.01 rounding tolerance). There are zero cases where `Total Spent` contradicts `Price Per Unit × Quantity`.

**Significance:** This is a strong positive consistency signal. It confirms that the dataset's internal financial logic was correctly enforced at the point of capture — the system calculated totals correctly. This also means that during re-engineering, `Total Spent` can be safely reconstructed as `Price Per Unit × Quantity` for the rows where it is missing, because the rule has been verified to hold across 100% of the 11,366 complete rows.

---

## 4. Format Consistency

### 4.1 `Transaction Date`

| Check | Result |
|---|---|
| Unparseable date values | **0** |
| Date format used | Mixed (e.g. `2024-04-08`, `2023-07-23`) |
| Parseable as ISO 8601 | Yes — all 12,575 values |
| Date range | 2022-01-01 → 2025-01-18 |
| Dates in the future (relative to last record) | 0 |

**Finding:** All 12,575 transaction dates are parseable, correctly ordered, and fall within a logical three-year window. No corrupted, out-of-range, or future-dated values exist.

**Re-engineering action justified:** Dates should be stored as a standardised ISO date string (`YYYY-MM-DD`) rather than left as a raw string object, and derived fields (`transaction_year`, `transaction_month`) should be added to support time-based analytics without requiring repeated date parsing.

### 4.2 `Transaction ID`

All Transaction IDs follow the format `TXN_XXXXXXX` (a 7-digit numeric suffix). No malformed IDs were found. This format consistency makes the field reliable as a unique transaction key.

### 4.3 `Customer ID`

All Customer IDs follow the format `CUST_XX` (a 2-digit numeric suffix, e.g. `CUST_09`). The format is consistent across all 12,575 rows. The limited range (2-digit suffix) indicates a bounded customer population, which is consistent with a test or synthetic dataset.

### 4.4 `Discount Applied`

| Value | Count |
|---|---:|
| `True` | 4,219 |
| `False` | 4,157 |
| `NaN` (missing) | 4,199 |
| Any other value | **0** |

**Finding:** The field contains only two distinct non-null values: `True` and `False`. There are no mixed representations (no `"true"`, `"1"`, `"yes"`, `"TRUE"` variants), no numeric encodings, and no invalid strings. Format is consistent within the non-null population.

**However:** The presence of 4,199 null values alongside `True`/`False` creates an implicit three-state field where the third state (`<NA>`) has an ambiguous meaning. This is a **consistency concern at the semantic level** — it is not clear whether `NaN` means "no discount was applied" or "discount status was not recorded." These two interpretations lead to fundamentally different analytical conclusions. Preserving `<NA>` as a distinct state (rather than coercing it to `False`) is the only consistent and honest treatment.

---

## 5. Range Consistency

### 5.1 `Quantity`

| Check | Result |
|---|---|
| Non-integer values | **0** |
| Values below 1 | **0** |
| Values above 10 | **0** |
| Observed range | 1 – 10 |
| Mean quantity | 5.54 |
| Standard deviation | 2.86 |

**Finding:** All 11,971 non-null `Quantity` values are whole numbers within the expected range of 1–10. The distribution is approximately uniform across the range, which is consistent with a retail setting where customers buy between 1 and 10 units of a single item per transaction.

### 5.2 `Price Per Unit`

| Check | Result |
|---|---|
| Values not on 0.50 increments | **0** |
| Negative prices | **0** |
| Zero prices | **0** |

**Finding:** Every non-null `Price Per Unit` value falls on a 0.50 price increment (e.g. `18.50`, `29.00`, `7.50`). This is a dataset-level business rule — prices are set in half-pound/half-dollar increments. Zero violations confirm the rule holds consistently across all 11,966 priced rows.

**Significance for re-engineering:** When `Price Per Unit` is reconstructed from `Total Spent ÷ Quantity` for missing rows, the result should be rounded to the nearest 0.50. This ensures the reconstructed value is consistent with the format rule observed in 100% of the known prices.

### 5.3 `Total Spent`

All non-null `Total Spent` values are positive. No negative transaction values (which would indicate refunds or data errors) were found.

---

## 6. Referential Consistency

### 6.1 `(Category, Price Per Unit)` → `Item` Mapping

This check asks: within the dataset, does the combination of `Category` and `Price Per Unit` always correspond to the same `Item`?

| Check | Result |
|---|---|
| Maximum distinct `Item` values per `(Category, Price Per Unit)` group | **1** |
| Groups with more than one distinct `Item` | **0** |
| Total distinct `(Category, Price Per Unit)` combinations | Multiple — all 1-to-1 |

**Finding:** Every `(Category, Price Per Unit)` pair maps to exactly one `Item` in this dataset. This is a perfect referential rule with zero exceptions.

**Significance:** This finding transforms the 1,213 missing `Item` values from an unrecoverable gap into a deterministically solvable problem. Given a row's category and unit price, the item name can be inferred with certainty — not guessed, not approximated, but looked up from a verified mapping that holds across 100% of the complete rows. This is one of the most valuable consistency findings in the dataset.

### 6.2 `Category` ↔ `Item` Relationship

Each item belongs to exactly one category, and each category contains multiple distinct items. No item appears across two categories. This confirms categorical hierarchy integrity.

---

## 7. Categorical Consistency

### 7.1 `Category`

| Category | Count |
|---|---:|
| Electric Household Essentials | 1,591 |
| Furniture | 1,591 |
| Food | 1,588 |
| Milk Products | 1,584 |
| Butchers | 1,568 |
| Beverages | 1,567 |
| Computers & Electric Accessories | 1,558 |
| Patisserie | 1,528 |

**Finding:** Exactly 8 distinct category values. No misspellings, no case variants (e.g. no `"food"` vs `"Food"`), no trailing whitespace. The distribution is balanced — the spread from the largest (1,591) to smallest (1,528) category is only 63 records (4%). No category dominates the dataset, which means analysis across all eight categories is well-supported.

### 7.2 `Payment Method`

| Payment Method | Count |
|---|---:|
| Cash | 4,310 |
| Digital Wallet | 4,144 |
| Credit Card | 4,121 |

**Finding:** Exactly 3 distinct values, no variants or misspellings. Distribution is balanced (34.3% / 33.0% / 32.8%), confirming that all three payment methods are actively used and that no method is so rare as to be analytically unreliable.

### 7.3 `Location`

| Location | Count |
|---|---:|
| Online | 6,354 |
| In-store | 6,221 |

**Finding:** Exactly 2 values. The online/in-store split is near-even (50.5% / 49.5%), which provides good analytical coverage for channel comparison. No ambiguous or hybrid values (e.g. `"in store"`, `"online order"`) were found.

---

## 8. Cross-Field Consistency

### 8.1 `Discount Applied` Across Categories and Channels

Among the 8,376 transactions where `Discount Applied` is known, the `True`/`False` split (50.4% / 49.6%) is consistent across all eight categories and both locations. No single category or channel has a suspiciously skewed discount pattern that would suggest a recording error.

### 8.2 `Transaction Date` Continuity

Transactions are distributed across the full 2022–2025 period with no unexplained gaps. Monthly distribution shows no months with zero transactions, confirming the date range is genuinely continuous and not the result of stitching together incomplete extracts.

---

## 9. Consistency Issues Summary

| Consistency Dimension | Check Performed | Result | Action Required |
|---|---|---|---|
| Arithmetic | `Total Spent = Price × Qty` | ✅ 0 violations | None — rule verified, safe to use for reconstruction |
| Format — dates | All dates parseable | ✅ 0 unparseable | Standardise to ISO string; add year/month fields |
| Format — IDs | Transaction ID and Customer ID patterns | ✅ Consistent | None |
| Format — discount | `Discount Applied` value formats | ✅ Only True/False/NaN | Preserve NaN as `<NA>`; do not coerce to `False` |
| Range — quantity | Whole numbers, 1–10 | ✅ 0 violations | None |
| Range — price | 0.50 increments only | ✅ 0 violations | Apply rounding rule when reconstructing missing prices |
| Referential | `(Category, Price) → Item` is 1-to-1 | ✅ Verified | Use as lookup to infer 1,213 missing item values |
| Categorical | Categories, payment methods, locations | ✅ No variants or misspellings | None |
| Semantic — discount NaN | NaN meaning is ambiguous | ⚠️ Unresolvable | Preserve as `<NA>`; label as "unknown" in all aggregations |

---

## 10. Justification for Data Re-engineering

The consistency analysis produces three direct re-engineering justifications:

**1. Arithmetic rule enables safe reconstruction**
Because `Total Spent = Price Per Unit × Quantity` holds without exception across all 11,366 complete rows, the formula can be used to reconstruct the 604 missing `Total Spent` values. This is not an approximation — it is a deterministic rule with 100% historical accuracy.

**2. Referential rule enables item inference**
Because every `(Category, Price Per Unit)` pair maps to exactly one `Item`, the 604 missing `Item` values in Pattern B rows (where price is known) can be inferred without ambiguity. This turns a missing-data problem into a lookup operation.

**3. Price increment rule must be preserved**
When `Price Per Unit` is reconstructed from `Total Spent ÷ Quantity`, the result must be rounded to the nearest 0.50. Failing to apply this rule would produce values inconsistent with every other price in the dataset — introducing a new inconsistency during the re-engineering step itself.

---

## 11. Conclusion

The consistency analysis of `retail_store_sales.csv` reveals a dataset with **strong internal logic and zero arithmetic errors**, but with one important semantic ambiguity in `Discount Applied` and five columns affected by missingness that prevents consistency checks from being applied to those rows.

The most significant finding is the verified `(Category, Price Per Unit) → Item` rule — a perfect referential mapping that enables deterministic recovery of 604 missing item values. This finding is only discoverable through consistency profiling; completeness analysis alone would have treated those 604 items as simply missing, with no path to recovery.

Consistency profiling does not just validate data — it reveals the rules embedded within it. Those rules are the basis for evidence-based re-engineering. Every action taken to clean or reconstruct this dataset is justified by a specific, measured, and documented consistency observation.
