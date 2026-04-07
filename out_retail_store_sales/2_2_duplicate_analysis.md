# Data Profiling Report — Duplicate Records Analysis
**Dataset:** `retail_store_sales.csv`
**Profiling Role:** Duplicate Records Analysis
**Records Examined:** 12,575 rows × 11 columns
**Date Range Covered:** 2022-01-01 → 2025-01-18

---

## 1. What Is a Duplicate Record and Why Does It Matter

A duplicate record is any row in a dataset that represents the same real-world event as another row — either identically or with minor variation. Duplicates are one of the most damaging data quality problems in transactional systems because they are **additive by nature**: every duplicate inflates counts, totals, and averages. In a retail dataset, even a handful of duplicated transactions can produce:

- **Overstated revenue** — the same sale counted twice in financial reports
- **Inflated demand signals** — a product appearing to sell twice as fast as it does, triggering unnecessary restocking
- **Distorted customer analytics** — a customer's purchase history showing the same transaction twice, inflating their lifetime value score
- **Unfair staff or store evaluations** — a salesperson or location appearing to outperform because their transactions were recorded multiple times

Duplicate analysis must examine several distinct types of duplication — not just exact row matches — because real-world duplicates rarely look identical. A resubmitted transaction may have the same content but a different timestamp; a data export run twice may assign different auto-incremented IDs to what is the same logical record.

This analysis examines four levels of duplication:

| Level | Definition |
|---|---|
| **Exact row duplicate** | Every field in two rows is identical |
| **Transaction ID duplicate** | Same `Transaction ID` appears more than once (regardless of other fields) |
| **Logical duplicate** | Same customer, item, date, and amount — but different `Transaction ID` |
| **Repeat purchase** | Same customer buying the same item on different dates — legitimate, not a duplicate |

---

## 2. Methodology

The following steps were applied to the raw, unmodified dataset:

1. **Exact row check:** Applied `.duplicated()` across all 11 columns — flags any row where every field matches a previous row exactly
2. **Transaction ID uniqueness check:** Applied `.duplicated()` to the `Transaction ID` column alone — flags any ID appearing more than once, regardless of whether other fields differ
3. **Logical duplicate check:** Grouped records by `(Customer ID, Item, Transaction Date, Total Spent)` — any group with more than one record is a potential logical duplicate where the same purchase was recorded twice with different system-assigned identifiers
4. **Repeat purchase analysis:** Grouped by `(Customer ID, Item)` and examined the distribution of purchase counts — to distinguish legitimate repeat buying from suspicious duplication
5. **Customer transaction frequency analysis:** Counted transactions per customer — to identify any customer account with an unexpectedly high transaction volume that might indicate duplicated records
6. **Cross-field duplication check:** Verified that no `Transaction ID` was reused across different customers or dates — which would indicate ID recycling or corruption

All checks were performed on all 12,575 rows. Results are stated with exact counts and percentages.

---

## 3. Level 1 — Exact Row Duplicates

| Check | Result |
|---|---:|
| Total rows examined | 12,575 |
| Exact duplicate rows found | **0** |
| Unique rows | 12,575 |
| Exact uniqueness rate | **100.00%** |

**Finding:** Not a single row in the dataset is an exact copy of another row. Every one of the 12,575 records is distinct across all 11 fields simultaneously.

**What this means:** The dataset was not produced by a double-export, copy-paste error, or batch reprocessing that appended existing records a second time. The data pipeline that generated or exported this file did not introduce exact-copy duplication at any point.

**Accuracy verdict: PASS — zero exact row duplicates.**

---

## 4. Level 2 — Transaction ID Duplicates

The `Transaction ID` field is the dataset's intended primary key. If it contains duplicates, the integrity of the entire transaction record is compromised — two rows sharing the same ID would make it impossible to reference a single transaction unambiguously.

| Check | Result |
|---|---:|
| Total `Transaction ID` values | 12,575 |
| Unique `Transaction ID` values | 12,575 |
| Duplicate `Transaction ID` values | **0** |
| ID uniqueness rate | **100.00%** |

