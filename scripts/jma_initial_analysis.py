import pandas as pd
import numpy as np
import statsmodels.api as sm

df1 = pd.read_csv('data/JMA-kaggle_dataest/sakura_first_bloom_dates.csv')
df2 = pd.read_csv('data/JMA-kaggle_dataest/sakura_full_bloom_dates.csv')

cols_to_drop = ['30 Year Average 1991-2020', 'Notes']
id_vars = ['Site Name', 'Currently Being Observed']
species_map = df1.set_index('Site Name')['Notes'].to_dict()

df1_melt = df1.drop(columns=cols_to_drop, errors='ignore').melt(
    id_vars=id_vars, var_name='Year', value_name='First_Bloom_Date'
)
df2_melt = df2.drop(columns=cols_to_drop, errors='ignore').melt(
    id_vars=id_vars, var_name='Year', value_name='Full_Bloom_Date'
)

df_merged = pd.merge(df1_melt, df2_melt, on=['Site Name', 'Currently Being Observed', 'Year'])

# Convert to datetime and extract DOY
df_merged['First_DOY'] = pd.to_datetime(df_merged['First_Bloom_Date'], errors='coerce').dt.dayofyear
df_merged['Full_DOY'] = pd.to_datetime(df_merged['Full_Bloom_Date'], errors='coerce').dt.dayofyear
df_merged['Year'] = pd.to_numeric(df_merged['Year'], errors='coerce')
df_merged = df_merged.dropna(subset=['Year'])

df_merged['Duration'] = df_merged['Full_DOY'] - df_merged['First_DOY']
df_valid = df_merged.dropna(subset=['First_DOY', 'Full_DOY'])

num_stations = df_merged['Site Name'].nunique()
print(f"Number of stations: {num_stations}")

valid_years_per_station = df_valid.groupby('Site Name').size()
print(f"Median valid years per station: {valid_years_per_station.median()}")

total_rows = len(df_merged)
missing_first = df_merged['First_DOY'].isna().sum()
missing_full = df_merged['Full_DOY'].isna().sum()
missing_both = df_merged['Duration'].isna().sum()
print(f"Total rows (Site-Years): {total_rows}")
print(f"Missing First Bloom: {missing_first}")
print(f"Missing Full Bloom: {missing_full}")
print(f"Missing Duration: {missing_both}")

results = []
for site, group in df_valid.groupby('Site Name'):
    n = len(group)
    if n < 15:
        continue
        
    X = sm.add_constant(group['Year'])
    
    # Trend for Full_DOY
    model_full = sm.OLS(group['Full_DOY'], X).fit()
    trend_full = model_full.params.iloc[1] * 10
    ci_full_lower = model_full.conf_int().iloc[1, 0] * 10
    ci_full_upper = model_full.conf_int().iloc[1, 1] * 10
    
    # Trend for Duration
    model_dur = sm.OLS(group['Duration'], X).fit()
    trend_dur = model_dur.params.iloc[1] * 10
    ci_dur_lower = model_dur.conf_int().iloc[1, 0] * 10
    ci_dur_upper = model_dur.conf_int().iloc[1, 1] * 10
    
    results.append({
        'Site Name': site,
        'Species': species_map.get(site, 'Unknown'),
        'n_years': n,
        'Full_DOY_Trend_days_per_decade': trend_full,
        'Full_DOY_CI_Lower': ci_full_lower,
        'Full_DOY_CI_Upper': ci_full_upper,
        'Duration_Trend_days_per_decade': trend_dur,
        'Duration_CI_Lower': ci_dur_lower,
        'Duration_CI_Upper': ci_dur_upper
    })

df_trends = pd.DataFrame(results)
df_trends.to_csv('data/JMA-kaggle_dataest/station_trends.csv', index=False)

pd.set_option('display.max_columns', None)
print("\n--- TRENDS SUMMARY (First 5 Rows) ---")
print(df_trends.head())
