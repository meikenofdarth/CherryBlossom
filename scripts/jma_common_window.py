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

df['First_DT'] = pd.to_datetime(df['First_Bloom_Date'], errors='coerce')
df['Full_DT'] = pd.to_datetime(df['Full_Bloom_Date'], errors='coerce')

def safe_doy(dt_series):
    norm = pd.to_datetime({'year': 2001, 'month': dt_series.dt.month, 'day': dt_series.dt.day})
    return norm.dt.dayofyear

df['First_DOY'] = safe_doy(df['First_DT'])
df['Full_DOY'] = safe_doy(df['Full_DT'])
df['Duration_DT'] = (df['Full_DT'] - df['First_DT']).dt.days
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df = df.dropna(subset=['Year'])

# Exclude species-change station
exclude_notes = df[df['Species'].str.contains("from 1995", na=False)]['Site Name'].unique()
df = df[~df['Site Name'].isin(exclude_notes)]

# Split datasets
taiwan_species = 'Taiwan cherry (Prunus campanulata)'
kurile_species = 'Kurile Island Cherry (Cerasus nipponica var. kurilensis)'
df_main = df[~df['Species'].isin([taiwan_species, kurile_species])]
df_taiwan = df[df['Species'] == taiwan_species]

df_valid = df_main.dropna(subset=['First_DOY', 'Full_DOY', 'Duration_DT'])

# --- (1) Per-station first/last year and n ---
print("--- (1) STATION COVERAGE ---")
for sp_label in ['Not stated', 'Sargent cherry (Prunus sargentii)']:
    sp_data = df_valid[df_valid['Species'] == sp_label]
    print(f"\n  === {sp_label} ===")
    for site, grp in sorted(sp_data.groupby('Site Name'), key=lambda x: x[0]):
        n = len(grp)
        if n < 15:
            continue
        first_yr = int(grp['Year'].min())
        last_yr = int(grp['Year'].max())
        print(f"  {site:20s} | {first_yr}-{last_yr} | n={n}")

# --- (2) Common window 1961-2010, >= 40 valid years ---
print("\n--- (2) COMMON WINDOW 1961-2010 (>= 40 valid years) ---")

def compute_trends(group):
    X = sm.add_constant(group['Year'])
    results = {}
    for label, col in [('First', 'First_DOY'), ('Full', 'Full_DOY'), ('Dur', 'Duration_DT')]:
        mod = sm.OLS(group[col], X).fit()
        results[f'{label}_Trend'] = mod.params.iloc[1] * 10
        results[f'{label}_CI_Lower'] = mod.conf_int().iloc[1, 0] * 10
        results[f'{label}_CI_Upper'] = mod.conf_int().iloc[1, 1] * 10
    return results

for sp_label in ['Not stated', 'Sargent cherry (Prunus sargentii)']:
    sp_data = df_valid[(df_valid['Species'] == sp_label) & 
                       (df_valid['Year'] >= 1961) & (df_valid['Year'] <= 2010)]
    
    cw_results = []
    for site, grp in sp_data.groupby('Site Name'):
        n = len(grp)
        if n < 40:
            continue
        trends = compute_trends(grp)
        trends['Site Name'] = site
        trends['n_years'] = n
        trends['Currently Being Observed'] = grp['Currently Being Observed'].iloc[0]
        cw_results.append(trends)
    
    cw = pd.DataFrame(cw_results)
    print(f"\n  === {sp_label} ===")
    print(f"  Stations kept: {len(cw)}")
    if len(cw) == 0:
        continue
    
    neg_full = (cw['Full_Trend'] < 0).mean() * 100
    ci_exc = ((cw['Full_CI_Upper'] < 0) | (cw['Full_CI_Lower'] > 0)).mean() * 100
    print(f"  Share with negative full-bloom trend: {neg_full:.1f}%")
    print(f"  Share with CI excluding zero (Full Bloom): {ci_exc:.1f}%")
    
    for col in ['First_Trend', 'Full_Trend', 'Dur_Trend']:
        med = cw[col].median()
        q1 = cw[col].quantile(0.25)
        q3 = cw[col].quantile(0.75)
        print(f"  {col}: Median = {med:.2f}, IQR = [{q1:.2f}, {q3:.2f}]")
    
    dur_below = cw[cw['Dur_CI_Upper'] < 0]
    dur_above = cw[cw['Dur_CI_Lower'] > 0]
    dur_span = cw[(cw['Dur_CI_Lower'] <= 0) & (cw['Dur_CI_Upper'] >= 0)]
    print(f"  Duration CIs entirely below zero: {len(dur_below)}")
    print(f"  Duration CIs entirely above zero: {len(dur_above)}")
    print(f"  Duration CIs spanning zero: {len(dur_span)}")

    # --- (3) List stations with duration CI not spanning zero ---
    if len(dur_below) > 0:
        print(f"\n  Duration CI entirely BELOW zero (common window):")
        for _, r in dur_below.iterrows():
            print(f"    {r['Site Name']:20s} | n={int(r['n_years'])} | Observed={r['Currently Being Observed']} | {r['Dur_Trend']:.2f} [{r['Dur_CI_Lower']:.2f}, {r['Dur_CI_Upper']:.2f}]")
    if len(dur_above) > 0:
        print(f"\n  Duration CI entirely ABOVE zero (common window):")
        for _, r in dur_above.iterrows():
            print(f"    {r['Site Name']:20s} | n={int(r['n_years'])} | Observed={r['Currently Being Observed']} | {r['Dur_Trend']:.2f} [{r['Dur_CI_Lower']:.2f}, {r['Dur_CI_Upper']:.2f}]")

# --- (4) Taiwan cherry: season-relative dates ---
print("\n--- (4) TAIWAN CHERRY: SEASON-RELATIVE DATES ---")

df_tw = df_taiwan.dropna(subset=['First_DT', 'Full_DT']).copy()
# Compute days from Jan 1 of the labelled Year
# December dates from the previous calendar year will be negative
df_tw['First_SRD'] = (df_tw['First_DT'] - pd.to_datetime(df_tw['Year'].astype(int).astype(str) + '-01-01')).dt.days
df_tw['Full_SRD'] = (df_tw['Full_DT'] - pd.to_datetime(df_tw['Year'].astype(int).astype(str) + '-01-01')).dt.days
df_tw['Duration_SRD'] = df_tw['Full_SRD'] - df_tw['First_SRD']

for site, grp in df_tw.groupby('Site Name'):
    n = len(grp)
    if n < 15:
        continue
    X = sm.add_constant(grp['Year'])
    
    mod_first = sm.OLS(grp['First_SRD'], X).fit()
    mod_full = sm.OLS(grp['Full_SRD'], X).fit()
    mod_dur = sm.OLS(grp['Duration_SRD'], X).fit()
    
    print(f"\n  {site} (n={n}):")
    print(f"    First_Trend: {mod_first.params.iloc[1]*10:.2f} [{mod_first.conf_int().iloc[1,0]*10:.2f}, {mod_first.conf_int().iloc[1,1]*10:.2f}]")
    print(f"    Full_Trend:  {mod_full.params.iloc[1]*10:.2f} [{mod_full.conf_int().iloc[1,0]*10:.2f}, {mod_full.conf_int().iloc[1,1]*10:.2f}]")
    print(f"    Dur_Trend:   {mod_dur.params.iloc[1]*10:.2f} [{mod_dur.conf_int().iloc[1,0]*10:.2f}, {mod_dur.conf_int().iloc[1,1]*10:.2f}]")
