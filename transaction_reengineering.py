#!/usr/bin/env python3
"""
Transaction CSV - Data Re-engineering Script

Default: load → cleanse → write data_clean.csv (id first; amount outliers → NULL;
invalid datetimes → text NULL or partial patterns like 'NULL YYYY-MM-DD' / 'HH:MM NULL') →
transform + normalise → write transformed CSV (TRX_* id, preserved id, success|failed,
date YYYY-MM-DD and time HH:MM:SS only, card/city maps, amount double).

Optional --full-pipeline: print quality report and diagnostics.
"""

from __future__ import annotations

import argparse
import calendar
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import pandas as pd

NULL_TOKEN = "NULL"

# Flexible time strings; impossible or incomplete datetimes become null after validation.
_MERIDIEM_SLASH_RE = re.compile(
    r"^\s*(\d{1,2})\s*(am|pm)\s+(\d{4})/(\d{2})/(\d{2})\s*$",
    re.IGNORECASE,
)
_TIME_ONLY_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")
# e.g. 03-00-2025 09-11 -> 2025-09-11 03:00:00 (clock HH-MM-YYYY then month-day)
_HHMM_YYYY_MMDD_RE = re.compile(
    r"^\s*(\d{1,2})-(\d{1,2})-(\d{4})\s+(\d{1,2})-(\d{1,2})\s*$",
)

# First valid calendar date (YYYY-MM-DD or YYYY/MM/DD) in a string; rejects impossible dates.
_DATE_YMD_FRAGMENT_RE = re.compile(r"\b(\d{4})[/-](\d{2})[/-](\d{2})\b")
# Clock fragments; only values that pass hour/minute/second range checks are used.
_TIME_HMS_FRAGMENT_RE = re.compile(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b")

_STRICT_DT_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%H:%M:%S %Y-%m-%d",
    "%H:%M %Y-%m-%d",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
)


def _validate_calendar_timestamp(ts: pd.Timestamp, max_year: int) -> bool:
    """Reject impossible clock values, future years, and invalid calendar dates (incl. leap years)."""
    if pd.isna(ts):
        return False
    if ts.year > max_year or ts.year < 1:
        return False
    if ts.hour > 23 or ts.minute > 59 or ts.second > 59:
        return False
    if ts.month < 1 or ts.month > 12:
        return False
    last_day = calendar.monthrange(ts.year, ts.month)[1]
    if ts.day < 1 or ts.day > last_day:
        return False
    return True


def _parse_meridiem_slash(value: str) -> pd.Timestamp:
    m = _MERIDIEM_SLASH_RE.match(value.strip())
    if not m:
        return pd.NaT
    h = int(m.group(1))
    mer = m.group(2).lower()
    y, mo, d = int(m.group(3)), int(m.group(4)), int(m.group(5))
    if mer == "am":
        if h == 12:
            h = 0
        elif not (1 <= h <= 11):
            return pd.NaT
    else:
        if h == 12:
            pass
        elif 1 <= h <= 11:
            h += 12
        else:
            return pd.NaT
    try:
        return pd.Timestamp(datetime(y, mo, d, h, 0, 0))
    except (ValueError, OverflowError):
        return pd.NaT


def _try_strict_formats(value: str) -> pd.Timestamp:
    for fmt in _STRICT_DT_FORMATS:
        ts = pd.to_datetime(value, format=fmt, errors="coerce")
        if pd.notna(ts):
            return ts
    return pd.NaT


def _parse_hhmm_yyyy_mmdd(value: str, max_year: int) -> pd.Timestamp:
    """Parse '03-00-2025 09-11' as 03:00 on 2025-09-11 (hour-minute-year month-day)."""
    m = _HHMM_YYYY_MMDD_RE.match(value.strip())
    if not m:
        return pd.NaT
    h, mn, y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
    if not (0 <= h <= 23 and 0 <= mn <= 59):
        return pd.NaT
    try:
        ts = pd.Timestamp(datetime(y, mo, d, h, mn, 0))
    except (ValueError, OverflowError):
        return pd.NaT
    return ts if _validate_calendar_timestamp(ts, max_year) else pd.NaT


