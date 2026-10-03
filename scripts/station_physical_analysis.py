import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm


PHENOLOGY_FILE = 'data/station_year_phenology.csv'
WEATHER_FILE = 'data/station_year_weather.csv'
WEATHER_FILE = os.environ.get('WEATHER_FILE', WEATHER_FILE)
COORDS_FILE = 'data/JMA-kaggle_dataest/station_coords_template.csv'
OUTPUT_SUFFIX = '_jma' if WEATHER_FILE.endswith('weather_jma.csv') else ''
SENSITIVITY_OUTPUT = f'data/station_temperature_sensitivity{OUTPUT_SUFFIX}.csv'
DYNAMICS_OUTPUT = f'data/station_restoring_force{OUTPUT_SUFFIX}.csv'
LATITUDE_OUTPUT = f'data/station_duration_slope_latitude{OUTPUT_SUFFIX}.csv'
TEMP_SLOPE_LATITUDE_OUTPUT = f'data/station_duration_temperature_slope_latitude{OUTPUT_SUFFIX}.csv'
DYNAMICS_PLOT = f'plots/station_phase_space_selected{OUTPUT_SUFFIX}.png'
LATITUDE_PLOT = f'plots/station_temperature_slope_latitude{OUTPUT_SUFFIX}.png'


def fit_temperature_slopes():
    phenology = pd.read_csv(PHENOLOGY_FILE)
    weather = pd.read_csv(WEATHER_FILE)
    coords = pd.read_csv(COORDS_FILE)
    data = phenology[phenology['Main_Analysis_Eligible']].merge(
        weather[['Site Name', 'Year', 'Mar_Temp', 'Feb_Mar_Temp']],
        on=['Site Name', 'Year'],
        how='inner',
        validate='one_to_one',
    )

    rows = []
    for site, group in data.groupby('Site Name'):
        bloom_model = sm.OLS(
            group['Full_DOY'], sm.add_constant(group['Mar_Temp'])
        ).fit()
        duration_model = sm.OLS(
            group['Duration_Days'], sm.add_constant(group['Feb_Mar_Temp'])
        ).fit()
        rows.append({
            'Site Name': site,
            'Species': group['Species'].iloc[0],
            'Latitude': coords.loc[coords['Site Name'].eq(site), 'Latitude'].iloc[0],
            'n': len(group),
            'Bloom_Temp_Slope': bloom_model.params.iloc[1],
            'Bloom_Temp_R2': bloom_model.rsquared,
            'Duration_Temp_Slope': duration_model.params.iloc[1],
            'Duration_Temp_R2': duration_model.rsquared,
        })

    result = pd.DataFrame(rows).sort_values('Bloom_Temp_Slope')
    result.to_csv(SENSITIVITY_OUTPUT, index=False)
    slope_model = sm.OLS(
        result['Duration_Temp_Slope'], sm.add_constant(result['Latitude'])
    ).fit()
    result[['Site Name', 'Latitude', 'Duration_Temp_Slope', 'n']].to_csv(
        TEMP_SLOPE_LATITUDE_OUTPUT, index=False
    )
    print('\n=== FULL STATION TEMPERATURE TABLE ===')
    print(result.to_string(index=False, float_format=lambda value: f'{value:.4f}'))
    print('\nDuration-temperature slope by latitude:')
    print(f'Estimate: {slope_model.params.iloc[1]:.4f}')
    print(f'95% CI: [{slope_model.conf_int().iloc[1, 0]:.4f}, {slope_model.conf_int().iloc[1, 1]:.4f}]')
    print(f'R2: {slope_model.rsquared:.4f} | p-value: {slope_model.pvalues.iloc[1]:.6g}')
    return result


