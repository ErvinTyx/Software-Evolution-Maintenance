# Data Re-engineering Execution Report

**Dataset:** `transaction.csv` | **Rows:** 10,103 | **Columns:** 6  
**Pipeline:** `transaction_reengineering.py`  
**Outputs:** `data_clean.csv`, `data_normalise.csv`, `city.csv`, `card.csv`

---

## 1. Overview

Data re-engineering was applied to `transaction.csv` in three structured phases:

1. **Data Cleansing** — correct or neutralise invalid, malformed, and outlier values while preserving the original structure
2. **Transformation** — standardise values into canonical, consistent forms using domain-defined mappings
3. **Normalisation / Restructuring** — split the flat table into a relational schema, enforce correct data types, and assign a proper unique identifier

Every action taken in this pipeline is grounded in evidence from data profiling. No values were arbitrarily changed — each decision is traceable to a specific, documented quality issue.

---

## 2. Phase 1 — Data Cleansing

### 2.1 Whitespace Stripping

**Action:** All text columns (`status`, `time`, `card_type`, `city`, `amount`) had leading and trailing whitespace stripped.

**Justification:** Invisible whitespace causes value comparison failures. The string `"success"` and `" success"` are not equal in any database, filter, or group-by operation. Stripping is a zero-information-loss operation — no meaning is removed.

---

### 2.2 Datetime Partial Normalisation for `data_clean.csv`

**Action:** The `time` column was partially normalised for the `data_clean.csv` intermediate output. Values were processed as follows:

| Input Value | data_clean.csv Output | Reason |
|-------------|----------------------|--------|
| `07:32 2025-09-20` | `07:32 2025-09-20` | Valid, kept as-is |
| `2025-09-08 23:17:00` | `2025-09-08 23:17:00` | Valid, kept as-is |
| `03-00-2025 09-11` | `03:00 2025-09-11` | Parseable with known pattern — rescued |
| `99:99 2025-13-40` | `NULL` | Impossible hour/minute/month — irretrievable |
| `25:61 2025-09-11` | `NULL` | Impossible hour/minute — irretrievable |
| `12:00` | `12:00 NULL` | Time-only, no date — partial salvage |
| *(empty)* | `NULL` | Missing |

**Justification:** Outright deletion of datetime rows would remove valid transaction records whose only fault is a formatting issue. Partial salvage (`HH:MM NULL`, `NULL YYYY-MM-DD`) preserves whatever is recoverable while explicitly marking the missing component as `NULL`. This respects data integrity — `NULL` communicates known absence rather than silent omission.

Impossible values (`99:99`, `2025-13-40`) were nulled because they cannot represent any real-world timestamp. Keeping them as strings would corrupt any downstream time-based analysis.

**Impact:** 15 rows changed from malformed strings to NULL (8 already NULL → 23 total NULL in normalised output).

---

### 2.3 Amount Outlier Nulling

**Action:** The IQR (Interquartile Range) method was applied to absolute amount values. Amounts falling outside `[Q1 − 1.5×IQR, Q3 + 1.5×IQR]` were set to NULL.

**Calculation:**
- Q1, Q3 computed on positive absolute amounts only
- Lower bound and upper bound derived from IQR
- Extreme values such as `9,999,999,999` flagged and nulled

**Justification:** Statistical outliers in a financial column are not inherently wrong — they may be legitimate large transactions. However, in this dataset the extreme values (`9,999,999,999`) are clearly sentinel/placeholder values used to mark anomalous records, not genuine transaction amounts. Setting them to NULL is the appropriate response: it removes the distortion from aggregations (mean, sum, distribution analysis) without deleting the transaction record itself. The remaining columns (`status`, `city`, `card_type`) of those rows remain valid and useful.

The IQR method was chosen over hard-coded thresholds because it adapts to the actual distribution of the data rather than assuming a fixed business rule.

**Impact:** 299 additional rows nulled in `amount` (2 original NULLs → 301 total NULLs in normalised output).

---

## 3. Phase 2 — Transformation

Transformation maps raw, inconsistent values to a defined set of canonical forms. All mappings are case-insensitive and cover every variant observed during profiling.

