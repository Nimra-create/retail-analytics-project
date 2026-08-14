# Retail Analytics Pipeline: Excel → Python → SQL → Power BI

An end-to-end business analytics project demonstrating a realistic messy-data-to-dashboard
workflow.

## Pipeline overview

```
data/raw/raw_sales_export.xlsx      (messy source export, 2,044 rows)
        │
        ▼  scripts/1_generate_messy_excel.py  (how the messy file was generated)
        │
        ▼  scripts/2_clean_and_load.py        (pandas cleaning + load to SQLite)
        │
sql/business.db                     (cleaned SQLite database)
        │
        ▼  sql/kpi_views.sql                  (7 KPI views defined in SQL)
        │
powerbi/                            (view exports + build guide for Power BI)
```

## What's in this repo

| Folder | Contents |
|---|---|
| `data/raw/` | The original messy Excel export — duplicates, inconsistent category spelling, mixed date formats, missing values, and invalid entries (negative prices, zero units) intentionally included to mirror a real-world data source. |
| `data/clean/` | The cleaned, flat CSV output after the Python cleaning stage. |
| `scripts/` | `1_generate_messy_excel.py` builds the messy source file. `2_clean_and_load.py` profiles the raw data, cleans it (dedup, whitespace trim, category/channel standardization, mixed-date parsing, validity filtering, missing-region imputation), and loads it into the SQLite database. |
| `sql/` | `business.db` — the cleaned `sales` table plus 7 KPI views. `kpi_views.sql` — the SQL that defines those views (`v_monthly_kpis`, `v_category_performance`, `v_region_performance`, `v_channel_performance`, `v_customer_value`, `v_top10_customers`, `v_repeat_purchase_rate`). |
| `powerbi/` | CSV exports of each SQL view, ready to import into Power BI, plus `POWER_BI_BUILD_GUIDE.md` with the data model, DAX measures, and suggested report layout. |

## How to reproduce

```bash
pip install pandas numpy openpyxl
python scripts/1_generate_messy_excel.py   # regenerate the messy source file
python scripts/2_clean_and_load.py         # clean it and rebuild sql/business.db
```

Then load `sql/kpi_views.sql` against `business.db` (via any SQLite client or
`sqlite3` in Python) to rebuild the KPI views.

## Key design decision

KPI logic (revenue, margin, CAC proxies, repeat purchase rate, etc.) is defined **once**,
in SQL — not recalculated separately in Excel formulas, Python, or Power BI DAX. Every
downstream tool reads from the same views, so the numbers can't drift out of sync between
a dashboard, an ad hoc query, and a report.

## Power BI dashboard

See `powerbi/POWER_BI_BUILD_GUIDE.md` for two ways to connect: live via ODBC to
`business.db`, or by importing the pre-exported CSVs directly. Includes the exact DAX
measures and a 3-page report layout (Executive Overview, Regional & Channel Mix,
Customers).

**Note on data model:** if you import both `sales_fact` and the summary views (like
`v_category_performance`) into the same Power BI file, do **not** relate them to each
other — the summary views are already pre-aggregated, and relating them to the fact table
(or to each other) causes double-counting. Keep them as standalone tables used directly
on visuals.
