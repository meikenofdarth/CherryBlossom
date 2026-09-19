import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import os

# --- 1. Load and Clean Data ---
df1 = pd.read_csv('data/JMA-kaggle_dataest/sakura_first_bloom_dates.csv')
df2 = pd.read_csv('data/JMA-kaggle_dataest/sakura_full_bloom_dates.csv')
coords_file = 'data/JMA-kaggle_dataest/station_coords_template.csv'

if not os.path.exists(coords_file):
    print(f"Error: {coords_file} not found.")
    exit()

coords = pd.read_csv(coords_file)
coords['Latitude'] = pd.to_numeric(coords['Latitude'], errors='coerce')
if coords['Latitude'].isna().all():
    print("Error: Latitude column is empty. Please fill in the coordinates in the CSV first.")
    exit()

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
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df = df.dropna(subset=['Year'])

def safe_doy(dt_series):
    norm = pd.to_datetime({'year': 2001, 'month': dt_series.dt.month, 'day': dt_series.dt.day})
    return norm.dt.dayofyear

df['First_DOY'] = safe_doy(df['First_DT'])
df['Full_DOY'] = safe_doy(df['Full_DT'])
df['Duration_DT'] = (df['Full_DT'] - df['First_DT']).dt.days

exclude_species = ['Taiwan cherry (Prunus campanulata)', 'Kurile Island Cherry (Cerasus nipponica var. kurilensis)']
exclude_notes = df[df['Species'].str.contains("from 1995", na=False)]['Site Name'].unique()
df_clean = df[~df['Species'].isin(exclude_species)]
df_clean = df_clean[~df_clean['Site Name'].isin(exclude_notes)]
df_valid = df_clean.dropna(subset=['First_DOY', 'Full_DOY', 'Duration_DT'])

# --- 2. Calculate Common Window (1961-2010) Trends for Yoshino ---
df_window = df_valid[(df_valid['Year'] >= 1961) & (df_valid['Year'] <= 2010)]
df_yoshino = df_window[df_window['Species'] == 'Not stated']

results = []
for site, group in df_yoshino.groupby('Site Name'):
    n = len(group)
    if n < 40:
        continue
    
    mean_doy = group['Full_DOY'].mean()
    
    X = sm.add_constant(group['Year'])
    mod_full = sm.OLS(group['Full_DOY'], X).fit()
    mod_dur = sm.OLS(group['Duration_DT'], X).fit()

    results.append({
        'Site Name': site,
        'Mean_Full_DOY': mean_doy,
        'Full_Trend': mod_full.params.iloc[1] * 10,
        'Dur_Trend': mod_dur.params.iloc[1] * 10,
    })

df_res = pd.DataFrame(results)

# --- 3. Merge Coordinates & Regress on Latitude ---
analysis_df = pd.merge(df_res, coords[['Site Name', 'Latitude']], on='Site Name').dropna(subset=['Latitude'])

print(f"Running latitude regression on {len(analysis_df)} Yoshino stations...")

def run_regression(y_col, y_name):
    X = sm.add_constant(analysis_df['Latitude'])
    y = analysis_df[y_col]
    mod = sm.OLS(y, X).fit()
    
    slope = mod.params.iloc[1]
    ci_low = mod.conf_int().iloc[1, 0]
    ci_high = mod.conf_int().iloc[1, 1]
    r2 = mod.rsquared
    p_val = mod.pvalues.iloc[1]
    
    print(f"\n--- {y_name} vs Latitude ---")
    print(f"Slope: {slope:.3f} per degree latitude")
    print(f"95% CI: [{ci_low:.3f}, {ci_high:.3f}]")
    print(f"R²: {r2:.3f} | p-value: {p_val:.4f}")
    
    return mod

mod_mean = run_regression('Mean_Full_DOY', 'Mean Full-Bloom DOY')
mod_trend = run_regression('Full_Trend', 'Full-Bloom Trend (days/decade)')
mod_dur = run_regression('Dur_Trend', 'Duration Trend (days/decade)')

# --- 4. Plotting ---
os.makedirs('plots', exist_ok=True)
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1: Mean DOY vs Lat
axes[0].scatter(analysis_df['Latitude'], analysis_df['Mean_Full_DOY'], alpha=0.7)
axes[0].plot(analysis_df['Latitude'], mod_mean.predict(sm.add_constant(analysis_df['Latitude'])), color='red')
axes[0].set_title('Mean Full Bloom DOY vs Latitude')
axes[0].set_xlabel('Latitude')
axes[0].set_ylabel('Day of Year (DOY)')

# Plot 2: Full Bloom Trend vs Lat
axes[1].scatter(analysis_df['Latitude'], analysis_df['Full_Trend'], alpha=0.7)
axes[1].plot(analysis_df['Latitude'], mod_trend.predict(sm.add_constant(analysis_df['Latitude'])), color='red')
axes[1].axhline(0, color='black', linestyle='--', linewidth=1)
axes[1].set_title('Full Bloom Trend vs Latitude')
axes[1].set_xlabel('Latitude')
axes[1].set_ylabel('Trend (days/decade)')

# Plot 3: Duration Trend vs Lat
axes[2].scatter(analysis_df['Latitude'], analysis_df['Dur_Trend'], alpha=0.7)
axes[2].plot(analysis_df['Latitude'], mod_dur.predict(sm.add_constant(analysis_df['Latitude'])), color='red')
axes[2].axhline(0, color='black', linestyle='--', linewidth=1)
axes[2].set_title('Duration Trend vs Latitude')
axes[2].set_xlabel('Latitude')
axes[2].set_ylabel('Duration Trend (days/decade)')

plt.tight_layout()
plt.savefig('plots/latitude_regressions.png', dpi=300)
print("\nPlots saved to plots/latitude_regressions.png")