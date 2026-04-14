# Advocacy & Professional Reflection

**Project:** Transaction CSV Data Re-engineering  
**Dataset:** `transaction.csv` | 10,103 rows · 6 columns

---

## Part 1 — Advocacy Artefact

### Why Data Re-engineering Matters

![Advocacy Infographic](../images/advocacy_infographic.png)

The infographic above presents six evidence-based arguments for why data re-engineering is not optional, drawn directly from the profiling and re-engineering of `transaction.csv`:

| Panel | Argument |
|-------|----------|
| 1 | Raw data actively produces wrong business answers — Visa transactions undercounted by 50%, MasterCard by 124% |
| 2 | A single city (Tehran) was fragmented into 5 entries, making it invisible as a unified entity |
| 3 | Overall data quality improved from 45/100 to 92/100 across five measured dimensions |
| 4 | 18,397+ affected rows across six distinct categories of issues — none of which are detectable without profiling |
| 5 | Every major business function — revenue reporting, geographic analysis, financial modelling, operational queries — was producing unreliable output |
| 6 | A structured three-phase pipeline (cleanse → transform → normalise) resolved every issue systematically and traceably |

**Core argument:** Dirty data does not just waste storage — it wastes decisions. Every query run against an uncleaned dataset produces answers that look correct but are not. The damage is not visible in the data itself; it only becomes visible when a wrong decision is made, a report is challenged, or an audit fails. By then, the cost is far greater than the re-engineering would have been.

---

## Part 2 — Professional Reflection

### How Our Attitude Toward Data Quality Evolved

#### Before: Data Quality as an Assumption

At the beginning of this project, the working assumption was that a CSV file containing transaction records would be fundamentally usable. Fields would have consistent names, amounts would be numbers, status values would be uniform, and IDs would identify rows uniquely. Data quality was treated as a background condition — something that could be assumed rather than verified.

This is, in hindsight, an extremely common and extremely dangerous assumption.

The first sign that this assumption was wrong came during the ID duplication check. The `id` column — the field most naturally associated with uniqueness — turned out to have a 100% duplication rate. There were only 99 distinct values across 10,103 rows. Every assumption about row identity, every planned JOIN operation, every deduplication strategy, depended on a field that offered zero uniqueness. That single finding changed the frame through which the rest of the dataset was viewed.

---

#### During: From Surprise to Systematic Scrutiny

Once the ID issue surfaced, profiling became less about confirming expectations and more about discovering what else was wrong. Each column revealed a new category of problem:

- **`status`** appeared clean at first glance — it had no nulls and only text values. But counting distinct values revealed 6 forms of a binary field. The assumption that `fail` and `failed` would already be unified was wrong.

- **`card_type`** revealed the depth of the problem. `MastCard` and `Vsa` are not edge cases or typos from one user — they appear in 1,010 and 810 rows respectively. This is systematic. It means no input validation existed at the source.

- **`city`** produced the most striking single finding: `tehr@n`. A city name with `@` substituted for `a`, appearing 335 times. This is not a random typo — it is a pattern, suggesting either a systematic keyboard mapping error, a data export encoding fault, or deliberate obfuscation. Whatever the cause, it makes the data unusable for geographic analysis without intervention.

- **`amount`** changed how we understood the relationship between data type and data quality. A column full of numbers is not automatically valid. `-999999` is a number. `9999999999` is a number. Neither represents a real transaction amount. The distinction between *parseable* and *meaningful* became concrete through this column.

By the end of the profiling phase, the attitude had shifted from verifying assumptions to expecting surprises. Profiling was no longer a formality — it was the most important step in the entire pipeline.

---

#### After: Data Quality as a Professional Responsibility

The re-engineering phase reinforced a realisation that goes beyond technical skill: **data quality is an ethical responsibility, not just a technical one.**

The 3,007 rows with non-canonical `card_type` values are not just a consistency problem. They represent thousands of transactions that cannot be correctly attributed to a card brand. If a business analyst used this data to decide which card processor to negotiate with, they would be negotiating with the wrong numbers. The MasterCard processing volume appeared to be 1,461 transactions. It was actually 3,268 — 124% more. A contract negotiation based on the raw figure would be materially wrong, and the data would be the silent cause.

The same logic applies to the city data. Karaj appeared to have 649 transactions. It had 1,048. If branch staffing decisions or infrastructure investments were made based on the raw figures, Karaj would be systematically under-resourced relative to its actual transaction load. The data would be creating an unfair outcome for a geographic region — not through any deliberate act of bias, but through the quiet accumulation of inconsistent city names.

These are not abstract concerns. They are the natural consequence of using uncleaned data to make real decisions.

---

#### The Shift: From Passive Consumer to Active Steward

The most significant attitudinal shift over the course of this project is the move from treating data as something to be used to treating data as something to be stewarded.

A passive consumer of data runs a query, receives a result, and trusts it. An active steward of data asks: where did this come from, how was it collected, what could be wrong with it, and what decisions will be made from it?

This project made that shift concrete through specifics:

- Seeing that `succeed` appears 221 times as a status value forces the question: what did the source system mean by this? Is it the same as `success`? The answer matters for 221 transaction records and for the reported success rate.

- Seeing that 299 amounts were nulled as IQR outliers forces the question: were any of these legitimate large transactions? The IQR method is statistically defensible, but it is not infallible. Responsible re-engineering means flagging these 299 rows for review rather than simply discarding them.

- Seeing that 23 timestamps were nulled forces the acknowledgement that those 23 transactions cannot be placed in time. Any time-series report built on this dataset must explicitly state that 0.23% of transactions have no timestamp — because silence about that gap would be a form of misrepresentation.

---

#### Conclusion: Why This Matters Beyond This Project

Data quality failures are not unique to this dataset. They are universal. Every organisation that collects data through human input, system integration, or automated pipelines accumulates quality debt over time. The decision to profile, re-engineer, and validate data is a decision to take that debt seriously before it compounds into wrong decisions, failed audits, or unfair outcomes.

The professional attitude this project developed is not one of distrust toward data — it is one of disciplined verification. Data is not assumed to be correct; it is checked, documented, corrected, and the corrections are explained. Every change is traceable. Every unknown is explicitly marked as unknown rather than silently omitted.

This is what it means to handle data responsibly. Not as a technical exercise, but as an act of professional accountability — to the decisions that will be made from the data, to the people those decisions affect, and to the integrity of the analysis itself.

> "You cannot improve what you have not measured. You cannot trust what you have not questioned."
