# 2.4 Validation, Ethics & Quality Review — Individual Report 2
**Dataset:** `retail_store_sales.csv`
**Focus:** Bias in Imputation · Fairness in Performance Evaluation · Discount Ethics
**Role:** Validating consistency and structural improvements with ethical reflection on bias, fairness, and the consequences of analytical decisions

---

## 1. Why Validation Must Include Ethics

Numbers can pass every technical test and still tell an unfair story. A dataset where missing quantities are imputed using a statistical mode is technically complete — but if those imputed values systematically over- or under-represent certain products or customers, the analyses built on them will be structurally biased. A dataset where 33% of discount statuses are unknown but reported as if they were known will misrepresent promotional performance — not through error, but through silence.

This report validates the technical improvements made to `retail_store_sales.csv` and then examines three specific ethical dimensions: bias introduced by imputation, fairness in performance evaluation, and the ethics of how missing discount data was handled.

---

## 2. Before vs After — Consistency and Structure Validation

### 2.1 Internal Consistency — Before and After

| Rule | Before | After | Change |
|---|---:|---:|---|
| `total_spent = price_per_unit × quantity` violations | 0 | **0** | Maintained — rule holds across all reconstructed rows |
| Non-integer quantity values | 0 | **0** | Maintained |
| Price values off 0.50 increments | 0 | **0** | Maintained — reconstruction used rounding rule |
| Unparseable date values | 0 | **0** | Maintained |
| Invalid categorical values | 0 | **0** | Maintained |

**Key finding:** The re-engineering introduced zero new consistency violations. Every reconstructed value conforms to the rules verified in the profiling stage. This confirms that the reconstruction methods were not just statistically reasonable — they were internally consistent with the dataset's own structure.

### 2.2 Completeness — Before and After

| Column | Before | After | Improvement |
|---|---:|---:|---|
| `item` missing | 1,213 | 0 | −1,213 (−100%) |
| `price_per_unit` missing | 609 | 0 | −609 (−100%) |
| `quantity` missing | 604 | 0 | −604 (−100%) |
| `total_spent` missing | 604 | 0 | −604 (−100%) |
| `discount_applied` missing | 4,199 | 4,199 | 0 (intentional) |
| **Total missing** | **7,229** | **4,199** | **−3,030 (−41.9%)** |

### 2.3 Structural Validation — Normalisation

| Metric | Before | After |
|---|---|---|
| Tables | 1 (flat file) | 6 (1 fact + 5 dimensions) |
| Redundant category strings | 1,591 repetitions per category | 1 row per category in `dim_category` |
| Redundant payment method strings | Up to 4,310 repetitions | 1 row per method in `dim_payment_method` |
| Referential integrity enforceable | No | Yes (via foreign key constraints) |
| Customer data isolatable for privacy | No | Yes (`dim_customer` is separable) |

The star schema eliminates redundancy structurally — not just by removing rows, but by making repetition architecturally impossible. Once `category` lives in `dim_category` and is referenced by integer key in `fact_sales`, there is no mechanism by which two different spellings of the same category can co-exist.

---

## 3. Ethical Reflection — Bias

### 3.1 Bias Risk in Quantity Imputation

**What was done:** 604 missing `quantity` values were imputed using a mode hierarchy: the most common quantity for that item, then for its category, then the global mode (10).

**Where bias can enter:**
The mode is the most frequent value — not the most accurate value for any given transaction. If certain items are typically bought in low quantities by most customers but in high quantities by a few, the mode will be high, and imputed records will over-represent bulk purchasing. Conversely, if high-value items are typically bought in quantities of 1 or 2, imputing the category mode (which includes cheaper, higher-volume items) could over-inflate the estimated quantity.

**Specific risk:** The global mode is 10 — the maximum possible quantity. This means that when neither item-level nor category-level mode is available, missing quantities are imputed as the highest possible value. This is a conservative estimate for demand but an aggressive estimate for revenue: a missing transaction with a price of £29.00 imputed with a quantity of 10 contributes £290 to the revenue total, when the actual transaction may have been for 1 or 2 units.

**Mitigation applied:** The three-level hierarchy (item → category → global) ensures that the most specific available information is used first. The global mode of 10 is only applied when no item or category mode is computable — which represents a small subset of the 604 imputed rows.

**Residual bias:** Despite the hierarchy, imputed rows carry inherent uncertainty. Any analysis that aggregates over imputed quantity values without acknowledging their imputed status may reach conclusions that do not reflect reality.

**Recommended analytical practice:** Flag all 604 imputed quantity rows in downstream analysis. For quantity-sensitive decisions — inventory replenishment, per-item demand forecasting — exclude imputed rows or report results with and without them.

### 3.2 Bias Risk in Category-Level Analyses

**Observation:** All eight product categories have approximately equal transaction counts (1,528–1,591 rows). The missing data (1,213 item values, 609 price values) is not concentrated in any single category — it appears distributed across the dataset.

**Why this matters for bias:** If missing data were concentrated in one category (say, all 609 price-missing rows were in Furniture), then post-imputation analyses of Furniture revenue would be disproportionately based on reconstructed values. Furniture comparisons to other categories would be unfair — built partly on estimates while others were built on observed data.

