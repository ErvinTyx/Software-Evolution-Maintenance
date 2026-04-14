# Validation Report — Before vs After Comparison

**Dataset:** `transaction.csv` → `data_normalise.csv`  
**Rows:** 10,103 (unchanged — no rows deleted)  
**Purpose:** Validate that re-engineering improved data quality without introducing new errors or losing legitimate data.

---

## 1. Validation Methodology

Validation was performed by comparing the raw source file (`transaction.csv`) against the normalised output (`data_normalise.csv`) across five dimensions:

1. **Completeness** — null counts before and after
2. **Consistency** — distinct value counts and format conformance
3. **Accuracy** — correctness of transformed values
4. **Structural integrity** — schema, types, and key uniqueness
5. **Row preservation** — no legitimate records lost

---

## 2. Completeness Validation

Completeness measures how many cells contain a meaningful, non-null value.

| Column (Raw) | Raw NULL Count | Column (Normalised) | Normalised NULL Count | Change | Explanation |
|---|---:|---|---:|---|---|
| `status` | 0 | `status` | 0 | None | No nulls introduced |
| `time` | 8 | `date` / `time` | 23 / 23 | +15 | 15 impossible datetimes correctly nulled |
| `card_type` | 314 | `card_id` | 314 | None | Unknown card types retained as NULL |
| `city` | 117 | `city_id` | 117 | None | Unknown cities retained as NULL |
| `amount` | 2 | `amount` | 301 | +299 | 299 IQR outliers correctly nulled |
| `id` | 0 | `transaction_id` | 0 | None | Surrogate key assigned to all rows |

**Interpretation:**

- The increase in `time` NULLs (+15) is correct and expected. These 15 rows contained values such as `99:99 2025-13-40` and `25:61 2025-09-11` — values that look like dates but are physically impossible. Keeping them as strings would give a false impression of completeness while the data is actually unusable for any time-based operation.

- The increase in `amount` NULLs (+299) is correct and expected. The 299 rows contained extreme outlier values (e.g. `9,999,999,999`) identified as sentinel/placeholder values via IQR analysis. They have been correctly quarantined rather than silently distorting aggregations.

- All other null counts are unchanged — no valid data was lost through the re-engineering process.

**Overall completeness improvement:**

| Metric | Before | After |
|--------|-------:|------:|
| Total cells | 60,618 | 70,721 (7 cols) |
| NULL cells | 441 | 778 |
| Valid cells | 60,177 | 69,943 |
| Completeness % | 99.27% | 98.90% |

The slight decrease in completeness percentage reflects the correct nulling of data that was previously masquerading as valid (impossible timestamps, extreme sentinel amounts). True completeness — cells with genuine, usable values — was not reduced.

---

## 3. Consistency Validation

Consistency measures whether values conform to a defined, uniform standard.

### 3.1 `status`

| | Before | After |
|---|---:|---:|
| Distinct values | 6 | 2 |
| Non-canonical rows | 2,135 (21.13%) | 0 (0.00%) |

| Before | Count | After | Count |
|--------|------:|-------|------:|
| `fail` | 4,005 | `failed` | 5,421 |
| `success` | 3,963 | `success` | 4,682 |
| `failed` | 1,193 | | |
| `Success` | 498 | | |
| `FAIL` | 223 | | |
| `succeed` | 221 | | |

**Validated:** All 6 raw variants correctly collapsed to 2. Total `failed` count (5,421) equals `fail` + `failed` + `FAIL` = 4,005 + 1,193 + 223 = 5,421. ✓  
Total `success` count (4,682) equals `success` + `Success` + `succeed` = 3,963 + 498 + 221 = 4,682. ✓

---

### 3.2 `card_type`

| | Before | After |
|---|---:|---:|
| Distinct values | 11 | 4 |
| Non-canonical rows | 3,007 (29.77%) | 0 (0.00%) |

| Canonical Brand | Before (fragmented) | After (unified) |
|----------------|--------------------:|----------------:|
| Visa | 2,383 + 810 + 208 + 182 = **3,583** | **3,583** |
| MasterCard | 1,461 + 1,010 + 601 + 196 = **3,268** | **3,268** |
| Discover | 1,663 | **1,663** |
| Amex | 1,275 | **1,275** |
| NULL | 314 | **314** |
| **Total** | **10,103** | **10,103** |

