# Ethics Report — Bias, Privacy, and Fairness in Data Re-engineering

**Dataset:** `transaction.csv`  
**Purpose:** Reflect on the ethical dimensions of the data profiling and re-engineering decisions made, and their potential consequences for individuals, businesses, and society.

---

## 1. Introduction

Data re-engineering is not a neutral technical exercise. Every decision to change, null, impute, or retain a value carries ethical weight — it shapes what the data says, who it represents, and what decisions will be made from it. This report examines the ethical considerations that arise from the `transaction.csv` re-engineering pipeline across three dimensions: **privacy**, **bias**, and **fairness**.

---

## 2. Privacy Considerations

### 2.1 What Personal Data Is Present

`transaction.csv` does not contain explicit personal identifiers such as names, national identity numbers, or email addresses. However, the combination of fields present constitutes a **quasi-identifier set** that can indirectly identify individuals:

| Field | Privacy Sensitivity |
|-------|-------------------|
| `id` | Low — not unique per person (99 values across 10,103 rows) |
| `city` | Low individually; combined with time and amount, raises risk |
| `card_type` | Moderate — narrows payment method used |
| `amount` | Moderate — specific transaction amounts can be distinctive |
| `time` | High — precise timestamps combined with city and amount can uniquely identify a person's transaction |
| `status` | Low |

**Assessment:** While no single field directly identifies a person, combining `time` + `city` + `amount` + `card_type` creates a fingerprint that could re-identify a cardholder if cross-referenced with bank records or merchant logs. This is known as a **linkage attack**.

### 2.2 What Was Done to Protect Privacy

- **No new identifying fields were added.** The surrogate key `TRX_00001` is a row reference, not linked to any person.
- **City values were generalised** to 8 canonical city names — this actually reduces geographic precision compared to a raw value like a street address or district, supporting privacy.
- **Card type was mapped to 4 brands** — no account numbers, card numbers, or expiry dates are present or inferred.

### 2.3 What Remains a Concern

- **Timestamp precision is preserved.** The normalised `date` + `time` columns retain second-level precision (`HH:MM:SS`). A transaction at a specific second, with a specific amount, in a specific city, on a specific card type is potentially uniquely identifiable.
- **Recommendation:** For any downstream analytical use (dashboards, reports), consider aggregating timestamps to the hour or day level. For any data sharing outside the organisation, pseudonymisation or time-bucketing should be applied.

---

## 3. Bias Considerations

### 3.1 Geographic Bias — City Normalisation

**Issue:** Tehran accounts for 3,516 of 10,103 transactions (34.8%) after normalisation. The five Tehran variants (`Tehran`, `TEHRAN`, `THR`, `ThRan`, `tehr@n`) were all mapped to a single canonical value — which is correct — but this concentration means any model or report trained on this data will be heavily weighted toward Tehran.

**Ethical concern:** If this data is used to allocate resources, set fraud thresholds, or evaluate branch performance, cities with fewer transactions (Ahvaz: 638, Qom: 676) may be systematically under-resourced or subject to less refined analysis simply because they are less represented.

**What was done:** The re-engineering did not introduce this imbalance — it already existed in the raw data. However, the normalisation makes it visible and measurable for the first time. **Making imbalance visible is the first step toward addressing it.**

**Recommendation:** Any downstream model or threshold should be calibrated per city, not globally. A fraud detection rule optimised on Tehran's transaction patterns may perform poorly in Ahvaz.

### 3.2 Temporal Bias — NULL Datetime Handling

**Issue:** 23 rows (0.23%) have NULL dates and times after re-engineering. These nulls are not random — they originated from specific data entry patterns (`99:99`, `25:61`, format errors). If these errors are concentrated in certain time periods or cities, their removal from time-series analysis could create a blind spot.

**Ethical concern:** If these 23 failed transactions cluster in a particular month or city, excluding them silently distorts fraud rate calculations or performance metrics for that period or location.

**What was done:** The rows were retained with NULL timestamps rather than deleted. The transaction record (status, city, card_type, amount) remains available for non-temporal analysis.

**Recommendation:** When performing time-based analysis, explicitly acknowledge and report the 23 rows with NULL timestamps as a data caveat.

### 3.3 Amount Bias — IQR Outlier Nulling

**Issue:** 299 rows had their `amount` set to NULL based on IQR outlier detection. The IQR method is statistically sound but carries an implicit assumption: that the distribution of transaction amounts is approximately symmetric and that extreme values are errors.

**Ethical concern:** In a payment context, extreme amounts may be legitimate large transactions (wholesale purchases, bulk payments, business transfers). If the dataset represents a mix of retail and commercial transactions, the IQR threshold may disproportionately null legitimate commercial transactions — effectively removing large-value business activity from the dataset.

**What was done:** Outlier rows were nulled in-place, not deleted. The `transaction_id`, `status`, `city`, `card_type`, and `date`/`time` fields remain intact. The null communicates "amount unknown" rather than asserting the amount was zero or fraudulent.

