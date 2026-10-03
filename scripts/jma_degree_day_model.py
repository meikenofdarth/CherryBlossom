import numpy as np
import pandas as pd
import statsmodels.api as sm


DAILY_FILE = 'data/jma_daily_observed_streaming.csv'
PHENOLOGY_FILE = 'data/station_year_phenology.csv'
OUTPUT = 'data/kyoto_jma_degree_day_results.csv'
BASE_TEMPERATURE = 0.0
THRESHOLD = 400.0
TRAIN_END = 1990


def rmse(actual, predicted):
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def main():
    daily = pd.read_csv(DAILY_FILE, parse_dates=['Date'])
    daily = daily[daily['Site Name'].eq('Kyoto')].copy()
    bloom = pd.read_csv(PHENOLOGY_FILE)
    bloom = bloom[(bloom['Site Name'].eq('Kyoto')) & bloom['Full_DOY'].notna()][['Year', 'Full_DOY']]

    predictions = []
    for year, group in daily[daily['Month'].ge(2)].groupby('Year'):
        group = group.sort_values('Date').copy()
        group['Heat'] = (group['Temp'] - BASE_TEMPERATURE).clip(lower=0)
        group['Cumulative_Heat'] = group['Heat'].cumsum()
        crossing = group[group['Cumulative_Heat'] >= THRESHOLD]
        if crossing.empty:
            continue
        date = crossing.iloc[0]['Date']
        doy = date.dayofyear - int(date.is_leap_year and date.dayofyear > 59)
        predictions.append({'Year': year, 'DegreeDay_Prediction': doy})

    monthly = (
        daily[daily['Month'].isin([2, 3])]
        .groupby('Year')['Temp']
        .mean()
        .rename('FebMar_Temp')
        .reset_index()
    )
    data = bloom.merge(pd.DataFrame(predictions), on='Year').merge(monthly, on='Year')
    train = data['Year'].le(TRAIN_END)
    test = data['Year'].gt(TRAIN_END)
    model = sm.OLS(data.loc[train, 'Full_DOY'], sm.add_constant(data.loc[train, 'FebMar_Temp'])).fit()
    data['Linear_Prediction'] = model.predict(sm.add_constant(data['FebMar_Temp'], has_constant='add'))
    data.to_csv(OUTPUT, index=False)

    print('Temperature source: JMA daily observed temperatures.')
    print(f'Base temperature: {BASE_TEMPERATURE:.1f} C')
    print('Start date: February 1')
    print(f'Heat threshold: {THRESHOLD:.0f} degree-days')
    print(f'Train years: <= {TRAIN_END}; test years: > {TRAIN_END}')
    print(f'Rows: {len(data)} | train: {int(train.sum())} | test: {int(test.sum())}')
    for label, column in [('DegreeDay', 'DegreeDay_Prediction'), ('Linear', 'Linear_Prediction')]:
        print(f'{label} in-sample RMSE: {rmse(data.loc[train, "Full_DOY"].to_numpy(), data.loc[train, column].to_numpy()):.4f}')
        print(f'{label} out-of-sample RMSE: {rmse(data.loc[test, "Full_DOY"].to_numpy(), data.loc[test, column].to_numpy()):.4f}')
    print(f'Saved {OUTPUT}')


if __name__ == '__main__':
    main()