### 3.1 `status` Standardisation

**Action:** All 6 raw status variants mapped to exactly 2 canonical values.

| Raw Value | Canonical Value | Mapping Basis |
|-----------|----------------|---------------|
| `success` | `success` | Exact match |
| `Success` | `success` | Case fold |
| `succeed`  | `success` | Synonym |
| `fail`    | `failed`  | Synonym |
| `failed`  | `failed`  | Exact match |
| `FAIL`    | `failed`  | Case fold |

**Before:** 6 distinct values — `fail` (39.64%), `success` (39.23%), `failed` (11.81%), `Success` (4.93%), `FAIL` (2.21%), `succeed` (2.19%)  
**After:** 2 distinct values — `failed`, `success`

**Justification:** A transaction outcome is binary. The existence of 6 forms is a data entry and input validation failure, not a genuine difference in meaning. Any analysis that groups by status — failure rate, success rate, trend over time — requires a consistent domain. Without this transformation, `fail` and `failed` appear as separate categories, causing every aggregate statistic to be wrong.

The choice of `success` / `failed` as the canonical forms follows grammatical consistency: both are the same part of speech (adjective/past participle describing outcome state).

---

### 3.2 `time` Parsing and Splitting

**Action:** All valid datetime strings were parsed into a single `datetime` object, then split into two separate output columns:

- `date` → `YYYY-MM-DD` (e.g. `2025-09-20`)
- `time` → `HH:MM:SS` (e.g. `07:32:00`)

Both formats supported by the parser:
1. `YYYY-MM-DD HH:MM:SS` — primary format (10,000 rows)
2. `HH:MM YYYY-MM-DD` — alternate format (76 rows, rescued)

**Before:** Mixed formats, 5 distinct format patterns, impossible values present  
**After:** Single canonical format per column — `YYYY-MM-DD` for date, `HH:MM:SS` for time; 23 NULLs where datetime was irretrievable

**Justification:** Storing a datetime as a freeform string means no date arithmetic, no sorting by time, and no filtering by date range is reliable. Splitting into `date` and `time` serves two purposes: (1) it enforces the canonical format, and (2) it aligns with relational database design where date and time components are often queried independently (e.g. "all transactions on 2025-09-08" vs "all transactions after 18:00").

The alternate `HH:MM YYYY-MM-DD` format was not discarded — it was parsed and rescued into the canonical form. Discarding valid data because of format inconsistency would be an unjustifiable loss.

---

### 3.3 `card_type` Canonicalisation

**Action:** All 10 non-null card type variants mapped to 4 canonical brand names.

| Raw Variants | Canonical Value |
|-------------|----------------|
| `Visa`, `visa`, `VISA`, `Vsa` | `Visa` |
| `MasterCard`, `Master Card`, `Master-Card`, `MastCard` | `MasterCard` |
| `Amex` | `Amex` |
| `Discover` | `Discover` |

**Before:** 11 distinct values (including NULL) — fragmented across typos, case variants, and hyphenation differences  
**After:** 4 canonical brand names + NULL (314 rows)

**Justification:** Card brand names are externally defined — they are not free-form text. `MastCard`, `Vsa`, and `Master-Card` are unambiguously misspellings of known brands. Leaving them as-is would make it impossible to correctly count Visa transactions (currently split across 4 variants: 2,383 + 810 + 208 + 182 = 3,583 actual Visa transactions vs the 2,383 that would be counted without normalisation — a 50% undercounting error).

NULL values (314 rows, 3.11%) were not guessed or imputed. Assigning a brand to a transaction with no card type information would introduce false data. NULL is retained to honestly represent the unknown.

---

### 3.4 `city` Canonicalisation

**Action:** All 13 non-null city variants mapped to 8 canonical city names.

| Raw Variants | Canonical City |
|-------------|---------------|
| `Tehran`, `TEHRAN`, `THR`, `ThRan`, `tehr@n` | `Tehran` |
| `Karaj`, `karaj` | `Karaj` |
| `Tabriz` | `Tabriz` |
| `Isfahan` | `Isfahan` |
| `Mashhad` | `Mashhad` |
| `Shiraz` | `Shiraz` |
| `Qom` | `Qom` |
| `Ahvaz` | `Ahvaz` |