def parse_transaction_datetime(value: object, max_year: int | None = None) -> pd.Timestamp:
    """Parse mixed time formats; return NaT if unparseable or invalid (e.g. 99:99, 2025-13-40, time-only)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    cap = max_year if max_year is not None else datetime.now().year

    if _TIME_ONLY_RE.fullmatch(text):
        return pd.NaT

    ts = _parse_hhmm_yyyy_mmdd(text, cap)
    if pd.isna(ts):
        ts = _parse_meridiem_slash(text)
    if pd.isna(ts):
        ts = _try_strict_formats(text)
    if pd.isna(ts):
        return pd.NaT
    if not _validate_calendar_timestamp(ts, cap):
        return pd.NaT
    return ts


def parse_transaction_datetime_series(s: pd.Series, max_year: int | None = None) -> pd.Series:
    cap = max_year if max_year is not None else datetime.now().year
    return s.map(lambda v: parse_transaction_datetime(v, cap))


def _extract_valid_calendar_date_fragment(text: str, max_year: int) -> str | None:
    """First YYYY-MM-DD (or slashes) substring that is a real calendar date."""
    for m in _DATE_YMD_FRAGMENT_RE.finditer(text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y > max_year or y < 1:
            continue
        if mo < 1 or mo > 12:
            continue
        last = calendar.monthrange(y, mo)[1]
        if d < 1 or d > last:
            continue
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


def _extract_valid_clock_fragment(text: str) -> str | None:
    """First HH:MM[:SS] substring with valid clock ranges (outputs HH:MM)."""
    for m in _TIME_HMS_FRAGMENT_RE.finditer(text):
        h, mn = int(m.group(1)), int(m.group(2))
        sec = int(m.group(3)) if m.group(3) is not None else 0
        if 0 <= h <= 23 and 0 <= mn <= 59 and 0 <= sec <= 59:
            return f"{h:02d}:{mn:02d}"
    return None


def format_time_field_for_data_clean(raw: str, max_year: int) -> str:
    """
    If the value parses as a full datetime, keep the stripped original.
    Otherwise: valid date + invalid/missing time -> 'NULL YYYY-MM-DD';
    valid time + invalid/missing date -> 'HH:MM NULL'; else text 'NULL'.
    """
    s = raw.strip()
    if not s:
        return NULL_TOKEN
    ts = parse_transaction_datetime(s, max_year)
    if pd.notna(ts):
        return s
    vd = _extract_valid_calendar_date_fragment(s, max_year)
    vt = _extract_valid_clock_fragment(s)
    if vd is not None and vt is not None:
        fused = f"{vt} {vd}"
        if pd.notna(parse_transaction_datetime(fused, max_year)):
            return fused
    if vd is not None and vt is None:
        return f"{NULL_TOKEN} {vd}"
    if vt is not None and vd is None:
        return f"{vt} {NULL_TOKEN}"
    return NULL_TOKEN


EXPECTED_COLUMNS = ("status", "time", "card_type", "city", "amount", "id")


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    return df


def apply_basic_cleansing(df: pd.DataFrame) -> None:
    """Strip whitespace on text fields."""
    for col in ("status", "time", "card_type", "city", "amount"):
        df[col] = df[col].astype("string").str.strip()


def cleansing_format_time_column_for_export(df: pd.DataFrame) -> int:
    """
    Normalize the time column for data_clean.csv: keep stripped text when it fully parses;
    impossible full datetimes become partial NULL patterns (NULL date, NULL time) or text NULL.
    """
    cap = datetime.now().year
    raw = df["time"].astype("string")

    def fmt(v: object) -> str:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return NULL_TOKEN
        if pd.isna(v):
            return NULL_TOKEN
        s = str(v).strip()
        if not s:
            return NULL_TOKEN
        return format_time_field_for_data_clean(s, cap)

    new_series = raw.map(fmt)
    n = int((new_series != raw.fillna("")).sum())
    df["time"] = new_series
    return n


def cleansing_null_amount_outliers(df: pd.DataFrame) -> int:
    """IQR on absolute amounts (same rule as full pipeline); null outliers; non-numeric amounts unchanged."""
    raw = df["amount"]
    one_hundred = raw.str.lower().eq("one hundred").fillna(False)
    raw_fixed = raw.where(~one_hundred, "100")
    amount_num = pd.to_numeric(raw_fixed, errors="coerce")
    amount_abs = amount_num.abs()
    positive = amount_abs[(amount_num.notna()) & (amount_abs > 0)]
    if len(positive) == 0:
        return 0
    q1 = positive.quantile(0.25)
    q3 = positive.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outlier_flag = amount_num.notna() & ((amount_abs < lower) | (amount_abs > upper))
    n = int(outlier_flag.sum())
    if n:
        df.loc[outlier_flag, "amount"] = pd.NA
    return n


def cleansing_phase(df: pd.DataFrame) -> Dict[str, int]:
    apply_basic_cleansing(df)
    n_time = cleansing_format_time_column_for_export(df)
    n_amt = cleansing_null_amount_outliers(df)
    return {
        "time_column_formatted_rows": n_time,
        "amount_outlier_nulled": n_amt,
    }


def transform_status(df: pd.DataFrame) -> Dict[str, int]:
    raw = df["status"]
    key = raw.str.lower()

    status_map = {
        "success": "success",
        "succeed": "success",
        "fail": "failed",
        "failed": "failed",
    }
    cleaned = key.map(status_map)

    df["status_clean"] = cleaned
    df["status_invalid_flag"] = cleaned.isna() & raw.notna() & (raw != "")

    return {
        "status_invalid_rows": int(df["status_invalid_flag"].sum()),
        "status_clean_null_rows": int(df["status_clean"].isna().sum()),
    }


def transform_time(df: pd.DataFrame) -> Dict[str, int]:
    """Parse timestamps only; strftime fields filled in normalisation_phase."""
    raw = df["time"]
    parsed = parse_transaction_datetime_series(df["time"])

    df["time_parsed"] = parsed
    df["time_valid_flag"] = parsed.notna()
    df["time_invalid_flag"] = parsed.isna() & raw.notna() & (raw != "")

    return {
        "time_valid_rows": int(df["time_valid_flag"].sum()),
        "time_invalid_rows": int(df["time_invalid_flag"].sum()),
        "time_null_rows": int(raw.isna().sum() + (raw == "").sum()),
    }


def normalise_time_columns(df: pd.DataFrame) -> Dict[str, int]:
    """Derive time_clean, date_clean, clock_time_clean from time_parsed."""
    p = df["time_parsed"]
    ok = p.notna()
    df["time_clean"] = pd.Series(pd.NA, index=df.index, dtype="string")
    df["date_clean"] = pd.Series(pd.NA, index=df.index, dtype="string")
    df["clock_time_clean"] = pd.Series(pd.NA, index=df.index, dtype="string")
    if ok.any():
        df.loc[ok, "time_clean"] = p.loc[ok].dt.strftime("%Y-%m-%d %H:%M:%S")
        df.loc[ok, "date_clean"] = p.loc[ok].dt.strftime("%Y-%m-%d")
        df.loc[ok, "clock_time_clean"] = p.loc[ok].dt.strftime("%H:%M:%S")
    return {}


def transform_card_type(df: pd.DataFrame) -> Dict[str, int]:
    raw = df["card_type"]
    key = raw.str.lower()

    card_map = {
        "visa": "Visa",
        "vsa": "Visa",
        "mastercard": "MasterCard",
        "master card": "MasterCard",
        "master-card": "MasterCard",
        "mastcard": "MasterCard",
        "amex": "Amex",
        "discover": "Discover",
    }

    cleaned = key.map(card_map)
    df["card_type_clean"] = cleaned
    df["card_type_invalid_flag"] = cleaned.isna() & raw.notna() & (raw != "")

    return {
        "card_type_invalid_rows": int(df["card_type_invalid_flag"].sum()),
        "card_type_clean_null_rows": int(df["card_type_clean"].isna().sum()),
    }


def transform_city(df: pd.DataFrame) -> Dict[str, int]:
    raw = df["city"]
    key = raw.str.lower()

    city_map = {
        "tehran": "Tehran",
        "thr": "Tehran",
        "thran": "Tehran",
        "tehr@n": "Tehran",
        "tabriz": "Tabriz",
        "isfahan": "Isfahan",
        "mashhad": "Mashhad",
        "shiraz": "Shiraz",
        "qom": "Qom",
        "karaj": "Karaj",
        "ahvaz": "Ahvaz",
    }

    cleaned = key.map(city_map)
    df["city_clean"] = cleaned
    df["city_invalid_flag"] = cleaned.isna() & raw.notna() & (raw != "")

    return {
        "city_invalid_rows": int(df["city_invalid_flag"].sum()),
        "city_clean_null_rows": int(df["city_clean"].isna().sum()),
    }


def transform_amount(df: pd.DataFrame) -> Dict[str, int]:
    """Coerce amount and IQR flags; amount_clean set in normalise_amount_clean."""
    raw = df["amount"]
    one_hundred = raw.str.lower().eq("one hundred").fillna(False)
    raw_fixed = raw.where(~one_hundred, "100")
    amount_num = pd.to_numeric(raw_fixed, errors="coerce")
    amount_abs = amount_num.abs()

    df["amount_non_numeric_flag"] = amount_num.isna() & raw.notna() & (raw != "")
    df["amount_negative_flag"] = (amount_num < 0) & amount_num.notna()

    positive = amount_abs[(amount_num.notna()) & (amount_abs > 0)]
    if len(positive) > 0:
        q1 = positive.quantile(0.25)
        q3 = positive.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_flag = amount_num.notna() & ((amount_abs < lower) | (amount_abs > upper))
    else:
        outlier_flag = pd.Series(False, index=df.index)

    df["amount_outlier_flag"] = outlier_flag
    df["amount_numeric"] = amount_abs.astype(float)

    return {
        "amount_non_numeric_rows": int(df["amount_non_numeric_flag"].sum()),
        "amount_negative_rows": int(df["amount_negative_flag"].sum()),
        "amount_outlier_rows": int(df["amount_outlier_flag"].sum()),
    }


def normalise_amount_clean(df: pd.DataFrame) -> Dict[str, int]:
    amount_clean = df["amount_numeric"].copy()
    amount_clean[df["amount_outlier_flag"]] = pd.NA
    df["amount_clean"] = amount_clean
    return {"amount_clean_null_rows": int(df["amount_clean"].isna().sum())}


def transformation_phase(df: pd.DataFrame) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    summary.update(transform_status(df))
    summary.update(transform_time(df))
    summary.update(transform_card_type(df))
    summary.update(transform_city(df))
    summary.update(transform_amount(df))
    return summary


def normalisation_phase(df: pd.DataFrame) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    summary.update(normalise_time_columns(df))
    summary.update(normalise_amount_clean(df))
    add_new_unique_id(df)
    return summary


def add_new_unique_id(df: pd.DataFrame) -> None:
    n = len(df)
    df["transaction_id"] = [f"TRX_{i:05d}" for i in range(1, n + 1)]


def build_cleaning_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column counts: valid / invalid / null before clean (raw) vs after clean (standardized)."""
    n = len(df)
    rows: List[Dict[str, Any]] = []

    rs = df["status"]
    b_null = int((rs.isna() | (rs == "")).sum())
    b_inv = int(df["status_invalid_flag"].sum())
    b_val = n - b_null - b_inv
    a_val = int(df["status_clean"].notna().sum())
    a_inv = b_inv
    a_null = n - a_val - a_inv
    rows.append(
        {
            "column": "status",
            "before_valid": b_val,
            "before_invalid": b_inv,
            "before_null": b_null,
            "after_valid": a_val,
            "after_invalid": a_inv,
            "after_null": a_null,
        }
    )

    rt = df["time"]
    b_null = int((rt.isna() | (rt == "")).sum())
    b_inv = int(df["time_invalid_flag"].sum())
    b_val = int(df["time_valid_flag"].sum())
    a_val = b_val
    a_inv = 0
    a_null = n - a_val
    rows.append(
        {
            "column": "time",
            "before_valid": b_val,
            "before_invalid": b_inv,
            "before_null": b_null,
            "after_valid": a_val,
            "after_invalid": a_inv,
            "after_null": a_null,
        }
    )

    rc = df["card_type"]
    b_null = int((rc.isna() | (rc == "")).sum())
    b_inv = int(df["card_type_invalid_flag"].sum())
    b_val = n - b_null - b_inv
    a_val = int(df["card_type_clean"].notna().sum())
    a_inv = b_inv
    a_null = n - a_val - a_inv
    rows.append(
        {
            "column": "card_type",
            "before_valid": b_val,
            "before_invalid": b_inv,
            "before_null": b_null,
            "after_valid": a_val,
            "after_invalid": a_inv,
            "after_null": a_null,
        }
    )

    rct = df["city"]
    b_null = int((rct.isna() | (rct == "")).sum())
    b_inv = int(df["city_invalid_flag"].sum())
    b_val = n - b_null - b_inv
    a_val = int(df["city_clean"].notna().sum())
    a_inv = b_inv
    a_null = n - a_val - a_inv
    rows.append(
        {
            "column": "city",
            "before_valid": b_val,
            "before_invalid": b_inv,
            "before_null": b_null,
            "after_valid": a_val,
            "after_invalid": a_inv,
            "after_null": a_null,
        }
    )

    ra = df["amount"]
    amount_raw_num = pd.to_numeric(ra, errors="coerce")
    b_null = int((ra.isna() | (ra == "")).sum())
    non_numeric_raw = amount_raw_num.isna() & ra.notna() & (ra != "")
    negative_raw = (amount_raw_num < 0) & amount_raw_num.notna()
    before_inv_mask = non_numeric_raw | negative_raw | df["amount_outlier_flag"]
    b_inv = int(before_inv_mask.sum())
    b_val = n - b_null - b_inv
    a_val = int(df["amount_clean"].notna().sum())
    a_inv = int(df["amount_non_numeric_flag"].sum())
    a_null = n - a_val - a_inv
    rows.append(
        {
            "column": "amount",
            "before_valid": b_val,
            "before_invalid": b_inv,
            "before_null": b_null,
            "after_valid": a_val,
            "after_invalid": a_inv,
            "after_null": a_null,
        }
    )

    return pd.DataFrame(rows)


