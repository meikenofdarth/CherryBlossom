import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.stats import kendalltau

# 1. Pre-processing
data = []
with open('data/kyoto2010flower.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                year = int(parts[0])
                if parts[1].strip() not in ('-', ''):
                    data.append((year, int(parts[1])))
            except ValueError: pass

df = pd.DataFrame(data, columns=['Year', 'n']).set_index('Year')

# Interpolate to create a continuous time series
full_years = np.arange(df.index.min(), df.index.max() + 1)
df_cont = df.reindex(full_years)
df_cont['n_interp'] = df_cont['n'].interpolate(method='linear')

# Focus on Pre-Industrial (800 AD to 1850 AD)
df_pre = df_cont.loc[(df_cont.index >= 800) & (df_cont.index <= 1850)].copy()

# Detrend using Gaussian filter (sigma=25 years)
df_pre['trend'] = gaussian_filter1d(df_pre['n_interp'], sigma=25)
df_pre['residuals'] = df_pre['n_interp'] - df_pre['trend']

# 2. Metrics (Rolling Variance and AR1 on residuals, window=50)
window = 50
df_pre['rolling_var'] = df_pre['residuals'].rolling(window=window).var()
df_pre['rolling_ar1'] = df_pre['residuals'].rolling(window=window).apply(lambda x: pd.Series(x).autocorr(lag=1), raw=False)

# 3. Statistical Inference (Kendall-tau from 1000 AD to 1850 AD)
df_csd = df_pre.loc[1000:1850].dropna()
tau_var, p_var = kendalltau(df_csd.index, df_csd['rolling_var'])
tau_ar1, p_ar1 = kendalltau(df_csd.index, df_csd['rolling_ar1'])

print("--- TRACK 1: CRITICAL SLOWING DOWN (CSD) ---")
print(f"Kendall-tau for Rolling Variance: {tau_var:.4f} (p-value: {p_var:.4e})")
print(f"Kendall-tau for Rolling AR1:      {tau_ar1:.4f} (p-value: {p_ar1:.4e})")
print("Interpretation: Positive tau values indicate an increasing trend, a hallmark of Critical Slowing Down before a tipping point.")

# 4. Output Plot
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Subplot A: Raw data and trend
ax1.plot(df_pre.index, df_pre['n_interp'], color='lightgray', label='Interpolated Data')
ax1.plot(df_pre.index, df_pre['trend'], color='blue', linewidth=2, label='Gaussian Trend (Slow Climate)')
ax1.set_title('(A) Cherry Blossom Full-Bloom Date (Pre-Industrial)')
ax1.set_ylabel('Day of Year (n)')
ax1.legend()
ax1.grid(True)

# Subplot B: Rolling AR1
ax2.plot(df_pre.index, df_pre['rolling_ar1'], color='orange', linewidth=2)
ax2.set_title('(B) Rolling Lag-1 Autocorrelation (AR1) of Residuals (50-yr window)')
ax2.set_ylabel('AR1')
ax2.axvline(1000, color='red', linestyle='--', alpha=0.5, label='CSD Analysis Start')
ax2.legend()
ax2.grid(True)

# Subplot C: Rolling Variance
ax3.plot(df_pre.index, df_pre['rolling_var'], color='green', linewidth=2)
ax3.set_title('(C) Rolling Variance of Residuals (50-yr window)')
ax3.set_xlabel('Year')
ax3.set_ylabel('Variance')
ax3.axvline(1000, color='red', linestyle='--', alpha=0.5)
ax3.grid(True)

plt.tight_layout()
plt.savefig('plots/Aono_Kyoto_CSD.png', dpi=300)
plt.close()