**Finding:** No evidence of systematic category-level concentration of missing values was found. The balanced category distribution seen in the complete fields extends to the missing-value distribution, reducing the risk of category-specific bias in the re-engineered data.

---

## 4. Ethical Reflection — Fairness in Performance Evaluation

**Context:** Retail transaction data is routinely used to evaluate staff performance, store performance, and channel performance. Sales volume, revenue per transaction, and transaction counts all feed performance dashboards. If the data underlying these metrics is incomplete or imputed, the evaluations derived from it may be unfair.

### 4.1 Staff and Store Performance

**Before re-engineering:** 604 transactions had no `total_spent` value. If staff or store performance was measured by total revenue generated, these 604 transactions contributed nothing to any individual's performance score — not because no sale was made, but because the total was not recorded.

**After re-engineering:** All 604 `total_spent` values have been reconstructed. These transactions now appear in revenue totals. Staff and store metrics calculated on the re-engineered data are more complete and more fair.

**Remaining risk:** 604 of the 12,575 total_spent values are reconstructed rather than observed. If reconstruction systematically over- or under-estimates the true transaction value for certain staff members or stores, it could introduce a new form of unfairness — replacing the unfairness of "your sale wasn't counted" with the unfairness of "your sale was counted incorrectly."

**Safeguard:** The reconstruction method (`price_per_unit × quantity`) is deterministic and based on verified rules. The only source of uncertainty is the imputed quantity values in 604 rows. Analysts evaluating performance should be aware that these rows carry imputed quantities and treat their contribution to revenue metrics accordingly.

### 4.2 The Discount Fairness Problem

**Before re-engineering:** 4,199 `discount_applied` values were missing. If store managers were evaluated on discount rate (the proportion of transactions with discounts applied), a manager whose store had more missing discount data would appear to have a lower discount rate — not because they applied fewer discounts, but because the recording gaps in their store were larger.

**Ethical position:** Evaluating a manager on a metric calculated from incomplete data is unfair. The missing discount values are not evidence of fewer discounts — they are evidence of a recording failure. Treating them as `False` to complete the metric would compound the unfairness by assigning a specific value to an unknown outcome.

**Action taken:** `discount_applied` missing values were preserved as `<NA>`. Any discount rate metric calculated from the re-engineered data should explicitly exclude `<NA>` values from both numerator and denominator — not treat them as `False`.

**Impact:** A manager whose store had 300 unknown discount values has a discount rate calculated from their known transactions only. This is not perfect — it still does not tell us what those 300 transactions were — but it is honest. It does not add false certainty that the manager did not give discounts when we simply do not know.

---

## 5. Ethical Reflection — The Ethics of What Was Not Done

**Observation:** Several re-engineering actions were considered and rejected. These rejections are ethically significant.

| Action not taken | Why it was rejected | Ethical principle |
|---|---|---|
| Impute `discount_applied` as `False` | Would misrepresent discount rate by ~17 percentage points | Honesty — do not fabricate values |
| Drop 609 fully-missing transaction rows | Would delete real customer purchase events | Fairness — every transaction deserves to be counted |
| Infer customer demographics from purchase patterns | No demographic data was requested or available | Privacy — do not derive personal attributes beyond what is needed |
| Correct item–category assignments | All existing assignments were verified accurate | Integrity — do not change correct data |

The discipline to not act is as important as the decision to act. Data re-engineering that over-reaches — filling every gap, correcting every perceived issue, enriching every field — does not improve data quality. It introduces assumptions disguised as facts.

---

## 6. Impact of Improved Data Quality

### On Business Decision-Making

| Decision type | Before | After |
|---|---|---|
| Revenue reporting | Understated by ~£55,000+ | Complete for all 12,575 transactions |
| Product performance ranking | Missing 1,213 item attributions | All transactions attributable to a product |
| Category demand forecasting | Based on incomplete quantity data | All quantities present (604 imputed — documented) |
| Promotional analysis | Based on 66.6% of transactions | Based on 66.6% — correctly reported, not inflated |

The last row is intentional. Promotional analysis is not better simply because the re-engineering is complete — it is limited by the genuine incompleteness of `discount_applied`. Reporting this limitation honestly is better than pretending the analysis is comprehensive.

### On Organisational Trust

Data that is well-profiled, carefully re-engineered, and honestly documented builds organisational trust in a way that silently-imputed, undocumented data cannot. When a finance team queries revenue from the re-engineered dataset, they can trace every value to either an original observation or a documented reconstruction. When they find a total_spent value that surprises them, they can check `metadata.json` and understand exactly how it was calculated.

That traceability is not a technical feature — it is a professional commitment to the people who depend on this data.

---

## 7. Conclusion

The re-engineering of `retail_store_sales.csv` produced measurable improvements: 3,030 missing values resolved, consistency maintained at 100%, and a normalised structure that supports reliable analytics. These improvements are validated by direct before-and-after comparison.

The ethical review reveals that the improvements were made with awareness of their risks. Imputation bias in quantity values is real and documented. Fairness in performance evaluation is improved but remains imperfect where quantities were estimated. The discount data remains incomplete — and that incompleteness is reported honestly rather than concealed.

The most important ethical finding is this: the re-engineering team chose not to fill every gap. The 4,199 unknown discount values were left unknown. That restraint — choosing honesty over apparent completeness — is the standard that responsible data professionals must hold themselves to.
