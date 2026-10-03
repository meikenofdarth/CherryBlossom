import os

import pandas as pd


DATA_DIR = 'data/JMA-kaggle_dataest'
OUTPUT = 'data/station_year_phenology.csv'
REPORT = 'data/station_year_validation.txt'


def normalized_doy(date_series):
    normalized = pd.to_datetime({
        'year': 2001,
        'month': date_series.dt.month,
        'day': date_series.dt.day,
    }, errors='coerce')
    return normalized.dt.dayofyear


def load_phenology():
    first = pd.read_csv(f'{DATA_DIR}/sakura_first_bloom_dates.csv')
    full = pd.read_csv(f'{DATA_DIR}/sakura_full_bloom_dates.csv')
    id_vars = ['Site Name', 'Currently Being Observed']
    drop_cols = ['30 Year Average 1991-2020', 'Notes']

    species_map = first.set_index('Site Name')['Notes'].fillna('Not stated')
    first_long = first.drop(columns=drop_cols, errors='ignore').melt(
        id_vars=id_vars, var_name='Year', value_name='First_Bloom_Date'
    )
    full_long = full.drop(columns=drop_cols, errors='ignore').melt(
        id_vars=id_vars, var_name='Year', value_name='Full_Bloom_Date'
    )
    data = first_long.merge(full_long, on=id_vars + ['Year'], validate='one_to_one')
    data['Year'] = pd.to_numeric(data['Year'], errors='coerce')
    data['Species'] = data['Site Name'].map(species_map).fillna('Not stated')
    data['First_DT'] = pd.to_datetime(data['First_Bloom_Date'], errors='coerce')
    data['Full_DT'] = pd.to_datetime(data['Full_Bloom_Date'], errors='coerce')
    data['First_DOY'] = normalized_doy(data['First_DT'])
    data['Full_DOY'] = normalized_doy(data['Full_DT'])
    data['Duration_Days'] = (data['Full_DT'] - data['First_DT']).dt.days
    return data


def add_flags(data):
    changed = data['Species'].str.contains('from 1995', na=False)
    excluded_species = data['Species'].isin({
        'Taiwan cherry (Prunus campanulata)',
        'Kurile Island Cherry (Cerasus nipponica var. kurilensis)',
    })
    data['Species_Assumption'] = data['Species'].eq('Not stated')
    data['Species_Change_Flag'] = changed
    data['Zero_Duration_Flag'] = data['Duration_Days'].eq(0)
    data['Main_Analysis_Eligible'] = (
        ~excluded_species
        & ~changed
        & data['First_DOY'].notna()
        & data['Full_DOY'].notna()
        & data['Duration_Days'].notna()
    )
    eligible_counts = data.groupby('Site Name')['Main_Analysis_Eligible'].transform('sum')
    data['Trend_Analysis_Eligible'] = data['Main_Analysis_Eligible'] & eligible_counts.ge(15)
    return data


def add_coordinates(data):
    coordinates = pd.read_csv(
        f'{DATA_DIR}/station_coords_template.csv',
        usecols=['Site Name', 'Latitude', 'Longitude'],
    )
    return data.merge(coordinates, on='Site Name', how='left', validate='many_to_one')


def validation_lines(data):
    valid_dates = data[['First_DT', 'Full_DT']].notna().all(axis=1)
    negative_duration = data['Duration_Days'].lt(0) & data['Duration_Days'].notna()
    zero_duration = data['Duration_Days'].eq(0)
    duplicate_rows = data.duplicated(['Site Name', 'Year']).sum()
    missing_coordinate_stations = data.loc[
        data[['Latitude', 'Longitude']].isna().any(axis=1), 'Site Name'
    ].nunique()
    eligible = data[data['Main_Analysis_Eligible']]
    trend_eligible = data[data['Trend_Analysis_Eligible']]

    return [
        f'Rows: {len(data)}',
        f'Stations: {data["Site Name"].nunique()}',
        f'Unique station-year duplicates: {duplicate_rows}',
        f'Rows with both bloom dates: {int(valid_dates.sum())}',
        f'Negative datetime durations: {int(negative_duration.sum())}',
        f'Zero datetime durations: {int(zero_duration.sum())}',
        f'Missing coordinate stations: {int(missing_coordinate_stations)}',
        f'Main-analysis eligible rows: {len(eligible)}',
        f'Main-analysis eligible stations: {eligible["Site Name"].nunique()}',
        f'Trend-analysis eligible rows (n >= 15): {len(trend_eligible)}',
        f'Trend-analysis eligible stations (n >= 15): {trend_eligible["Site Name"].nunique()}',
        'Species counts:',
        data.groupby('Species', dropna=False)['Site Name'].nunique().to_string(),
    ]


def main():
    data = add_coordinates(add_flags(load_phenology()))
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    data.to_csv(OUTPUT, index=False)
    lines = validation_lines(data)
    with open(REPORT, 'w') as report:
        report.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'Wrote {OUTPUT}')
    print(f'Wrote {REPORT}')


if __name__ == '__main__':
    main()