"""Test how phase-space paths change with smoothing and derivative choices.

The analysis uses four prespecified representative stations and both bloom
dates. It compares smoothing splines at fixed residual budgets with a Gaussian
kernel smoother evaluated on actual calendar years. The unsmoothed annual
finite-difference path is included as a noisy reference.

Run from the repository root:
    python3 scripts/phase_space_smoothing_sensitivity.py
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
PLOT_DIR = ROOT / "plots" / "phase_space_smoothing_sensitivity"
SUMMARY_CSV = ROOT / "data" / "phase_space_smoothing_sensitivity.csv"
STATIONS = ["Kyoto", "Wakkanai", "Kagoshima", "Osaka"]
SPLINE_S_PER_POINT = [0, 5, 25, 100]
KERNEL_BANDWIDTHS_YEARS = [3, 7, 12]
GRID_SIZE = 600
SPLINE_COLORS = {0: "#9aa0a6", 5: "#377eb8", 25: "#e68613", 100: "#d62728"}
KERNEL_COLORS = {3: "#4daf4a", 7: "#984ea3", 12: "#795548"}


def normalized_doy(value):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return np.nan
    if parsed.month == 2 and parsed.day == 29:
        return 59.5
    return date(2001, parsed.month, parsed.day).timetuple().tm_yday


def load_series(path, site):
    frame = pd.read_csv(path)
    match = frame.loc[frame["Site Name"] == site]
    if match.empty:
        return np.array([], dtype=float), np.array([], dtype=float)
    row = match.iloc[0]
    pairs = []
    for column in frame.columns:
        if str(column).strip().isdigit():
            doy = normalized_doy(row[column])
            if not np.isnan(doy):
                pairs.append((int(str(column).strip()), doy))
    pairs.sort()
    if not pairs:
        return np.array([], dtype=float), np.array([], dtype=float)
    years, doys = np.asarray(pairs, dtype=float).T
    return years, doys


def kernel_smooth(years, values, grid, bandwidth):
    """Gaussian local-constant estimate and its analytic time derivative."""
    delta = years[None, :] - grid[:, None]
    weights = np.exp(-0.5 * (delta / bandwidth) ** 2)
    weight_sum = weights.sum(axis=1)
    estimate = (weights @ values) / weight_sum
    derivative = (weights * delta) @ (values - estimate[:, None]).T
    derivative = np.diag(derivative) / (bandwidth**2 * weight_sum)
    return estimate, derivative


def path_metrics(x, dx, scale_x, scale_dx):
    coords = np.column_stack((x / scale_x, dx / scale_dx))
    steps = np.diff(coords, axis=0)
    length = float(np.linalg.norm(steps, axis=1).sum())
    displacement = float(np.linalg.norm(coords[-1] - coords[0]))
    closure = float(displacement / np.sqrt(2))
    # Count reversals in the smoothed state variable, ignoring exact zeros.
    signs = np.sign(np.diff(x))
    signs = signs[signs != 0]
    reversals = int(np.sum(signs[1:] != signs[:-1])) if len(signs) > 1 else 0
    return length, displacement, closure, reversals


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    sources = {
        "First bloom": DATA_DIR / "sakura_first_bloom_dates.csv",
        "Full bloom": DATA_DIR / "sakura_full_bloom_dates.csv",
    }
    records = []

    for station in STATIONS:
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), constrained_layout=True)
        fig.suptitle(f"{station}: phase-space sensitivity to smoothing", fontsize=14)

        for ax, (bloom_label, source) in zip(axes, sources.items()):
            years, values = load_series(source, station)
            if len(years) < 10:
                ax.set_title(f"{bloom_label}: insufficient data (n={len(years)})")
                continue

            grid = np.linspace(years.min(), years.max(), GRID_SIZE)
            raw_dx = np.gradient(values, years)
            raw_scale_x = max(float(np.ptp(values)), 1.0)
            raw_scale_dx = max(float(np.ptp(raw_dx)), 0.1)
            scale_dx = raw_scale_dx

            ax.scatter(values, raw_dx, color="0.55", s=12, alpha=0.55,
                       label="Annual finite differences", zorder=1)

            reference_path = None
            plotted = []
            for s_per_point in SPLINE_S_PER_POINT:
                spline = UnivariateSpline(years, values, s=s_per_point * len(years))
                smooth_x = spline(grid)
                smooth_dx = spline.derivative()(grid)
                label = f"Spline s/n={s_per_point:g}"
                line, = ax.plot(
                    smooth_x, smooth_dx, lw=2.2 if s_per_point == 25 else 1.5,
                    alpha=0.9 if s_per_point in (25, 100) else 0.65,
                    color=SPLINE_COLORS[s_per_point], label=label,
                )
                plotted.append((label, smooth_x, smooth_dx, line.get_color(), s_per_point))
                if s_per_point == 25:
                    reference_path = np.column_stack((smooth_x, smooth_dx))

            for bandwidth in KERNEL_BANDWIDTHS_YEARS:
                smooth_x, smooth_dx = kernel_smooth(years, values, grid, bandwidth)
                label = f"Gaussian kernel h={bandwidth} y"
                line, = ax.plot(
                    smooth_x, smooth_dx, lw=1.7, ls="--", alpha=0.9,
                    color=KERNEL_COLORS[bandwidth], label=label,
                )
                plotted.append((label, smooth_x, smooth_dx, line.get_color(), bandwidth))

            # Use observed state and finite-difference ranges for common scaling
            # across all candidate paths at this station and bloom stage.
            scale_x = raw_scale_x
            for label, smooth_x, smooth_dx, color, parameter in plotted:
                length, displacement, closure, reversals = path_metrics(
                    smooth_x, smooth_dx, scale_x, scale_dx
                )
                rmse = np.nan
                if label.startswith("Spline"):
                    s_per_point = parameter
                    fitted = UnivariateSpline(years, values, s=s_per_point * len(years))(years)
                    rmse = float(np.sqrt(np.mean((values - fitted) ** 2)))
                coords = np.column_stack((smooth_x / scale_x, smooth_dx / scale_dx))
                hausdorff_to_reference = np.nan
                if reference_path is not None:
                    ref = reference_path.copy()
                    ref[:, 0] /= scale_x
                    ref[:, 1] /= scale_dx
                    # Symmetric discrete Hausdorff distance, measured in ranges
                    # of the observed state and raw derivative.
                    distances = np.sqrt(((coords[:, None, :] - ref[None, :, :]) ** 2).sum(axis=2))
                    hausdorff_to_reference = float(max(distances.min(axis=0).max(), distances.min(axis=1).max()))
                records.append({
                    "station": station,
                    "bloom_stage": bloom_label,
                    "n_observations": len(years),
                    "start_year": int(years.min()),
                    "end_year": int(years.max()),
                    "method": label.split()[0],
                    "spline_s_per_observation": parameter if label.startswith("Spline") else np.nan,
                    "kernel_bandwidth_years": parameter if label.startswith("Gaussian") else np.nan,
                    "fit_rmse_days": rmse,
                    "phase_path_length_scaled": length,
                    "endpoint_distance_scaled": displacement,
                    "closure_distance_scaled_0_to_1": closure,
                    "state_direction_reversals": reversals,
                    "hausdorff_distance_to_spline_s25_scaled": hausdorff_to_reference,
                })

            ax.set_title(f"{bloom_label} (n={len(years)}, {int(years.min())}–{int(years.max())})")
            ax.set_xlabel("Bloom date (normalized day of year)")
            ax.set_ylabel("Rate of change (days/year)")
            ax.axhline(0, color="0.35", lw=0.8)
            ax.grid(alpha=0.25)
            ax.legend(fontsize=7, loc="best", ncol=2)

        fig.savefig(PLOT_DIR / f"{station.lower()}_sensitivity.png", dpi=170)
        plt.close(fig)

    summary = pd.DataFrame(records)
    summary.to_csv(SUMMARY_CSV, index=False)
    print(f"Stations: {len(STATIONS)}; candidate paths summarized: {len(summary)}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"Wrote sensitivity plots to {PLOT_DIR.relative_to(ROOT)}")
    print("Spline residual RMSE by smoothing level:")
    print(summary.loc[summary["method"] == "Spline"].groupby(
        ["bloom_stage", "spline_s_per_observation"]
    )["fit_rmse_days"].median().round(2).to_string())


if __name__ == "__main__":
    main()
