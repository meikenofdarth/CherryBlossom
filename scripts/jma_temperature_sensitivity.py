import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import os

# --- 1. Load Data ---
df1 = pd.read_csv('data/JMA-kaggle_dataest/sakura_first_bloom_dates.csv')
df2 = pd.read_csv('data/JMA-kaggle_dataest/sakura_full_bloom_dates.csv')
df_temp = pd.read_csv('data/jma_temperatures.csv')

cols_to_drop = ['30 Year Average 1991-2020', 'Notes']
id_vars = ['Site Name', 'Currently Being Observed']

df1_melt = df1.drop(columns=cols_to_drop, errors='ignore').melt(
    id_vars=id_vars, var_name='Year', value_name='First_Bloom_Date'
)
df2_melt = df2.drop(columns=cols_to_drop, errors='ignore').melt(
    id_vars=id_vars, var_name='Year', value_name='Full_Bloom_Date'
)

df = pd.merge(df1_melt, df2_melt, on=['Site Name', 'Currently Being Observed', 'Year'])

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

df_valid = df.dropna(subset=['First_DOY', 'Full_DOY', 'Duration_DT'])

# --- 2. Prepare Temperature Data ---
# Average Feb and March temps to represent the late-winter/early-spring warming phase
df_temp['Feb_Mar_Temp'] = (df_temp['Feb_Temp'] + df_temp['Mar_Temp']) / 2
df_merged = pd.merge(df_valid, df_temp, on=['Site Name', 'Year'])

print("=== STATION TEMPERATURE SENSITIVITY ===")
print("Comparing bloom timings against spring temperatures:\n")

results = []
for site, group in df_merged.groupby('Site Name'):
    # Regress Full DOY vs March Temp (How much does a warmer March advance the bloom?)
    X_march = sm.add_constant(group['Mar_Temp'])
    mod_march = sm.OLS(group['Full_DOY'], X_march).fit()
    
    # Regress Duration vs Feb-Mar Mean Temp (Does a warmer late winter stretch the bloom?)
    X_fm = sm.add_constant(group['Feb_Mar_Temp'])
    mod_dur = sm.OLS(group['Duration_DT'], X_fm).fit()
    
    print(f"{site.upper()}:")
    print(f"  DOY vs March Temp:   {mod_march.params.iloc[1]:.2f} days/°C (R² = {mod_march.rsquared:.2f})")
    print(f"  Duration vs Feb/Mar: {mod_dur.params.iloc[1]:.2f} days/°C (R² = {mod_dur.rsquared:.2f})\n")

# --- 3. Plotting ---
os.makedirs('plots', exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(15, 5))

sites_to_plot = ['Asahikawa', 'Kyoto', 'Kagoshima']
colors = ['blue', 'green', 'red']

# Plot 1: Full Bloom vs March Temp
for site, color in zip(sites_to_plot, colors):
    subset = df_merged[df_merged['Site Name'] == site]
    if not subset.empty:
        axes[0].scatter(subset['Mar_Temp'], subset['Full_DOY'], label=site, alpha=0.6, color=color)
        z = np.polyfit(subset['Mar_Temp'], subset['Full_DOY'], 1)
        axes[0].plot(subset['Mar_Temp'], np.poly1d(z)(subset['Mar_Temp']), color=color)

axes[0].set_title('Full Bloom DOY vs March Temperature')
axes[0].set_xlabel('March Mean Temperature (°C)')
axes[0].set_ylabel('Full Bloom DOY')
axes[0].legend()

# Plot 2: Duration vs Feb-Mar Temp
for site, color in zip(sites_to_plot, colors):
    subset = df_merged[df_merged['Site Name'] == site]
    if not subset.empty:
        axes[1].scatter(subset['Feb_Mar_Temp'], subset['Duration_DT'], label=site, alpha=0.6, color=color)
        z = np.polyfit(subset['Feb_Mar_Temp'], subset['Duration_DT'], 1)
        axes[1].plot(subset['Feb_Mar_Temp'], np.poly1d(z)(subset['Feb_Mar_Temp']), color=color)

axes[1].set_title('Bloom Duration vs Feb-Mar Mean Temperature')
axes[1].set_xlabel('Feb-Mar Mean Temperature (°C)')
axes[1].set_ylabel('Duration (Days)')
axes[1].legend()

plt.tight_layout()
plt.savefig('plots/temperature_sensitivity.png', dpi=300)
print("Plots saved to plots/temperature_sensitivity.png")