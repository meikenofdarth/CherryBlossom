import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

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

df = pd.merge(df1_melt, df2_melt, on=['Site Name', 'Currently Being Observed', 'Year'])

# 1. Parse dates safely and verify leap years
def safe_doy(date_series):
    dt = pd.to_datetime(date_series, errors='coerce')
    norm_dt = pd.to_datetime({
        'year': 2001,
        'month': dt.dt.month,
        'day': dt.dt.day
    })
    return norm_dt.dt.dayofyear

df['First_DOY'] = safe_doy(df['First_Bloom_Date'])
df['Full_DOY'] = safe_doy(df['Full_Bloom_Date'])

print("--- DATE PARSING VERIFICATION (LEAP YEARS 1956, 1960) ---")
leap_year_samples = df[df['Year'].isin(['1956', '1960'])].dropna(subset=['First_Bloom_Date', 'Full_Bloom_Date']).head(2)
print(leap_year_samples[['Year', 'First_Bloom_Date', 'First_DOY', 'Full_Bloom_Date', 'Full_DOY']])

# Count unparseable dates (where string exists but DOY is NaN)
unparseable_first = df[(df['First_Bloom_Date'].notna()) & (df['First_Bloom_Date'] != '-') & (df['First_DOY'].isna())].shape[0]
unparseable_full = df[(df['Full_Bloom_Date'].notna()) & (df['Full_Bloom_Date'] != '-') & (df['Full_DOY'].isna())].shape[0]
print(f"\nUnparseable First Bloom dates: {unparseable_first}")
print(f"Unparseable Full Bloom dates: {unparseable_full}")

df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df = df.dropna(subset=['Year'])
df['Duration'] = df['Full_DOY'] - df['First_DOY']

# 3. Negative and extreme durations
negative_durations = df[df['Duration'] < 0].shape[0]
print(f"\nNegative durations count: {negative_durations}")
print("5 Most Extreme Durations (Absolute magnitude):")
ext_dur = df.dropna(subset=['Duration']).copy()
ext_dur['Abs_Duration'] = ext_dur['Duration'].abs()
print(ext_dur.sort_values(by='Abs_Duration', ascending=False)[['Site Name', 'Year', 'First_DOY', 'Full_DOY', 'Duration']].head(5))

# Species filling and Exclude species change station
df['Species'] = df['Site Name'].map(species_map).fillna('Not stated')
# 2. Exclude station that changed species in 1995
changed_station = df[df['Species'].str.contains("from 1995", na=False)]['Site Name'].unique()
if len(changed_station) > 0:
    print(f"\nExcluding station due to species change: {changed_station[0]}")
    df = df[df['Site Name'] != changed_station[0]]

df_valid = df.dropna(subset=['First_DOY', 'Full_DOY', 'Duration'])

results = []
for site, group in df_valid.groupby('Site Name'):
    n = len(group)
    if n < 15:
        results.append({'Site Name': site, 'n_years': n, 'Skip': True, 'Species': group['Species'].iloc[0]})
        continue
        
    X = sm.add_constant(group['Year'])
    mod_first = sm.OLS(group['First_DOY'], X).fit()
    mod_full = sm.OLS(group['Full_DOY'], X).fit()
    mod_dur = sm.OLS(group['Duration'], X).fit()
    
    results.append({
        'Site Name': site,
        'Species': group['Species'].iloc[0],
        'Skip': False,
        'n_years': n,
        'First_Trend': mod_first.params.iloc[1] * 10,
        'First_CI_Lower': mod_first.conf_int().iloc[1, 0] * 10,
        'First_CI_Upper': mod_first.conf_int().iloc[1, 1] * 10,
        'Full_Trend': mod_full.params.iloc[1] * 10,
        'Full_CI_Lower': mod_full.conf_int().iloc[1, 0] * 10,
        'Full_CI_Upper': mod_full.conf_int().iloc[1, 1] * 10,
        'Dur_Trend': mod_dur.params.iloc[1] * 10,
        'Dur_CI_Lower': mod_dur.conf_int().iloc[1, 0] * 10,
        'Dur_CI_Upper': mod_dur.conf_int().iloc[1, 1] * 10
    })

df_res = pd.DataFrame(results)
kept = df_res[df_res['Skip'] == False].copy()

# 6. Sparsest station
min_n = kept['n_years'].min()
sparse_station = kept[kept['n_years'] == min_n]['Site Name'].iloc[0]
print(f"\nSparsest station kept: {sparse_station} (n={min_n})")

# 4 & 5. Summary block per species
target_species = [
    'Not stated', 
    'Sargent cherry (Prunus sargentii)', 
    'Taiwan cherry (Prunus campanulata)'
]

for sp in target_species:
    sp_data = kept[kept['Species'] == sp]
    print(f"\n=== SUMMARY: {sp} ===")
    n_kept = len(sp_data)
    print(f"Stations kept (n >= 15): {n_kept}")
    if n_kept == 0:
        continue
        
    neg_full = (sp_data['Full_Trend'] < 0).mean() * 100
    ci_exc_zero = ((sp_data['Full_CI_Upper'] < 0) | (sp_data['Full_CI_Lower'] > 0)).mean() * 100
    print(f"Share with negative full-bloom trend: {neg_full:.1f}%")
    print(f"Share with CI excluding zero (Full Bloom): {ci_exc_zero:.1f}%")
    
    for col in ['First_Trend', 'Full_Trend', 'Dur_Trend']:
        q1 = sp_data[col].quantile(0.25)
        q3 = sp_data[col].quantile(0.75)
        med = sp_data[col].median()
        print(f"{col}: Median = {med:.2f}, IQR = [{q1:.2f}, {q3:.2f}]")
        
    # 5. Duration CI directions
    dur_below = (sp_data['Dur_CI_Upper'] < 0).sum()
    dur_above = (sp_data['Dur_CI_Lower'] > 0).sum()
    dur_span = ((sp_data['Dur_CI_Lower'] <= 0) & (sp_data['Dur_CI_Upper'] >= 0)).sum()
    print(f"Duration CIs entirely below zero: {dur_below}")
    print(f"Duration CIs entirely above zero: {dur_above}")
    print(f"Duration CIs spanning zero: {dur_span}")
