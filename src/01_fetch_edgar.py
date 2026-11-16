"""Download P&G's financial data from SEC EDGAR and save clean quarterly numbers.

Run from the project folder:  python src/01_fetch_edgar.py
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------- 1. Settings
from dotenv import load_dotenv
load_dotenv()
HEADERS = {"User-Agent": os.getenv("SEC_USER_AGENT")}
CIK = "0000080424"  # P&G's ID number at the SEC, padded to 10 digits
URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"
RAW = Path("data/raw")
PROCESSED = Path("data/processed")
FIRST_FISCAL_YEAR = 2022  # keep FY22 onward
LAST_FISCAL_YEAR = 2026   # exclude FY27 until the original FY27 view is committed, so the forecast stays blind

# Each metric lists possible XBRL tag names; companies sometimes switch tags over the years.
# Flow items are amounts over a period (P&L, cash flow). Instant items are balances on a date.
FLOW_TAGS = {
    "net_sales": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"],
    "cost_of_sales": ["CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    "sga": ["SellingGeneralAndAdministrativeExpense"],
    "operating_income": ["OperatingIncomeLoss"],
    "interest_expense": ["InterestExpense", "InterestExpenseNonoperating"],
    "income_tax": ["IncomeTaxExpenseBenefit"],
    "net_earnings_pg": ["NetIncomeLoss"],
    "d_and_a": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "dividends_paid": ["PaymentsOfDividends", "PaymentsOfDividendsCommonStock"],
    "buybacks": ["PaymentsForRepurchaseOfCommonStock"],
}
INSTANT_TAGS = {
    "receivables": ["AccountsReceivableNetCurrent"],
    "inventory": ["InventoryNet"],
    "payables": ["AccountsPayableCurrent"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
}

# ---------------------------------------------------------------- 2. Download
response = requests.get(URL, headers=HEADERS, timeout=30)
response.raise_for_status()  # stops with a clear error if the download failed
facts = response.json()
(RAW / "pg_companyfacts.json").write_text(json.dumps(facts))
usgaap = facts["facts"]["us-gaap"]
print(f"Downloaded {len(usgaap)} us-gaap tags")

# Diagnostic mode: "python src/01_fetch_edgar.py list" prints each tag and its latest period, then exits
if len(sys.argv) > 1 and sys.argv[1] == "list":
    for metric, tags in {**FLOW_TAGS, **INSTANT_TAGS}.items():
        for tag in tags:
            if tag in usgaap:
                obs = [o for unit in usgaap[tag]["units"].values() for o in unit]
                print(f"{metric:22s} {tag:55s} latest period end {max(o['end'] for o in obs)}")
            else:
                print(f"{metric:22s} {tag:55s} NOT FOUND")
    sys.exit()


# ---------------------------------------------------------------- 3. Flatten into one table
def collect(tag_map):
    rows = []
    for metric, tags in tag_map.items():
        for tag in tags:
            for unit, observations in usgaap.get(tag, {}).get("units", {}).items():
                for obs in observations:
                    rows.append({"metric": metric, "tag": tag, "unit": unit, **obs})
    df = pd.DataFrame(rows)
    df["end"] = pd.to_datetime(df["end"])
    if "start" in df:
        df["start"] = pd.to_datetime(df["start"])
    # later filings repeat old periods; keep the most recently filed value for each period
    keys = ["metric", "start", "end"] if "start" in df else ["metric", "end"]
    return df.sort_values("filed").drop_duplicates(keys, keep="last")


def fiscal_year(dates):
    # P&G's fiscal year ends June 30: Jul 2025 to Jun 2026 is FY2026
    return dates.dt.year + (dates.dt.month >= 7).astype(int)


# ---------------------------------------------------------------- 4. Flow items: quarters from year-to-date values
flows = collect(FLOW_TAGS)
flows = flows[(flows["start"].dt.month == 7) & (flows["start"].dt.day == 1)].copy()  # periods starting Jul 1 = year to date
flows["days"] = (flows["end"] - flows["start"]).dt.days
flows["ytd_quarters"] = pd.cut(flows["days"], bins=[80, 100, 190, 280, 375], labels=[1, 2, 3, 4]).astype(float)
flows = flows.dropna(subset=["ytd_quarters"]).copy()
flows["fiscal_year"] = fiscal_year(flows["end"])

ytd = flows.pivot_table(index=["metric", "fiscal_year"], columns="ytd_quarters", values="val", aggfunc="last")
ytd = ytd.reindex(columns=[1.0, 2.0, 3.0, 4.0])  # make sure all four columns exist
quarterly = pd.DataFrame({
    1: ytd[1.0],
    2: ytd[2.0] - ytd[1.0],
    3: ytd[3.0] - ytd[2.0],
    4: ytd[4.0] - ytd[3.0],
})
quarterly = quarterly.reset_index().melt(id_vars=["metric", "fiscal_year"], var_name="fiscal_quarter", value_name="value")

# ---------------------------------------------------------------- 5. Instant items: balances at quarter end
inst = collect(INSTANT_TAGS)
inst = inst[inst["end"].dt.month.isin([9, 12, 3, 6])].copy()
inst["fiscal_year"] = fiscal_year(inst["end"])
inst["fiscal_quarter"] = inst["end"].dt.month.map({9: 1, 12: 2, 3: 3, 6: 4})
inst = inst.rename(columns={"val": "value"})[["metric", "fiscal_year", "fiscal_quarter", "value"]]

# ---------------------------------------------------------------- 6. Combine, convert to $ millions, save
out = pd.concat([quarterly, inst], ignore_index=True)
out = out[out["fiscal_year"].between(FIRST_FISCAL_YEAR, LAST_FISCAL_YEAR)].dropna(subset=["value"])
out["value"] = (out["value"] / 1e6).round(1)
out["fiscal_year"] = out["fiscal_year"].astype(int)
out["fiscal_quarter"] = out["fiscal_quarter"].astype(int)
out["period_id"] = "FY" + (out["fiscal_year"] % 100).astype(str).str.zfill(2) + "Q" + out["fiscal_quarter"].astype(str)
out = out.sort_values(["metric", "fiscal_year", "fiscal_quarter"])
out[["period_id", "fiscal_year", "fiscal_quarter", "metric", "value"]].to_csv(PROCESSED / "edgar_quarterly.csv", index=False)

print(out.pivot_table(index="period_id", columns="metric", values="value").tail(8).to_string())
print(f"Saved {len(out)} rows to {PROCESSED / 'edgar_quarterly.csv'}")