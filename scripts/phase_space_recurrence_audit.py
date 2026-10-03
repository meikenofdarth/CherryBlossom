"""Quantify closure and recurrence in observed/smoothed phenology paths.

Four representative stations are analyzed using annual first/full bloom DOY.
The script compares raw finite differences, the selected smoothing spline
(s/n=25), and a 7-year Gaussian kernel. It also examines bloom-date versus
February-March temperature anomalies where matched JMA data are available.

Recurrence thresholds are prespecified diagnostics, not formal evidence of a
limit cycle: states must be at least 8 years apart, within 0.10 scaled phase
units, and (for the state-rate plane) have similarly directed local motion.
Run from the repository root:
    python3 scripts/phase_space_recurrence_audit.py
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
WEATHER_CSV = ROOT / "data" / "station_year_weather_jma.csv"
PLOT_DIR = ROOT / "plots" / "phase_space_recurrence_audit"
SUMMARY_CSV = ROOT / "data" / "phase_space_recurrence_audit.csv"
STATIONS = ["Kyoto", "Wakkanai", "Kagoshima", "Osaka"]
MIN_RETURN_LAG_YEARS = 8
RETURN_DISTANCE_THRESHOLD = 0.10


def normalized_doy(value):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return np.nan
    if parsed.month == 2 and parsed.day == 29:
        return 59.5
    return date(2001, parsed.month, parsed.day).timetuple().tm_yday


def load_phenology(path, site):
    frame = pd.read_csv(path)
    matches = frame.loc[frame["Site Name"] == site]
    if matches.empty:
        return np.array([], dtype=float), np.array([], dtype=float)
    row = matches.iloc[0]
    points = []
    for column in frame.columns:
        if str(column).strip().isdigit():
            doy = normalized_doy(row[column])
            if not np.isnan(doy):
                points.append((int(str(column).strip()), doy))
    points.sort()
    if not points:
        return np.array([], dtype=float), np.array([], dtype=float)
    years, values = np.asarray(points, dtype=float).T
    return years, values


def gaussian_kernel(years, values, bandwidth=7.0):
    delta = years[:, None] - years[None, :]
    weights = np.exp(-0.5 * (delta / bandwidth) ** 2)
    estimates = weights @ values / weights.sum(axis=1)
    derivative = np.sum(weights * delta * (values[None, :] - estimates[:, None]), axis=1)
    derivative /= bandwidth**2 * weights.sum(axis=1)
    return estimates, derivative


def local_direction(coords, years):
    if len(years) < 2:
        return np.zeros_like(coords)
    return np.gradient(coords, years, axis=0)


def recurrence_metrics(years, coords, threshold=RETURN_DISTANCE_THRESHOLD):
    """Return endpoint, early/late, and separated-return diagnostics."""
    if len(years) < 3:
        return {}
    distances = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=2))
    lag = np.abs(years[:, None] - years[None, :])
    eligible = np.triu(lag >= MIN_RETURN_LAG_YEARS, k=1)
    if not eligible.any():
        return {}

    eligible_distances = np.where(eligible, distances, np.inf)
    i_min, j_min = np.unravel_index(np.argmin(eligible_distances), eligible_distances.shape)
    directions = local_direction(coords, years)
    norm = np.linalg.norm(directions, axis=1)
    cosines = np.full_like(distances, np.nan)
    valid = np.outer(norm > 0, norm > 0)
    dot = directions @ directions.T
    cosines[valid] = dot[valid] / np.outer(norm, norm)[valid]
    close_returns = eligible & (distances <= threshold)
    aligned_returns = close_returns & (cosines >= 0.5)

    third = (years.max() - years.min()) / 3
    early = np.flatnonzero(years <= years.min() + third)
    late = np.flatnonzero(years >= years.max() - third)
    early_late_distances = distances[np.ix_(early, late)]
    early_pos, late_pos = np.unravel_index(np.argmin(early_late_distances), early_late_distances.shape)
    ei, li = int(early[early_pos]), int(late[late_pos])
    early_late_cosines = cosines[np.ix_(early, late)]
    early_late_close = early_late_distances <= threshold
    early_late_aligned = early_late_close & (early_late_cosines >= 0.5)

    path_length = float(np.linalg.norm(np.diff(coords, axis=0), axis=1).sum())
    endpoint_distance = float(np.linalg.norm(coords[-1] - coords[0]))
    nearest_cosine = float(cosines[i_min, j_min]) if np.isfinite(cosines[i_min, j_min]) else np.nan
    return {
        "endpoint_distance_scaled": endpoint_distance,
        "endpoint_distance_over_path_length": endpoint_distance / path_length if path_length else np.nan,
        "path_length_scaled": path_length,
        "closest_return_distance_scaled": float(distances[i_min, j_min]),
        "closest_return_year_1": int(years[i_min]),
        "closest_return_year_2": int(years[j_min]),
        "closest_return_lag_years": float(lag[i_min, j_min]),
        "closest_return_direction_cosine": nearest_cosine,
        "close_return_pair_count": int(close_returns.sum()),
        "aligned_close_return_pair_count": int(aligned_returns.sum()),
        "early_late_min_distance_scaled": float(early_late_distances[early_pos, late_pos]),
        "early_years_with_close_late_match": int(np.any(early_late_close, axis=1).sum()),
        "early_years_with_aligned_close_late_match": int(np.any(early_late_aligned, axis=1).sum()),
        "early_late_match_direction_cosine": float(cosines[ei, li]) if np.isfinite(cosines[ei, li]) else np.nan,
        "early_late_year_1": int(years[ei]),
        "early_late_year_2": int(years[li]),
    }


def scaled_state_rate(years, values, derivative):
    x_scale = max(float(np.ptp(values)), 1.0)
    dx_scale = max(float(np.ptp(derivative)), 0.1)
    return np.column_stack(((values - np.mean(values)) / x_scale,
                            (derivative - np.mean(derivative)) / dx_scale))


def scaled_driver_state(years, bloom, temperature):
    """Remove linear drift from state and driver before phase-plane comparison."""
    centered_years = years - years.mean()
    bloom_resid = bloom - np.polyval(np.polyfit(centered_years, bloom, 1), centered_years)
    temp_resid = temperature - np.polyval(np.polyfit(centered_years, temperature, 1), centered_years)
    scales = [max(float(np.ptp(bloom_resid)), 1.0), max(float(np.ptp(temp_resid)), 0.1)]
    return np.column_stack((bloom_resid / scales[0], temp_resid / scales[1]))


def add_metrics(records, station, stage, representation, years, coords, n_observations):
    metrics = recurrence_metrics(years, coords)
    if not metrics:
        return
    records.append({
        "station": station,
        "bloom_stage": stage,
        "representation": representation,
        "n_observations": n_observations,
        "start_year": int(years.min()),
        "end_year": int(years.max()),
        "minimum_return_lag_years": MIN_RETURN_LAG_YEARS,
        "return_distance_threshold_scaled": RETURN_DISTANCE_THRESHOLD,
        **metrics,
    })


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    weather = pd.read_csv(WEATHER_CSV)
    records = []
    bloom_sources = {
        "First bloom": (DATA_DIR / "sakura_first_bloom_dates.csv", "First_DOY"),
        "Full bloom": (DATA_DIR / "sakura_full_bloom_dates.csv", "Full_DOY"),
    }

    for station in STATIONS:
        station_weather = weather.loc[weather["Site Name"] == station].copy()
        fig, axes = plt.subplots(2, 2, figsize=(12.5, 9), constrained_layout=True)
        fig.suptitle(f"{station}: observed recurrence and climate-state checks", fontsize=14)

        for row_idx, (stage, (source, weather_doy_col)) in enumerate(bloom_sources.items()):
            years, values = load_phenology(source, station)
            ax_phase, ax_driver = axes[row_idx]
            if len(years) < 10:
                ax_phase.set_axis_off()
                ax_driver.set_axis_off()
                continue

            raw_derivative = np.gradient(values, years)
            spline = UnivariateSpline(years, values, s=25 * len(years))
            spline_values = spline(years)
            spline_derivative = spline.derivative()(years)
            kernel_values, kernel_derivative = gaussian_kernel(years, values)

            state_paths = [
                ("Observed finite difference", values, raw_derivative, "#777777", "o"),
                ("Spline s/n=25", spline_values, spline_derivative, "#e68613", "s"),
                ("Gaussian kernel h=7 y", kernel_values, kernel_derivative, "#377eb8", "^"),
            ]
            for label, state, derivative, color, marker in state_paths:
                coords = scaled_state_rate(years, state, derivative)
                add_metrics(records, station, stage, label, years, coords, len(years))
                ax_phase.plot(coords[:, 0], coords[:, 1], color=color, alpha=0.72,
                              lw=1.2, marker=marker, markevery=max(1, len(years) // 12),
                              ms=3.5, label=label)
                ax_phase.scatter(coords[0, 0], coords[0, 1], color=color, marker="o", s=36,
                                 edgecolor="black", linewidth=0.4, zorder=4)
                ax_phase.scatter(coords[-1, 0], coords[-1, 1], color=color, marker="*", s=65,
                                 edgecolor="black", linewidth=0.4, zorder=4)

            # Compare bloom-state recurrence jointly with an independent JMA
            # temperature driver, after removing linear drift from each series.
            matched = pd.DataFrame({"Year": years.astype(int), "Bloom": values}).merge(
                station_weather[["Year", weather_doy_col, "Feb_Mar_Temp"]],
                on="Year", how="inner",
            ).dropna(subset=["Bloom", "Feb_Mar_Temp"])
            if len(matched) >= 10:
                climate_years = matched["Year"].to_numpy(dtype=float)
                bloom = matched["Bloom"].to_numpy(dtype=float)
                temp = matched["Feb_Mar_Temp"].to_numpy(dtype=float)
                driver_coords = scaled_driver_state(climate_years, bloom, temp)
                add_metrics(records, station, stage, "Bloom vs detrended Feb-Mar temperature",
                            climate_years, driver_coords, len(matched))
                bloom_residual = bloom - np.polyval(
                    np.polyfit(climate_years - climate_years.mean(), bloom, 1),
                    climate_years - climate_years.mean(),
                )
                temp_residual = temp - np.polyval(
                    np.polyfit(climate_years - climate_years.mean(), temp, 1),
                    climate_years - climate_years.mean(),
                )
                records[-1]["detrended_bloom_temperature_correlation"] = float(
                    np.corrcoef(bloom_residual, temp_residual)[0, 1]
                )
                ax_driver.plot(driver_coords[:, 0], driver_coords[:, 1], color="#4daf4a",
                               lw=1.1, marker="o", ms=3.2, alpha=0.75,
                               label="Bloom vs temperature anomalies")
                ax_driver.scatter(driver_coords[0, 0], driver_coords[0, 1], color="#4daf4a",
                                  marker="o", s=40, edgecolor="black", label="Start")
                ax_driver.scatter(driver_coords[-1, 0], driver_coords[-1, 1], color="#4daf4a",
                                  marker="*", s=75, edgecolor="black", label="End")
                ax_driver.set_title(f"{stage}: state vs detrended Feb–Mar temperature (n={len(matched)})")
                ax_driver.set_xlabel("Bloom DOY anomaly / range")
                ax_driver.set_ylabel("Temperature anomaly / range")
                ax_driver.axhline(0, color="0.6", lw=0.6)
                ax_driver.axvline(0, color="0.6", lw=0.6)
                ax_driver.grid(alpha=0.25)
                ax_driver.legend(fontsize=7)
            else:
                ax_driver.text(0.5, 0.5, f"Insufficient matched JMA temperature data (n={len(matched)})",
                               ha="center", va="center", transform=ax_driver.transAxes)
                ax_driver.set_axis_off()

            ax_phase.set_title(f"{stage}: scaled state-rate path; start ○, end ★")
            ax_phase.set_xlabel("Centered bloom state / range")
            ax_phase.set_ylabel("Centered rate / derivative range")
            ax_phase.axhline(0, color="0.55", lw=0.6)
            ax_phase.grid(alpha=0.25)
            ax_phase.legend(fontsize=7, loc="best")

        fig.savefig(PLOT_DIR / f"{station.lower()}_recurrence.png", dpi=170)
        plt.close(fig)

    summary = pd.DataFrame(records)
    summary.to_csv(SUMMARY_CSV, index=False)
    print(f"Recurrence representations summarized: {len(summary)}")
    print(f"Minimum return lag: {MIN_RETURN_LAG_YEARS} years; scaled distance threshold: {RETURN_DISTANCE_THRESHOLD:.2f}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"Wrote plots to {PLOT_DIR.relative_to(ROOT)}")
    view = summary[["station", "bloom_stage", "representation",
                    "endpoint_distance_over_path_length", "closest_return_distance_scaled",
                    "closest_return_lag_years", "aligned_close_return_pair_count"]]
    print(view.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
