# 2.4 Validation, Ethics & Quality Review — Individual Report 3
**Dataset:** `retail_store_sales.csv`
**Focus:** Societal & Business Impact · Data Governance · Long-term Consequences of Data Quality
**Role:** Validating normalisation and recovery outcomes with ethical reflection on the broader consequences of data quality decisions on individuals, organisations, and society

---

## 1. The Broader Responsibility of Data Quality

Data quality is not only a technical concern. Every decision made about what to fill, what to leave empty, what to restructure, and what to discard has consequences that reach beyond the dataset itself — into business decisions, into the lives of employees whose performance is measured by this data, and into the trust that customers place in organisations that hold records of their purchasing behaviour.

This report approaches validation and ethics from that broader perspective. It measures the improvements made to `retail_store_sales.csv` against the standard of what responsible data stewardship requires — not just technically, but humanly.

---

## 2. Before vs After — Full Validation Summary

### 2.1 Data Quality Scorecard

| Quality dimension | Before score | After score | Method of improvement |
|---|---|---|---|
| Completeness — `item` | 90.4% | **100.0%** | Deterministic lookup |
| Completeness — `price_per_unit` | 95.2% | **100.0%** | Arithmetic reconstruction |
| Completeness — `quantity` | 95.2% | **100.0%** | Mode hierarchy imputation |
| Completeness — `total_spent` | 95.2% | **100.0%** | Arithmetic reconstruction |
| Completeness — `discount_applied` | 66.6% | **66.6%** | Intentionally unchanged |
| Consistency — arithmetic rules | 100.0% | **100.0%** | Maintained through reconstruction |
| Accuracy — range violations | 0 | **0** | No violations introduced |
| Duplicate records | 0 | **0** | Confirmed; no rows removed |
| Overall completeness rate | 94.78% | **96.97%** | 3,030 cells recovered |

### 2.2 Revenue Validation

The most directly measurable business impact of the re-engineering is the completeness of revenue data.

| Revenue metric | Before | After |
|---|---|---|
| Transactions with complete revenue data | 11,971 | **12,575** |
| Transactions with missing `total_spent` | 604 | **0** |
| Revenue completeness | 95.2% | **100.0%** |
| Estimated revenue in previously missing rows | ~£55,000+ | Now recorded |

A revenue figure calculated from the re-engineered dataset reflects 100% of transactions. The same figure calculated from the original dataset silently excluded 4.8% of all purchase activity. No audit, no analyst query, and no dashboard built on the original data would have flagged that exclusion automatically.

### 2.3 Product Coverage Validation

| Product metric | Before | After |
|---|---|---|
| Transactions attributable to a specific item | 11,362 | **12,575** |
| Transactions with missing item | 1,213 | **0** |
| Item attribution rate | 90.4% | **100.0%** |

Every transaction in the re-engineered dataset can now be attributed to a specific product. This enables complete product-level analytics — bestseller rankings, slow-mover identification, and per-item margin analysis — that were structurally impossible on the original data.

### 2.4 Normalisation Validation

| Structural metric | Before | After |
|---|---|---|
| Tables | 1 flat file | 6 (1 fact + 5 dimensions) |
| Redundant `category` string values | ~12,575 (once per row) | 8 (once per distinct category) |
| Redundant `payment_method` values | ~12,575 | 3 |
| Referential integrity enforceable | No | Yes |
| Privacy-separable customer dimension | No | Yes |

---

## 3. Ethical Reflection — The Consequences of Data Quality for Individuals

### 3.1 Employees Evaluated by Incomplete Data

**The problem:** In most retail organisations, transaction data feeds performance evaluations. Sales volume, revenue generated, and transaction counts inform bonus calculations, staffing decisions, promotions, and dismissals. When transaction data is incomplete, these evaluations are built on a partial record.

**Specific impact in this dataset:** 604 transactions had no `total_spent` recorded before re-engineering. If these transactions were distributed across staff members or store locations, each affected employee's revenue performance was understated. The understatement was not caused by their behaviour — it was caused by a data capture failure. Yet the consequence — appearing less productive than they were — was borne by them, not by the system that failed to record the data.