def build_issue_counts(df: pd.DataFrame, summary: Dict[str, int]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"column": "status", "issue": "invalid status values", "count": summary["status_invalid_rows"]},
            {"column": "time", "issue": "invalid datetime values", "count": summary["time_invalid_rows"]},
            {"column": "card_type", "issue": "invalid card_type values", "count": summary["card_type_invalid_rows"]},
            {"column": "city", "issue": "invalid city values", "count": summary["city_invalid_rows"]},
            {"column": "amount", "issue": "non-numeric values", "count": summary["amount_non_numeric_rows"]},
            {"column": "amount", "issue": "negative values", "count": summary["amount_negative_rows"]},
            {"column": "amount", "issue": "IQR outlier values", "count": summary["amount_outlier_rows"]},
            {"column": "id", "issue": "duplicated original id rows", "count": int(df["id"].astype("string").duplicated(keep=False).sum())},
        ]
    )


def run_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int], pd.DataFrame]:
    """Cleansing → transformation → normalisation; summary merges all phase stats."""
    summary: Dict[str, int] = {}
    summary.update(cleansing_phase(df))
    summary.update(transformation_phase(df))
    summary.update(normalisation_phase(df))

    issues_df = build_issue_counts(df, summary)
    return df, summary, issues_df


def run_transformation_after_cleansing(df: pd.DataFrame) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Assume cleansing_phase already applied. Returns (transformation_summary, normalisation_summary)."""
    t = transformation_phase(df)
    n = normalisation_phase(df)
    return t, n


def _export_string_cell(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return NULL_TOKEN
    if isinstance(val, str) and val.strip() == "":
        return NULL_TOKEN
    if pd.isna(val):
        return NULL_TOKEN
    return str(val)


def _export_amount_cell(val: Any) -> Union[str, float]:
    if val is None or pd.isna(val):
        return NULL_TOKEN
    return float(val)


def _export_id_cell(val: Any) -> Any:
    if val is None or pd.isna(val):
        return NULL_TOKEN
    try:
        f = float(val)
        if f == int(f):
            return int(f)
    except (TypeError, ValueError):
        pass
    return val


def _export_preserve_original(val: Any) -> Any:
    """Original values for export; NULL token for missing/empty; whole floats as integer strings."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return NULL_TOKEN
    if pd.isna(val):
        return NULL_TOKEN
    if isinstance(val, str) and val.strip() == "":
        return NULL_TOKEN
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        return str(val)
    return str(val)


