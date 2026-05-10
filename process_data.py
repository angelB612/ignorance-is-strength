import pandas as pd
from pathlib import Path

RAW = Path("data")
OUT = Path("data/processed")
OUT.mkdir(exist_ok=True)

CASE_COUNTRIES = ["Germany", "Russia", "Chile", "China", "Hungary", "United States of America"]

REGIME_LABELS = {
    0: "Closed Autocracy",
    1: "Electoral Autocracy",
    2: "Electoral Democracy",
    3: "Liberal Democracy",
}

VDEM_COLS = [
    "country_name", "country_text_id", "country_id", "year",
    "v2xca_academ",
    "v2x_polyarchy", "v2x_libdem", "v2x_partipdem",
    "v2x_delibdem", "v2x_egaldem",
    "v2x_regime",
]


def tag_administration(yr, q):
    if yr == 2017 and q == 1:
        return "Obama"
    if (yr == 2017 and q >= 2) or yr in range(2018, 2021) or (yr == 2021 and q == 1):
        return "Trump 1st"
    if (yr == 2021 and q >= 2) or yr in range(2022, 2025) or (yr == 2025 and q == 1):
        return "Biden"
    return "Trump 2nd"


# 1. V-DEM 
vdem_raw = pd.read_csv(RAW / "V-Dem-CY-Core-v16.csv", usecols=VDEM_COLS, low_memory=False)
vdem_raw["regime_label"] = vdem_raw["v2x_regime"].map(REGIME_LABELS)

# Global snapshot (latest year per country) — for choropleth
latest_year = vdem_raw["year"].max()
vdem_global = (
    vdem_raw[vdem_raw["year"] == latest_year]
    .dropna(subset=["v2xca_academ", "v2x_libdem"])
    .reset_index(drop=True)
)
vdem_global.to_csv(OUT / "vdem_global.csv", index=False)
print(f"  vdem_global.csv — {len(vdem_global)} countries, year {latest_year}")

# Regime timeline (post-1900, all countries) — for area chart
regime_timeline = (
    vdem_raw[vdem_raw["year"] >= 1900]
    .groupby(["year", "regime_label"])
    .size()
    .reset_index(name="count")
)
total_by_year = regime_timeline.groupby("year")["count"].transform("sum")
regime_timeline["share"] = regime_timeline["count"] / total_by_year
regime_timeline.to_csv(OUT / "vdem_regime_timeline.csv", index=False)
print(f"  vdem_regime_timeline.csv — {len(regime_timeline)} rows")

# Case countries (2010–latest) — for line/rank chart
cases = vdem_raw[
    vdem_raw["country_name"].isin(CASE_COUNTRIES) &
    (vdem_raw["year"] >= 2010)
].copy()
cases["rank"] = cases.groupby("year")["v2x_libdem"].rank(ascending=False, method="min")
cases.to_csv(OUT / "vdem_cases.csv", index=False)
print(f"  vdem_cases.csv — {len(cases)} rows")

# US full series (for composite chart)
us_series = (
    vdem_raw[vdem_raw["country_name"] == "United States of America"]
    [["year", "v2xca_academ", "v2x_libdem", "v2x_polyarchy"]]
    .sort_values("year")
    .reset_index(drop=True)
)
us_series.to_csv(OUT / "vdem_us.csv", index=False)
print(f"  vdem_us.csv — {len(us_series)} rows")


# 2. BOOK BANS
bans_raw = pd.read_csv(RAW / "banned-book-list.csv")
bans_raw["date"] = pd.to_datetime(bans_raw["Date of Challenge/Removal"], format="%b-%y")
bans_raw["year"] = bans_raw["date"].dt.year
bans_raw["month"] = bans_raw["date"].dt.to_period("M").astype(str)

# Clean version (all records)
bans_clean = bans_raw[[
    "Title", "Author", "State", "District",
    "Type of Ban", "Origin of Challenge", "date", "year", "month"
]].copy()
bans_clean.columns = [
    "title", "author", "state", "district",
    "ban_type", "origin", "date", "year", "month"
]
bans_clean.to_csv(OUT / "book_bans_clean.csv", index=False)
print(f"  book_bans_clean.csv — {len(bans_clean)} rows")

