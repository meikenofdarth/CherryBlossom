import os

import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm


DATA_DIR = 'data/JMA-kaggle_dataest'
OUTPUT = 'plots/histogram_full_trends.png'


def safe_doy(date_series):
    normalized = pd.to_datetime({
        'year': 2001,
        'month': date_series.dt.month,
        'day': date_series.dt.day,
    })
    return normalized.dt.dayofyear


def main():
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
    data['Full_DOY'] = safe_doy(data['Full_DT'])

    excluded_species = {
        'Taiwan cherry (Prunus campanulata)',
        'Kurile Island Cherry (Cerasus nipponica var. kurilensis)',
    }
    changed = data.loc[
        data['Species'].str.contains('from 1995', na=False), 'Site Name'
    ].unique()
    data = data[~data['Species'].isin(excluded_species)]
    data = data[~data['Site Name'].isin(changed)]
    data = data.dropna(subset=['Year', 'Full_DOY'])

    trends = []
    for site, group in data.groupby('Site Name'):
        if len(group) < 15:
            continue
        model = sm.OLS(group['Full_DOY'], sm.add_constant(group['Year'])).fit()
        trends.append({
            'Site Name': site,
            'Species': group['Species'].iloc[0],
            'Full_Trend': model.params.iloc[1] * 10,
        })

    result = pd.DataFrame(trends)
    os.makedirs('plots', exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.hist(result['Full_Trend'], bins=16, color='skyblue', edgecolor='black')
    plt.axvline(0, color='red', linestyle='--', linewidth=2)
    plt.axvline(result['Full_Trend'].median(), color='black', linewidth=2)
    plt.title('Full-Bloom Trends Across Yoshino and Sargent Stations')
    plt.xlabel('Trend (days/decade)')
    plt.ylabel('Station count')
    plt.tight_layout()
    plt.savefig(OUTPUT, dpi=300)
    plt.close()

    print(f'Stations included: {len(result)}')
    print(result['Species'].value_counts().to_string())
    print(f"Median full-bloom trend: {result['Full_Trend'].median():.2f} days/decade")
    print(f'Saved {OUTPUT}')


if __name__ == '__main__':
    main()