def export_data_clean_preserved(df: pd.DataFrame, out_path: Path) -> None:
    """data_clean.csv: id first, then stripped originals; no transaction_id column."""
    n = len(df)
    rows_out: Dict[str, List[Any]] = {
        "id": [_export_id_cell(df["id"].iloc[i]) for i in range(n)],
        "status": [_export_preserve_original(df["status"].iloc[i]) for i in range(n)],
        "time": [_export_preserve_original(df["time"].iloc[i]) for i in range(n)],
        "card_type": [_export_preserve_original(df["card_type"].iloc[i]) for i in range(n)],
        "city": [_export_preserve_original(df["city"].iloc[i]) for i in range(n)],
        "amount": [_export_preserve_original(df["amount"].iloc[i]) for i in range(n)],
    }
    pd.DataFrame(rows_out).to_csv(out_path, index=False)


def export_transformed(df: pd.DataFrame, out_path: Path) -> None:
    """Transformed CSV: id, TRX_*, success|failed, date + time (clock) only, maps, amount float."""
    n = len(df)
    rows_out: Dict[str, List[Any]] = {
        "id": [_export_id_cell(df["id"].iloc[i]) for i in range(n)],
        "transaction_id": list(df["transaction_id"]),
        "status": [_export_string_cell(df["status_clean"].iloc[i]) for i in range(n)],
        "date": [_export_string_cell(df["date_clean"].iloc[i]) for i in range(n)],
        "time": [_export_string_cell(df["clock_time_clean"].iloc[i]) for i in range(n)],
        "card_type": [_export_string_cell(df["card_type_clean"].iloc[i]) for i in range(n)],
        "city": [_export_string_cell(df["city_clean"].iloc[i]) for i in range(n)],
        "amount": [_export_amount_cell(df["amount_clean"].iloc[i]) for i in range(n)],
    }
    out_df = pd.DataFrame(rows_out)
    out_df.to_csv(out_path, index=False)