def fit_latitude_relationships():
    trends = []
    phenology = pd.read_csv(PHENOLOGY_FILE)
    coords = pd.read_csv(COORDS_FILE)
    eligible = phenology[
        phenology['Trend_Analysis_Eligible']
        & phenology['Species'].eq('Not stated')
        & phenology['Year'].between(1961, 2010)
    ]
    for site, group in eligible.groupby('Site Name'):
        if len(group) < 40:
            continue
        model = sm.OLS(group['Duration_Days'], sm.add_constant(group['Year'])).fit()
        latitude = coords.loc[coords['Site Name'].eq(site), 'Latitude'].iloc[0]
        trends.append({
            'Site Name': site,
            'Latitude': latitude,
            'Duration_Trend': model.params.iloc[1] * 10,
            'n': len(group),
        })

    result = pd.DataFrame(trends).sort_values('Latitude')
    result.to_csv(LATITUDE_OUTPUT, index=False)
    model = sm.OLS(result['Duration_Trend'], sm.add_constant(result['Latitude'])).fit()
    print('\n=== DURATION TREND BY LATITUDE TABLE ===')
    print(result.to_string(index=False, float_format=lambda value: f'{value:.4f}'))
    print('\nLatitude slope for duration trend:')
    print(f'Estimate: {model.params.iloc[1]:.4f}')
    print(f'95% CI: [{model.conf_int().iloc[1, 0]:.4f}, {model.conf_int().iloc[1, 1]:.4f}]')
    print(f'R2: {model.rsquared:.4f} | p-value: {model.pvalues.iloc[1]:.6g}')

    plt.figure(figsize=(8, 5))
    plt.scatter(result['Latitude'], result['Duration_Trend'], color='black')
    order = np.argsort(result['Latitude'].to_numpy())
    x = result['Latitude'].to_numpy()[order]
    plt.plot(x, model.predict(sm.add_constant(x)), color='firebrick', linewidth=2)
    plt.axhline(0, color='gray', linestyle='--', linewidth=1)
    plt.xlabel('Latitude')
    plt.ylabel('Duration trend (days/decade)')
    plt.title('Duration Trend vs Latitude: Not stated Stations')
    plt.tight_layout()
    plt.savefig(LATITUDE_PLOT, dpi=300)
    plt.close()
    return result


def fit_restoring_force(station, group):
    group = group.sort_values('Year').copy()
    years = group['Year'].to_numpy(dtype=float)
    bloom = group['Full_DOY'].to_numpy(dtype=float)
    derivative = np.gradient(bloom, years)
    model = sm.OLS(derivative, sm.add_constant(bloom)).fit()
    params = np.asarray(model.params)
    confidence = np.asarray(model.conf_int())
    slope = params[1]
    intercept = params[0]
    k = -slope
    equilibrium = intercept / k if k != 0 else np.nan
    slope_ci = confidence[1]
    intercept_ci = confidence[0]
    k_low, k_high = -slope_ci[1], -slope_ci[0]
    if k != 0:
        equilibrium_gradient = np.array([1 / k, -intercept / (k * k)])
        covariance = np.asarray(model.cov_params())
        equilibrium_se = np.sqrt(equilibrium_gradient @ covariance @ equilibrium_gradient)
        equilibrium_low = equilibrium - 1.96 * equilibrium_se
        equilibrium_high = equilibrium + 1.96 * equilibrium_se
    else:
        equilibrium_low = np.nan
        equilibrium_high = np.nan

    return {
        'Site Name': station,
        'n': len(group),
        'k_per_year': k,
        'k_CI_Lower': k_low,
        'k_CI_Upper': k_high,
        'c_DOY_per_year': intercept,
        'c_CI_Lower': intercept_ci[0],
        'c_CI_Upper': intercept_ci[1],
        'n_eq_DOY': equilibrium,
        'n_eq_CI_Lower': equilibrium_low,
        'n_eq_CI_Upper': equilibrium_high,
        'R2': model.rsquared,
        'Years_First': int(years.min()),
        'Years_Last': int(years.max()),
        'Years': years,
        'Bloom': bloom,
        'Derivative': derivative,
    }