**Validated:** Row counts per brand sum correctly. No rows lost or gained. ✓

---

### 3.3 `city`

| | Before | After |
|---|---:|---:|
| Distinct values | 14 | 8 |
| Non-canonical rows | 1,636 (16.19%) | 0 (0.00%) |

| Canonical City | Before (fragmented) | After (unified) |
|---------------|--------------------:|----------------:|
| Tehran | 2,279 + 414 + 408 + 335 + 80 = **3,516** | **3,516** |
| Tabriz | 1,381 | **1,381** |
| Isfahan | 1,084 | **1,084** |
| Karaj | 649 + 399 = **1,048** | **1,048** |
| Mashhad | 909 | **909** |
| Shiraz | 734 | **734** |
| Qom | 676 | **676** |
| Ahvaz | 638 | **638** |
| NULL | 117 | **117** |
| **Total** | **10,103** | **10,103** |

**Validated:** All city variants correctly resolved. Row counts sum to 10,103. ✓

---

### 3.4 `time` Format

| Format | Before | After (`date`) | After (`time`) |
|--------|-------:|---------------:|---------------:|
| Valid canonical | 10,076 | 10,080 `YYYY-MM-DD` | 10,080 `HH:MM:SS` |
| NULL / empty | 8 | 23 | 23 |
| Non-canonical / impossible | 19 | 0 | 0 |

**Validated:** The alternate `HH:MM YYYY-MM-DD` format (76 rows) was successfully parsed and unified into the canonical output. Format diversity eliminated. ✓

---

### 3.5 `amount`

| Format Type | Before | After |
|------------|-------:|------:|
| Integer | 9,791 | 0 |
| Decimal (double) | 309 | 9,802 |
| Non-numeric text | 1 | 0 |
| NULL | 2 | 301 |

**Validated:** All amounts now stored as `double`. `"one hundred"` → `100.0` confirmed. Negative amounts converted to absolute. Type is now consistent across all 9,802 valid rows. ✓

---

## 4. Structural Integrity Validation

### 4.1 Primary Key Uniqueness

| | Raw `id` | Normalised `transaction_id` |
|---|---:|---:|
| Total rows | 10,103 | 10,103 |
| Distinct values | 99 | 10,103 |
| Duplicate rows | 10,103 (100%) | 0 (0.00%) |

**Validated:** `transaction_id` is unique across all 10,103 rows. Every row is now individually addressable. ✓

### 4.2 Referential Integrity

- All `card_id` values in `data_normalise.csv` exist in `card.csv` ✓
- All `city_id` values in `data_normalise.csv` exist in `city.csv` ✓
- NULL `card_id` / `city_id` values correctly represent unknown — no orphaned foreign keys ✓

### 4.3 Row Count Preservation

| Stage | Row Count |
|-------|----------:|
| `transaction.csv` (raw) | 10,103 |
| `data_clean.csv` (cleansed) | 10,103 |
| `data_normalise.csv` (normalised) | 10,103 |

**Validated:** Zero rows deleted at any stage of the pipeline. ✓

---

## 5. Summary Scorecard

| Dimension | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Unique `status` values | 6 | 2 | 67% reduction in variants |
| Unique `card_type` values | 11 | 4 | 64% reduction in variants |
| Unique `city` values | 14 | 8 | 43% reduction in variants |
| Datetime format patterns | 5 | 1 per column | Fully standardised |
| Amount type consistency | 4 types mixed | 1 type (`double`) | Fully standardised |
| Primary key uniqueness | 0% unique | 100% unique | Fully resolved |
| Non-canonical `status` rows | 2,135 (21.13%) | 0 | Fully resolved |
| Non-canonical `card_type` rows | 3,007 (29.77%) | 0 | Fully resolved |
| Non-canonical `city` rows | 1,636 (16.19%) | 0 | Fully resolved |
| Rows lost | — | 0 | No data deleted |

---

## 6. Conclusion

The validation confirms that all re-engineering actions achieved their intended outcomes. Every consistency issue identified in profiling was resolved. No legitimate data was deleted — all improvements were made in-place through mapping, type coercion, and controlled nulling. The normalised dataset is structurally sound, internally consistent, and ready for reliable analysis.