def export_cleaned(df: pd.DataFrame, out_path: Path) -> None:
    """Backward-compatible alias for export_transformed."""
    export_transformed(df, out_path)


def print_summary(df: pd.DataFrame, summary: Dict[str, int], issues_df: pd.DataFrame) -> None:
    print("\n=== Quality snapshot: valid / invalid / null (before clean vs after clean) ===")
    q = build_cleaning_quality_summary(df)
    print(q.to_string(index=False))
    print(
        "Notes: time: after_invalid is 0 (bad datetimes have no standardized value; counted under after_null). "
        "amount: before_valid excludes raw non-numeric text, negatives, and IQR outliers."
    )

    print("\n=== Cleaned DataFrame Preview ===")
    preview_cols = [
        "status", "status_clean",
        "time", "time_clean", "date_clean", "clock_time_clean", "time_valid_flag", "time_invalid_flag",
        "card_type", "card_type_clean",
        "city", "city_clean",
        "amount", "amount_numeric", "amount_clean", "amount_non_numeric_flag", "amount_negative_flag", "amount_outlier_flag",
        "id", "transaction_id",
    ]
    preview_cols = [c for c in preview_cols if c in df.columns]
    print(df[preview_cols].head(10).to_string(index=False))

    print("\n=== Summary of Transformations Applied ===")
    for k, v in summary.items():
        print(f"- {k}: {v}")

    print("\n=== Count of Invalid Rows / Issues by Column ===")
    print(issues_df.to_string(index=False))

    print_invalid_time_rows(df)