**Recommendation:** Before using `amount` for any business performance analysis, investigate whether the 299 nulled values cluster by `card_type` or `city`. If commercial cards (e.g. Amex) are disproportionately affected, the IQR threshold may need to be stratified by segment.

### 3.4 Status Mapping Bias — `succeed` Classification

**Issue:** The value `succeed` (221 rows, 2.19%) was mapped to `success`. This mapping is linguistically reasonable but was made as an assumption — the original data source may have used `succeed` to indicate a different transaction sub-state (e.g. a pending authorisation that later cleared, as opposed to an immediate success).

**Ethical concern:** If `succeed` had a different business meaning than `success`, misclassifying 221 rows as `success` could inflate the reported success rate, affecting KPIs, fraud metrics, or SLA compliance reporting.

**What was done:** The mapping was applied consistently and is documented. The original values are preserved in `data_clean.csv`.

**Recommendation:** The data owner should confirm whether `succeed` was intended as a synonym for `success` or as a distinct state. If the latter, the mapping should be revised and `succeed` treated as a separate canonical value.

---

## 4. Fairness Considerations

### 4.1 Impact on Business Decisions

The quality of this dataset directly affects the decisions made from it. The following business decisions are materially impacted by data quality:

| Business Decision | Impact of Poor Data Quality | Impact After Re-engineering |
|------------------|----------------------------|-----------------------------|
| Transaction success rate by city | Severely distorted — Tehran split into 5 groups | Accurate — all Tehran variants unified |
| Revenue by card brand | Visa undercounted by 50% (3,583 actual vs 2,383 raw) | Accurate — all variants consolidated |
| Fraud detection thresholds | Corrupted by negative/sentinel amounts | More reliable — outliers nulled |
| Time-based transaction analysis | Broken by mixed formats and impossible datetimes | Reliable for 99.77% of rows |
| Branch/city performance ranking | Karaj undercounted (649 raw vs 1,048 after `karaj` merge) | Accurate |

**Ethical concern:** Before re-engineering, a business analyst running a query on this data would unknowingly receive wrong answers. Karaj would appear to have 649 transactions when it actually had 1,048. This is not a minor rounding error — it is a 61% undercount. Decisions about resource allocation, staffing, or fraud response based on this figure would have been materially unfair to Karaj as a business unit.

### 4.2 Data Loss and Its Consequences

**What was lost:**
- 299 amount values (outliers → NULL): downstream analysis cannot use these amounts
- 15 datetime values (impossible timestamps → NULL): these transactions cannot be placed in time

**What was not lost:**
- No transaction rows were deleted
- All `status`, `city`, `card_type` fields for affected rows remain intact
- Affected rows are still countable and auditable

**Ethical concern:** The 299 rows with nulled amounts represent real transactions by real cardholders. If these transactions were large-value legitimate purchases, nulling their amounts means they will be excluded from any revenue or volume calculation. The decision to null rather than impute was made to avoid fabricating financial data — but this comes at the cost of those transactions being invisible in amount-based analysis.

**What responsible re-engineering requires:** The 299 nulled rows should be flagged in any downstream report. Analysts must know that 2.97% of transaction amounts are unknown — not zero, not missing by accident, but flagged as statistically anomalous and requiring human review before use.

### 4.3 Responsibility of the Data Re-engineer

The re-engineering of this dataset was performed with the following ethical commitments:

| Commitment | How It Was Upheld |
|------------|-------------------|
| **Do not fabricate data** | No values were invented or imputed from guesswork; only unambiguous transformations were applied |
| **Do not delete without cause** | All 10,103 rows preserved; nulling was applied to specific fields, not rows |
| **Document every change** | All mappings and thresholds are recorded in `transaction_reengineering.py` and the re-engineering report |
| **Preserve original data** | `data_clean.csv` retains the stripped originals; `transaction.csv` is unchanged |
| **Be transparent about uncertainty** | NULL explicitly communicates unknown, not absent or zero |

---

## 5. Conclusion

The `transaction.csv` dataset does not contain overtly sensitive personal data, but it carries meaningful privacy risk through quasi-identification, and material fairness risk through the distorted business metrics it produces in its raw state. The re-engineering process improved both dimensions: it made the data more truthful, more consistent, and less likely to produce biased business decisions.

However, ethical responsibility does not end with re-engineering. The 299 nulled amounts, the 23 null timestamps, the 314 unknown card types, and the 117 unknown cities all represent genuine gaps in knowledge. Any analysis built on this dataset must acknowledge these gaps explicitly. Silent omission of known unknowns is itself an ethical failure — one that re-engineering alone cannot prevent. That responsibility falls on the analysts, developers, and decision-makers who consume this data downstream.

**Re-engineering this data responsibly is not just a technical task — it is an act of accountability to every stakeholder whose decisions, resources, or reputation depends on what this data says.**
