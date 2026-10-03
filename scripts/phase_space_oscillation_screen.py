"""Screen annual bloom-date residuals for detrending-sensitive periods.

This exploratory screen uses the four representative stations, analyzes first
and full bloom separately, and compares linear, quadratic, and smoothing-spline
trends. A least-squares sinusoid scan handles missing years using actual year
values. It does not calculate significance or validate periodic predictions.

Run from the repository root:
    python3 scripts/phase_space_oscillation_screen.py
"""

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "JMA-kaggle_dataest"
PLOT_DIR = ROOT / "plots" / "phase_space_oscillation_screen"
SUMMARY_CSV = ROOT / "data" / "phase_space_oscillation_screen.csv"
STATIONS = ["Kyoto", "Wakkanai", "Kagoshima", "Osaka"]
PERIOD_MIN_YEARS = 3.0
PERIOD_MAX_YEARS = 30.0
FREQUENCY_COUNT = 1200
TOP_PERIODS = 3
METHODS = ["linear", "quadratic", "smoothing_spline_s25"]


def normalized_doy(value):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return np.nan
    if parsed.month == 2 and parsed.day == 29:
        return 59.5
    return date(2001, parsed.month, parsed.day).timetuple().tm_yday


def load_series(path, site):
    frame = pd.read_csv(path)
    matches = frame.loc[frame["Site Name"] == site]
    if matches.empty:
        return np.array([], dtype=float), np.array([], dtype=float)
    row = matches.iloc[0]
    points = []
    for column in frame.columns:
        if str(column).strip().isdigit():
            value = normalized_doy(row[column])
            if not np.isnan(value):
                points.append((int(str(column).strip()), value))
    points.sort()
    if not points:
        return np.array([], dtype=float), np.array([], dtype=float)
    years, doys = np.asarray(points, dtype=float).T
    return years, doys


def fit_trend(years, values, method):
    centered_years = years - years.mean()
    if method == "linear":
        coefficients = np.polyfit(centered_years, values, 1)
        fitted = np.polyval(coefficients, centered_years)
        trend_grid = None
        return fitted, lambda grid: np.polyval(coefficients, grid - years.mean())
    if method == "quadratic":
        coefficients = np.polyfit(centered_years, values, 2)
        fitted = np.polyval(coefficients, centered_years)
        return fitted, lambda grid: np.polyval(coefficients, grid - years.mean())
    spline = UnivariateSpline(years, values, s=25 * len(years))
    return spline(years), lambda grid: spline(grid)


def sinusoid_scan(years, residuals):
    """Return variance reduction from fitting sin/cos at each frequency."""
    frequencies = np.linspace(1 / PERIOD_MAX_YEARS, 1 / PERIOD_MIN_YEARS,
                              FREQUENCY_COUNT)
    centered = residuals - residuals.mean()
    null_ss = float(centered @ centered)
    powers = np.zeros_like(frequencies)
    if null_ss <= 0:
        return 1 / frequencies, powers

    for index, frequency in enumerate(frequencies):
        phase = 2 * np.pi * frequency * years
        design = np.column_stack((np.sin(phase), np.cos(phase)))
        coefficients, *_ = np.linalg.lstsq(design, centered, rcond=None)
        unexplained = centered - design @ coefficients
        powers[index] = max(0.0, 1 - float(unexplained @ unexplained) / null_ss)
    return 1 / frequencies, powers


def separated_peak_indices(periods, powers, count):
    order = np.argsort(powers)[::-1]
    selected = []
    for index in order:
        if all(abs(periods[index] - periods[other]) >= 1.0 for other in selected):
            selected.append(int(index))
            if len(selected) == count:
                break
    return selected


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    sources = {
        "First bloom": DATA_DIR / "sakura_first_bloom_dates.csv",
        "Full bloom": DATA_DIR / "sakura_full_bloom_dates.csv",
    }
    records = []
    colors = {"linear": "#377eb8", "quadratic": "#e68613",
              "smoothing_spline_s25": "#d62728"}

    for station in STATIONS:
        fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
        fig.suptitle(f"{station}: trend and exploratory period screen", fontsize=14)
        for row_index, (bloom_label, source) in enumerate(sources.items()):
            years, values = load_series(source, station)
            ax_time, ax_spectrum = axes[row_index]
            if len(years) < 20:
                ax_time.text(0.5, 0.5, f"Insufficient data (n={len(years)})",
                             ha="center", va="center", transform=ax_time.transAxes)
                ax_spectrum.set_axis_off()
                continue

            dense_years = np.linspace(years.min(), years.max(), 500)
            ax_time.scatter(years, values, color="0.25", s=14, alpha=0.6,
                            label="Observed normalized DOY")
            ax_time.set_title(f"{bloom_label}: observations and trend fits (n={len(years)})")
            ax_time.set_xlabel("Year")
            ax_time.set_ylabel("Bloom date (day of year)")
            ax_time.grid(alpha=0.25)

            for method in METHODS:
                fitted, trend_at = fit_trend(years, values, method)
                residuals = values - fitted
                periods, powers = sinusoid_scan(years, residuals)
                ax_time.plot(dense_years, trend_at(dense_years), color=colors[method],
                             lw=1.8, label=method.replace("_", " "))
                ax_spectrum.plot(periods, powers, color=colors[method], lw=1.6,
                                 label=method.replace("_", " "))

                peak_indices = separated_peak_indices(periods, powers, TOP_PERIODS)
                top = [(float(periods[i]), float(powers[i])) for i in peak_indices]
                record = {
                    "station": station,
                    "bloom_stage": bloom_label,
                    "n_observations": len(years),
                    "start_year": int(years.min()),
                    "end_year": int(years.max()),
                    "max_observation_gap_years": int(np.diff(years).max()),
                    "detrending_method": method,
                    "residual_sd_days": float(np.std(residuals, ddof=1)),
                }
                for rank in range(TOP_PERIODS):
                    record[f"peak{rank + 1}_period_years"] = top[rank][0] if rank < len(top) else np.nan
                    record[f"peak{rank + 1}_variance_reduction"] = top[rank][1] if rank < len(top) else np.nan
                records.append(record)

            ax_time.legend(fontsize=8, loc="best")
            ax_spectrum.set_title(f"{bloom_label}: sinusoid scan of detrended residuals")
            ax_spectrum.set_xlabel("Candidate period (years)")
            ax_spectrum.set_ylabel("Fraction of residual variance explained")
            ax_spectrum.set_xlim(PERIOD_MIN_YEARS, PERIOD_MAX_YEARS)
            ax_spectrum.grid(alpha=0.25)
            ax_spectrum.legend(fontsize=8, loc="best")

        fig.savefig(PLOT_DIR / f"{station.lower()}_trend_period_screen.png", dpi=170)
        plt.close(fig)

    summary = pd.DataFrame(records)
    summary.to_csv(SUMMARY_CSV, index=False)
    print(f"Station-stage-method records: {len(summary)}")
    print(f"Candidate periods scanned: {PERIOD_MIN_YEARS:g}–{PERIOD_MAX_YEARS:g} years")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"Wrote plots to {PLOT_DIR.relative_to(ROOT)}")
    print("Top period for each station, bloom stage and detrending method:")
    view = summary[["station", "bloom_stage", "detrending_method",
                    "peak1_period_years", "peak1_variance_reduction"]]
    print(view.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