def fit_selected_dynamics():
    phenology = pd.read_csv(PHENOLOGY_FILE)
    coords = pd.read_csv(COORDS_FILE)
    main = phenology[phenology['Main_Analysis_Eligible']].copy()
    if 'Latitude' not in main.columns:
        main = main.merge(coords[['Site Name', 'Latitude']], on='Site Name', how='left')

    station_groups = {
        site: group for site, group in main.groupby('Site Name')
        if len(group) >= 40 and group['Full_DOY'].notna().sum() >= 40
    }
    lat_site = max(station_groups, key=lambda site: main.loc[main['Site Name'].eq(site), 'Latitude'].iloc[0])
    low_site = min(station_groups, key=lambda site: main.loc[main['Site Name'].eq(site), 'Latitude'].iloc[0])
    trend_data = main[main['Year'].between(1961, 2010) & main['Full_DOY'].notna()]
    trend_rows = []
    for site, group in trend_data.groupby('Site Name'):
        if len(group) >= 40:
            model = sm.OLS(group['Full_DOY'], sm.add_constant(group['Year'])).fit()
            trend_rows.append((site, model.params.iloc[1] * 10))
    strongest_site = min(trend_rows, key=lambda value: value[1])[0]
    selected = [lat_site, low_site, strongest_site, 'Kyoto']
    selected = list(dict.fromkeys(selected))

    fits = []
    for site in selected:
        fit = fit_restoring_force(site, station_groups[site])
        fits.append(fit)
    output = pd.DataFrame([{key: value for key, value in fit.items() if key not in {'Years', 'Bloom', 'Derivative'}} for fit in fits])
    output.to_csv(DYNAMICS_OUTPUT, index=False)

    print('\n=== SELECTED RESTORING-FORCE FITS ===')
    print(output.to_string(index=False, float_format=lambda value: f'{value:.6f}'))
    print(f'Selected stations: {selected}')

    fig, axes = plt.subplots(1, len(fits), figsize=(5 * len(fits), 4), sharey=True)
    axes = np.atleast_1d(axes)
    for axis, fit in zip(axes, fits):
        scatter = axis.scatter(fit['Bloom'], fit['Derivative'], c=fit['Years'], cmap='viridis', s=18)
        x = np.linspace(fit['Bloom'].min(), fit['Bloom'].max(), 100)
        axis.plot(x, fit['c_DOY_per_year'] - fit['k_per_year'] * x, color='firebrick')
        axis.set_title(fit['Site Name'])
        axis.set_xlabel('Full-bloom DOY')
        axis.axhline(0, color='gray', linestyle='--', linewidth=1)
    axes[0].set_ylabel('d(DOY)/dt (days/year)')
    fig.colorbar(scatter, ax=axes.tolist(), label='Year')
    fig.suptitle('Station Phase Space: d(DOY)/dt vs Full-Bloom DOY')
    fig.tight_layout()
    fig.savefig(DYNAMICS_PLOT, dpi=300)
    plt.close(fig)
    return output


def fetch_kyoto_daily():
    response = requests.get(
        'https://archive-api.open-meteo.com/v1/archive',
        params={
            'latitude': 35.0117,
            'longitude': 135.7350,
            'start_date': '1953-01-01',
            'end_date': '2024-12-31',
            'daily': 'temperature_2m_mean',
            'timezone': 'Asia/Tokyo',
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()['daily']
    daily = pd.DataFrame({'Date': pd.to_datetime(payload['time']), 'Temp': payload['temperature_2m_mean']})
    daily['Year'] = daily['Date'].dt.year
    daily['Month'] = daily['Date'].dt.month
    return daily.dropna()


def fit_degree_day_comparison():
    bloom = pd.read_csv(PHENOLOGY_FILE)
    bloom = bloom[(bloom['Site Name'] == 'Kyoto') & bloom['Full_DOY'].notna()][['Year', 'Full_DOY']]
    daily = fetch_kyoto_daily()
    predictions = []
    for year, group in daily[daily['Month'] >= 2].groupby('Year'):
        group = group.sort_values('Date').copy()
        group['Accumulated'] = group['Temp'].clip(lower=0).cumsum()
        crossing = group[group['Accumulated'] >= 400]
        if not crossing.empty:
            first = crossing.iloc[0]
            doy = first['Date'].dayofyear - int(first['Date'].is_leap_year and first['Date'].dayofyear > 59)
            predictions.append({'Year': year, 'DegreeDay_Prediction': doy})
    degree = pd.DataFrame(predictions)
    data = bloom.merge(degree, on='Year').merge(
        daily[daily['Month'].isin([2, 3])].groupby('Year')['Temp'].mean().rename('FebMar_Temp'),
        on='Year',
    )
    train = data['Year'] <= 1990
    test = data['Year'] > 1990
    linear = sm.OLS(data.loc[train, 'Full_DOY'], sm.add_constant(data.loc[train, 'FebMar_Temp'])).fit()
    data['Linear_Prediction'] = linear.predict(sm.add_constant(data['FebMar_Temp']))
    for label, column in [('DegreeDay', 'DegreeDay_Prediction'), ('Linear', 'Linear_Prediction')]:
        print(f'{label} in-sample RMSE: {np.sqrt(np.mean((data.loc[train, column] - data.loc[train, "Full_DOY"]) ** 2)):.4f}')
        print(f'{label} out-of-sample RMSE: {np.sqrt(np.mean((data.loc[test, column] - data.loc[test, "Full_DOY"]) ** 2)):.4f}')
    print('Temperature source: Open-Meteo archive daily reanalysis/derived data; not JMA observed temperatures.')


if __name__ == '__main__':
    os.makedirs('plots', exist_ok=True)
    fit_temperature_slopes()
    fit_latitude_relationships()
    fit_selected_dynamics()
    fit_degree_day_comparison()
