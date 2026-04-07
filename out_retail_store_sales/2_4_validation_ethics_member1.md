# 2.4 Validation, Ethics & Quality Review — Individual Report 1
**Dataset:** `retail_store_sales.csv`
**Focus:** Quantitative Validation · Privacy · Assumption Transparency
**Role:** Validating completeness and reconstruction improvements with ethical reflection on data recovery decisions

---

## 1. Purpose of This Review

Validation is the process of measuring whether re-engineering actually improved the data — not assuming it did, but proving it with numbers. Ethics review is the process of asking whether the improvements were made responsibly — not just whether they worked, but whether they were the right thing to do.

These two responsibilities cannot be separated. A re-engineering action can be technically effective and ethically irresponsible at the same time. A data professional who validates improvements without reflecting on how they were made is not doing their full job.

This report validates the specific improvements made to `retail_store_sales.csv` through before-and-after measurement, then reflects deeply on the ethical dimensions of three re-engineering decisions: reconstruction of missing values, treatment of `Discount Applied`, and the introduction of a normalised customer dimension.

---

## 2. Before vs After — Quantitative Validation

### 2.1 Completeness Improvement

| Column | Missing (Before) | Missing (After) | Resolved | Resolution method |
|---|---:|---:|---:|---|
| `item` | 1,213 | **0** | 1,213 (100%) | Category–price lookup |
| `price_per_unit` | 609 | **0** | 609 (100%) | `total_spent ÷ quantity`, rounded to 0.50 |
| `quantity` | 604 | **0** | 604 (100%) | Mode hierarchy (item → category → global) |
| `total_spent` | 604 | **0** | 604 (100%) | `price_per_unit × quantity` |
| `discount_applied` | 4,199 | **4,199** | 0 (0%) | Intentionally preserved as `<NA>` |

**Total missing cells reduced: 7,229 → 4,199 (a 41.9% reduction)**

The 4,199 remaining missing values in `discount_applied` are not a failure of re-engineering — they are a deliberate and correct decision. This distinction is central to ethical validation: success is not always measured by how many gaps were closed.

### 2.2 Consistency Improvement

| Consistency rule | Violations (Before) | Violations (After) |
|---|---:|---:|
| `total_spent = price_per_unit × quantity` | 0 | **0** |
| Quantity is a whole number | 0 | **0** |
| Quantity within 1–10 | 0 | **0** |
| Price on 0.50 increments | 0 | **0** |

The re-engineering maintained all existing consistency rules. No new violations were introduced during value reconstruction — confirming that the recovery methods were consistent with the dataset's own rules.

### 2.3 Structural Improvement

| Dimension | Before | After |
|---|---|---|
| Table structure | 1 flat file, 11 columns | 1 fact table + 5 dimension tables |
| Row count | 12,575 | 12,575 (no rows added or removed) |
| Column count (wide) | 11 | 15 (4 derived fields added) |
| Surrogate keys | None | `row_id` in fact; dimension keys in each table |
| Duplicate rows | 0 | 0 |
| Duplicate transaction IDs | 0 | 0 |

### 2.4 Revenue Completeness

| Metric | Before | After |
|---|---|---|
| Transactions with `total_spent` recorded | 11,971 | **12,575** |
| Transactions with `total_spent` missing | 604 | **0** |
| Revenue completeness rate | 95.2% | **100.0%** |

Every transaction now has a recorded revenue value. The dataset can produce a complete revenue total for the first time.

---

## 3. Ethical Reflection

### 3.1 Privacy — Customer ID Pseudonymisation

**Observation:** `Customer ID` values follow the format `CUST_XX` (e.g. `CUST_09`). No names, email addresses, phone numbers, or location data beyond a binary `Online`/`In-store` flag are present.

**Positive finding:** The pseudonymous format supports privacy. An analyst working with this dataset cannot identify a specific individual from a `Customer ID` alone. This reduces the risk of unauthorised personal data disclosure.

**Ethical concern:** Pseudonymisation is not anonymisation. If this dataset were combined with a second dataset that maps `CUST_XX` to real customer names — a loyalty programme database, for example — full purchase histories could be reconstructed for identifiable individuals. The privacy protection offered by `CUST_XX` depends entirely on that mapping remaining inaccessible.