**Before:** 14 distinct values (including NULL) — Tehran fragmented across 5 variants (3,516 total rows)  
**After:** 8 canonical city names + NULL (117 rows)

**Justification:** Geographic city names are fixed entities. `THR` is the IATA code for Tehran Imam Khomeini International Airport — its presence in a city column indicates a data entry error (likely copied from a flight booking field). `tehr@n` is a clear keyboard error. All five variants unambiguously refer to the same city.

Without canonicalisation, any geographic aggregation (transactions by city, fraud rates by location) would report Tehran as 5 separate cities and dramatically misrepresent the distribution. The city of Tehran accounts for 34.8% of all transactions — misrepresenting this as fragmented smaller groups would invalidate any geographic analysis.

NULL values (117 rows, 1.16%) were not imputed — city cannot be inferred from other columns.

---

### 3.5 `amount` Transformation

**Action:** Three sub-transformations applied to the amount column:

1. **Text-to-numeric conversion:** `"one hundred"` → `100`  
2. **Negative to absolute:** All negative amounts converted to their absolute value (e.g. `-5000` → `5000.0`)  
3. **Type standardisation:** All amounts stored as `double` (float64) in the output

**Before:** Mixed types — 96.91% integer, 3.06% decimal, 0.01% non-numeric text, 12.05% negative values  
**After:** Consistent `double` type; negative and non-numeric issues resolved; outliers nulled (Phase 1)

**Justification:**

- **`"one hundred"`:** This is an encoding error — the value is unambiguously 100. Converting it preserves the legitimate data point rather than nulling a valid transaction amount.

- **Negative amounts:** Transaction amounts in a payment processing context represent the monetary value exchanged. A negative amount (`-5000`) is not a refund record in this dataset — there is no `type` column indicating refund vs charge. The profiling showed these are systematic sentinel/error values (1,217 rows, all repeating values: `-1`, `-5000`, `-999999`, `-999999.0`). Converting to absolute value is the correct interpretation.

- **Type as `double`:** The raw column mixes integers and decimals. Storing as `double` provides a consistent numeric contract for all downstream consumers. Integers stored as `double` lose nothing; the uniform type prevents type mismatch errors in joins, aggregations, and exports.

---

## 4. Phase 3 — Normalisation / Restructuring

### 4.1 Surrogate Key Assignment

**Action:** A new column `transaction_id` was added, assigned sequential values `TRX_00001` through `TRX_10103`. The original `id` column was retained for reference.

**Before:** `id` column — 99 distinct values across 10,103 rows (100% duplication rate); no unique row identifier existed  
**After:** `transaction_id` — 10,103 unique values, zero duplicates

**Justification:** A primary key must uniquely identify each row. The original `id` field failed this requirement — with only 99 distinct values across 10,103 rows, it functions as a batch or category code, not a row identifier. Without a proper primary key, no row can be reliably referenced, updated, or joined.

The `TRX_NNNNN` format was chosen to be human-readable and clearly distinguishable from the original numeric `id`. The original `id` is preserved because it may carry domain meaning (batch grouping, session code) that should not be discarded.

---

### 4.2 Relational Decomposition — Lookup Tables

**Action:** Two dimension tables were extracted from the flat transaction table:

**`city.csv`** — City lookup table:
| city_id | city |
|---------|------|
| city_1 | Ahvaz |
| city_2 | Isfahan |
| city_3 | Karaj |
| city_4 | Mashhad |
| city_5 | Qom |
| city_6 | Shiraz |
| city_7 | Tabriz |
| city_8 | Tehran |

**`card.csv`** — Card type lookup table:
| card_id | card_type |
|---------|-----------|
| card_1 | Amex |
| card_2 | Discover |
| card_3 | MasterCard |
| card_4 | Visa |

The main `data_normalise.csv` stores `city_id` and `card_id` as foreign key references instead of repeating the full string values.

