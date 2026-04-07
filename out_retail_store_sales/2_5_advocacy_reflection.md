# 2.5 Advocacy & Professional Reflection
**Dataset:** `retail_store_sales.csv`
**Section:** Advocacy Artefact Description · Group Reflection
**Artefact:** `advocacy_infographic.png` (generated in `out_retail_store_sales/`)

---

## 1. The Advocacy Artefact

### What It Is

`advocacy_infographic.png` is a four-panel visual summary produced at the end of the re-engineering pipeline. It was designed to communicate — to any audience, at any level of technical knowledge — what was wrong with the data, what was done about it, and why it mattered. It is not a technical report. It is a persuasion tool.

The infographic serves as evidence that data re-engineering produces real, measurable change — and that the people who carried it out did so with professional values, not just technical methods.

---

## 2. Panel-by-Panel Description

### Panel 1 — Missing Values: Before vs After (Bar Chart)

**What it shows:** A grouped bar chart comparing the number of missing values per column before re-engineering (red bars) and after (green bars) for every column that had missing data: `Item`, `Price Per Unit`, `Quantity`, `Total Spent`, and `Discount Applied`.

**What it communicates:**
- Four columns drop completely to zero — the red bar disappears and only a green bar of height zero remains. This visual contrast is immediate and striking: the gap is gone.
- `Discount Applied` is the only column where both bars are equal and tall. Rather than hiding this, the infographic makes it prominent. This is a deliberate advocacy choice: showing that one gap was intentionally left open is more honest — and ultimately more persuasive — than showing a chart where everything appears solved.

**Why this panel matters for advocacy:** Numbers in a table require effort to interpret. A bar dropping from 1,213 to 0 requires none. Decision-makers who will never read a profiling report will look at this panel and immediately understand that something meaningful was fixed.

---

### Panel 2 — Transactions by Category (Horizontal Bar Chart)

**What it shows:** A horizontal bar chart displaying the number of transactions per product category across all 12,575 records, coloured by category.

**Categories displayed:**
| Category | Approximate transaction count |
|---|---:|
| Electric Household Essentials | 1,591 |
| Furniture | 1,591 |
| Food | 1,588 |
| Milk Products | 1,584 |
| Butchers | 1,568 |
| Beverages | 1,567 |
| Computers & Electric Accessories | 1,558 |
| Patisserie | 1,528 |

**What it communicates:** The distribution is balanced. Every category is equally represented. This is significant context for the missing-value problem: the data quality issues are not isolated to one area of the business — they affect all eight product lines. A business that uses this data for category-level decisions — stocking, pricing, promotion — has incomplete information across its entire product range, not just one corner of it.

**Why this panel matters for advocacy:** It anchors the data quality problem in a real business context. It is no longer abstract — it is about Furniture sales, Beverages inventory, and Patisserie demand. Data quality becomes a business problem, not an IT problem.

---

### Panel 3 — Consistency & Accuracy Checks Table

**What it shows:** A before-and-after comparison table covering the key consistency and accuracy metrics profiled during the analysis:

| Check | Before | After |
|---|---:|---:|
| Total ≠ price × qty | 0 | 0 |
| Qty non-integer | 0 | 0 |
| Qty outside 1–10 | 0 | 0 |
| Unparseable dates | 0 | 0 |
| Duplicate Transaction IDs | 0 | 0 |

**What it communicates:** Every consistency and accuracy check was already at zero before re-engineering — and remains at zero after. This tells a two-part story:

1. **The data present was accurate.** The re-engineering team did not introduce new inconsistencies by fixing the missing values. Every reconstructed value conforms to the same rules verified in the original data. This is evidence of careful, disciplined re-engineering.

2. **The problem was not corruption — it was incompleteness.** A viewer who understands this panel will grasp the nature of the data quality problem correctly: the issue was not that values were wrong, it was that values were absent. This distinction matters for the advocacy message — it shows that the re-engineering was targeted and appropriate, not a blanket overwrite of questionable data.

**Why this panel matters for advocacy:** It defends the quality of the re-engineering work itself. Stakeholders who might worry that "fixing" data means distorting it can see that no accuracy was compromised. The team improved completeness without degrading correctness.

---

### Panel 4 — Professional Values Upheld

**What it shows:** Four colour-coded boxes, each naming a professional value and describing how it was upheld during the re-engineering process:

| Value | Colour | Description shown |
|---|---|---|
| **Data Quality** | Blue | Arithmetic reconstruction recovers missing prices, quantities, totals |
| **Integrity** | Green | All imputation strategies logged in metadata.json — fully auditable |
| **Responsibility** | Amber | Discount status left nullable: unknown ≠ False |
| **Ethical Use** | Purple | No re-identification attempted; imputed records flagged for analysts |

**What it communicates:** Re-engineering is not just a technical task — it is a professional act. The choice to document every decision, to preserve unknowns as unknowns, and to flag imputed values for downstream analysts reflects a commitment to values that go beyond getting the numbers right. It reflects a commitment to doing the work honestly.

The amber box — `Responsibility: unknown ≠ False` — is the most important advocacy statement in the entire infographic. It captures, in five words, the central ethical decision of the entire project. It would have been easier to impute `False`. It would have made the dataset appear more complete. It would also have been wrong. The infographic makes that choice visible and names it as an act of professional responsibility.

