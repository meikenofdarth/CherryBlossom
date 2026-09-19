import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

# 1. Load Data with temp_source column
flower_data = []
with open('data/kyoto2010flower.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                year = int(parts[0])
                if parts[1].strip() not in ('-', ''):
                    flower_data.append((year, int(parts[1])))
            except ValueError: pass
df_flower = pd.DataFrame(flower_data, columns=['Year', 'DOY']).set_index('Year')

temp_data = []
with open('data/kyoto2010temp.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 3:
            try:
                year = int(parts[0])
                temprec = float(parts[1])
                tempobs = float(parts[2])
                
                if tempobs != -999.9:
                    temp_data.append((year, tempobs, 'observed'))
                else:
                    if temprec != -999.9:
                        temp_data.append((year, temprec, 'reconstructed'))
            except ValueError: pass
df_temp = pd.DataFrame(temp_data, columns=['Year', 'Temp_March', 'temp_source']).set_index('Year')

df = df_flower.join(df_temp, how='inner').sort_index()

# 2. DOY-vs-temperature regression on OBSERVED years only
df_obs = df[df['temp_source'] == 'observed'].copy()
X_obs = df_obs[['Temp_March']]
y_obs = df_obs['DOY']

reg_obs = LinearRegression().fit(X_obs, y_obs)
y_pred_obs = reg_obs.predict(X_obs)
r2_obs = r2_score(y_obs, y_pred_obs)
rmse_obs = np.sqrt(mean_squared_error(y_obs, y_pred_obs))
n_obs = len(df_obs)
slope_obs = reg_obs.coef_[0]

print("--- REGRESSION (OBSERVED TEMPERATURES ONLY) ---")
print(f"n: {n_obs}")
print(f"Slope (days/°C): {slope_obs:.2f}")
print(f"R-squared: {r2_obs:.4f}")
print(f"RMSE: {rmse_obs:.2f} days\n")

# 3. Residuals vs Year and Durbin-Watson
residuals = y_obs - y_pred_obs
dw_stat = durbin_watson(residuals)

print("--- AUTOCORRELATION CHECK ---")
print(f"Durbin-Watson statistic: {dw_stat:.4f}\n")

plt.figure(figsize=(10, 5))
plt.scatter(df_obs.index, residuals, alpha=0.7, color='purple', s=20)
plt.axhline(0, color='black', linestyle='--')
plt.title('Residuals vs Year (Observed Temp Years)')
plt.xlabel('Year')
plt.ylabel('Residuals (Days)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/residuals_vs_year_observed.png', dpi=300)
plt.close()

# 4. 30-year rolling mean + separate pre/post 1850 trends
full_years = np.arange(df.index.min(), df.index.max() + 1)
df_cont = df.reindex(full_years)
df_cont['DOY_interp'] = df_cont['DOY'].interpolate(method='linear')
df_cont['rolling_30yr'] = df_cont['DOY_interp'].rolling(window=30, center=True).mean()

df_pre = df[df.index < 1850].dropna(subset=['DOY'])
X_pre = df_pre.index.values.reshape(-1, 1)
reg_pre = LinearRegression().fit(X_pre, df_pre['DOY'])
slope_pre = reg_pre.coef_[0] * 100

df_post = df[df.index >= 1850].dropna(subset=['DOY'])
X_post = df_post.index.values.reshape(-1, 1)
reg_post = LinearRegression().fit(X_post, df_post['DOY'])
slope_post = reg_post.coef_[0] * 100

print("--- TIME TRENDS ---")
print(f"Pre-1850 trend: {slope_pre:.2f} days/century")
print(f"Post-1850 trend: {slope_post:.2f} days/century\n")

plt.figure(figsize=(12, 6))
plt.scatter(df.index, df['DOY'], color='lightgray', s=10, alpha=0.5, label='Annual DOY')
plt.plot(df_cont.index, df_cont['rolling_30yr'], color='blue', linewidth=2, label='30-yr Rolling Mean')
plt.plot(X_pre, reg_pre.predict(X_pre), color='green', linewidth=2, linestyle='--', label='Pre-1850 Trend')
plt.plot(X_post, reg_post.predict(X_post), color='red', linewidth=2, linestyle='--', label='Post-1850 Trend')
plt.axvline(1850, color='black', linestyle=':', label='1850 Split')
plt.title('Bloom DOY Over Time (Rolling Mean & Split Trends)')
plt.xlabel('Year')
plt.ylabel('Day of Year (DOY)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/doy_trends_split.png', dpi=300)
plt.close()

# 5. Train/Test Split (Out-of-sample RMSE)
df_train = df_obs[df_obs.index <= 1960]
df_test = df_obs[df_obs.index > 1960]

X_train = df_train[['Temp_March']]
y_train = df_train['DOY']
reg_split = LinearRegression().fit(X_train, y_train)

X_test = df_test[['Temp_March']]
y_test = df_test['DOY']
y_pred_test = reg_split.predict(X_test)
rmse_out_of_sample = np.sqrt(mean_squared_error(y_test, y_pred_test))

print("--- OUT-OF-SAMPLE TEST (Train <= 1960, Test > 1960) ---")
print(f"Train n: {len(df_train)}")
print(f"Test n: {len(df_test)}")
print(f"Out-of-sample RMSE: {rmse_out_of_sample:.2f} days")

