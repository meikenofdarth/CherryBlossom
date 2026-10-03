"""Summarize coverage and metadata for the 102-station dynamics inputs.

This is a descriptive input audit. It does not classify phase-space paths or
select stations based on how strongly their plots resemble a cycle.

Run from the repository root:
    python3 scripts/audit_advanced_dynamics_stations.py
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "JMA-kaggle_dataest"
FIRST_BLOOM_CSV = DATA_DIR / "sakura_first_bloom_dates.csv"
FULL_BLOOM_CSV = DATA_DIR / "sakura_full_bloom_dates.csv"
OUTPUT_CSV = ROOT / "data" / "advanced_dynamics_station_audit.csv"


def year_columns(frame):
    """Return integer year columns, sorted chronologically."""
    return sorted(
        (column for column in frame.columns if str(column).strip().isdigit()),
        key=lambda column: int(str(column).strip()),
    )


def normalized_doy(value):
    """Map a date to a non-leap reference year, matching the plot generator."""
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return np.nan
    if parsed.month == 2 and parsed.day == 29:
        return 59.5
    return date(2001, parsed.month, parsed.day).timetuple().tm_yday


def summarize_series(row, years):
    valid_years = []
    doys = []
    for year in years:
        doy = normalized_doy(row.get(year))
        if not np.isnan(doy):
            valid_years.append(int(str(year).strip()))
            doys.append(doy)

    if not valid_years:
        return {
            "n": 0,
            "start": np.nan,
            "end": np.nan,
            "span": 0,
            "missing_within_span": 0,
            "max_gap_years": np.nan,
            "valid_years": set(),
            "normalized_doys": {},
        }

    valid_years = np.asarray(valid_years, dtype=int)
    gaps = np.diff(valid_years)
    return {
        "n": len(valid_years),
        "start": int(valid_years.min()),
        "end": int(valid_years.max()),
        "span": int(valid_years.max() - valid_years.min() + 1),
        "missing_within_span": int(valid_years.max() - valid_years.min() + 1 - len(valid_years)),
        # Gap is the number of calendar years between observations, e.g. 2 means
        # one intervening year is missing.
        "max_gap_years": int(gaps.max()) if len(gaps) else 0,
        "valid_years": set(valid_years.tolist()),
        "normalized_doys": dict(zip(valid_years.tolist(), doys)),
    }


def main():
    first = pd.read_csv(FIRST_BLOOM_CSV)
    full = pd.read_csv(FULL_BLOOM_CSV)
    first_years = year_columns(first)
    full_years = year_columns(full)

    # Use the first-bloom table's station order, while checking the full-bloom
    # table by name rather than assuming row order is identical.
    full_by_site = full.set_index("Site Name", drop=False)
    records = []
    for index, first_row in first.iterrows():
        site = first_row["Site Name"]
        first_summary = summarize_series(first_row, first_years)
        if site in full_by_site.index:
            full_row = full_by_site.loc[site]
            if isinstance(full_row, pd.DataFrame):
                full_row = full_row.iloc[0]
            full_summary = summarize_series(full_row, full_years)
            full_notes = full_row.get("Notes", "")
        else:
            full_summary = summarize_series(pd.Series(dtype=object), full_years)
            full_notes = ""

        common_years = first_summary["valid_years"] & full_summary["valid_years"]
        first_notes = first_row.get("Notes", "")
        notes = str(first_notes).strip() if pd.notna(first_notes) else ""
        full_notes = str(full_notes).strip() if pd.notna(full_notes) else ""
        records.append({
            "source_order": index + 1,
            "site_name": site,
            "currently_being_observed": first_row.get("Currently Being Observed", np.nan),
            "first_bloom_species_notes": notes,
            "full_bloom_species_notes": full_notes,
            "species_notes_match": notes == full_notes,
            "first_n": first_summary["n"],
            "first_start_year": first_summary["start"],
            "first_end_year": first_summary["end"],
            "first_span_years": first_summary["span"],
            "first_missing_within_span": first_summary["missing_within_span"],
            "first_max_gap_years": first_summary["max_gap_years"],
            "full_n": full_summary["n"],
            "full_start_year": full_summary["start"],
            "full_end_year": full_summary["end"],
            "full_span_years": full_summary["span"],
            "full_missing_within_span": full_summary["missing_within_span"],
            "full_max_gap_years": full_summary["max_gap_years"],
            "common_first_full_n": len(common_years),
            "common_first_full_start_year": min(common_years) if common_years else np.nan,
            "common_first_full_end_year": max(common_years) if common_years else np.nan,
            "first_full_notes_discrepancy": notes != full_notes,
        })

    result = pd.DataFrame(records)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_CSV, index=False)

    print(f"Stations audited: {len(result)}")
    print(f"Species-note mismatches: {int(result['first_full_notes_discrepancy'].sum())}")
    print("Top coverage stations (common first/full bloom years):")
    columns = ["site_name", "common_first_full_n", "common_first_full_start_year",
               "common_first_full_end_year", "first_bloom_species_notes"]
    print(result.sort_values("common_first_full_n", ascending=False)[columns].head(12).to_string(index=False))
    print(f"Wrote {OUTPUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
