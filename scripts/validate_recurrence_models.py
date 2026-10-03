"""Compare trend, JMA-temperature and recurrence models out of sample.

Uses four representative stations and first/full bloom separately. Every model
uses the same JMA-weather matched years and the same chronological split
(training through 1990; testing after 1990). An AR model is evaluated as a
one-step-ahead forecast using the previous observed bloom date. A periodic
component is selected using training data only.

Run from the repository root:
    python3 scripts/validate_recurrence_models.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WEATHER_CSV = ROOT / "data" / "station_year_weather_jma.csv"
OUTPUT_CSV = ROOT / "data" / "recurrence_model_holdout_scores.csv"
PREDICTIONS_CSV = ROOT / "data" / "recurrence_model_holdout_predictions.csv"
PLOT_DIR = ROOT / "plots" / "recurrence_model_holdout"
STATIONS = ["Kyoto", "Wakkanai", "Kagoshima", "Osaka"]
TRAIN_END_YEAR = 1990
MIN_TRAIN_N = 20
MIN_TEST_N = 8
PERIOD_MIN = 3.0
PERIOD_MAX_CAP = 15.0
PERIOD_STEP = 0.05


def design_matrix(years, temperatures, previous=None, period=None, year_origin=None):
    if year_origin is None:
        year_origin = float(np.mean(years))
    columns = [np.ones(len(years))]
    if previous is not None:
        columns.append(np.asarray(previous, dtype=float))
    columns.append(np.asarray(temperatures, dtype=float))
    columns.append(np.asarray(years, dtype=float) - year_origin)
    if period is not None:
        phase = 2 * np.pi * (np.asarray(years, dtype=float) - year_origin) / period
        columns.extend([np.sin(phase), np.cos(phase)])
    return np.column_stack(columns)


def fit_predict(train_x, train_y, test_x):
    coefficients, *_ = np.linalg.lstsq(train_x, train_y, rcond=None)
    return train_x @ coefficients, test_x @ coefficients, coefficients


def rmse(actual, predicted):
    return float(np.sqrt(np.mean((np.asarray(actual) - np.asarray(predicted)) ** 2)))


def mae(actual, predicted):
    return float(np.mean(np.abs(np.asarray(actual) - np.asarray(predicted))))


def selected_period(years, values, temperatures, train_mask, year_origin):
    train_years = years[train_mask]
    train_y = values[train_mask]
    train_t = temperatures[train_mask]
    span = float(train_years.max() - train_years.min())
    max_period = min(PERIOD_MAX_CAP, span / 2)
    if max_period <= PERIOD_MIN:
        return np.nan
    best_period, best_rss = np.nan, np.inf
    for period in np.arange(PERIOD_MIN, max_period + PERIOD_STEP / 2, PERIOD_STEP):
        x = design_matrix(train_years, train_t, period=period, year_origin=year_origin)
        prediction, _, _ = fit_predict(x, train_y, x)
        rss = float(np.sum((train_y - prediction) ** 2))
        if rss < best_rss:
            best_rss, best_period = rss, float(period)
    return best_period


def evaluate_station_stage(site, stage, data):
    y_col = "First_DOY" if stage == "First bloom" else "Full_DOY"
    group = data.loc[data["Site Name"] == site,
                     ["Site Name", "Year", y_col, "Feb_Mar_Temp"]].dropna().copy()
    group = group.sort_values("Year")
    group["Previous_DOY"] = group[y_col].shift(1)
    group["Year_Gap"] = group["Year"].diff()
    # A common paired sample permits a fair comparison with the one-step AR model.
    group = group.loc[(group["Year_Gap"] == 1) & group["Previous_DOY"].notna()].copy()
    if group.empty:
        return [], []

    years = group["Year"].to_numpy(dtype=float)
    values = group[y_col].to_numpy(dtype=float)
    temperatures = group["Feb_Mar_Temp"].to_numpy(dtype=float)
    previous = group["Previous_DOY"].to_numpy(dtype=float)
    train_mask = years <= TRAIN_END_YEAR
    test_mask = years > TRAIN_END_YEAR
    n_train, n_test = int(train_mask.sum()), int(test_mask.sum())
    if n_train < MIN_TRAIN_N or n_test < MIN_TEST_N:
        return [], []

    year_origin = float(years[train_mask].mean())
    fitted_period = selected_period(years, values, temperatures, train_mask, year_origin)
    models = {
        "Temperature only": (
            design_matrix(years, temperatures, year_origin=year_origin, period=None)[:, [0, 1]],
            None,
        ),
        "Trend only": (
            np.column_stack((np.ones(len(years)), years - year_origin)), None,
        ),
        "Trend + temperature": (
            design_matrix(years, temperatures, year_origin=year_origin), None,
        ),
        "Trend + temperature + selected period": (
            design_matrix(years, temperatures, year_origin=year_origin, period=fitted_period),
            fitted_period,
        ),
        "AR(1) + trend + temperature (one-step)": (
            design_matrix(years, temperatures, previous=previous, year_origin=year_origin), None,
        ),
    }

    score_rows, prediction_rows = [], []
    for model_name, (design, period) in models.items():
        train_prediction, test_prediction, coefficients = fit_predict(
            design[train_mask], values[train_mask], design[test_mask]
        )
        actual_test = values[test_mask]
        score_rows.append({
            "station": site,
            "bloom_stage": stage,
            "model": model_name,
            "n_train": n_train,
            "n_test": n_test,
            "train_end_year": TRAIN_END_YEAR,
            "test_start_year": int(years[test_mask].min()),
            "test_end_year": int(years[test_mask].max()),
            "selected_period_years": period,
            "train_rmse_days": rmse(values[train_mask], train_prediction),
            "test_rmse_days": rmse(actual_test, test_prediction),
            "test_mae_days": mae(actual_test, test_prediction),
            "test_bias_days": float(np.mean(test_prediction - actual_test)),
            "forecast_type": "one-step using previous observed bloom" if "AR(1)" in model_name else "direct held-out prediction",
        })
        for year, actual, prediction in zip(years[test_mask], actual_test, test_prediction):
            prediction_rows.append({
                "station": site,
                "bloom_stage": stage,
                "model": model_name,
                "year": int(year),
                "observed_doy": float(actual),
                "predicted_doy": float(prediction),
                "selected_period_years": period,
            })
    return score_rows, prediction_rows


def plot_predictions(site, predictions):
    subset = predictions.loc[predictions["station"] == site]
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), constrained_layout=True)
    fig.suptitle(f"{site}: held-out bloom predictions (test years > {TRAIN_END_YEAR})")
    for ax, stage in zip(axes, ["First bloom", "Full bloom"]):
        panel = subset.loc[subset["bloom_stage"] == stage]
        if panel.empty:
            ax.set_axis_off()
            continue
        observed = panel.drop_duplicates("year").sort_values("year")
        ax.plot(observed["year"], observed["observed_doy"], "ko-", lw=1.6,
                ms=3.5, label="Observed")
        for model, group in panel.groupby("model", sort=False):
            group = group.sort_values("year")
            ax.plot(group["year"], group["predicted_doy"], lw=1.2, alpha=0.8,
                    label=model)
        ax.set_title(stage)
        ax.set_xlabel("Year")
        ax.set_ylabel("Bloom date (day of year)")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7, ncol=2)
    fig.savefig(PLOT_DIR / f"{site.lower()}_heldout_predictions.png", dpi=170)
    plt.close(fig)


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(WEATHER_CSV)
    score_rows, prediction_rows = [], []
    for site in STATIONS:
        for stage in ["First bloom", "Full bloom"]:
            scores, predictions = evaluate_station_stage(site, stage, data)
            score_rows.extend(scores)
            prediction_rows.extend(predictions)

    scores = pd.DataFrame(score_rows)
    predictions = pd.DataFrame(prediction_rows)
    scores.to_csv(OUTPUT_CSV, index=False)
    predictions.to_csv(PREDICTIONS_CSV, index=False)
    for site in STATIONS:
        plot_predictions(site, predictions)

    print(f"Station/stage/model score rows: {len(scores)}")
    print(f"All models use the same consecutive-year JMA-matched observations; split: <= {TRAIN_END_YEAR} / > {TRAIN_END_YEAR}.")
    print("AR forecasts are one-step-ahead using the previous observed bloom date.")
    print(f"Wrote {OUTPUT_CSV.relative_to(ROOT)}")
    print(f"Wrote {PREDICTIONS_CSV.relative_to(ROOT)}")
    print(f"Wrote plots to {PLOT_DIR.relative_to(ROOT)}")
    summary = scores.groupby("model")["test_rmse_days"].agg(["median", "mean", "count"])
    print("Median test RMSE by model:")
    print(summary.round(3).to_string())
    print("Per-station and bloom-stage test RMSE:")
    print(scores.pivot_table(index=["station", "bloom_stage"], columns="model",
                             values="test_rmse_days").round(2).to_string())


if __name__ == "__main__":
    main()
