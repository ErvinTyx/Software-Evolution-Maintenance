# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a coursework data re-engineering project. It contains Python scripts and a Jupyter notebook that profile, clean, normalize, and report on two datasets:

- `calorie_efficiency_dataset.csv` — fitness/health metrics with a categorical outcome label
- `retail_store_sales.csv` — retail transaction data (dirty, for cleaning exercises)
- `uncleaned bike sales data.csv` — bike sales dataset explored in the Jupyter notebook

## Running the scripts

```bash
# Activate the virtual environment first
source .venv/bin/activate

# Calorie efficiency pipeline
python calorie_efficiency_reengineering.py
python calorie_efficiency_reengineering.py --input calorie_efficiency_dataset.csv --output-dir out_calorie_efficiency

# Retail store sales pipeline
python retail_store_sales_reengineering.py
python retail_store_sales_reengineering.py --input retail_store_sales.csv --output-dir out_retail_store_sales

# Flags available for both scripts:
#   --sample-rows N         Process only first N rows (for faster iteration)
#   --no-write-datasets     Skip writing cleaned/normalized CSVs (report + infographic only)
```

## Architecture

Both `calorie_efficiency_reengineering.py` and `retail_store_sales_reengineering.py` follow the same pipeline pattern:

1. **`load_dataset`** — reads the raw CSV (with optional row sampling)
2. **`profile_dataset`** — returns a frozen `Profile` dataclass summarising missingness, duplicates, rule violations, and observations
3. **`clean_dataset`** — returns `(df_clean, metadata_dict)`: renames columns to `snake_case`, standardises types and labels, imputes/reconstructs missing values, and adds a surrogate key (`record_id` / `row_id`)
4. **`normalize_tables`** — splits the wide cleaned table into normalized output files
5. **`write_report`** — generates a Markdown report structured around the coursework sections (2.1–2.5)
6. **`write_infographic`** — generates `advocacy_infographic.png` using matplotlib

Each script writes its outputs to a dedicated directory (`out_calorie_efficiency/` or `out_retail_store_sales/`), including:
- `metadata.json` — rename map, imputation decisions, and post-clean checks
- `*_reengineering_report.md` — the coursework write-up
- `advocacy_infographic.png` — before/after summary visual
- Cleaned wide CSV + normalized dimension/fact CSVs

### Calorie efficiency normalization
Wide table → 3 CSVs keyed by `record_id`: `demographics.csv`, `activity.csv`, `outcomes.csv`

### Retail sales normalization
Wide table → star schema: `fact_sales.csv` + `dim_customer.csv`, `dim_category.csv`, `dim_item.csv`, `dim_payment_method.csv`, `dim_location.csv`

## Jupyter notebook

`bike-sales-data.ipynb` is an exploratory notebook for the bike sales dataset. It does inline EDA: date parsing/consistency checks, missing value imputation, month name standardisation, and age group validation. Run it with Jupyter in the activated venv.
