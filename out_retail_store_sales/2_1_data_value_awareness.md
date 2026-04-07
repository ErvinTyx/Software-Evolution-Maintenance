# 2.1 Data Value Awareness & Dataset Selection
**Dataset:** `retail_store_sales.csv`
**Records:** 12,575 transactions | 11 columns | Date range: 2022-01-01 → 2025-01-18

---

## What This Data Is and Why It Matters

The retail store sales dataset is a transactional record of customer purchases across eight product categories — Beverages, Butchers, Computers & Electric Accessories, Electric Household Essentials, Food, Furniture, Milk Products, and Patisserie — spanning three years of sales activity across online and in-store channels.

Retail transaction data is one of the most business-critical assets an organisation holds. Every field in this dataset feeds a real decision:

| Field | Business decision it drives |
|---|---|
| `Item` / `Category` | Inventory restocking, supplier negotiations |
| `Price Per Unit` / `Total Spent` | Revenue reporting, pricing strategy, tax compliance |
| `Quantity` | Demand forecasting, warehouse planning |
| `Discount Applied` | Promotion effectiveness, margin analysis |
| `Customer ID` | Customer lifetime value, loyalty segmentation |
| `Transaction Date` | Seasonal trend analysis, staff scheduling |
| `Location` / `Payment Method` | Channel performance, fraud detection |

When any of these fields are missing, inconsistent, or wrong, the decisions built on top of them are wrong too — silently and at scale.

---

## Data Quality Issues Identified

### 1. Missing Values

| Column | Missing Count | % of Records | Business Impact |
|---|---:|---:|---|
| `Discount Applied` | 4,199 | **33.4%** | One in three transactions has unknown discount status — any discount-rate KPI is unreliable |
| `Item` | 1,213 | 9.6% | Nearly 1 in 10 transactions cannot be attributed to a product — inventory and product-level revenue analysis are incomplete |
| `Price Per Unit` | 609 | 4.8% | Unit price is unknown — revenue per unit and pricing reports are understated |
| `Quantity` | 604 | 4.8% | Quantity sold is unknown — demand forecasting and stock replenishment signals are distorted |
| `Total Spent` | 604 | 4.8% | Total revenue is unknown for these transactions — turnover figures are understated |

**Structured missingness pattern:** 609 records have `Item`, `Price Per Unit`, `Quantity`, and `Total Spent` all missing at the same time. This is not random noise — it points to a systematic data-capture failure, most likely a point-of-sale (POS) system outage or an incomplete export from the transaction database. Understanding *why* data is missing is as important as filling it.

---

### 2. Duplication

| Check | Result |
|---|---|
| Exact duplicate rows | **0** |
| Duplicate `Transaction ID` values | **0** |

No duplication was found at the row or transaction-ID level. Each transaction is uniquely identified, which confirms the dataset's grain is intact. This is a positive quality signal — deduplication is not required.

---

### 3. Inconsistency

| Consistency Rule | Violations |
|---|---:|
| `Total Spent` ≠ `Price Per Unit × Quantity` (tolerance ±0.01) | **0** |
| `Quantity` non-integer values | **0** |
| `Quantity` outside expected range (1–10) | **0** |
| `Price Per Unit` not in 0.50 increments | **0** |
| Unparseable `Transaction Date` values | **0** |

All complete records pass every arithmetic and format consistency check. The internal logic of the dataset is sound — meaning the missing-value problem is isolated and can be addressed systematically without broader data corruption concerns.

**Notable inconsistency — `Discount Applied`:** This field contains three states: `True`, `False`, and missing (`NaN`). The missing state is genuinely ambiguous — it could mean the discount status was not captured, or that it was not applicable. Treating `NaN` as `False` would be an inconsistency introduced *by the analyst*, not present in the raw data. The correct treatment is to preserve it as unknown.

---

## Why Improving This Data Is Valuable

### Business Impact

**Revenue understatement:** 604 transactions have no recorded `Total Spent`. Based on the average transaction value in the dataset (~£92), this represents an estimated **£55,000+ in unaccounted revenue** in the current export. For a finance team closing monthly or quarterly books, this gap matters.

**Flawed promotional analysis:** With 4,199 discount records missing (33.4%), any analysis of promotion effectiveness — conversion rates, discount-driven revenue lift, margin erosion — is built on fewer than two-thirds of the data. A marketing team using these figures could over- or under-invest in future promotions based on a structurally incomplete picture.

**Broken inventory signals:** 1,213 transactions with no `Item` recorded cannot contribute to product-level sales velocity. A buyer relying on sales data to decide reorder quantities for Patisserie items, for example, is working with a dataset that silently excludes ~150 of its own transactions.

### Professional & Ethical Responsibility

**Fairness in performance evaluation:** If staff or store performance is measured by sales volume or revenue generated, missing transaction data directly disadvantages the teams responsible for those 609 unrecorded transactions. Re-engineering the data — by recovering what can be recovered and clearly flagging what cannot — is an act of fairness, not just technical hygiene.

**Customer trust:** Pseudonymous `Customer ID` values (e.g. `CUST_09`) indicate the organisation is handling customer data. Inaccurate records tied to customer identifiers could lead to incorrect loyalty points, wrong purchase histories, or flawed churn predictions — all of which have a direct impact on the customer relationship.

**Auditability and compliance:** Transaction records are frequently subject to financial audits and tax reporting. A dataset where 4.8% of revenue figures are missing or reconstructed without documentation would not pass scrutiny. Documenting every imputation decision in `metadata.json` ensures the data trail is transparent and defensible.

---

## Summary: Data as a Critical Asset

This dataset demonstrates a core truth about real-world data: **surface cleanliness hides deeper problems.** There are no duplicate rows, no arithmetic errors, and dates are all valid. At a glance, the data looks acceptable. But 33% of discount fields are unknown, nearly 10% of items are unidentified, and over 600 transactions have no financial record at all.

A data professional who stops at "no duplicates, no format errors" and calls the dataset clean would be missing the issues that matter most. The value of data re-engineering lies precisely in looking deeper — understanding missingness patterns, questioning what is absent, and documenting every assumption made during recovery.

Improving this data is not a cosmetic exercise. It directly protects revenue reporting accuracy, ensures fair performance evaluation, supports responsible customer data stewardship, and produces an analytical foundation that stakeholders can trust.

> *"Bad data does not announce itself. It hides in dashboards, averages, and forecasts — until a decision built on it fails."*
