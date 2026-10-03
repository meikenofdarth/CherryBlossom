import pandas as pd
import statsmodels.api as sm


DATA_DIR = 'data/JMA-kaggle_dataest'
WINDOWS = [(1961, 2010), (1971, 2020), (1976, 2025)]
MIN_YEARS = 40


def safe_doy(date_series):
    normalized = pd.to_datetime({
        'year': 2001,
        'month': date_series.dt.month,
        'day': date_series.dt.day,
    })
    return normalized.dt.dayofyear


def load_data():
    first = pd.read_csv(f'{DATA_DIR}/sakura_first_bloom_dates.csv')
    full = pd.read_csv(f'{DATA_DIR}/sakura_full_bloom_dates.csv')
    id_vars = ['Site Name', 'Currently Being Observed']
    drop_cols = ['30 Year Average 1991-2020', 'Notes']
    species_map = first.set_index('Site Name')['Notes'].to_dict()

    first_long = first.drop(columns=drop_cols, errors='ignore').melt(
        id_vars=id_vars, var_name='Year', value_name='First_Date'
    )
    full_long = full.drop(columns=drop_cols, errors='ignore').melt(
        id_vars=id_vars, var_name='Year', value_name='Full_Date'
    )
    data = first_long.merge(full_long, on=id_vars + ['Year'])
    data['Species'] = data['Site Name'].map(species_map).fillna('Not stated')
    data['Year'] = pd.to_numeric(data['Year'], errors='coerce')
    data['First_DT'] = pd.to_datetime(data['First_Date'], errors='coerce')
    data['Full_DT'] = pd.to_datetime(data['Full_Date'], errors='coerce')
    data['First_DOY'] = safe_doy(data['First_DT'])
    data['Full_DOY'] = safe_doy(data['Full_DT'])
    data['Duration'] = (data['Full_DT'] - data['First_DT']).dt.days

    excluded = {
        'Taiwan cherry (Prunus campanulata)',
        'Kurile Island Cherry (Cerasus nipponica var. kurilensis)',
    }
    changed = data.loc[
        data['Species'].str.contains('from 1995', na=False), 'Site Name'
    ].unique()
    data = data[~data['Species'].isin(excluded)]
    data = data[~data['Site Name'].isin(changed)]
    return data.dropna(subset=['Year', 'Full_DOY', 'Duration'])


def summarize_window(data, start, end):
    window = data[data['Year'].between(start, end)]
    records = []
    for site, group in window.groupby('Site Name'):
        if len(group) < MIN_YEARS:
            continue
        model_full = sm.OLS(
            group['Full_DOY'], sm.add_constant(group['Year'])
        ).fit()
        model_duration = sm.OLS(
            group['Duration'], sm.add_constant(group['Year'])
        ).fit()
        records.append({
            'Site Name': site,
            'Species': group['Species'].iloc[0],
            'Full_Trend': model_full.params.iloc[1] * 10,
            'Duration_Trend': model_duration.params.iloc[1] * 10,
            'Duration_CI_Lower': model_duration.conf_int().iloc[1, 0] * 10,
            'Duration_CI_Upper': model_duration.conf_int().iloc[1, 1] * 10,
        })

    result = pd.DataFrame(records)
    print(f'\nWindow: {start}-{end}')
    for species in ['Not stated', 'Sargent cherry (Prunus sargentii)']:
        group = result[result['Species'] == species]
        if group.empty:
            print(f'{species}: no stations')
            continue
        duration_below = (group['Duration_CI_Upper'] < 0).sum()
        duration_above = (group['Duration_CI_Lower'] > 0).sum()
        print(f'{species}: stations={len(group)}')
        print(f"  negative full-bloom trends={100 * (group['Full_Trend'] < 0).mean():.1f}%")
        print(f"  full-bloom median={group['Full_Trend'].median():.2f} days/decade")
        print(f"  duration median={group['Duration_Trend'].median():.2f} days/decade")
        print(f'  duration CIs below/above zero={duration_below}/{duration_above}')


def main():
    data = load_data()
    for start, end in WINDOWS:
        summarize_window(data, start, end)


if __name__ == '__main__':
    main()