**Why this panel matters for advocacy:** It shifts the conversation from "what was fixed" to "why it was fixed this way." Values-based advocacy is more persuasive and more durable than numbers-based advocacy. Anyone can present a before-and-after table. It takes genuine professional reflection to present the values that shaped every decision in between.

---

## 3. Why the Infographic Works as an Advocacy Artefact

An effective advocacy artefact must do three things:

**1. Make the problem visible**
Panel 1 (missing values) and Panel 3 (consistency checks) make the starting condition of the dataset concrete and immediately understandable. The tall red bars in Panel 1 are the problem. They are hard to ignore.

**2. Make the solution credible**
The green bars reaching zero in Panel 1 and the unchanged zeros in Panel 3 make the solution credible. The re-engineering did not overclaim. It fixed what could be fixed, maintained what was already correct, and preserved what could not be determined. A solution that admits its limits is more credible than one that appears to solve everything.

**3. Make the values explicit**
Panel 4 names the values behind the work. This is what separates advocacy from reporting. A report shows what happened. An advocacy artefact argues why it matters and who it is for. The professional values panel makes that argument — to business stakeholders, to data governance teams, to future analysts who will use this data.

The infographic does all three on a single page, in a format that works in a presentation, a printed handout, or an email attachment.

---

## 4. Group Reflection — How Our Attitude Toward Data Quality Evolved

### Where We Started

At the beginning of this project, the approach to data quality was largely reactive: find the missing values, fill them in, and consider the job done. A dataset with no duplicate rows and no format errors seemed like a good dataset. The work seemed straightforward.

That assumption did not survive the profiling stage.

### What the Profiling Stage Revealed

The completeness analysis showed that 33.4% of discount statuses were unknown — a figure that only becomes visible when you look at it directly. A standard data load would have silently ignored those nulls. No error would have been raised. No warning would have appeared. The analysis would have proceeded on 66.6% of the data, and the other third would have simply vanished from every summary statistic.

The consistency analysis revealed that `(Category, Price Per Unit)` maps deterministically to `Item` — a rule embedded in the data that no column header, data dictionary, or schema definition mentioned. Finding that rule required looking at the relationships between fields, not just the values within them. It changed 1,213 missing item values from an unrecoverable gap into a lookup operation.

The duplicate analysis found nothing — but finding nothing required proving it. The absence of duplicates is not an assumption. It is a verified result. That distinction, once understood, changes how you approach every data quality check: you do not assume a clean result and move on. You verify the clean result and document it.

### The Shift in Thinking

The most significant shift was from thinking about data quality as a list of problems to fix, to thinking about it as a set of responsibilities to uphold.

The decision not to impute `Discount Applied` as `False` is the clearest example of this shift. Before this project, the instinct would have been to complete the field — to fill every gap and produce a dataset with no missing values. After this project, the instinct is to ask: *what does this value mean, and what are the consequences of giving it a value it does not have?*

Imputing `False` for 4,199 unknown discount statuses would have made the dataset look better. It would have made the discount rate appear lower than it actually is. It would have misled every promotional analysis built on top of it. And it would have done all of this silently — with no warning, no footnote, and no way for the analyst to know.

Choosing `<NA>` instead of `False` is a small technical decision with a large ethical implication: it means the dataset tells the truth about what it does not know. That is the standard we now hold data quality work to.

### The Role of Documentation

Before this project, documentation felt like an administrative overhead — something done after the real work was finished. After this project, documentation is understood as part of the work itself.

`metadata.json` is not a byproduct of the re-engineering pipeline. It is the audit trail that makes the re-engineering trustworthy. Every imputation strategy, every reconstruction count, every column renamed — all of it is recorded and traceable. A future analyst who questions why a quantity value is 10 can find the answer. A future auditor who asks how `total_spent` was calculated for a specific row can verify it. Without that record, the re-engineering decisions are invisible and unverifiable — which means they cannot be trusted.

Data quality without documentation is not data quality. It is just undisclosed manipulation.

### What We Would Do Differently

With the perspective gained from this project, there is one thing we would do differently from the very beginning: **treat the root cause as part of the scope.**

The 609 transactions with all financial fields missing together are not a data problem. They are evidence of a POS system failure. Re-engineering addressed the data — but the system failure that produced the gap will continue producing it in every future export unless someone fixes it at the source.

A data quality project that profiles, re-engineers, and documents without reporting the root cause to the people who can fix it has only done half the job. The other half is communication — making sure the findings reach the teams responsible for data collection, system maintenance, and operational process design.

Data quality is not a project with a start and an end date. It is an ongoing professional commitment.

---

## 5. Final Advocacy Statement

> Data is the foundation of every decision an organisation makes.
> A flawed foundation does not announce itself.
> It hides in revenue totals, performance evaluations, promotional strategies, and inventory plans — until a decision built on it fails.
>
> Re-engineering this dataset recovered over £55,000 in unrecorded revenue, restored identity to 1,213 invisible transactions, and gave 604 employees' sales a complete and accurate record for the first time.
>
> But the most important thing re-engineering did was make the data honest.
> It kept the 4,199 unknown discount values unknown, rather than filling them with a convenient fiction.
> It documented every assumption, so that every future analyst knows exactly what they are working with.
> It retained every transaction record, so that no customer interaction was silently erased.
>
> Data quality is not about making data look clean.
> It is about making data tell the truth.
> That is the standard every data professional must hold themselves to — because the people whose work, whose purchases, and whose business decisions depend on this data deserve nothing less.