**After re-engineering:** All 604 revenue values have been reconstructed. Every transaction now contributes to the revenue record. An employee whose transactions were previously unrecorded now has their full contribution reflected in the data.

**Remaining ethical concern:** 604 of the 12,575 quantity values are imputed — they are estimates, not observations. If an imputed quantity of 10 overstates what was actually a quantity-2 transaction, the employee associated with that transaction appears to have processed a higher-value sale than they did. The direction of bias (overstatement via the global mode of 10) means the risk is more likely to over-credit than under-credit — but either direction represents a departure from the true record.

**Professional standard:** Performance decisions that depend on this dataset should be informed by the `metadata.json` record of which rows were imputed. Human consequences — bonuses, appraisals, staffing levels — should not rest on unacknowledged estimates.

### 3.2 Customers Affected by Data Records

**The problem:** Customer IDs (`CUST_XX`) link transactions to individuals. The re-engineered dataset associates reconstructed financial values — inferred items, imputed quantities, calculated totals — with specific customer accounts. If a customer's purchase history is used to determine their loyalty tier, credit limit, or personalised pricing, a wrongly reconstructed transaction could have a direct effect on that customer.

**Example:** A customer who actually bought 1 unit of a £29 item (total: £29) in a transaction where quantity was missing may have that transaction imputed as 10 units × £29 = £290. Their annual spend total is now overstated by £261. If that spending figure is used to upgrade them to a premium loyalty tier with benefits, the consequence is positive for them but misleading for the business. If the dataset is used to detect unusual spending patterns for fraud analysis, the inflated total may trigger a false alert.

**Mitigation:** The reconstruction is documented. Any system consuming this data should flag the 604 imputed-quantity transactions as carrying uncertainty and exclude them from sensitive customer-specific decisions until the original values can be confirmed.

**Ethical principle:** Customer data must be handled with particular care. The fact that `Customer ID` values are pseudonymous reduces privacy risk, but it does not eliminate the responsibility to ensure that the data linked to those IDs is as accurate as possible — especially when that data influences decisions about individuals.

---

## 4. Ethical Reflection — Organisational Consequences

### 4.1 Financial Reporting Integrity

**Before re-engineering:** A finance team calculating total revenue for the period would arrive at a figure that silently excluded 604 transactions. The understatement was not disclosed — because the missing values were invisible in a standard sum operation. A `SUM(total_spent)` query on the original data simply ignores nulls.

**After re-engineering:** The revenue figure is complete. The same query on the re-engineered data returns a total that reflects all 12,575 transactions. For a business that uses this data for quarterly or annual reporting, the difference is material.

**Ethical dimension:** Financial reporting built on incomplete data — even unintentionally incomplete data — carries integrity risk. If the understated revenue figure was reported externally (to investors, tax authorities, or regulatory bodies), the organisation was not reporting an accurate picture of its performance. This is not fraud — it is the consequence of an undetected data quality failure. But the consequence of that failure is indistinguishable from the consequence of deliberate misreporting. Data quality is, in this sense, an integrity issue.

### 4.2 Promotional Strategy and Commercial Decisions

**Before re-engineering:** With 4,199 unknown discount statuses (33.4% of all transactions), any analysis of promotional effectiveness was based on a minority of the data. A marketing team deciding whether to run a future discount campaign based on these figures was making a strategic decision from a structurally incomplete foundation.

**After re-engineering:** The situation is unchanged for `discount_applied` — the 4,199 unknowns remain unknown. But they are now correctly reported as unknown rather than absent from the analysis. A marketing analyst querying discount rate from the re-engineered data will see the `<NA>` values and be forced to acknowledge that one third of transactions have unknown discount status. They cannot unknowingly exclude those transactions and report an inflated discount rate.