**Responsible action taken:** During re-engineering, no attempt was made to enrich or cross-reference customer data. The `dim_customer` table was created with `customer_id` only — no additional attributes were inferred or derived. The normalised structure also supports future privacy controls: access to customer identity can be restricted to `dim_customer` alone, while analysts working on sales performance queries access only the fact table with integer `customer_key` values.

**Professional standard upheld:** The re-engineered data structure makes privacy-respecting access control architecturally possible — a measurable improvement over the original flat file.

---

### 3.2 Transparency of Reconstruction — Assumption Risk

**Observation:** Four columns were partially or fully reconstructed using rules verified from the existing data. These reconstructed values are present in the cleaned dataset alongside original recorded values, with no visual distinction between them.

**Ethical concern:** An analyst using the cleaned dataset cannot tell, from the data alone, which `total_spent` values were originally recorded and which were calculated as `price_per_unit × quantity`. If the reconstruction rule is wrong for any edge case, the error is invisible. This is a form of hidden assumption.

**Evidence that the risk is managed:**
- The reconstruction rule (`total_spent = price_per_unit × quantity`) was verified against 11,366 complete rows with zero violations — a 100% accuracy rate
- The item inference rule (`(category, price_per_unit) → item`) was verified with zero exceptions across all complete rows
- All reconstruction decisions, counts, and strategies are documented in `metadata.json`

**What still carries risk:** The 604 quantity values imputed by mode are statistical estimates, not recovered facts. A transaction where a customer actually bought 2 units but the mode for that item is 8 will be recorded with a quantity of 8 — and a total_spent of 8 × price. This is not wrong in the sense of violating a rule, but it is not the ground truth.

**Responsible action taken:** The imputation strategy is fully documented in `metadata.json`. Future analyses that depend on quantity accuracy — particularly customer-level basket size analysis or per-item demand forecasting — should exclude imputed rows or treat them with explicit uncertainty.

**Ethical standard:** Hiding the reconstruction would be irresponsible. Documenting it makes the risk visible and manageable.

---

### 3.3 Data Loss — What Was Not Recovered

**Observation:** The 609 transactions identified in the completeness analysis as having `item`, `price_per_unit`, `quantity`, and `total_spent` all missing simultaneously were not dropped. Their financial fields were recovered through reconstruction.

**What this means:** No transaction records were deleted during re-engineering. The final dataset contains all 12,575 rows present in the original.

**Why this matters ethically:** Removing the 609 incomplete records would have been easier. It would have produced a cleaner-looking dataset with no missing financial fields. But it would also have:
- Deleted the purchase history of real customers
- Removed real transactions from category-level counts
- Created a systematic bias against whichever categories or time periods had more POS failures
- Produced revenue figures that excluded real customer activity without disclosing the exclusion

Choosing to retain and reconstruct rather than drop was an act of data stewardship. The completeness of the record matters — not just the cleanliness of the numbers.

---

## 4. Impact of Data Quality on Business Decisions

**Before re-engineering, the following decisions could not be made correctly:**

| Decision | Impact of missing data |
|---|---|
| Total revenue for the period | Understated by ~£55,000+ (604 missing totals) |
| Product bestseller ranking | Incomplete — 1,213 transactions had no item |
| Discount rate reporting | Based on only 66.6% of transactions |
| Inventory restocking for any item | Based on incomplete sales velocity data |

**After re-engineering, all of the above are addressable** — with the documented caveat that 604 quantity values are imputed estimates and 4,199 discount values remain unknown.

The difference between "incorrect" and "correctly uncertain" is what responsible re-engineering produces. The cleaned dataset does not pretend to know everything. It knows more than it did, and it is honest about what it still does not know.

---

## 5. Conclusion

The validation confirms that re-engineering materially improved the dataset: missing values reduced by 41.9%, all four recoverable columns are now 100% complete, no rows were lost, and no existing accuracy was degraded. The structural normalisation into a star schema provides a foundation for reliable, scalable analytics.

The ethical review confirms that the improvements were made responsibly. Privacy is supported by pseudonymisation and by the separability of the `dim_customer` table. Reconstruction assumptions are documented and traceable. No data was silently fabricated — the 4,199 unknown discount values remain unknown, and the 604 imputed quantities are identified as estimates in the metadata.

A dataset that is more complete AND more honest about its limitations is a better dataset than one that appears perfect but conceals its assumptions.