def print_invalid_time_rows(df: pd.DataFrame) -> None:
    """Print rows where raw time was non-empty but did not parse to a valid calendar datetime."""
    if "time_invalid_flag" not in df.columns:
        return
    cols = [c for c in ("transaction_id", "id", "time") if c in df.columns]
    inv = df.loc[df["time_invalid_flag"], cols]
    print("\n=== Invalid time/date after clean (raw value could not be normalized) ===")
    if inv.empty:
        print("(none)")
        return
    print(inv.to_string(index=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="Data re-engineering for transaction.csv")
    parser.add_argument("--input", type=Path, default=Path("transaction.csv"))
    parser.add_argument("--output", type=Path, default=Path("data_clean.csv"))
    parser.add_argument(
        "--transform-output",
        type=Path,
        default=Path("data_transformed.csv"),
        help="Transformed CSV (TRX_*, maps, date + time columns, amount double).",
    )
    parser.add_argument(
        "--no-transform",
        action="store_true",
        help="Only write data_clean.csv (skip transformation export).",
    )
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Print quality report and issue counts after transformation.",
    )
    args = parser.parse_args()

    df = load_data(args.input)
    clean_stats = cleansing_phase(df)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_data_clean_preserved(df, args.output)
    print(f"Preserved data_clean saved: {args.output} ({len(df)} rows)")
    print(
        f"Cleansing: time column formatted (NULL / partial patterns): "
        f"{clean_stats['time_column_formatted_rows']}, "
        f"amount outlier -> NULL: {clean_stats['amount_outlier_nulled']}"
    )

    if not args.no_transform:
        t_sum, n_sum = run_transformation_after_cleansing(df)
        summary = {**clean_stats, **t_sum, **n_sum}
        args.transform_output.parent.mkdir(parents=True, exist_ok=True)
        export_transformed(df, args.transform_output)
        print(f"Transformed data saved: {args.transform_output} ({len(df)} rows)")
        if args.full_pipeline:
            issues_df = build_issue_counts(df, summary)
            print_summary(df, summary, issues_df)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