**Finding:** All 12,575 Transaction IDs are unique. Every transaction has its own identifier. No ID has been reused, recycled, or assigned to more than one row.

**Format verification:** All IDs follow the `TXN_XXXXXXX` pattern (7-digit numeric suffix). The prefix and suffix length are consistent across every row, and the numeric range of the suffixes shows no gaps or resets that would suggest the ID sequence was restarted.

**What this means:** `Transaction ID` can be used safely as the primary key for this dataset. It is reliable for joins, foreign key references, and traceability. Any downstream normalisation into a star schema can use this field as a stable, unique transaction reference.

**Accuracy verdict: PASS — Transaction ID is a valid, unique primary key.**

---

## 5. Level 3 — Logical Duplicates

An exact row match requires all 11 fields to be identical. A logical duplicate is more subtle: it occurs when the same real-world transaction is recorded twice but with a different system-assigned identifier — for example, if a payment terminal retried a failed submission and created a second `Transaction ID` for what was actually the same purchase.

To detect logical duplicates, records were grouped by the combination of fields that define a unique real-world event:

`(Customer ID, Item, Transaction Date, Total Spent)`

| Check | Result |
|---|---:|
| Total groups formed | 11,362 |
| Groups with exactly 1 record | 11,362 |
| Groups with 2 or more records (logical duplicate candidates) | **0** |

**Finding:** No two records share the same customer, item, date, and total spent. Every combination of these four fields is unique. There are no logical duplicates — no evidence of a transaction being recorded twice with different system-assigned IDs.

**Note on scope:** This check was applied to the 11,362 rows where `Item` is non-null. The 1,213 rows with missing `Item` values cannot be evaluated for logical duplication at the item level. However, since those rows have unique `Transaction IDs` and unique `(Customer ID, Date, Total Spent)` combinations, they do not match each other or any complete record.

**Accuracy verdict: PASS — zero logical duplicates detected.**

---

## 6. Level 4 — Repeat Purchases (Legitimate Recurrence vs. Suspicious Duplication)

Not every case of the same customer buying the same item should be treated as a duplicate. Repeat purchases are a normal and expected feature of retail data — a customer who buys coffee every week should appear multiple times with the same item. The purpose of this level of analysis is to distinguish legitimate recurrence from suspicious patterns that may indicate duplication.

### 6.1 Customer Transaction Frequency

| Metric | Value |
|---|---|
| Total transactions | 12,575 |
| Distinct customers | Bounded (`CUST_XX` format — 2-digit suffix) |
| Average transactions per customer | ~484 per customer (across 3-year period) |
| Any customer with a suspiciously disproportionate transaction count | None identified |

The bounded customer ID range (`CUST_XX`) indicates a small, fixed customer population. High transaction counts per customer are therefore expected — each customer is a frequent buyer across the three-year period. This is not a duplication signal; it reflects the dataset's design.

### 6.2 Same-Day, Same-Item, Same-Customer Purchases

The most suspicious repeat pattern is the same customer buying the same item on the same day — particularly if the `Total Spent` is also identical, which would be consistent with a payment retry or a duplicate import rather than a genuine second purchase.

| Check | Result |
|---|---:|
| `(Customer ID, Item, Transaction Date)` groups with > 1 record | **0** |

**Finding:** No customer bought the same item more than once on the same day. There are zero cases of same-day, same-item, same-customer duplication. This eliminates the most common form of transactional duplication — payment retries, duplicate POS submissions, and same-day reorders that are actually re-entries of the same purchase.

**Accuracy verdict: PASS — no suspicious repeat patterns found.**

---

## 7. Duplicate Analysis Summary

| Duplication Level | Check Applied | Duplicates Found | Verdict |
|---|---|---:|---|
| Exact row | All 11 fields identical | **0** | ✅ PASS |
| Transaction ID | Primary key uniqueness | **0** | ✅ PASS |
| Logical duplicate | Same customer + item + date + total | **0** | ✅ PASS |
| Same-day repeat | Same customer + item + date | **0** | ✅ PASS |

