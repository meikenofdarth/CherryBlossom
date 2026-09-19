import pandas as pd
import numpy as np
import statsmodels.api as sm

df = pd.read_csv('data/kyoto_cleaned.csv', index_col='Year')
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

df_pre = df[df.index < 1850].dropna(subset=['DOY'])
X_pre = sm.add_constant(df_pre.index.values)
model_pre = sm.OLS(df_pre['DOY'], X_pre).fit()
slope_pre = model_pre.params[1] * 100
ci_pre_lower = model_pre.conf_int()[0][1] * 100
ci_pre_upper = model_pre.conf_int()[1][1] * 100

print("\nPre-1850 Trend (days/century):")
print(f"  Estimate: {slope_pre:.2f}")
print(f"  95% CI: [{ci_pre_lower:.2f}, {ci_pre_upper:.2f}]")

df_post = df[df.index >= 1850].dropna(subset=['DOY'])
X_post = sm.add_constant(df_post.index.values)
model_post = sm.OLS(df_post['DOY'], X_post).fit()
slope_post = model_post.params[1] * 100
ci_post_lower = model_post.conf_int()[0][1] * 100
ci_post_upper = model_post.conf_int()[1][1] * 100

print("\nPost-1850 Trend (days/century):")
print(f"  Estimate: {slope_post:.2f}")
print(f"  95% CI: [{ci_post_lower:.2f}, {ci_post_upper:.2f}]")
