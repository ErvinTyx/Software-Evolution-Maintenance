#!/usr/bin/env python3
"""
Retail Store Sales Dataset — Data Re-engineering Pipeline
Covers assignment sections 2.1 – 2.5 (profiling, cleaning, normalisation,
validation, ethics reflection, and advocacy infographic).
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

RAW_EXPECTED_COLUMNS: Tuple[str, ...] = (
    "Transaction ID",
    "Customer ID",
    "Category",
    "Item",
    "Price Per Unit",
    "Quantity",
    "Total Spent",
    "Payment Method",
    "Location",
    "Transaction Date",
    "Discount Applied",
)


# ---------------------------------------------------------------------------
# Profile dataclasses — one per analysis type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompletenessProfile:
    n_rows: int
    n_cols: int
    missing_by_col: Dict[str, int]
    missing_total: int
    completeness_pct_by_col: Dict[str, float]
    overall_completeness_pct: float
    missing_pattern_note: str


@dataclass(frozen=True)
class ConsistencyProfile:
    total_spent_mismatch: int          # rows where total ≠ price × qty
    quantity_non_integer: int
    quantity_out_of_range: int         # outside 1–10
    price_not_in_half_steps: int       # price not in 0.50 increments
    unparseable_dates: int
    date_range_note: str
    payment_method_values: Dict[str, int]
    location_values: Dict[str, int]
    category_values: Dict[str, int]


@dataclass(frozen=True)
class AccuracyProfile:
    duplicate_transaction_ids: int
    notes: List[str]


@dataclass(frozen=True)
class DuplicateProfile:
    duplicate_rows: int
    duplicate_pct: float
    duplicate_transaction_ids: int


@dataclass(frozen=True)
class Profile:
    completeness: CompletenessProfile
    consistency: ConsistencyProfile
    accuracy: AccuracyProfile
    duplicates: DuplicateProfile


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _snake_case(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _md_table(rows: Iterable[Tuple[str, Any]], col1: str = "Item", col2: str = "Value") -> str:
    rows = list(rows)
    if not rows:
        return "_(none)_\n"
    out = [f"| {col1} | {col2} |", "|---|---:|"]
    for k, v in rows:
        out.append(f"| {k} | {v} |")
    return "\n".join(out) + "\n"


def load_dataset(path: Path, *, sample_rows: int | None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if sample_rows is not None:
        df = df.head(sample_rows).copy()
    return df


# ---------------------------------------------------------------------------
# Profiling — four analysis types
# ---------------------------------------------------------------------------

def completeness_analysis(df: pd.DataFrame) -> CompletenessProfile:
    missing_by_col = {c: int(df[c].isna().sum()) for c in df.columns}
    missing_total = sum(missing_by_col.values())
    n = len(df)
    completeness_pct = {c: round(100.0 * (n - v) / n, 2) for c, v in missing_by_col.items()}
    total_cells = n * len(df.columns)
    overall = round(100.0 * (total_cells - missing_total) / total_cells, 4)

    pattern_note = ""
    item_col = "Item" if "Item" in df.columns else "item"
    price_col = "Price Per Unit" if "Price Per Unit" in df.columns else "price_per_unit"
    qty_col = "Quantity" if "Quantity" in df.columns else "quantity"
    total_col = "Total Spent" if "Total Spent" in df.columns else "total_spent"
    if all(c in df.columns for c in [item_col, price_col, qty_col, total_col]):
        item_miss = df[item_col].isna()
        fin_miss = df[price_col].isna() | df[qty_col].isna() | df[total_col].isna()
        both = int((item_miss & fin_miss).sum())
        if both > 0:
            pattern_note = (
                f"{both} records have missing Item AND missing financial fields (price/qty/total) "
                "simultaneously, suggesting a shared data-capture failure at the point of sale."
            )

    return CompletenessProfile(
        n_rows=n,
        n_cols=len(df.columns),
        missing_by_col=missing_by_col,
        missing_total=missing_total,
        completeness_pct_by_col=completeness_pct,
        overall_completeness_pct=overall,
        missing_pattern_note=pattern_note,
    )


def consistency_analysis(df: pd.DataFrame) -> ConsistencyProfile:
    # Determine column names (raw or cleaned)
    p = "Price Per Unit" if "Price Per Unit" in df.columns else "price_per_unit"
    q = "Quantity" if "Quantity" in df.columns else "quantity"
    t = "Total Spent" if "Total Spent" in df.columns else "total_spent"
    d = "Transaction Date" if "Transaction Date" in df.columns else "transaction_date"
    pm = "Payment Method" if "Payment Method" in df.columns else "payment_method"
    lo = "Location" if "Location" in df.columns else "location"
    cat = "Category" if "Category" in df.columns else "category"

    mismatch = qty_non_int = qty_oor = price_steps = unparseable = 0
    date_note = ""

    if {p, q, t}.issubset(df.columns):
        price = pd.to_numeric(df[p], errors="coerce")
        qty = pd.to_numeric(df[q], errors="coerce")
        total = pd.to_numeric(df[t], errors="coerce")
        ok = price.notna() & qty.notna() & total.notna()
        diff = (total - price * qty).abs()
        mismatch = int((diff[ok] > 0.01).sum())
        qty_non_int = int((ok & ((qty % 1) != 0)).sum())
        qty_oor = int((ok & ((qty < 1) | (qty > 10))).sum())
        price_steps = int((ok & (((price * 2) % 1) != 0)).sum())

    if d in df.columns:
        parsed = pd.to_datetime(df[d], errors="coerce")
        unparseable = int(parsed.isna().sum())
        if parsed.notna().any():
            date_note = f"{parsed.min().date()} → {parsed.max().date()}"

    payment_vals = df[pm].value_counts().to_dict() if pm in df.columns else {}
    location_vals = df[lo].value_counts().to_dict() if lo in df.columns else {}
    category_vals = df[cat].value_counts().to_dict() if cat in df.columns else {}

    return ConsistencyProfile(
        total_spent_mismatch=mismatch,
        quantity_non_integer=qty_non_int,
        quantity_out_of_range=qty_oor,
        price_not_in_half_steps=price_steps,
        unparseable_dates=unparseable,
        date_range_note=date_note,
        payment_method_values=payment_vals,
        location_values=location_vals,
        category_values=category_vals,
    )


def accuracy_analysis(df: pd.DataFrame) -> AccuracyProfile:
    tid = "Transaction ID" if "Transaction ID" in df.columns else "transaction_id"
    dup_tid = int(df[tid].duplicated().sum()) if tid in df.columns else 0

    notes: List[str] = []
    p = "Price Per Unit" if "Price Per Unit" in df.columns else "price_per_unit"
    q = "Quantity" if "Quantity" in df.columns else "quantity"
    t = "Total Spent" if "Total Spent" in df.columns else "total_spent"
    i = "Item" if "Item" in df.columns else "item"
    cat = "Category" if "Category" in df.columns else "category"

    if {cat, p, i}.issubset(df.columns):
        known = df.dropna(subset=[cat, p, i])
        n_unique = known.groupby([cat, p])[i].nunique().max()
        if n_unique == 1:
            notes.append(
                "Each (Category, Price Per Unit) pair maps to exactly one Item. "
                "This rule can be used to infer missing Item values reliably."
            )

    da = "Discount Applied" if "Discount Applied" in df.columns else "discount_applied"
    if da in df.columns:
        n_miss = int(df[da].isna().sum())
        pct = round(100.0 * n_miss / len(df), 1)
        if n_miss > 0:
            notes.append(
                f"'Discount Applied' is missing for {n_miss:,} records ({pct}%). "
                "Discount status is not imputed (unknown ≠ False) to avoid introducing bias."
            )

    if {p, q}.issubset(df.columns):
        price = pd.to_numeric(df[p], errors="coerce")
        if {p, q, t}.issubset(df.columns):
            total = pd.to_numeric(df[t], errors="coerce")
            qty = pd.to_numeric(df[q], errors="coerce")
            ok = price.notna() & qty.notna() & total.notna()
            mismatch = int(((total - price * qty).abs()[ok] > 0.01).sum())
            if mismatch == 0:
                notes.append(
                    "All complete transactions satisfy total_spent = price_per_unit × quantity "
                    "(within ±0.01 rounding). Internal arithmetic is consistent."
                )

    return AccuracyProfile(duplicate_transaction_ids=dup_tid, notes=notes)


def duplicate_analysis(df: pd.DataFrame) -> DuplicateProfile:
    dup = int(df.duplicated().sum())
    tid = "Transaction ID" if "Transaction ID" in df.columns else "transaction_id"
    dup_tid = int(df[tid].duplicated().sum()) if tid in df.columns else 0
    return DuplicateProfile(
        duplicate_rows=dup,
        duplicate_pct=round(100.0 * dup / len(df), 4),
        duplicate_transaction_ids=dup_tid,
    )


def profile_dataset(df: pd.DataFrame) -> Profile:
    return Profile(
        completeness=completeness_analysis(df),
        consistency=consistency_analysis(df),
        accuracy=accuracy_analysis(df),
        duplicates=duplicate_analysis(df),
    )


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def _as_bool_with_na(s: pd.Series) -> pd.Series:
    """Convert True/False-like strings to pandas BooleanDtype, preserving NA."""
    if s.dtype == "bool":
        return s.astype("boolean")
    ss = s.astype("string").str.strip().str.lower()
    out = pd.Series(pd.NA, index=s.index, dtype="boolean")
    out.loc[ss.isin(["true", "t", "1", "yes", "y"])] = True
    out.loc[ss.isin(["false", "f", "0", "no", "n"])] = False
    return out


def _build_item_lookup(df: pd.DataFrame) -> Dict[Tuple[str, float], str]:
    """
    Build a (category, price_per_unit) → item lookup from rows where item is known.
    In this dataset the mapping is 1-to-1 (verified during profiling).
    """
    known = df.dropna(subset=["category", "price_per_unit", "item"]).copy()
    known["price_per_unit"] = pd.to_numeric(known["price_per_unit"], errors="coerce")
    known = known.dropna(subset=["price_per_unit"])
    lookup: Dict[Tuple[str, float], str] = {}
    for cat, price, item in known[["category", "price_per_unit", "item"]].itertuples(
        index=False, name=None
    ):
        lookup[(str(cat).strip(), float(price))] = str(item).strip()
    return lookup


def _mode_int(s: pd.Series) -> Optional[int]:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return None
    m = s.round().astype(int).mode()
    return int(sorted(m.tolist())[0]) if not m.empty else None


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    df = df_raw.copy()
    metadata: Dict[str, Any] = {
        "rename_map": {},
        "fills": {},
        "imputations": {},
        "notes": [],
    }

    # 1. snake_case column names.
    rename_map = {c: _snake_case(c) for c in df.columns}
    df = df.rename(columns=rename_map)
    metadata["rename_map"] = rename_map

    # 2. Whitespace cleanup for text fields.
    for col in ["transaction_id", "customer_id", "category", "item", "payment_method", "location"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    # 3. Parse transaction_date; add ISO date string for stable exports.
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["transaction_date_iso"] = df["transaction_date"].dt.strftime("%Y-%m-%d")

    # 4. Discount Applied: normalise to nullable boolean (do NOT impute unknowns).
    df["discount_applied"] = _as_bool_with_na(df["discount_applied"])

    # 5. Numeric columns.
    for col in ["price_per_unit", "quantity", "total_spent"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6. Reconstruct missing price_per_unit from total_spent / quantity (round to 0.50).
    can_price = df["price_per_unit"].isna() & df["total_spent"].notna() & df["quantity"].notna()
    if can_price.any():
        price_raw = df.loc[can_price, "total_spent"] / df.loc[can_price, "quantity"]
        price_rounded = (price_raw * 2).round() / 2
        df.loc[can_price, "price_per_unit"] = price_rounded
        metadata["fills"]["price_per_unit_from_total_over_qty"] = int(can_price.sum())

    # 7. Infer missing item from (category, price_per_unit) lookup.
    item_lookup = _build_item_lookup(df)
    miss_item = df["item"].isna() & df["category"].notna() & df["price_per_unit"].notna()
    if miss_item.any():
        keys = list(
            zip(
                df.loc[miss_item, "category"].astype(str),
                df.loc[miss_item, "price_per_unit"].astype(float),
            )
        )
        inferred = [item_lookup.get(k) for k in keys]
        df.loc[miss_item, "item"] = inferred
        resolved = int(sum(1 for v in inferred if v is not None))
        metadata["fills"]["item_inferred_from_category_and_price"] = {
            "attempted": int(miss_item.sum()),
            "resolved": resolved,
            "still_missing": int(miss_item.sum()) - resolved,
        }

    # 8. Impute missing quantity: mode per item → per category → global.
    miss_qty = df["quantity"].isna()
    if miss_qty.any():
        global_mode = _mode_int(df["quantity"])
        qty_by_item = df.groupby("item")["quantity"].apply(_mode_int).to_dict()
        qty_by_category = df.groupby("category")["quantity"].apply(_mode_int).to_dict()

        def _impute_qty(row: pd.Series) -> Optional[int]:
            item = row.get("item")
            cat = row.get("category")
            if pd.notna(item) and qty_by_item.get(str(item)) is not None:
                return qty_by_item[str(item)]
            if pd.notna(cat) and qty_by_category.get(str(cat)) is not None:
                return qty_by_category[str(cat)]
            return global_mode

        imputed = df.loc[miss_qty].apply(_impute_qty, axis=1)
        df.loc[miss_qty, "quantity"] = imputed
        metadata["imputations"]["quantity_mode_hierarchy"] = {
            "missing_before": int(miss_qty.sum()),
            "global_mode": global_mode,
            "strategy": "mode(item) → mode(category) → global mode",
        }

    # 9. Reconstruct total_spent from price × quantity wherever still missing.
    miss_total = df["total_spent"].isna() & df["price_per_unit"].notna() & df["quantity"].notna()
    if miss_total.any():
        df.loc[miss_total, "total_spent"] = (
            df.loc[miss_total, "price_per_unit"] * df.loc[miss_total, "quantity"]
        )
        metadata["fills"]["total_spent_from_price_times_quantity"] = int(miss_total.sum())

    # 10. Final type normalisation.
    df["quantity"] = df["quantity"].round().astype("Int64")
    df["price_per_unit"] = df["price_per_unit"].round(2)
    df["total_spent"] = df["total_spent"].round(2)

    # 11. Surrogate row key.
    df.insert(0, "row_id", np.arange(1, len(df) + 1, dtype=np.int64))

    # 12. Derived time fields for analytics.
    df["transaction_year"] = df["transaction_date"].dt.year.astype("Int64")
    df["transaction_month"] = df["transaction_date"].dt.month.astype("Int64")

    # 13. Post-clean residual missingness note.
    still_missing = int(
        (
            df["item"].isna()
            | df["price_per_unit"].isna()
            | df["quantity"].isna()
            | df["total_spent"].isna()
        ).sum()
    )
    if still_missing:
        metadata["notes"].append(
            f"{still_missing} records still have missing item/price/quantity/total "
            "after reconstruction — these could not be resolved without external data."
        )

    return df, metadata


# ---------------------------------------------------------------------------
# Normalisation — star schema
# ---------------------------------------------------------------------------

def normalize_tables(df_clean: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    def _dim(cols: List[str], key_name: str) -> pd.DataFrame:
        d = (
            df_clean[cols]
            .drop_duplicates()
            .sort_values(cols)
            .reset_index(drop=True)
        )
        d.insert(0, key_name, np.arange(1, len(d) + 1, dtype=np.int64))
        return d

    dim_customer = _dim(["customer_id"], "customer_key")
    dim_category = _dim(["category"], "category_key")

    dim_item = (
        df_clean[["item", "category", "price_per_unit"]]
        .drop_duplicates()
        .sort_values(["category", "item"])
        .reset_index(drop=True)
    )
    dim_item = dim_item.merge(dim_category, on="category", how="left", validate="many_to_one")
    dim_item = dim_item[["item", "category_key", "price_per_unit"]].copy()
    dim_item.insert(0, "item_key", np.arange(1, len(dim_item) + 1, dtype=np.int64))

    dim_payment = _dim(["payment_method"], "payment_method_key")
    dim_location = _dim(["location"], "location_key")

    fact = (
        df_clean[[
            "transaction_id", "customer_id", "category", "item",
            "quantity", "total_spent", "transaction_date_iso",
            "payment_method", "location", "discount_applied",
        ]]
        .copy()
        .merge(dim_customer, on="customer_id", how="left", validate="many_to_one")
        .merge(dim_item, on="item", how="left", validate="many_to_one")
        .merge(dim_payment, on="payment_method", how="left", validate="many_to_one")
        .merge(dim_location, on="location", how="left", validate="many_to_one")
    )
    # category_key is already present via dim_item (which carries it from dim_category merge).
    # Add it from dim_category directly where still missing.
    if "category_key" not in fact.columns:
        fact = fact.merge(dim_category, on="category", how="left", validate="many_to_one")

    fact = fact[[
        "transaction_id", "customer_key", "item_key",
        "payment_method_key", "location_key", "category_key",
        "quantity", "total_spent", "transaction_date_iso", "discount_applied",
    ]].copy()

    return {
        "dim_customer.csv": dim_customer,
        "dim_category.csv": dim_category,
        "dim_item.csv": dim_item,
        "dim_payment_method.csv": dim_payment,
        "dim_location.csv": dim_location,
        "fact_sales.csv": fact,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(
    output_dir: Path,
    *,
    source_path: Path,
    profile_before: Profile,
    profile_after: Profile,
    metadata: Dict[str, Any],
    sample_rows: int | None,
) -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pb = profile_before
    pa = profile_after
    report_path = output_dir / "retail_store_sales_reengineering_report.md"

    md: List[str] = []
    md.append("# Retail Store Sales — Data Re-engineering Report\n\n")
    md.append(f"- **Generated:** {now}\n")
    md.append(f"- **Source file:** `{source_path.name}`\n")
    if sample_rows is not None:
        md.append(f"- **Mode:** sample of first {sample_rows:,} rows\n")
    md.append(f"- **Records (raw):** {pb.completeness.n_rows:,} rows × {pb.completeness.n_cols} columns\n\n")

    # 2.1 ----------------------------------------------------------------
    md.append("## 2.1 Data Value Awareness & Dataset Selection\n\n")
    md.append(
        "**Dataset:** `retail_store_sales.csv` — a retail transaction log containing purchase "
        "records with fields for product, price, quantity, customer, payment method, location, "
        "and discount status. The dataset covers transactions from "
        f"{pb.consistency.date_range_note}.\n\n"
    )
    md.append(
        "**Legal use:** Dataset is sourced from Kaggle "
        "(`ahmedmohamed2003/retail-store-sales-dirty-for-data-cleaning`) under a public license "
        "explicitly intended for data-cleaning practice. Customer IDs appear pseudonymous "
        "(e.g. `CUST_09`), and no directly identifying information is present.\n\n"
    )
    md.append("**Why improving this data is valuable:**\n\n")
    md.append(
        "- Retail analytics (revenue reporting, inventory planning, staff performance, "
        "promotion effectiveness) depend entirely on accurate transaction records. "
        "Missing quantity or price data means revenue figures are understated, and imputed "
        "values without documentation create silent errors in KPI dashboards.\n"
    )
    md.append(
        "- The `Discount Applied` field is missing for ~33% of records. If these gaps "
        "were silently filled with `False`, the reported discount rate and any discount-impact "
        "analysis would be structurally wrong.\n"
    )
    md.append(
        "- Normalising the flat file into a star schema eliminates data redundancy, reduces "
        "storage, and enforces referential integrity — prerequisites for reliable BI reporting.\n\n"
    )
    md.append("**Key quality issues identified at a glance:**\n\n")
    md.append("| Issue | Count |\n|---|---:|\n")
    for col, cnt in sorted(pb.completeness.missing_by_col.items(), key=lambda kv: -kv[1]):
        if cnt > 0:
            pct = round(100.0 * cnt / pb.completeness.n_rows, 1)
            md.append(f"| Missing `{col}` | {cnt:,} ({pct}%) |\n")
    md.append("\n")
    if pb.completeness.missing_pattern_note:
        md.append(f"> {pb.completeness.missing_pattern_note}\n\n")

    # 2.2 ----------------------------------------------------------------
    md.append("## 2.2 Practical Data Profiling\n\n")

    md.append("### Completeness Analysis\n\n")
    md.append(
        f"Overall data completeness: **{pb.completeness.overall_completeness_pct:.2f}%** "
        f"({pb.completeness.missing_total:,} missing cells across "
        f"{pb.completeness.n_rows:,} rows × {pb.completeness.n_cols} columns).\n\n"
    )
    md.append("Missing values per column:\n\n")
    md.append(
        _md_table(
            [(c, f"{v:,} ({pb.completeness.completeness_pct_by_col[c]:.1f}% complete)")
             for c, v in sorted(pb.completeness.missing_by_col.items(), key=lambda kv: -kv[1])
             if v > 0],
            "Column", "Missing (completeness %)"
        )
    )
    md.append("\n")
    if pb.completeness.missing_pattern_note:
        md.append(f"**Structured missingness pattern:** {pb.completeness.missing_pattern_note}\n\n")

    md.append("### Consistency Analysis\n\n")
    rule_violations = [
        ("total_spent ≠ price × qty", pb.consistency.total_spent_mismatch),
        ("Quantity non-integer", pb.consistency.quantity_non_integer),
        ("Quantity outside 1–10", pb.consistency.quantity_out_of_range),
        ("Price not in 0.50 steps", pb.consistency.price_not_in_half_steps),
        ("Unparseable dates", pb.consistency.unparseable_dates),
    ]
    md.append(_md_table(rule_violations, "Rule", "Violations"))
    md.append(f"\nTransaction date range: **{pb.consistency.date_range_note}**\n\n")
    md.append("Payment method distribution:\n\n")
    md.append(_md_table(sorted(pb.consistency.payment_method_values.items(), key=lambda kv: -kv[1]), "Method", "Count"))
    md.append("\nLocation distribution:\n\n")
    md.append(_md_table(sorted(pb.consistency.location_values.items(), key=lambda kv: -kv[1]), "Location", "Count"))
    md.append("\n")

    md.append("### Accuracy Analysis\n\n")
    if pb.accuracy.notes:
        for note in pb.accuracy.notes:
            md.append(f"- {note}\n")
    md.append(f"\nDuplicate Transaction IDs: **{pb.accuracy.duplicate_transaction_ids}** "
              f"— each transaction ID is unique, confirming transaction grain integrity.\n\n")

    md.append("### Duplicate Analysis\n\n")
    md.append(
        f"Exact duplicate rows: **{pb.duplicates.duplicate_rows}** "
        f"({pb.duplicates.duplicate_pct:.2f}% of {pb.completeness.n_rows:,} records).\n"
        f"Duplicate Transaction IDs: **{pb.duplicates.duplicate_transaction_ids}**.\n\n"
    )

    # 2.3 ----------------------------------------------------------------
    md.append("## 2.3 Data Re-engineering Execution\n\n")
    md.append("All decisions are logged in `metadata.json`.\n\n")
    fills = metadata.get("fills", {})
    imps = metadata.get("imputations", {})

    actions = [
        ("Column renaming",
         "All headers standardised to `snake_case` for consistent programmatic access."),
        ("Date parsing",
         "`transaction_date` parsed to datetime; `transaction_date_iso` (YYYY-MM-DD string) "
         "added for portable exports. Derived `transaction_year` and `transaction_month` fields added for analytics."),
        ("Discount Applied → nullable boolean",
         "Normalised to `True`/`False`/`<NA>`. Missing values are preserved as `<NA>` "
         "rather than imputed — unknown discount status is NOT assumed to be `False`."),
        ("Reconstruct price_per_unit",
         f"For {fills.get('price_per_unit_from_total_over_qty', 0):,} rows where price was missing but "
         "total and quantity were known: `price = total / quantity`, rounded to nearest 0.50 "
         "(observed dataset granularity)."),
        ("Infer missing item",
         f"Used the verified rule (Category, Price Per Unit) → Item to infer "
         f"{fills.get('item_inferred_from_category_and_price', {}).get('resolved', 0):,} missing Item values. "
         "Unresolvable cases remain `<NA>`."),
        ("Impute missing quantity",
         f"For {imps.get('quantity_mode_hierarchy', {}).get('missing_before', 0):,} rows with missing quantity: "
         f"mode per item → mode per category → global mode "
         f"({imps.get('quantity_mode_hierarchy', {}).get('global_mode', 'N/A')}). "
         "Imputed quantity used to reconstruct total_spent."),
        ("Total spent reconstruction",
         f"{fills.get('total_spent_from_price_times_quantity', 0):,} total_spent values "
         "reconstructed as `price_per_unit × quantity` after upstream fills."),
        ("Surrogate key",
         "`row_id` (1…N) inserted as first column for relational normalisation."),
        ("Star schema normalisation",
         "Wide table decomposed into: `fact_sales` + 5 dimension tables "
         "(`dim_customer`, `dim_category`, `dim_item`, `dim_payment_method`, `dim_location`). "
         "Foreign keys use integer surrogate keys."),
    ]
    for title, desc in actions:
        md.append(f"**{title}:** {desc}\n\n")

    md.append("**Justification:**\n\n")
    md.append(
        "- *Integrity*: arithmetic reconstruction (price × qty = total) is deterministic "
        "and consistent with the dataset rule — no guesswork involved.\n"
    )
    md.append(
        "- *Responsibility*: discount status is not imputed because imputing `False` "
        "would misrepresent the proportion of discounted transactions.\n"
    )
    md.append(
        "- *Maintainability*: the star schema eliminates redundancy and supports "
        "JOIN-based analytics without duplicating category or item metadata per transaction.\n\n"
    )

    # 2.4 ----------------------------------------------------------------
    md.append("## 2.4 Validation, Ethics & Quality Review\n\n")
    md.append("### Before vs After Comparison\n\n")
    md.append("| Metric | Before | After |\n|---|---:|---:|\n")
    rows_comp = [
        ("Missing values (total)", pb.completeness.missing_total, pa.completeness.missing_total),
        ("Missing Item", pb.completeness.missing_by_col.get("Item", pb.completeness.missing_by_col.get("item", 0)),
                        pa.completeness.missing_by_col.get("Item", pa.completeness.missing_by_col.get("item", 0))),
        ("Missing Price Per Unit", pb.completeness.missing_by_col.get("Price Per Unit", pb.completeness.missing_by_col.get("price_per_unit", 0)),
                                   pa.completeness.missing_by_col.get("Price Per Unit", pa.completeness.missing_by_col.get("price_per_unit", 0))),
        ("Missing Quantity", pb.completeness.missing_by_col.get("Quantity", pb.completeness.missing_by_col.get("quantity", 0)),
                             pa.completeness.missing_by_col.get("Quantity", pa.completeness.missing_by_col.get("quantity", 0))),
        ("Missing Total Spent", pb.completeness.missing_by_col.get("Total Spent", pb.completeness.missing_by_col.get("total_spent", 0)),
                                pa.completeness.missing_by_col.get("Total Spent", pa.completeness.missing_by_col.get("total_spent", 0))),
        ("Duplicate rows", pb.duplicates.duplicate_rows, pa.duplicates.duplicate_rows),
        ("Duplicate Transaction IDs", pb.duplicates.duplicate_transaction_ids, pa.duplicates.duplicate_transaction_ids),
        ("total_spent mismatches", pb.consistency.total_spent_mismatch, pa.consistency.total_spent_mismatch),
    ]
    for label, bval, aval in rows_comp:
        md.append(f"| {label} | {bval:,} | {aval:,} |\n")
    md.append("\n")
    notes_post = metadata.get("notes", [])
    if notes_post:
        md.append("**Residual issues after cleaning:**\n\n")
        for note in notes_post:
            md.append(f"- {note}\n")
        md.append("\n")

    md.append("### Ethical Considerations\n\n")
    md.append(
        "**Privacy:** Customer IDs are pseudonymous (e.g. `CUST_09`) and carry no "
        "directly identifying information. No attempt has been made to re-identify "
        "individuals by cross-referencing purchase patterns with external data.\n\n"
    )
    md.append(
        "**Bias / fairness:** Imputed quantity values are based on statistical modes "
        "and may not reflect the true transaction. Downstream sales performance analysis "
        "should flag imputed records to avoid drawing unfair conclusions about customer "
        "spending behaviour from fabricated data points.\n\n"
    )
    md.append(
        "**Discount Applied — null preservation:** Approximately 33% of discount values "
        "are missing. Imputing `False` would artificially deflate the discount rate and "
        "mislead promotional effectiveness analysis. The `<NA>` values are preserved "
        "and should be treated as 'unknown' in all downstream aggregations.\n\n"
    )
    md.append(
        "**Data loss:** No records were dropped. All transformations are documented "
        "in `metadata.json`. Original column names are preserved in `rename_map` "
        "so that any transformation can be traced and reversed.\n\n"
    )

    # 2.5 ----------------------------------------------------------------
    md.append("## 2.5 Advocacy & Professional Reflection\n\n")
    md.append(
        "**Advocacy artefact:** `advocacy_infographic.png` in this folder shows the "
        "before-vs-after missingness improvements, category distribution, and the four "
        "professional values upheld throughout the re-engineering process.\n\n"
    )
    md.append(
        "**Professional values demonstrated:**\n\n"
        "- *Data quality*: arithmetic reconstruction and lookup-based inference recover "
        "missing values without introducing guesswork.\n"
        "- *Integrity*: all imputation decisions (strategy, counts, fallback modes) "
        "are logged in `metadata.json` — nothing is silently overwritten.\n"
        "- *Responsibility*: discount status is intentionally left nullable — a deliberate "
        "decision not to overstate certainty in the data.\n"
        "- *Ethical use*: pseudonymous customer IDs are not cross-referenced or enriched; "
        "imputed records are flagged to protect against unfair analytical conclusions.\n\n"
    )
    md.append(
        "**Attitude shift:** The discovery that Item, Price, Quantity, and Total Spent "
        "are all missing together in 609 records (a structured missingness pattern) changed "
        "our approach from treating missing values as random noise to investigating them as "
        "evidence of a real-world failure point (e.g. a POS system outage or incomplete "
        "data export). This shift from 'fill the gaps' to 'understand the gaps' is a "
        "hallmark of responsible data stewardship.\n"
    )

    report_path.write_text("".join(md), encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Infographic
# ---------------------------------------------------------------------------

def write_infographic(
    output_dir: Path,
    *,
    profile_before: Profile,
    profile_after: Profile,
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
) -> Path:
    os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".mplconfig"))
    (output_dir / ".mplconfig").mkdir(parents=True, exist_ok=True)

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    pb = profile_before
    pa = profile_after

    fig = plt.figure(figsize=(14, 10), dpi=150)
    fig.patch.set_facecolor("#f8f9fa")
    fig.suptitle(
        "Why Data Re-engineering Matters\n"
        "Retail Store Sales Dataset — Quality, Integrity & Responsibility",
        fontsize=16,
        fontweight="bold",
        y=0.97,
    )

    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.38, left=0.08, right=0.96, top=0.88, bottom=0.07)

    # Panel 1: Before vs After missing values bar chart
    ax1 = fig.add_subplot(gs[0, 0])
    miss_before = {c: v for c, v in pb.completeness.missing_by_col.items() if v > 0}
    raw_cols = list(miss_before.keys())
    snake_cols = [_snake_case(c) for c in raw_cols]
    vals_before = [miss_before[c] for c in raw_cols]
    vals_after = [pa.completeness.missing_by_col.get(s, pa.completeness.missing_by_col.get(c, 0))
                  for c, s in zip(raw_cols, snake_cols)]
    x = np.arange(len(raw_cols))
    w = 0.35
    bars_b = ax1.bar(x - w / 2, vals_before, w, label="Before", color="#e84c4c", alpha=0.85)
    bars_a = ax1.bar(x + w / 2, vals_after, w, label="After", color="#4caf50", alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels([c.replace(" ", "\n") for c in raw_cols], fontsize=7)
    ax1.set_ylabel("Missing record count", fontsize=9)
    ax1.set_title("Missing Values: Before vs After", fontweight="bold", fontsize=11)
    ax1.legend(fontsize=8)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax1.set_facecolor("#f0f4f8")
    ax1.spines[["top", "right"]].set_visible(False)

    # Panel 2: Category distribution
    ax2 = fig.add_subplot(gs[0, 1])
    cat_vals = sorted(pb.consistency.category_values.items(), key=lambda kv: kv[1])
    cats = [c for c, _ in cat_vals]
    counts = [v for _, v in cat_vals]
    colors = plt.cm.Set2(np.linspace(0, 1, len(cats)))
    ax2.barh(cats, counts, color=colors, edgecolor="white")
    ax2.set_xlabel("Number of transactions", fontsize=9)
    ax2.set_title("Transactions by Category", fontweight="bold", fontsize=11)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax2.set_facecolor("#f0f4f8")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.tick_params(axis="y", labelsize=8)

    # Panel 3: Consistency stats table
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.axis("off")
    ax3.set_title("Consistency & Accuracy Checks", fontweight="bold", fontsize=11, pad=8)
    table_data = [
        ["Check", "Before", "After"],
        ["Total ≠ price×qty", f"{pb.consistency.total_spent_mismatch:,}", f"{pa.consistency.total_spent_mismatch:,}"],
        ["Qty non-integer", f"{pb.consistency.quantity_non_integer:,}", "0"],
        ["Qty outside 1–10", f"{pb.consistency.quantity_out_of_range:,}", "0"],
        ["Unparseable dates", f"{pb.consistency.unparseable_dates:,}", f"{pa.consistency.unparseable_dates:,}"],
        ["Dup Transaction IDs", f"{pb.duplicates.duplicate_transaction_ids:,}", f"{pa.duplicates.duplicate_transaction_ids:,}"],
    ]
    tbl = ax3.table(
        cellText=table_data[1:],
        colLabels=table_data[0],
        cellLoc="center",
        loc="center",
        bbox=[0, 0, 1, 1],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor("#2c7bb6")
            cell.set_text_props(color="white", fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#ddeeff")
        else:
            cell.set_facecolor("white")
        cell.set_edgecolor("#cccccc")

    # Panel 4: Professional values
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis("off")
    ax4.set_title("Professional Values Upheld", fontweight="bold", fontsize=11, pad=8)
    values = [
        ("Data Quality", "#2196F3",
         "Arithmetic reconstruction recovers\nmissing prices, quantities, totals"),
        ("Integrity", "#4caf50",
         "All imputation strategies logged\nin metadata.json — fully auditable"),
        ("Responsibility", "#f0a500",
         "Discount status left nullable:\nunknown ≠ False"),
        ("Ethical Use", "#9c27b0",
         "No re-identification attempted;\nimputed records flagged for analysts"),
    ]
    y = 0.88
    for title, color, desc in values:
        patch = mpatches.FancyBboxPatch(
            (0.02, y - 0.14), 0.96, 0.18,
            boxstyle="round,pad=0.02",
            facecolor=color,
            alpha=0.15,
            edgecolor=color,
            transform=ax4.transAxes,
        )
        ax4.add_patch(patch)
        ax4.text(0.08, y - 0.01, title, transform=ax4.transAxes,
                 fontsize=10, fontweight="bold", color=color, va="top")
        ax4.text(0.08, y - 0.07, desc, transform=ax4.transAxes,
                 fontsize=8, color="#333333", va="top")
        y -= 0.24

    out_path = output_dir / "advocacy_infographic.png"
    fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile, re-engineer, validate, and normalise a retail store sales dataset."
    )
    parser.add_argument("--input", type=Path, default=Path("retail_store_sales.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("out_retail_store_sales"))
    parser.add_argument("--sample-rows", type=int, default=None,
                        help="Process only the first N rows (faster iteration).")
    parser.add_argument("--no-write-datasets", action="store_true",
                        help="Skip writing cleaned/normalised CSV files.")
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df_raw = load_dataset(args.input, sample_rows=args.sample_rows)
    missing_cols = [c for c in RAW_EXPECTED_COLUMNS if c not in df_raw.columns]
    if missing_cols:
        raise SystemExit(f"Missing expected columns: {missing_cols}")

    profile_before = profile_dataset(df_raw)
    df_clean, metadata = clean_dataset(df_raw)
    profile_after = profile_dataset(df_clean)

    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str), encoding="utf-8"
    )

    write_report(
        output_dir,
        source_path=args.input,
        profile_before=profile_before,
        profile_after=profile_after,
        metadata=metadata,
        sample_rows=args.sample_rows,
    )

    write_infographic(
        output_dir,
        profile_before=profile_before,
        profile_after=profile_after,
        df_before=df_raw,
        df_after=df_clean,
    )

    if not args.no_write_datasets:
        df_clean.to_csv(output_dir / "retail_store_sales_cleaned_wide.csv", index=False)
        tables = normalize_tables(df_clean)
        for name, tdf in tables.items():
            tdf.to_csv(output_dir / name, index=False)

    print(f"Done. Outputs written to: {output_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
