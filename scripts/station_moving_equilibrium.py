import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


PHENOLOGY_FILE = 'data/station_year_phenology.csv'
WEATHER_FILE = 'data/station_year_weather.csv'
WEATHER_FILE = os.environ.get('WEATHER_FILE', WEATHER_FILE)
OUTPUT = 'data/station_moving_equilibrium.csv'
PLOT = 'plots/station_moving_equilibrium.png'
if WEATHER_FILE.endswith('weather_jma.csv'):
    OUTPUT = 'data/station_moving_equilibrium_jma.csv'
    PLOT = 'plots/station_moving_equilibrium_jma.png'
TRAIN_END = 1990


def rmse(actual, predicted):
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def build_data():
    phenology = pd.read_csv(PHENOLOGY_FILE)
    weather = pd.read_csv(WEATHER_FILE)
    data = phenology[phenology['Main_Analysis_Eligible']].merge(
        weather[['Site Name', 'Year', 'Feb_Mar_Temp']],
        on=['Site Name', 'Year'],
        how='inner',
        validate='one_to_one',
    )
    return data.sort_values(['Site Name', 'Year'])


def fit_station(site, group):
    group = group.sort_values('Year').copy()
    group['Previous_DOY'] = group['Full_DOY'].shift(1)
    group['Previous_Year'] = group['Year'].shift(1)
    group['Year_Gap'] = group['Year'] - group['Previous_Year']
    group = group[(group['Year_Gap'] == 1) & group['Previous_DOY'].notna()].copy()
    train = group[group['Year'] <= TRAIN_END]
    test = group[group['Year'] > TRAIN_END]
    if len(train) < 20 or len(test) < 5:
        return None

    # D_t = a + phi D_(t-1) + beta T_t + gamma t + error.
    # If 0 < phi < 1, this resembles relaxation toward a moving equilibrium.
    features = ['Previous_DOY', 'Feb_Mar_Temp', 'Year']
    model = sm.OLS(train['Full_DOY'], sm.add_constant(train[features])).fit()
    baseline = sm.OLS(train['Full_DOY'], sm.add_constant(train[['Feb_Mar_Temp']])).fit()
    train_prediction = model.predict(sm.add_constant(train[features], has_constant='add'))
    test_prediction = model.predict(sm.add_constant(test[features], has_constant='add'))
    baseline_test_prediction = baseline.predict(
        sm.add_constant(test[['Feb_Mar_Temp']], has_constant='add')
    )
    phi = model.params['Previous_DOY']
    relaxation_rate = 1 - phi

    return {
        'Site Name': site,
        'Species': group['Species'].iloc[0],
        'n_train': len(train),
        'n_test': len(test),
        'phi_previous_year': phi,
        'relaxation_rate': relaxation_rate,
        'relaxation_CI_Lower': -model.conf_int().loc['Previous_DOY', 1],
        'relaxation_CI_Upper': -model.conf_int().loc['Previous_DOY', 0],
        'Temperature_Coefficient': model.params['Feb_Mar_Temp'],
        'Year_Coefficient': model.params['Year'],
        'R2_train': model.rsquared,
        'RMSE_train': rmse(train['Full_DOY'].to_numpy(), train_prediction.to_numpy()),
        'RMSE_test': rmse(test['Full_DOY'].to_numpy(), test_prediction.to_numpy()),
        'Baseline_RMSE_test': rmse(
            test['Full_DOY'].to_numpy(), baseline_test_prediction.to_numpy()
        ),
        'RMSE_Improvement': rmse(
            test['Full_DOY'].to_numpy(), baseline_test_prediction.to_numpy()
        ) - rmse(test['Full_DOY'].to_numpy(), test_prediction.to_numpy()),
        'Model': model,
        'Train': train,
        'Test': test,
        'Test_Prediction': test_prediction,
    }


def main():
    data = build_data()
    fits = []
    for site, group in data.groupby('Site Name'):
        fit = fit_station(site, group)
        if fit is not None:
            fits.append(fit)

    rows = [{key: value for key, value in fit.items() if key not in {'Model', 'Train', 'Test', 'Test_Prediction'}} for fit in fits]
    result = pd.DataFrame(rows).sort_values('RMSE_test')
    result.to_csv(OUTPUT, index=False)

    print('=== TEMPERATURE-FORCED MOVING-EQUILIBRIUM MODEL ===')
    print('Model: Full_DOY(t) = a + phi*Full_DOY(t-1) + beta*FebMar_Temp(t) + gamma*Year(t)')
    print(f'Training years: <= {TRAIN_END}; test years: > {TRAIN_END}')
    print('Temperature source: Open-Meteo archive; not JMA observed temperatures.')
    print(result.to_string(index=False, float_format=lambda value: f'{value:.4f}'))
    print(f'\nStations fitted: {len(result)}')
    print(f'Median test RMSE: {result["RMSE_test"].median():.4f} days')
    print(f'Median baseline test RMSE: {result["Baseline_RMSE_test"].median():.4f} days')
    print(f'Stations improved over baseline: {(result["RMSE_Improvement"] > 0).sum()} of {len(result)}')
    relaxation_includes_zero = (
        (result['relaxation_CI_Lower'] <= 0)
        & (result['relaxation_CI_Upper'] >= 0)
    ).sum()
    print(f'Median relaxation rate: {result["relaxation_rate"].median():.4f} per year')
    print(f'Relaxation CIs including zero: {relaxation_includes_zero} of {len(result)}')
    print('Interpretation rule: a relaxation interpretation requires 0 < phi < 1; this is not a tipping-point test.')

    best = result.iloc[0]
    best_fit = next(fit for fit in fits if fit['Site Name'] == best['Site Name'])
    plt.figure(figsize=(10, 5))
    plt.plot(best_fit['Test']['Year'], best_fit['Test']['Full_DOY'], 'o-', label='Observed')
    plt.plot(best_fit['Test']['Year'], best_fit['Test_Prediction'], 's--', label='Moving-equilibrium prediction')
    plt.xlabel('Year')
    plt.ylabel('Full-bloom DOY')
    plt.title(f'Moving-Equilibrium Test Prediction: {best_fit["Site Name"]}')
    plt.legend()
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig(PLOT, dpi=300)
    plt.close()
    print(f'Saved {OUTPUT}')
    print(f'Saved {PLOT}')


if __name__ == '__main__':
    main()
