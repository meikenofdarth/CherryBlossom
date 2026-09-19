import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from scipy.stats import ttest_1samp

# 1. Load Data
flower_data = []
with open('data/kyoto2010flower.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                if parts[1].strip() not in ('-', ''):
                    flower_data.append((int(parts[0]), int(parts[1])))
            except: pass
df_flower = pd.DataFrame(flower_data, columns=['Year', 'DOY']).set_index('Year')

temp_data = []
with open('data/kyoto2010temp.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 3:
            try:
                y = int(parts[0])
                tobs = float(parts[2])
                if tobs != -999.9:
                    temp_data.append((y, tobs, 'observed'))
            except: pass
df_temp = pd.DataFrame(temp_data, columns=['Year', 'Temp_March', 'temp_source']).set_index('Year')
df_obs = df_flower.join(df_temp, how='inner').sort_index()
df_all = df_flower.copy() # For full time trends

# Output file
out = open('data/kyoto_results.txt', 'w')
def pr(text):
    print(text)
    out.write(text + '\n')

pr("=== KYOTO MASTER ANALYSIS (OBSERVED TEMP YEARS ONLY) ===")

# Model: DOY ~ Temp_March
X_temp = sm.add_constant(df_obs['Temp_March'])
y_doy = df_obs['DOY']
model_temp = sm.OLS(y_doy, X_temp).fit()

pr(f"\nTemperature Slope (days/°C): {model_temp.params.iloc[1]:.2f}")
pr(f"95% CI: [{model_temp.conf_int().iloc[1, 0]:.2f}, {model_temp.conf_int().iloc[1, 1]:.2f}]")
pr(f"R-squared: {model_temp.rsquared:.4f}")
pr(f"n: {len(df_obs)}")

residuals = model_temp.resid
pr(f"Durbin-Watson: {durbin_watson(residuals):.4f}")

# Post-1990 residuals
res_post1990 = residuals[df_obs.index > 1990]
n_post1990 = len(res_post1990)
mean_res_post1990 = res_post1990.mean()
t_stat, p_val = ttest_1samp(res_post1990, 0.0)
pr(f"\nPost-1990 Residuals Check:")
pr(f"n: {n_post1990}")
pr(f"Mean Residual: {mean_res_post1990:.2f} days")
pr(f"t-test p-value (H0: mean=0): {p_val:.4f}")

# Pre vs Post 1950 Interaction
df_obs['Post1950'] = (df_obs.index > 1950).astype(int)
df_obs['Temp_x_Post1950'] = df_obs['Temp_March'] * df_obs['Post1950']
X_int = sm.add_constant(df_obs[['Temp_March', 'Post1950', 'Temp_x_Post1950']])
model_int = sm.OLS(df_obs['DOY'], X_int).fit()
pr(f"\nTemp x Post1950 Interaction p-value: {model_int.pvalues.iloc[3]:.4f}")

# DOY ~ Temp + Year
df_obs['Year'] = df_obs.index
X_both = sm.add_constant(df_obs[['Temp_March', 'Year']])
model_both = sm.OLS(df_obs['DOY'], X_both).fit()
pr(f"\nDOY ~ Temp + Year:")
pr(f"Year Coefficient: {model_both.params.iloc[2]:.4f}")
pr(f"Year p-value: {model_both.pvalues.iloc[2]:.4f}")

pr("\n=== KYOTO FULL 1200-YEAR TIME TRENDS ===")
# Pre 1850
df_pre = df_all[df_all.index < 1850].dropna(subset=['DOY'])
X_pre = sm.add_constant(df_pre.index.values)
model_pre = sm.OLS(df_pre['DOY'], X_pre).fit()
pr(f"\nPre-1850 Trend (days/century): {model_pre.params.iloc[1]*100:.2f}")
pr(f"95% CI: [{model_pre.conf_int().iloc[1, 0]*100:.2f}, {model_pre.conf_int().iloc[1, 1]*100:.2f}]")

# Post 1850
df_post = df_all[df_all.index >= 1850].dropna(subset=['DOY'])
X_post = sm.add_constant(df_post.index.values)
model_post = sm.OLS(df_post['DOY'], X_post).fit()
pr(f"\nPost-1850 Trend (days/century): {model_post.params.iloc[1]*100:.2f}")
pr(f"95% CI: [{model_post.conf_int().iloc[1, 0]*100:.2f}, {model_post.conf_int().iloc[1, 1]*100:.2f}]")

# Post 1950 (or 1970)
df_post1950 = df_all[df_all.index >= 1950].dropna(subset=['DOY'])
X_post1950 = sm.add_constant(df_post1950.index.values)
model_post1950 = sm.OLS(df_post1950['DOY'], X_post1950).fit()
pr(f"\nPost-1950 Trend (days/century): {model_post1950.params.iloc[1]*100:.2f}")
pr(f"95% CI: [{model_post1950.conf_int().iloc[1, 0]*100:.2f}, {model_post1950.conf_int().iloc[1, 1]*100:.2f}]")

out.close()
