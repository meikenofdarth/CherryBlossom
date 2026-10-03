import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import os

# --- 1. Load canonical station-year weather data ---
weather_file = os.environ.get('WEATHER_FILE', 'data/station_year_weather.csv')
df_merged = pd.read_csv(weather_file)
df_merged = df_merged[df_merged['Main_Analysis_Eligible']].copy()

results = []

print("=== STATION TEMPERATURE SENSITIVITY ===")
print("Comparing bloom timings against spring temperatures:\n")

for site, group in df_merged.groupby('Site Name'):
    # Regress Full DOY vs March Temp (How much does a warmer March advance the bloom?)
    X_march = sm.add_constant(group['Mar_Temp'])
    mod_march = sm.OLS(group['Full_DOY'], X_march).fit()
    
    # Regress Duration vs Feb-Mar Mean Temp (Does a warmer late winter stretch the bloom?)
    X_fm = sm.add_constant(group['Feb_Mar_Temp'])
    mod_dur = sm.OLS(group['Duration_Days'], X_fm).fit()

    results.append({
        'Site Name': site,
        'Species': group['Species'].iloc[0],
        'n_years': len(group),
        'Bloom_Temp_Slope': mod_march.params.iloc[1],
        'Bloom_Temp_R2': mod_march.rsquared,
        'Bloom_Temp_CI_Lower': mod_march.conf_int().iloc[1, 0],
        'Bloom_Temp_CI_Upper': mod_march.conf_int().iloc[1, 1],
        'Duration_Temp_Slope': mod_dur.params.iloc[1],
        'Duration_Temp_R2': mod_dur.rsquared,
        'Duration_Temp_CI_Lower': mod_dur.conf_int().iloc[1, 0],
        'Duration_Temp_CI_Upper': mod_dur.conf_int().iloc[1, 1],
    })
    
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
        axes[1].scatter(subset['Feb_Mar_Temp'], subset['Duration_Days'], label=site, alpha=0.6, color=color)
        z = np.polyfit(subset['Feb_Mar_Temp'], subset['Duration_Days'], 1)
        axes[1].plot(subset['Feb_Mar_Temp'], np.poly1d(z)(subset['Feb_Mar_Temp']), color=color)

axes[1].set_title('Bloom Duration vs Feb-Mar Mean Temperature')
axes[1].set_xlabel('Feb-Mar Mean Temperature (°C)')
axes[1].set_ylabel('Duration (Days)')
axes[1].legend()

plt.tight_layout()
plt.savefig('plots/temperature_sensitivity.png', dpi=300)
suffix = '_jma' if weather_file.endswith('weather_jma.csv') else ''
pd.DataFrame(results).to_csv(f'data/station_temperature_sensitivity{suffix}.csv', index=False)
print("Plots saved to plots/temperature_sensitivity.png")
print(f"Saved data/station_temperature_sensitivity{suffix}.csv")