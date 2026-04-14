#!/usr/bin/env python3
"""Generate and save all profiling charts to images/."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.use("Agg")

OUT = Path("images")
OUT.mkdir(exist_ok=True)

df = pd.read_csv("transaction.csv")

# ── helpers ──────────────────────────────────────────────────────────────────

def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(OUT / name, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"saved {name}")

# ─────────────────────────────────────────────────────────────────────────────
# COMPLETENESS
# ─────────────────────────────────────────────────────────────────────────────

total_rows = len(df)
missing_count = df.isna().sum()
missing_pct   = (missing_count / total_rows * 100).round(2)
complete_count = total_rows - missing_count
complete_pct  = (complete_count / total_rows * 100).round(2)

completeness_table = pd.DataFrame({
    "column": df.columns,
    "missing_count": missing_count.values,
    "missing_pct": missing_pct.values,
    "complete_count": complete_count.values,
    "complete_pct": complete_pct.values,
}).sort_values("missing_count", ascending=False).reset_index(drop=True)

# 1. Missing % bar chart
bar_df = completeness_table.sort_values("missing_pct", ascending=False)
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(bar_df["column"], bar_df["missing_pct"], color="#e15759")
ax.set_title("Missing Percentage by Column")
ax.set_ylabel("Missing %")
ax.set_ylim(0, max(1, float(bar_df["missing_pct"].max()) * 1.25))
ax.tick_params(axis="x", rotation=30)
for bar, v in zip(bars, bar_df["missing_pct"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{v:.2f}%",
            ha="center", va="bottom", fontsize=8)
save("completeness_missing_pct_bar.png")

# 2. Missingness heatmap
missing_matrix = df.isna().astype(int).T.values
fig, ax = plt.subplots(figsize=(14, 4))
im = ax.imshow(missing_matrix, aspect="auto", cmap="Reds", interpolation="nearest")
ax.set_title(f"Missingness Heatmap (all {total_rows} rows)")
ax.set_xlabel("Row index")
ax.set_ylabel("Column")
ax.set_yticks(np.arange(len(df.columns)))
ax.set_yticklabels(df.columns)
plt.colorbar(im, ax=ax).set_label("Missing (1) / Present (0)")
save("completeness_heatmap.png")

# 3. Stacked bar: complete vs missing
cols = completeness_table["column"]
complete = completeness_table["complete_count"]
missing = completeness_table["missing_count"]
x = np.arange(len(cols))

fig, ax = plt.subplots(figsize=(8, 5))
bars_c = ax.bar(x, complete, color="#4e79a7", label="Complete")
bars_m = ax.bar(x, missing, bottom=complete, color="#e15759", label="Missing")
ax.set_title("Complete vs Missing per Column")
ax.set_xticks(x); ax.set_xticklabels(cols, rotation=30, ha="right")
ax.set_ylabel("Row count"); ax.legend()
for bar, m in zip(bars_m, missing):
    if m > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2,
                str(int(m)), ha="center", va="center", fontsize=8, color="white", fontweight="bold")
save("completeness_stacked_bar.png")

# 4. Overall completeness pie
total_cells   = df.shape[0] * df.shape[1]
missing_cells = int(df.isna().sum().sum())
complete_cells = total_cells - missing_cells

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie([complete_cells, missing_cells],
       labels=[f"Complete\n{complete_cells:,}", f"Missing\n{missing_cells:,}"],
       colors=["#4e79a7", "#e15759"], autopct="%1.2f%%", startangle=90,
       wedgeprops={"edgecolor": "white", "linewidth": 1.5})
ax.set_title("Overall Cell Completeness")
save("completeness_pie.png")

# 5. Before/after treatment grouped bar
df_clean = df.copy()
df_clean = df_clean.dropna(subset=["amount", "time"])
df_clean["card_type"] = df_clean["card_type"].fillna("Unknown")
df_clean["city"]      = df_clean["city"].fillna("Unknown")

before   = df.isna().sum()
after    = df_clean.isna().sum()
cols_all = df.columns.tolist()
x2       = np.arange(len(cols_all))
width    = 0.35

fig, ax = plt.subplots(figsize=(8, 5))
bars_b = ax.bar(x2 - width/2, before[cols_all], width, color="#e15759", label="Before")
bars_a = ax.bar(x2 + width/2, after[cols_all],  width, color="#59a14f", label="After")
for bar, val in zip(bars_b, before[cols_all]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            str(int(val)), ha="center", va="bottom", fontsize=8, color="#e15759")
for bar, val in zip(bars_a, after[cols_all]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            str(int(val)), ha="center", va="bottom", fontsize=8, color="#59a14f")
ax.set_title("Missing Count: Before vs After Treatment")
ax.set_xticks(x2); ax.set_xticklabels(cols_all, rotation=30, ha="right")
ax.set_ylabel("Missing count"); ax.legend()
save("completeness_before_after.png")

# ─────────────────────────────────────────────────────────────────────────────
# CONSISTENCY
# ─────────────────────────────────────────────────────────────────────────────

# 6. Status distribution
status_clean = df["status"].astype("string").str.strip()
status_counts = status_clean.value_counts(dropna=False).reset_index()
status_counts.columns = ["status", "count"]

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(status_counts["status"], status_counts["count"],
              color=["#4e79a7","#e15759","#f28e2b","#59a14f","#b07aa1","#76b7b2"])
ax.set_title("Status Column — Distinct Value Distribution")
ax.set_xlabel("Raw Status Value"); ax.set_ylabel("Row Count")
ax.tick_params(axis="x", rotation=20)
for bar, v in zip(bars, status_counts["count"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f"{v:,}", ha="center", va="bottom", fontsize=9)
save("consistency_status_distribution.png")

# 7. Card type distribution
card_clean = df["card_type"].astype("string").str.strip().fillna("<NULL>")
card_counts = card_clean.value_counts().reset_index()
card_counts.columns = ["card_type", "count"]

fig, ax = plt.subplots(figsize=(10, 4))
colors = plt.cm.tab10(np.linspace(0, 1, len(card_counts)))
bars = ax.bar(card_counts["card_type"], card_counts["count"], color=colors)
ax.set_title("card_type Column — Distinct Value Distribution (11 variants → 4 canonical)")
ax.set_xlabel("Raw card_type Value"); ax.set_ylabel("Row Count")
ax.tick_params(axis="x", rotation=40)
for bar, v in zip(bars, card_counts["count"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f"{v:,}", ha="center", va="bottom", fontsize=8)
save("consistency_card_type_distribution.png")

# 8. City distribution
city_clean = df["city"].astype("string").str.strip().fillna("<NULL>")
city_counts = city_clean.value_counts().reset_index()
city_counts.columns = ["city", "count"]

fig, ax = plt.subplots(figsize=(12, 4))
colors = plt.cm.tab20(np.linspace(0, 1, len(city_counts)))
bars = ax.bar(city_counts["city"], city_counts["count"], color=colors)
ax.set_title("city Column — Distinct Value Distribution (14 variants → 8 canonical)")
ax.set_xlabel("Raw City Value"); ax.set_ylabel("Row Count")
ax.tick_params(axis="x", rotation=40)
for bar, v in zip(bars, city_counts["count"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f"{v:,}", ha="center", va="bottom", fontsize=8)
save("consistency_city_distribution.png")

# 9. Amount type distribution
amount_txt = df["amount"].astype("string").str.strip()
amount_num = pd.to_numeric(amount_txt, errors="coerce")
amount_type = pd.Series("non_numeric", index=df.index, dtype="string")
null_mask    = amount_txt.isna() | (amount_txt == "")
amount_type[null_mask] = "NULL"
numeric_mask = amount_num.notna() & ~null_mask
amount_type[numeric_mask & ((amount_num % 1) == 0)] = "integer"
amount_type[numeric_mask & ((amount_num % 1) != 0)] = "decimal"

type_counts = amount_type.value_counts().reset_index()
type_counts.columns = ["type", "count"]

fig, ax = plt.subplots(figsize=(7, 4))
colors_amt = ["#4e79a7", "#f28e2b", "#e15759", "#9e9e9e"]
bars = ax.bar(type_counts["type"], type_counts["count"], color=colors_amt[:len(type_counts)])
ax.set_title("amount Column — Value Type Distribution")
ax.set_xlabel("Amount Type"); ax.set_ylabel("Row Count")
for bar, v in zip(bars, type_counts["count"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f"{v:,}", ha="center", va="bottom", fontsize=9)
save("consistency_amount_type.png")

# ─────────────────────────────────────────────────────────────────────────────
# ACCURACY — Amount
# ─────────────────────────────────────────────────────────────────────────────

one_hundred   = amount_txt.str.lower().eq("one hundred").fillna(False)
amount_fixed  = amount_txt.where(~one_hundred, "100")
amount_num2   = pd.to_numeric(amount_fixed, errors="coerce")
amount_abs    = amount_num2.abs()

null_mask2      = amount_txt.isna() | (amount_txt == "")
non_numeric_mask = amount_num2.isna() & ~null_mask2
valid_mask2     = amount_num2.notna() & (amount_num2 > 0)

amount_status = pd.Series("invalid", index=df.index, dtype="string")
amount_status[null_mask2]  = "NULL"
amount_status[valid_mask2] = "valid"

# 10. Amount accuracy grouped bar
valid_count             = int((amount_status == "valid").sum())
invalid_numeric_count   = int(((amount_num2 < 0) & amount_num2.notna()).sum())
invalid_non_numeric_count = int(non_numeric_mask.sum())

fig, ax = plt.subplots(figsize=(8, 4.8))
x_a = np.arange(2); w = 0.35
b1 = ax.bar(x_a - w/2, [valid_count, invalid_numeric_count],   w, label="Numeric",     color="#4e79a7")
b2 = ax.bar(x_a + w/2, [0, invalid_non_numeric_count],         w, label="Non-numeric", color="#f28e2b")
ax.set_title("Amount Accuracy: Valid vs Invalid")
ax.set_xticks(x_a); ax.set_xticklabels(["Valid", "Invalid"])
ax.set_ylabel("Count"); ax.legend()
for bars in [b1, b2]:
    for b in bars:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2, h, f"{int(h):,}",
                    ha="center", va="bottom", fontsize=9)
save("accuracy_amount_validity.png")

# 11. Amount IQR outlier scatter
positive = amount_abs[(amount_num2.notna()) & (amount_abs > 0)]
q1 = positive.quantile(0.25); q3 = positive.quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outlier_mask2  = amount_num2.notna() & ((amount_abs < lower_bound) | (amount_abs > upper_bound))
non_out_mask   = amount_num2.notna() & ~outlier_mask2

fig, ax = plt.subplots(figsize=(10, 4))
ax.scatter(np.where(non_out_mask)[0], amount_abs[non_out_mask], s=6, alpha=0.5,
           color="#4e79a7", label="Normal")
ax.scatter(np.where(outlier_mask2)[0], amount_abs[outlier_mask2], s=15, alpha=0.8,
           color="#e15759", label=f"Outlier (>{upper_bound:,.0f})")
ax.axhline(upper_bound, color="#e15759", linestyle="--", linewidth=1, label=f"IQR upper = {upper_bound:,.0f}")
ax.set_title("Amount — IQR Outlier Detection")
ax.set_xlabel("Row index"); ax.set_ylabel("Amount (absolute)")
ax.legend(fontsize=8)
save("accuracy_amount_outliers_scatter.png")

# ─────────────────────────────────────────────────────────────────────────────
# ACCURACY — Time
# ─────────────────────────────────────────────────────────────────────────────
import re

time_raw = df["time"].astype("string").str.strip()
null_t   = time_raw.isna() | (time_raw == "")
fmt1_ok  = time_raw.str.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", na=False)
fmt1_parsed = pd.to_datetime(time_raw, format="%Y-%m-%d %H:%M:%S", errors="coerce")
fmt1_valid  = fmt1_ok & fmt1_parsed.notna()
fmt2_ok  = time_raw.str.fullmatch(r"\d{2}:\d{2} \d{4}-\d{2}-\d{2}", na=False)
fmt2_parsed = pd.to_datetime(time_raw, format="%H:%M %Y-%m-%d", errors="coerce")
fmt2_valid  = fmt2_ok & fmt2_parsed.notna()
valid_t  = fmt1_valid | fmt2_valid
impossible_t = (~null_t) & (fmt1_ok | fmt2_ok) & (~valid_t)

dt_status = pd.Series("invalid_format", index=df.index, dtype="string")
dt_status[null_t]       = "NULL"
dt_status[valid_t]      = "valid"
dt_status[impossible_t] = "impossible"

# 12. Time accuracy status bar
time_counts = dt_status.value_counts().reindex(
    ["valid", "impossible", "invalid_format", "NULL"], fill_value=0).reset_index()
time_counts.columns = ["status", "count"]

fig, ax = plt.subplots(figsize=(7, 4))
colors_t = ["#59a14f", "#e15759", "#f28e2b", "#9e9e9e"]
bars = ax.bar(time_counts["status"], time_counts["count"], color=colors_t)
ax.set_title("time Column — Datetime Validity")
ax.set_xlabel("Status"); ax.set_ylabel("Row Count")
for bar, v in zip(bars, time_counts["count"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f"{v:,}", ha="center", va="bottom", fontsize=9)
save("accuracy_time_validity.png")

# ─────────────────────────────────────────────────────────────────────────────
# DUPLICATION
# ─────────────────────────────────────────────────────────────────────────────

id_series    = df["id"].astype("string").str.strip()
null_id      = id_series.isna() | (id_series == "")
non_null_ids = id_series[~null_id]
dup_mask     = non_null_ids.duplicated(keep=False)

rows_dup_id  = int(dup_mask.sum())
rows_uniq_id = int((~dup_mask).sum())
full_row_dup = int(df.duplicated(keep=False).sum())

id_counts   = non_null_ids.value_counts()
uniq_id_n   = int((id_counts == 1).sum())
dup_id_n    = int((id_counts > 1).sum())
top15       = id_counts[id_counts > 1].head(15)

# 13. Row-level duplication bar
fig, ax = plt.subplots(figsize=(8, 4))
labels = ["Rows with\ndupl. ID", "Rows with\nunique ID", "Full-row\nduplicates"]
values = [rows_dup_id, rows_uniq_id, full_row_dup]
colors_d = ["#e15759", "#4e79a7", "#f28e2b"]
bars = ax.bar(labels, values, color=colors_d)
ax.set_title("Row-Level Duplication Summary")
ax.set_ylabel("Row count")
for i, v in enumerate(values):
    ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=9)
save("duplication_row_level.png")

# 14. ID value distribution pie
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie([uniq_id_n, dup_id_n],
       labels=[f"Unique ID values\n{uniq_id_n}", f"Duplicated ID values\n{dup_id_n}"],
       autopct="%1.1f%%", colors=["#59a14f", "#f28e2b"], startangle=90)
ax.set_title("ID Value Distribution")
save("duplication_id_pie.png")

# 15. Top duplicated IDs bar
fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(top15.index.astype(str), top15.values, color="#b07aa1")
ax.set_title("Top 15 Most Duplicated ID Values")
ax.set_ylabel("Occurrence count")
ax.tick_params(axis="x", rotation=45)
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h, f"{int(h)}",
            ha="center", va="bottom", fontsize=8)
save("duplication_top_ids.png")

print("\nAll charts saved to images/")