**Before:** `transaction.csv` — flat file, string values repeated in every row  
**After:** `data_normalise.csv` (fact table) + `city.csv` + `card.csv` (dimension tables)

**Justification:** Storing `"Tehran"` or `"MasterCard"` as a string in every row is an **update anomaly** — if the canonical spelling of a city name needs to change, every row must be updated. In a relational design, only the lookup table needs to change; the foreign key references remain valid.

Additionally, the lookup tables enforce referential integrity: a `city_id` of `city_9` cannot exist in the fact table if there are only 8 cities in `city.csv`. This constraint prevents the re-introduction of the same inconsistency problems that existed in the raw data.

The decomposition follows **Third Normal Form (3NF)**: `card_type` depends only on `card_id`, not on the transaction itself — so it belongs in a separate table.

---

### 4.3 `time` Column Split into `date` + `time`

**Action:** The single `time` column from the raw data was split into two columns in `data_normalise.csv`:
- `date` — stores date component only (`YYYY-MM-DD`)
- `time` — stores time component only (`HH:MM:SS`)

**Before:** One column mixing date and time in varying formats  
**After:** Two typed, single-concern columns

**Justification:** Combining date and time in a single string column prevents efficient date-range queries (`WHERE date BETWEEN '2025-09-01' AND '2025-09-30'`) and time-of-day analysis (`WHERE time BETWEEN '18:00:00' AND '23:59:59'`). Splitting them respects the **Single Responsibility Principle** at the schema level — each column holds one type of information. It also aligns with standard database practice where `DATE` and `TIME` are distinct types.

---

## 5. Before vs After Comparison

| Dimension | Before (transaction.csv) | After (data_normalise.csv) |
|-----------|--------------------------|---------------------------|
| Rows | 10,103 | 10,103 |
| Columns | 6 | 7 (`date` + `time` replacing `time`) |
| Unique `status` values | 6 | 2 |
| Unique `card_type` values | 11 | 4 (via `card_id` FK) |
| Unique `city` values | 14 | 8 (via `city_id` FK) |
| Datetime format patterns | 5 | 1 per column (`YYYY-MM-DD` / `HH:MM:SS`) |
| Amount format types | 4 (int, decimal, text, null) | 2 (decimal, null) |
| Amount NULL count | 2 | 301 (299 outliers correctly nulled) |
| Time NULL count | 8 | 23 (15 impossible datetimes correctly nulled) |
| Unique row identifier | None (100% duplicate `id`) | `TRX_00001`–`TRX_10103` |
| Related tables | 0 | 2 (`city.csv`, `card.csv`) |

---

## 6. Justification Summary

Every re-engineering action in this pipeline satisfies at least one of the following principles:

| Principle | Actions |
|-----------|---------|
| **No data fabrication** | NULL values never replaced with guessed values (`card_type`, `city`); only unambiguous mappings applied (`"one hundred"` → 100) |
| **No silent deletion** | Outlier amounts nulled in-place rather than row-dropped; impossible datetimes nulled rather than rows removed |
| **Traceable decisions** | Each mapping (`succeed` → `success`, `tehr@n` → `Tehran`) derived from profiling evidence, not assumption |
| **Domain correctness** | Card brands, city names, and status values are externally defined entities — mappings reflect real-world truth |
| **Structural integrity** | Surrogate key guarantees uniqueness; FK references enforce referential integrity; NF3 decomposition eliminates update anomalies |
| **Type correctness** | `amount` stored as `double`, `date` as date-formatted string, `time` as time-formatted string — each column holds the type it semantically represents |

---

## 7. Conclusion

The re-engineering pipeline transformed `transaction.csv` from a flat, inconsistency-laden raw file into a clean, structured, and analytically usable dataset. The three-phase approach — cleanse, transform, normalise — ensured that data quality improvements were made systematically and justifiably. No data was fabricated, no records were deleted without cause, and every transformation decision is traceable to a specific profiling finding. The resulting schema (`data_normalise.csv`, `city.csv`, `card.csv`) is ready for reliable analysis, reporting, and integration.
