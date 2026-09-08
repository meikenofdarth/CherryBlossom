import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# Read the data
data = []
with open('data/kyoto2010flower.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                year = int(parts[0])
                if parts[1].strip() != '-' and parts[1].strip() != '':
                    doy = int(parts[1])
                    data.append((year, doy))
            except ValueError: pass

df = pd.DataFrame(data, columns=['Year', 'n'])
df = df.set_index('Year').sort_index()

# Local slope calculation
window_size = 21 # 21 years seems reasonable to capture local climate trends while smoothing out year-to-year noise
half_window = window_size // 2

local_slopes = []
local_n = []
years = []

for year in df.index:
    # get data within the window [year - half_window, year + half_window]
    window_data = df.loc[year - half_window : year + half_window]
    if len(window_data) >= 7: # need enough points to calculate a meaningful slope
        slope, intercept, r_value, p_value, std_err = linregress(window_data.index, window_data['n'])
        local_slopes.append(slope)
        local_n.append(df.loc[year, 'n'])
        years.append(year)

results = pd.DataFrame({'Year': years, 'n': local_n, 'dn_dt': local_slopes})

# Plot dn/dt vs n
plt.figure(figsize=(10, 8))
plt.scatter(results['n'], results['dn_dt'], alpha=0.5, s=15, c=results['Year'], cmap='viridis')
cbar = plt.colorbar()
cbar.set_label('Year')
plt.title(f'Local Slope (dn/dt) vs Bloom Date (n) - {window_size}-Year Window')
plt.xlabel('Time of Full Bloom (n)')
plt.ylabel('Local dn/dt (days/year)')
plt.axhline(0, color='red', linestyle='--', alpha=0.5)
plt.grid(True)
plt.tight_layout()
plt.savefig('plots/Aono_Kyoto_local_dndt_vs_n.png', dpi=300)
plt.close()

# Also plot n and smoothed n over time
plt.figure(figsize=(12, 6))
plt.scatter(df.index, df['n'], alpha=0.2, color='gray', label='Raw Data', s=10)
# Add smoothed n (moving average)
df['n_smooth'] = df['n'].rolling(window=window_size, min_periods=7, center=True).mean()
plt.plot(df.index, df['n_smooth'], color='blue', linewidth=2, label=f'{window_size}-Year Moving Average')
plt.title('Bloom Date (n) vs Time (t) with Moving Average')
plt.xlabel('Year (t)')
plt.ylabel('Day of Year (n)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('plots/Aono_Kyoto_n_vs_t_smoothed.png', dpi=300)
plt.close()

print("Local slope analysis complete. Plots saved to plots/ directory.")