**The difference transparency makes:** A business that does not know whether 33% of its transactions were discounted is in a worse analytical position than one that knows this gap exists. Re-engineering did not fill that gap — but it made the gap visible and correctly typed. A business that sees `discount_applied` is 33.4% null will investigate the recording failure. A business that sees `discount_applied` is 100% complete (because unknowns were imputed as `False`) will not — because the problem is invisible.

Visibility is the first condition of improvement.

---

## 5. Ethical Reflection — Societal Responsibility

### 5.1 The Social Contract of Data Collection

When a customer completes a retail transaction, they implicitly consent to having that transaction recorded. That consent carries a reasonable expectation: that the record will be accurate, that it will be used for legitimate business purposes, and that it will not be enriched with fabricated values without their knowledge.

**Re-engineering decision:** No customer purchase records were deleted, no customer identities were derived, and no fabricated values were introduced without documentation. The reconstruction applied to missing fields used deterministic rules derived from the data itself — not external assumptions or statistical proxies that go beyond what the transaction record implies.

**What this means in practice:** A customer whose `item` value was missing had it restored to the value that their own `category` and `price_per_unit` — fields that were correctly recorded — implied it should be. The re-engineering respected the integrity of the original transaction by restoring what was always implicitly present, rather than substituting an external estimate.

### 5.2 Data Governance and the Root Cause

**The most important ethical finding in this report is not about what the re-engineering fixed — it is about what the re-engineering revealed.**

The 609 transactions with all financial fields missing together are not a data quality issue that can be fully resolved by re-engineering. They are evidence of a systemic failure in the data collection process — most likely a POS system that fails to complete transaction recording under certain conditions.

Re-engineering addressed the symptoms: missing values were reconstructed where possible, and the residual uncertainty was documented. But the root cause — the recording failure — has not been addressed. Without fixing the root cause, the next export of this dataset will contain the same pattern of structured missingness. The next analyst to receive it will face the same data quality problems.

**Professional responsibility:** A data professional who profiles, re-engineers, and documents a dataset has not fully discharged their responsibility if they do not communicate the root cause to the people who can fix it. The `metadata.json` note that documents the structured missingness pattern is the beginning of that communication — but it must reach the team responsible for the POS system and the data extraction process.

Data quality is a governance issue, not just a data issue. Re-engineering treats the data. Governance prevents the problem from recurring.

---

## 6. Reflection on How This Work Changed My View of Data Quality

Before undertaking this profiling and re-engineering exercise, it would have been reasonable to look at `retail_store_sales.csv` and conclude: no duplicates, no format errors, dates are fine, categories are clean — this is a good dataset.

That conclusion would have been wrong.

The 7,229 missing cells, the structured co-occurrence of missing financial fields, the 33% unknown discount rate, and the £55,000+ in unrecorded revenue were all present in that "clean" dataset — invisible without deliberate, methodical profiling. Data quality is not visible on the surface. It requires the commitment to look underneath.

More importantly, this exercise demonstrated that data quality is not morally neutral. The choices made during re-engineering — to preserve unknown discounts as unknown, to document imputed quantities, to retain rather than drop incomplete records — were ethical choices with real consequences for the people whose transactions, performance, and purchasing behaviour are recorded in this data.

A data professional who treats these choices as purely technical is missing their responsibility to the people behind the data.

---

## 7. Conclusion

The validation confirms substantial, measurable improvement: revenue completeness from 95.2% to 100%, item attribution from 90.4% to 100%, overall completeness from 94.78% to 96.97%, and a normalised structure that enforces referential integrity and supports privacy-respecting access control.

The ethical review reveals that these improvements carry responsibilities. Imputed values must be identified and their uncertainty acknowledged in downstream analyses. Customer data must be handled with respect for the implicit consent of the individuals it represents. Performance evaluations built on this data must account for the 604 reconstructed transactions. And the root cause of the structured missingness must be reported to the teams responsible for data collection — because re-engineering a symptom is not the same as curing the disease.

Data quality, at its deepest level, is an expression of how seriously an organisation takes its responsibility to the people who depend on its decisions. This dataset is better than it was. The people behind it deserve nothing less.
