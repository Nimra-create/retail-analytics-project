"""
Stage 1: Clean messy Excel export with Python (pandas)
Stage 2: Load cleaned data into a SQL database (SQLite)
=========================================================
Input:  raw/raw_sales_export.xlsx  (real-world messy export)
Output: clean/sales_clean.csv      (cleaned flat file, for inspection)
        sql/business.db           (SQL database — the layer Power BI/SQL connect to)
"""

import pandas as pd
import numpy as np
import sqlite3
import re

# -----------------------------------------------------------
# STAGE 1: Load and clean
# -----------------------------------------------------------
df = pd.read_excel("raw/raw_sales_export.xlsx", sheet_name="Sales Export")

print("=" * 60)
print("RAW DATA PROFILE")
print("=" * 60)
print(f"Rows: {len(df)}")
print(f"Duplicate rows: {df.duplicated().sum()}")
print(f"Missing Region: {df['Region'].isna().sum()}")
print(f"Missing/blank CustomerID: {(df['CustomerID'].isna() | (df['CustomerID'].astype(str).str.strip() == '')).sum()}")
print(f"Negative UnitPrice: {(df['UnitPrice'] < 0).sum()}")
print(f"Zero Units: {(df['Units'] == 0).sum()}")
print(f"Unique Category spellings (raw): {df['Category'].nunique()}")
print(f"Unique Channel spellings (raw): {df['Channel'].nunique()}")

cleaning_log = []

# 1. Drop exact duplicate rows
before = len(df)
df = df.drop_duplicates()
cleaning_log.append(f"Removed {before - len(df)} exact duplicate rows")

# 2. Trim whitespace on all text columns
text_cols = ["CustomerID", "Region", "Category", "Channel"]
for col in text_cols:
    df[col] = df[col].astype(str).str.strip()
    df[col] = df[col].replace({"nan": np.nan, "": np.nan, "None": np.nan})
cleaning_log.append("Trimmed whitespace on text columns; converted blanks to null")

# 3. Standardize Category to a canonical spelling
category_map = {
    "electronics": "Electronics",
    "apparel": "Apparel", "appare l": "Apparel",
    "home & kitchen": "Home & Kitchen", "home and kitchen": "Home & Kitchen",
    "sports": "Sports",
    "beauty": "Beauty",
}
df["Category"] = df["Category"].str.lower().map(category_map).fillna(df["Category"])
cleaning_log.append(f"Standardized Category to {df['Category'].nunique()} canonical values (was messy casing/variants)")

# 4. Standardize Channel
channel_map = {"online": "Online", "in-store": "In-Store", "in store": "In-Store"}
df["Channel"] = df["Channel"].str.lower().map(channel_map).fillna(df["Channel"])
cleaning_log.append(f"Standardized Channel to {df['Channel'].nunique()} canonical values")

# 5. Parse mixed date formats robustly
def parse_mixed_date(val):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%m/%d/%y"):
        try:
            return pd.to_datetime(val, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.to_datetime(val, errors="coerce")  # last resort

df["OrderDate"] = df["OrderDate"].apply(parse_mixed_date)
n_unparsed = df["OrderDate"].isna().sum()
cleaning_log.append(f"Parsed {len(df) - n_unparsed} dates from 4 mixed formats ({n_unparsed} unparseable)")

# 6. Drop rows with invalid economics: negative price, zero units, or missing CustomerID
before = len(df)
df = df[(df["UnitPrice"] > 0) & (df["Units"] > 0) & df["CustomerID"].notna() & df["OrderDate"].notna()]
cleaning_log.append(f"Removed {before - len(df)} rows with negative price, zero units, missing customer, or unparseable date")

# 7. Region: impute missing with "Unknown" rather than dropping (preserves revenue)
n_missing_region = df["Region"].isna().sum()
df["Region"] = df["Region"].fillna("Unknown")
cleaning_log.append(f"Imputed {n_missing_region} missing Region values as 'Unknown' (kept rows — revenue still counts)")

# 8. Recompute Profit and enforce types
df["Profit"] = df["Revenue"] - df["Cost"]
df["OrderID"] = df["OrderID"].astype(int)
df["Units"] = df["Units"].astype(int)
df = df.sort_values("OrderDate").reset_index(drop=True)

print("\n" + "=" * 60)
print("CLEANING LOG")
print("=" * 60)
for line in cleaning_log:
    print(f"  - {line}")

print(f"\nFinal clean row count: {len(df)}")

df.to_csv("clean/sales_clean.csv", index=False)

# -----------------------------------------------------------
# STAGE 2: Load into SQL database
# -----------------------------------------------------------
conn = sqlite3.connect("sql/business.db")
df_sql = df.rename(columns={
    "OrderID": "order_id", "OrderDate": "order_date", "CustomerID": "customer_id",
    "Region": "region", "Category": "category", "Channel": "channel",
    "Units": "units", "UnitPrice": "unit_price", "Revenue": "revenue",
    "Cost": "cost", "Profit": "profit",
})
df_sql["order_date"] = df_sql["order_date"].dt.strftime("%Y-%m-%d")
df_sql.to_sql("sales", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(order_date)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)")
conn.commit()
conn.close()

print("\nLoaded cleaned data into sql/business.db (table: sales)")
