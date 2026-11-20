"""Load all processed data into SQLite, run reconciliation checks, and export the model feed.

Run from the project folder:  python src/02_load_sql.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

PROCESSED = Path("data/processed")
DB = Path("data/pg.db")
SEGMENTS = {
    "FHC": "Fabric & Home Care",
    "BFFC": "Baby, Feminine & Family Care",
    "BEAUTY": "Beauty",
    "HEALTH": "Health Care",
    "GROOM": "Grooming",
    "CORP": "Corporate",
}

# ---------------------------------------------------------------- 1. Read the CSVs
edgar = pd.read_csv(PROCESSED / "edgar_quarterly.csv")
segments = pd.read_csv(PROCESSED / "segment_quarterly.csv")
core = pd.read_csv(PROCESSED / "core_quarterly.csv")
guidance = pd.read_csv(PROCESSED / "guidance_history.csv")

# ---------------------------------------------------------------- 2. Build the period table (one row per quarter)
ids = pd.concat([edgar["period_id"], segments["period_id"], core["period_id"]]).drop_duplicates()
dim_period = pd.DataFrame({"period_id": ids})
dim_period["fiscal_year"] = 2000 + dim_period["period_id"].str[2:4].astype(int)
dim_period["fiscal_quarter"] = dim_period["period_id"].str[5].astype(int)
dim_period = dim_period.sort_values(["fiscal_year", "fiscal_quarter"]).reset_index(drop=True)
# P&G's Q1 = Jul to Sep, Q2 = Oct to Dec (both in the previous calendar year), Q3 = Jan to Mar, Q4 = Apr to Jun
cal_year = dim_period["fiscal_year"] - dim_period["fiscal_quarter"].isin([1, 2]).astype(int)
start_month = dim_period["fiscal_quarter"].map({1: 7, 2: 10, 3: 1, 4: 4})
dim_period["start_date"] = pd.to_datetime(dict(year=cal_year, month=start_month, day=1)).dt.date
dim_period["end_date"] = (pd.to_datetime(dim_period["start_date"]) + pd.offsets.QuarterEnd(0)).dt.date
dim_period["period_index"] = range(1, len(dim_period) + 1)

dim_segment = pd.DataFrame({"segment_id": list(SEGMENTS), "name": list(SEGMENTS.values())})

# ---------------------------------------------------------------- 3. Reconciliation checks (fail loudly)
unknown = set(segments["segment_id"]) - set(SEGMENTS)
assert not unknown, f"Unknown segment codes in segment_quarterly.csv: {unknown}"

counts = segments.groupby("period_id")["segment_id"].count()
assert (counts == 6).all(), f"Every quarter needs 6 segment rows:\n{counts[counts != 6]}"

seg_total = segments.groupby("period_id")["net_sales"].sum()
edgar_sales = edgar[edgar["metric"] == "net_sales"].set_index("period_id")["value"]
tie = pd.concat({"segments": seg_total, "edgar": edgar_sales}, axis=1).dropna()
tie["diff"] = tie["segments"] - tie["edgar"]
bad = tie[tie["diff"].abs() > 3]
assert bad.empty, f"Segment sales do not tie to EDGAR total net sales:\n{bad}"
print(f"Check passed: segments tie to EDGAR in {len(tie)} quarters (max gap ${tie['diff'].abs().max():.0f}M)")

# ---------------------------------------------------------------- 4. Write everything to SQLite
with sqlite3.connect(DB) as con:
    dim_period.to_sql("dim_period", con, if_exists="replace", index=False)
    dim_segment.to_sql("dim_segment", con, if_exists="replace", index=False)
    edgar.to_sql("fact_financials", con, if_exists="replace", index=False)
    segments.to_sql("fact_segment", con, if_exists="replace", index=False)
    core.to_sql("fact_core", con, if_exists="replace", index=False)
    guidance.to_sql("fact_guidance", con, if_exists="replace", index=False)
    con.executescript(Path("src/schema.sql").read_text())

    # ------------------------------------------------------------ 5. Export one wide file for Excel and Power BI
    pl = pd.read_sql("SELECT * FROM v_quarterly_pl", con)

seg_wide = segments.pivot(index="period_id", columns="segment_id", values="net_sales").add_prefix("sales_")
feed = pl.merge(core, on="period_id", how="left").merge(seg_wide, on="period_id", how="left")
feed.to_csv(PROCESSED / "model_feed.csv", index=False)
print(f"Database written to {DB}; model feed has {len(feed)} quarters and {feed.shape[1]} columns")