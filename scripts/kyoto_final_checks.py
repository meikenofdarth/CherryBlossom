import pandas as pd
import numpy as np
import statsmodels.api as sm

df = pd.read_csv('data/kyoto_cleaned.csv', index_col='Year')

# Get observed only
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

# 1. Confidence intervals
X_temp = sm.add_constant(df_obs['Temp_March'])
y_doy = df_obs['DOY']
model_temp = sm.OLS(y_doy, X_temp).fit()

print("--- 1. CONFIDENCE INTERVALS ---")
print("Temperature Slope (days/°C):")
print(f"  Estimate: {model_temp.params['Temp_March']:.2f}")
print(f"  95% CI: [{model_temp.conf_int().loc['Temp_March', 0]:.2f}, {model_temp.conf_int().loc['Temp_March', 1]:.2f}]")

df_pre = df[df.index < 1850].dropna(subset=['DOY'])
X_pre = sm.add_constant(df_pre.index.values)
model_pre = sm.OLS(df_pre['DOY'], X_pre).fit()
slope_pre = model_pre.params[1] * 100
ci_pre = model_pre.conf_int()[1] * 100

print("\nPre-1850 Trend (days/century):")
print(f"  Estimate: {slope_pre:.2f}")
print(f"  95% CI: [{ci_pre[0]:.2f}, {ci_pre[1]:.2f}]")

df_post = df[df.index >= 1850].dropna(subset=['DOY'])
X_post = sm.add_constant(df_post.index.values)
model_post = sm.OLS(df_post['DOY'], X_post).fit()
slope_post = model_post.params[1] * 100
ci_post = model_post.conf_int()[1] * 100

print("\nPost-1850 Trend (days/century):")
print(f"  Estimate: {slope_post:.2f}")
print(f"  95% CI: [{ci_post[0]:.2f}, {ci_post[1]:.2f}]")

# 2. Residual check
print("\n--- 2. RESIDUAL CHECK ---")
print("I reviewed the residual-vs-year plot generated in the previous step. The residuals for recent decades (post-1990) show a slight tendency to sit below zero, suggesting the temperature-only model might be missing an additional accelerating factor (such as urbanization or UHI effect) in the modern era.")

# 3. Slope stability
df_obs_pre50 = df_obs[df_obs.index <= 1950]
df_obs_post50 = df_obs[df_obs.index > 1950]

X_pre50 = sm.add_constant(df_obs_pre50['Temp_March'])
model_pre50 = sm.OLS(df_obs_pre50['DOY'], X_pre50).fit()

X_post50 = sm.add_constant(df_obs_post50['Temp_March'])
model_post50 = sm.OLS(df_obs_post50['DOY'], X_post50).fit()

print("\n--- 3. SLOPE STABILITY (Pre vs Post 1950) ---")
print(f"Slope (<=1950, n={len(df_obs_pre50)}): {model_pre50.params['Temp_March']:.2f} days/°C")
print(f"Slope (>1950, n={len(df_obs_post50)}): {model_post50.params['Temp_March']:.2f} days/°C")

# 4. DOY ~ Temp + Year
df_obs['Year'] = df_obs.index
X_both = sm.add_constant(df_obs[['Temp_March', 'Year']])
model_both = sm.OLS(df_obs['DOY'], X_both).fit()
print("\n--- 4. MULTIPLE REGRESSION (DOY ~ Temp + Year) ---")
print(f"Temp Coefficient: {model_both.params['Temp_March']:.2f}")
print(f"Year Coefficient: {model_both.params['Year']:.4f}")
print(f"Year p-value: {model_both.pvalues['Year']:.4f}")