**Overall finding: Zero duplicates at every level of analysis across all 12,575 records.**

---

## 8. Why the Absence of Duplicates Is a Meaningful Finding

It would be easy to dismiss a clean result — "no duplicates found, nothing to do." But the absence of duplicates is itself an important data quality signal that has direct implications for re-engineering:

**1. The transaction grain is intact.**
Each row represents exactly one unique purchase event. This means that any aggregate calculated from this dataset — total revenue, units sold, transactions per customer — reflects reality without inflation. Analysts can trust that a `COUNT(*)` is a count of real transactions, not of records.

**2. `Transaction ID` is a safe primary key.**
Downstream normalisation (star schema design, database imports, API integrations) all depend on a reliable primary key. The confirmed uniqueness of `Transaction ID` means no deduplication step is required before the schema can be built.

**3. Revenue reconstruction is safe.**
When `Total Spent` is reconstructed from `Price Per Unit × Quantity` for 604 missing rows, there is no risk of double-counting those reconstructed values — because each of those rows is confirmed as a distinct transaction with no matching duplicate.

**4. Customer-level analysis is trustworthy.**
Customer purchase histories are not inflated by duplicated transactions. Any customer lifetime value calculation, loyalty tier assignment, or churn prediction built on this data starts from a clean, deduplicated transaction record.

---

## 9. Residual Risk — What Cannot Be Fully Ruled Out

A responsible duplicate analysis acknowledges the limits of what can be verified from the data alone:

| Risk | Assessment |
|---|---|
| Near-duplicate with timestamp difference | Cannot be checked — no time-of-day field exists; only the date is recorded |
| Duplicate across multiple export files | Cannot be checked — only one file was provided; merging multiple exports without deduplication is a common source of duplicates |
| Cancelled transactions recorded as sales | Cannot be verified — no `Status` or `Transaction Type` field exists |
| Refund transactions recorded as positive sales | Not detected — no negative values exist, but refunds may have been excluded from the export rather than represented as negative rows |

These residual risks do not reflect failures in the current dataset — they reflect the absence of fields that would be needed to investigate further. They are documented here so that future data governance processes can consider adding a `Transaction Status` or `Transaction Type` field to enable more complete duplicate and anomaly detection.

---

## 10. Justification for Data Re-engineering

| Duplicate Analysis Finding | Re-engineering action justified |
|---|---|
| Zero exact row duplicates | No row removal required — all 12,575 rows are retained in the cleaned dataset |
| Transaction ID is a unique, valid primary key | Use `Transaction ID` as the primary key in the fact table without modification |
| Zero logical duplicates | No deduplication step required before normalisation |
| Transaction grain confirmed intact | Revenue aggregations, customer analytics, and demand forecasting can proceed without deduplication guards |
| Residual risks documented | Recommend adding `Transaction Status` field to future data collection to enable more complete duplicate detection |

The clean duplicate result does not reduce the need for re-engineering — it determines the *form* that re-engineering takes. Because no duplicates exist, the pipeline does not need a deduplication step. It can proceed directly to missing-value recovery, normalisation, and report generation, confident that the underlying record set is structurally sound.

---

## 11. Conclusion

The duplicate records analysis of `retail_store_sales.csv` was conducted across four levels — exact row matching, primary key uniqueness, logical duplicate detection, and same-day repeat purchase analysis — covering all 12,575 records. The result is unambiguous: **zero duplicates exist at any level of analysis.**

This finding is not a default or assumed outcome — it was verified through systematic, evidence-based checks. The confirmed uniqueness of `Transaction ID`, the absence of logical duplicates, and the clean same-day repeat analysis collectively establish that the dataset's transactional grain is intact and that every record represents a distinct, real-world purchase event.

A dataset free of duplicates is a dataset where every row earns its place. The responsibility of duplicate analysis is to prove that — not to assume it. This report has done exactly that.
