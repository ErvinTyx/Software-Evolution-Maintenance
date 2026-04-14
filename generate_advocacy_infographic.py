#!/usr/bin/env python3
"""Generate advocacy infographic: Why Data Re-engineering Matters."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path

OUT = Path("images")
OUT.mkdir(exist_ok=True)

# ── colour palette ────────────────────────────────────────────────────────────
RED    = "#e15759"
BLUE   = "#4e79a7"
GREEN  = "#59a14f"
ORANGE = "#f28e2b"
PURPLE = "#b07aa1"
GREY   = "#9e9e9e"
DARK   = "#2d2d2d"
LIGHT  = "#f5f5f5"

fig = plt.figure(figsize=(20, 26), facecolor=DARK)
fig.patch.set_facecolor(DARK)

# ── title banner ──────────────────────────────────────────────────────────────
title_ax = fig.add_axes([0.0, 0.93, 1.0, 0.07])
title_ax.set_facecolor(BLUE)
title_ax.axis("off")
title_ax.text(0.5, 0.65, "WHY DATA RE-ENGINEERING MATTERS",
              ha="center", va="center", fontsize=28, fontweight="bold",
              color="white", transform=title_ax.transAxes)
title_ax.text(0.5, 0.22, "A data advocacy infographic based on real profiling of transaction.csv  |  10,103 rows · 6 columns",
              ha="center", va="center", fontsize=12, color="#d0e4f7",
              transform=title_ax.transAxes)

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 1 — The Cost of Dirty Data (wrong answers from raw data)
# ─────────────────────────────────────────────────────────────────────────────
ax1 = fig.add_axes([0.04, 0.69, 0.44, 0.22], facecolor="#1e1e1e")
ax1.set_facecolor("#1e1e1e")

ax1.text(0.5, 1.03, "PANEL 1 — The Cost of Dirty Data",
         ha="center", va="bottom", fontsize=13, fontweight="bold",
         color=ORANGE, transform=ax1.transAxes)
ax1.text(0.5, 0.98, "Raw data gives WRONG answers. Without re-engineering:",
         ha="center", va="top", fontsize=10, color=GREY,
         transform=ax1.transAxes)

# Visa undercounting example
brands      = ["Visa\n(raw)", "Visa\n(actual)", "MasterCard\n(raw)", "MasterCard\n(actual)"]
raw_counts  = [2383, 3583, 1461, 3268]
colors_bar  = [RED, GREEN, RED, GREEN]
x = np.arange(len(brands))

bars = ax1.bar(x, raw_counts, color=colors_bar, width=0.55, edgecolor="white", linewidth=0.5)
for bar, v in zip(bars, raw_counts):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 30,
             f"{v:,}", ha="center", va="bottom", fontsize=10,
             color="white", fontweight="bold")

ax1.set_xticks(x)
ax1.set_xticklabels(brands, color="white", fontsize=9)
ax1.set_ylabel("Transaction count", color=GREY, fontsize=9)
ax1.tick_params(colors="white")
ax1.spines[:].set_color(GREY)
ax1.set_facecolor("#1e1e1e")

# annotation arrows
ax1.annotate("", xy=(1, 3583), xytext=(0, 2383),
             arrowprops=dict(arrowstyle="->", color=GREEN, lw=2))
ax1.text(0.5, 3100, "+50%\nundercounted!", ha="center", va="center",
         fontsize=9, color=GREEN, fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#1e1e1e", edgecolor=GREEN))

ax1.annotate("", xy=(3, 3268), xytext=(2, 1461),
             arrowprops=dict(arrowstyle="->", color=GREEN, lw=2))
ax1.text(2.5, 2600, "+124%\nundercounted!", ha="center", va="center",
         fontsize=9, color=GREEN, fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#1e1e1e", edgecolor=GREEN))

red_patch   = mpatches.Patch(color=RED,   label="Raw (wrong)")
green_patch = mpatches.Patch(color=GREEN, label="Actual (after re-engineering)")
ax1.legend(handles=[red_patch, green_patch], loc="upper left",
           facecolor="#1e1e1e", edgecolor=GREY, labelcolor="white", fontsize=8)

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 2 — Tehran: One City, Five Names
# ─────────────────────────────────────────────────────────────────────────────
ax2 = fig.add_axes([0.52, 0.69, 0.44, 0.22], facecolor="#1e1e1e")
ax2.set_facecolor("#1e1e1e")

ax2.text(0.5, 1.03, "PANEL 2 — One City, Five Names",
         ha="center", va="bottom", fontsize=13, fontweight="bold",
         color=ORANGE, transform=ax2.transAxes)
ax2.text(0.5, 0.98, "Tehran was split across 5 variants — invisible without normalisation:",
         ha="center", va="top", fontsize=10, color=GREY,
         transform=ax2.transAxes)

tehran_variants = ["Tehran\n(correct)", "THR\n(IATA code)", "TEHRAN\n(upper)", "tehr@n\n(typo)", "ThRan\n(mixed)"]
tehran_counts   = [2279, 414, 408, 335, 80]
tehran_colors   = [GREEN, RED, RED, RED, RED]

bars2 = ax2.barh(tehran_variants, tehran_counts,
                 color=tehran_colors, edgecolor="white", linewidth=0.5)
for bar, v in zip(bars2, tehran_counts):
    ax2.text(v + 15, bar.get_y() + bar.get_height()/2,
             f"{v:,}", va="center", ha="left", fontsize=10,
             color="white", fontweight="bold")

ax2.set_xlabel("Row count", color=GREY, fontsize=9)
ax2.tick_params(colors="white")
ax2.spines[:].set_color(GREY)
ax2.set_facecolor("#1e1e1e")

total_tehran = sum(tehran_counts)
ax2.text(0.98, 0.05,
         f"Total Tehran transactions:\n{total_tehran:,}  (34.8% of all rows)\n\nWithout normalisation:\nappears as 5 separate cities",
         ha="right", va="bottom", fontsize=9, color=RED,
         transform=ax2.transAxes,
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#2d2d2d", edgecolor=RED))

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 3 — Before vs After: Quality Scorecard
# ─────────────────────────────────────────────────────────────────────────────
ax3 = fig.add_axes([0.04, 0.43, 0.44, 0.23], facecolor="#1e1e1e")
ax3.set_facecolor("#1e1e1e")

ax3.text(0.5, 1.03, "PANEL 3 — Quality Score: Before vs After",
         ha="center", va="bottom", fontsize=13, fontweight="bold",
         color=ORANGE, transform=ax3.transAxes)

dimensions  = ["Completeness", "Consistency", "Accuracy", "Uniqueness", "Validity"]
before_scores = [85, 38, 55, 1, 44]
after_scores  = [83, 100, 90, 100, 88]

x3     = np.arange(len(dimensions))
width3 = 0.35

b3_before = ax3.bar(x3 - width3/2, before_scores, width3,
                    color=RED,   label="Before (raw)",  alpha=0.9,
                    edgecolor="white", linewidth=0.5)
b3_after  = ax3.bar(x3 + width3/2, after_scores,  width3,
                    color=GREEN, label="After (normalised)", alpha=0.9,
                    edgecolor="white", linewidth=0.5)

for bar, v in zip(b3_before, before_scores):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             str(v), ha="center", va="bottom", fontsize=9,
             color=RED, fontweight="bold")
for bar, v in zip(b3_after, after_scores):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             str(v), ha="center", va="bottom", fontsize=9,
             color=GREEN, fontweight="bold")

ax3.set_xticks(x3)
ax3.set_xticklabels(dimensions, color="white", fontsize=9)
ax3.set_ylabel("Score / 100", color=GREY, fontsize=9)
ax3.set_ylim(0, 115)
ax3.tick_params(colors="white")
ax3.spines[:].set_color(GREY)
ax3.set_facecolor("#1e1e1e")
ax3.legend(facecolor="#1e1e1e", edgecolor=GREY, labelcolor="white", fontsize=9,
           loc="upper left")

overall_before = 45
overall_after  = 92
ax3.text(0.98, 0.97,
         f"Overall\n{overall_before}/100  →  {overall_after}/100",
         ha="right", va="top", fontsize=14, fontweight="bold",
         color=GREEN, transform=ax3.transAxes,
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#2d2d2d", edgecolor=GREEN))

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 4 — What Was Fixed (issue count breakdown)
# ─────────────────────────────────────────────────────────────────────────────
ax4 = fig.add_axes([0.52, 0.43, 0.44, 0.23], facecolor="#1e1e1e")
ax4.set_facecolor("#1e1e1e")

ax4.text(0.5, 1.03, "PANEL 4 — Issues Found & Fixed",
         ha="center", va="bottom", fontsize=13, fontweight="bold",
         color=ORANGE, transform=ax4.transAxes)

issues = [
    ("Non-canonical status\n(6 variants → 2)", 2135, GREEN),
    ("Non-canonical card_type\n(11 variants → 4)", 3007, BLUE),
    ("Non-canonical city\n(14 variants → 8)", 1636, PURPLE),
    ("Negative amounts\n(→ absolute value)", 1217, ORANGE),
    ("IQR outlier amounts\n(→ NULL)", 299, RED),
    ("Duplicate ID\n(surrogate key assigned)", 10103, "#76b7b2"),
]

labels4 = [i[0] for i in issues]
counts4 = [i[1] for i in issues]
colors4 = [i[2] for i in issues]

y4 = np.arange(len(labels4))
bars4 = ax4.barh(y4, counts4, color=colors4, edgecolor="white", linewidth=0.5, height=0.6)
for bar, v in zip(bars4, counts4):
    ax4.text(v + 50, bar.get_y() + bar.get_height()/2,
             f"{v:,} rows", va="center", ha="left",
             color="white", fontsize=9, fontweight="bold")

ax4.set_yticks(y4)
ax4.set_yticklabels(labels4, color="white", fontsize=8.5)
ax4.set_xlabel("Rows affected", color=GREY, fontsize=9)
ax4.tick_params(colors="white")
ax4.spines[:].set_color(GREY)
ax4.set_facecolor("#1e1e1e")
ax4.set_xlim(0, 13000)

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 5 — Business Impact: What Wrong Data Costs
# ─────────────────────────────────────────────────────────────────────────────
ax5 = fig.add_axes([0.04, 0.17, 0.44, 0.23], facecolor="#1e1e1e")
ax5.set_facecolor("#1e1e1e")
ax5.axis("off")

ax5.text(0.5, 1.03, "PANEL 5 — Business Impact of Uncleaned Data",
         ha="center", va="bottom", fontsize=13, fontweight="bold",
         color=ORANGE, transform=ax5.transAxes)

impacts = [
    (RED,    "Revenue reporting",
             "Visa transactions undercounted by 1,200 rows (50%).\nMasterCard undercounted by 1,807 rows (124%).\nBrand-level revenue reports are materially wrong."),
    (PURPLE, "Geographic analysis",
             "Tehran fragmented into 5 entries.\nKaraj undercounted by 399 rows (61%).\nCity-level KPIs and branch rankings are unreliable."),
    (ORANGE, "Financial analysis",
             "1,217 negative amounts distort mean, sum, and trend.\n299 sentinel values (9,999,999,999) inflate totals by orders of magnitude."),
    (BLUE,   "Operational queries",
             "100% duplicate IDs make row-level lookups impossible.\nNo transaction can be uniquely referenced or audited."),
]

y_pos = 0.88
for color, title, desc in impacts:
    ax5.add_patch(FancyBboxPatch((0.01, y_pos - 0.17), 0.98, 0.19,
                                  boxstyle="round,pad=0.01",
                                  facecolor="#2a2a2a", edgecolor=color,
                                  linewidth=1.5, transform=ax5.transAxes))
    ax5.text(0.04, y_pos - 0.01, f"■  {title}",
             ha="left", va="top", fontsize=10, fontweight="bold",
             color=color, transform=ax5.transAxes)
    ax5.text(0.06, y_pos - 0.06, desc,
             ha="left", va="top", fontsize=8.5, color="#cccccc",
             transform=ax5.transAxes, linespacing=1.5)
    y_pos -= 0.23

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 6 — The 3-Phase Pipeline
# ─────────────────────────────────────────────────────────────────────────────
ax6 = fig.add_axes([0.52, 0.17, 0.44, 0.23], facecolor="#1e1e1e")
ax6.set_facecolor("#1e1e1e")
ax6.axis("off")

ax6.text(0.5, 1.03, "PANEL 6 — The Re-engineering Pipeline",
         ha="center", va="bottom", fontsize=13, fontweight="bold",
         color=ORANGE, transform=ax6.transAxes)

phases = [
    (BLUE,   "① CLEANSE",
             "Strip whitespace  ·  Null impossible datetimes\n"
             "Null IQR outlier amounts  ·  Preserve partial datetime fragments"),
    (ORANGE, "② TRANSFORM",
             "status: 6 variants → success | failed\n"
             "card_type: 11 variants → 4 canonical brands\n"
             "city: 14 variants → 8 canonical cities\n"
             "amount: text → numeric, negative → absolute, typed as double"),
    (GREEN,  "③ NORMALISE",
             "Split time → date (YYYY-MM-DD) + time (HH:MM:SS)\n"
             "Assign surrogate key TRX_00001 – TRX_10103\n"
             "Decompose: city.csv + card.csv dimension tables\n"
             "Output: data_normalise.csv (fact table)"),
]

y_pos6 = 0.90
for color, title, desc in phases:
    ax6.add_patch(FancyBboxPatch((0.01, y_pos6 - 0.25), 0.98, 0.27,
                                  boxstyle="round,pad=0.01",
                                  facecolor="#2a2a2a", edgecolor=color,
                                  linewidth=2.0, transform=ax6.transAxes))
    ax6.text(0.05, y_pos6 - 0.02, title,
             ha="left", va="top", fontsize=11, fontweight="bold",
             color=color, transform=ax6.transAxes)
    ax6.text(0.05, y_pos6 - 0.09, desc,
             ha="left", va="top", fontsize=8.5, color="#cccccc",
             transform=ax6.transAxes, linespacing=1.6)
    y_pos6 -= 0.31

# ─────────────────────────────────────────────────────────────────────────────
# BOTTOM BANNER — Key Facts
# ─────────────────────────────────────────────────────────────────────────────
banner_ax = fig.add_axes([0.0, 0.08, 1.0, 0.07])
banner_ax.set_facecolor("#1a3a5c")
banner_ax.axis("off")

facts = [
    ("18,297", "cells corrected\nor standardised"),
    ("45 → 92", "quality score\n(out of 100)"),
    ("0", "rows deleted\n(zero data loss)"),
    ("100%", "ID uniqueness\nachieved"),
    ("5 of 6", "columns had\ncritical issues"),
    ("3", "output tables\n(normalised schema)"),
]

x_step = 1.0 / len(facts)
for i, (num, label) in enumerate(facts):
    cx = x_step * i + x_step / 2
    banner_ax.text(cx, 0.72, num,
                   ha="center", va="center", fontsize=18, fontweight="bold",
                   color=GREEN if num not in ("0", "5 of 6") else
                         (GREEN if num == "0" else RED),
                   transform=banner_ax.transAxes)
    banner_ax.text(cx, 0.26, label,
                   ha="center", va="center", fontsize=8.5,
                   color="#aaaaaa", transform=banner_ax.transAxes)

# ─────────────────────────────────────────────────────────────────────────────
# BOTTOM FOOTER — call to action
# ─────────────────────────────────────────────────────────────────────────────
footer_ax = fig.add_axes([0.0, 0.0, 1.0, 0.08])
footer_ax.set_facecolor(DARK)
footer_ax.axis("off")

footer_ax.text(0.5, 0.72,
               "\"Dirty data does not just waste storage — it wastes decisions.\"",
               ha="center", va="center", fontsize=13, style="italic",
               color="#dddddd", transform=footer_ax.transAxes)
footer_ax.text(0.5, 0.30,
               "Data re-engineering is not optional — it is the foundation of every reliable analysis, every fair decision, and every trustworthy report.",
               ha="center", va="center", fontsize=10,
               color=GREY, transform=footer_ax.transAxes)

plt.savefig(OUT / "advocacy_infographic.png", dpi=130,
            bbox_inches="tight", facecolor=DARK)
plt.close()
print("Saved: images/advocacy_infographic.png")