# Monthly aggregates — for timeline chart
bans_monthly = (
    bans_clean.groupby("month")
    .size()
    .reset_index(name="count")
    .sort_values("month")
)
bans_monthly.to_csv(OUT / "bans_monthly.csv", index=False)
print(f"  bans_monthly.csv — {len(bans_monthly)} rows")

# By state — for choropleth
bans_by_state = (
    bans_clean.groupby("state")
    .size()
    .reset_index(name="bans")
    .rename(columns={"state": "state_title"})
)

# By state + ban type breakdown
bans_state_type = (
    bans_clean.groupby(["state", "ban_type"])
    .size()
    .reset_index(name="count")
)
bans_state_type.to_csv(OUT / "bans_state_type.csv", index=False)
print(f"  bans_state_type.csv — {len(bans_state_type)} rows")

# Origin breakdown — for "94% administrators" chart
bans_origin = (
    bans_clean["origin"]
    .value_counts()
    .reset_index(name="count")
    .rename(columns={"index": "origin"})
)
bans_origin["share"] = bans_origin["count"] / bans_origin["count"].sum()
bans_origin.to_csv(OUT / "bans_origin.csv", index=False)
print(f"  bans_origin.csv — {len(bans_origin)} rows")


# 3. PRESIDENTIAL RESULTS + BAN MERGE
elect_raw = pd.read_csv(RAW / "1976-2020-president.csv")
rep_2020 = elect_raw[
    (elect_raw["year"] == 2020) &
    (elect_raw["party_simplified"] == "REPUBLICAN")
][["state", "state_po", "candidatevotes", "totalvotes"]].copy()
rep_2020["gop_share"] = rep_2020["candidatevotes"] / rep_2020["totalvotes"] * 100
rep_2020["state_title"] = rep_2020["state"].str.title()
rep_2020["party_2020"] = rep_2020["gop_share"].apply(
    lambda x: "Republican" if x >= 50 else "Democrat"
)

bans_by_state_merged = rep_2020.merge(bans_by_state, on="state_title", how="left")
bans_by_state_merged["bans"] = bans_by_state_merged["bans"].fillna(0).astype(int)
bans_by_state_merged.to_csv(OUT / "bans_by_state.csv", index=False)
print(f"  bans_by_state.csv — {len(bans_by_state_merged)} rows")


# 4. DOE SPENDING 
edu_raw = pd.read_csv(RAW / "results-over-time-by-quarter-1777527703100.csv")
edu_raw[["q", "yr"]] = edu_raw["fiscal_quarter"].str.split(" ", expand=True)
edu_raw["yr"] = edu_raw["yr"].astype(int)
edu_raw["q_num"] = edu_raw["q"].str[1].astype(int)
edu_raw = edu_raw[edu_raw["total_obligations"] > 0].copy()
edu_raw = edu_raw.sort_values(["yr", "q_num"]).reset_index(drop=True)
edu_raw["obligations_bn"] = edu_raw["total_obligations"] / 1e9
edu_raw["administration"] = edu_raw.apply(
    lambda r: tag_administration(r["yr"], r["q_num"]), axis=1
)
edu_raw.to_csv(OUT / "doe_spending_clean.csv", index=False)
print(f"  doe_spending_clean.csv — {len(edu_raw)} rows")

# Annual aggregates (for composite chart alignment)
edu_annual = (
    edu_raw.groupby("yr")["obligations_bn"]
    .sum()
    .reset_index()
    .rename(columns={"yr": "year", "obligations_bn": "total_bn"})
)
edu_annual.to_csv(OUT / "doe_spending_annual.csv", index=False)
print(f"  doe_spending_annual.csv — {len(edu_annual)} rows")

 
# 5. US COMPOSITE (aligned annual)
bans_annual = (
    bans_clean.groupby("year")
    .size()
    .reset_index(name="ban_count")
)

composite = (
    us_series[us_series["year"] >= 2017]
    .merge(edu_annual, on="year", how="left")
    .merge(bans_annual, on="year", how="left")
)
composite["ban_count"] = composite["ban_count"].fillna(0).astype(int)
composite.to_csv(OUT / "us_composite.csv", index=False)
print(f"  us_composite.csv — {len(composite)} rows")

print("\nDone. Processed files written to data/processed/")
