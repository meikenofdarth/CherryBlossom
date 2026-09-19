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

df = pd.merge(df1_melt, df2_melt, on=['Site Name', 'Currently Being Observed', 'Year'])
df['Species'] = df['Site Name'].map(species_map).fillna('Not stated')

# Parse real datetimes
df['First_DT'] = pd.to_datetime(df['First_Bloom_Date'], errors='coerce')
df['Full_DT'] = pd.to_datetime(df['Full_Bloom_Date'], errors='coerce')
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df = df.dropna(subset=['Year'])

# Leap-year-safe DOY
def safe_doy(dt_series):
    norm = pd.to_datetime({'year': 2001, 'month': dt_series.dt.month, 'day': dt_series.dt.day})
    return norm.dt.dayofyear

df['First_DOY'] = safe_doy(df['First_DT'])
df['Full_DOY'] = safe_doy(df['Full_DT'])
df['Duration_DT'] = (df['Full_DT'] - df['First_DT']).dt.days

# Define exclusion rules
exclude_species = [
    'Taiwan cherry (Prunus campanulata)',
    'Kurile Island Cherry (Cerasus nipponica var. kurilensis)',
]
exclude_notes = df[df['Species'].str.contains("from 1995", na=False)]['Site Name'].unique()

df_clean = df[~df['Species'].isin(exclude_species)]
df_clean = df_clean[~df_clean['Site Name'].isin(exclude_notes)]
df_valid = df_clean.dropna(subset=['First_DOY', 'Full_DOY', 'Duration_DT'])


# --- (1) First and last year with valid data and n ---
print("--- (1) Valid Data Coverage (Not stated & Sargent) ---")
coverage = df_valid.groupby(['Site Name', 'Species'])['Year'].agg(['min', 'max', 'count']).reset_index()
for _, row in coverage.iterrows():
    print(f"{row['Site Name']}: {int(row['min'])}-{int(row['max'])}, n={int(row['count'])}")


# --- (2) Common window 1961-2010 trends (>=40 valid years) ---
print("\n--- (2) Common Window 1961-2010 Trends ---")
df_window = df_valid[(df_valid['Year'] >= 1961) & (df_valid['Year'] <= 2010)]

results = []
for site, group in df_window.groupby('Site Name'):
    n = len(group)
    if n < 40:
        continue
    
    X = sm.add_constant(group['Year'])
    mod_first = sm.OLS(group['First_DOY'], X).fit()
    mod_full = sm.OLS(group['Full_DOY'], X).fit()
    mod_dur = sm.OLS(group['Duration_DT'], X).fit()

    results.append({
        'Site Name': site,
        'Species': group['Species'].iloc[0],
        'n_years': n,
        'First_Trend': mod_first.params.iloc[1] * 10,
        'Full_Trend': mod_full.params.iloc[1] * 10,
        'Dur_Trend': mod_dur.params.iloc[1] * 10,
        'Dur_CI_Lower': mod_dur.conf_int().iloc[1, 0] * 10,
        'Dur_CI_Upper': mod_dur.conf_int().iloc[1, 1] * 10,
    })

df_res = pd.DataFrame(results)

for sp_label in ['Not stated', 'Sargent cherry (Prunus sargentii)']:
    sp = df_res[df_res['Species'] == sp_label]
    print(f"\nSpecies: {sp_label}")
    print(f"Stations remaining: {len(sp)}")
    if len(sp) == 0:
        continue
    neg_full = (sp['Full_Trend'] < 0).mean() * 100
    print(f"Share with negative full-bloom trend: {neg_full:.1f}%")
    
    for col in ['First_Trend', 'Full_Trend', 'Dur_Trend']:
        med = sp[col].median()
        q1 = sp[col].quantile(0.25)
        q3 = sp[col].quantile(0.75)
        print(f"{col}: Median = {med:.2f}, IQR = [{q1:.2f}, {q3:.2f}]")


# --- (3) Stations with duration CI entirely above or below zero (Common window) ---
print("\n--- (3) Duration CI entirely above or below zero (Common window) ---")
dur_below = df_res[df_res['Dur_CI_Upper'] < 0]
dur_above = df_res[df_res['Dur_CI_Lower'] > 0]

print("Duration shortening (CI < 0):")
for _, r in dur_below.iterrows():
    print(f"  {r['Site Name']:20s}: {r['Dur_Trend']:5.2f} [{r['Dur_CI_Lower']:5.2f}, {r['Dur_CI_Upper']:5.2f}]")
    
print("\nDuration lengthening (CI > 0):")
for _, r in dur_above.iterrows():
    print(f"  {r['Site Name']:20s}: {r['Dur_Trend']:5.2f} [{r['Dur_CI_Lower']:5.2f}, {r['Dur_CI_Upper']:5.2f}]")


# --- (4) Taiwan cherry redo (Days from Jan 1) ---
print("\n--- (4) Taiwan cherry analysis (Days from Jan 1) ---")
df_tc = df[df['Species'] == 'Taiwan cherry (Prunus campanulata)'].copy()
df_tc = df_tc.dropna(subset=['First_DT', 'Full_DT'])

# Recompute dates as days from Jan 1 of the labelled Year
jan1 = pd.to_datetime({'year': df_tc['Year'], 'month': 1, 'day': 1})
df_tc['First_Days'] = (df_tc['First_DT'] - jan1).dt.days
df_tc['Full_Days'] = (df_tc['Full_DT'] - jan1).dt.days
df_tc['Duration_Days'] = df_tc['Full_Days'] - df_tc['First_Days']

for site, group in df_tc.groupby('Site Name'):
    group = group.dropna(subset=['First_Days', 'Full_Days', 'Duration_Days'])
    n = len(group)
    if n < 3:
        continue
        
    X = sm.add_constant(group['Year'])
    mod_first = sm.OLS(group['First_Days'], X).fit()
    mod_full = sm.OLS(group['Full_Days'], X).fit()
    mod_dur = sm.OLS(group['Duration_Days'], X).fit()
    
    print(f"\n{site} (n={n}):")
    print(f"  First_Trend: {mod_first.params.iloc[1]*10:6.2f} [{mod_first.conf_int().iloc[1,0]*10:6.2f}, {mod_first.conf_int().iloc[1,1]*10:6.2f}]")
    print(f"  Full_Trend:  {mod_full.params.iloc[1]*10:6.2f} [{mod_full.conf_int().iloc[1,0]*10:6.2f}, {mod_full.conf_int().iloc[1,1]*10:6.2f}]")
    print(f"  Dur_Trend:   {mod_dur.params.iloc[1]*10:6.2f} [{mod_dur.conf_int().iloc[1,0]*10:6.2f}, {mod_dur.conf_int().iloc[1,1]*10:6.2f}]")