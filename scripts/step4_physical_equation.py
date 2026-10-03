import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import statsmodels.api as sm
import os

# --- 1. Load Actual Kyoto Bloom Data ---
df_full = pd.read_csv('data/JMA-kaggle_dataest/sakura_full_bloom_dates.csv')
cols_to_drop = ['30 Year Average 1991-2020', 'Notes']
df2_melt = df_full.drop(columns=cols_to_drop, errors='ignore').melt(
    id_vars=['Site Name', 'Currently Being Observed'], var_name='Year', value_name='Full_Bloom_Date'
)
kyoto_actual = df2_melt[df2_melt['Site Name'] == 'Kyoto'].copy()
kyoto_actual['Full_DT'] = pd.to_datetime(kyoto_actual['Full_Bloom_Date'], errors='coerce')
kyoto_actual['Year'] = pd.to_numeric(kyoto_actual['Year'], errors='coerce')
kyoto_actual = kyoto_actual.dropna(subset=['Full_DT'])

# Mathematically safe DOY (Subtracts 1 from DOY after Feb 28 in leap years)
def safe_doy(dt_series):
    doy = dt_series.dt.dayofyear
    is_leap = dt_series.dt.is_leap_year.fillna(False)
    adjusted = np.where(is_leap & (doy > 59), doy - 1, doy)
    return pd.Series(adjusted, index=dt_series.index)

kyoto_actual['Actual_DOY'] = safe_doy(kyoto_actual['Full_DT'])

# --- 2. Fetch Daily Data for Kyoto (Open-Meteo) ---
print("Fetching daily temperatures for Kyoto to run physical model...")
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 35.0116,
    "longitude": 135.7681,
    "start_date": "1953-01-01",
    "end_date": "2024-12-31",
    "daily": "temperature_2m_mean",
    "timezone": "Asia/Tokyo"
}

response = requests.get(url, params=params)
data = response.json()

df_temp = pd.DataFrame({
    'Date': pd.to_datetime(data['daily']['time']),
    'Temp': data['daily']['temperature_2m_mean']
})
df_temp = df_temp.dropna()
df_temp['Year'] = df_temp['Date'].dt.year
df_temp['Month'] = df_temp['Date'].dt.month

# Map Open-Meteo dates to our non-leap normalized DOY
df_temp['DOY_Norm'] = safe_doy(df_temp['Date'])

# --- 3. Apply 400-Degree Rule ---
predictions = []
# Rule: Sum daily mean temperatures starting Feb 1st. Bloom happens when sum >= 400.
for year in df_temp['Year'].unique():
    year_data = df_temp[(df_temp['Year'] == year) & (df_temp['Month'] >= 2)].copy()
    year_data = year_data.sort_values('Date')

    # We only sum positive temperatures
    year_data['Temp_Effective'] = year_data['Temp'].apply(lambda x: x if x > 0 else 0)
    year_data['CumSum_400'] = year_data['Temp_Effective'].cumsum()

    bloom_day = year_data[year_data['CumSum_400'] >= 400]
    if not bloom_day.empty:
        pred_doy = bloom_day.iloc[0]['DOY_Norm']
        predictions.append({'Year': year, 'Pred_DOY_400': pred_doy})

df_pred = pd.DataFrame(predictions)
results = pd.merge(kyoto_actual[['Year', 'Actual_DOY']], df_pred, on='Year')

# --- 4. Calculate Errors ---
results['Error_400'] = results['Pred_DOY_400'] - results['Actual_DOY']
rmse_400 = np.sqrt((results['Error_400']**2).mean())

# Fallback: Statistical Linear Model (DOY = a - b * FebMar_Temp)
fm_temp = df_temp[df_temp['Month'].isin([2,3])].groupby('Year')['Temp'].mean().reset_index()
fm_temp.columns = ['Year', 'FebMar_Temp']
results = pd.merge(results, fm_temp, on='Year')

X = sm.add_constant(results['FebMar_Temp'])
mod = sm.OLS(results['Actual_DOY'], X).fit()
results['Pred_Linear'] = mod.predict(X)
rmse_linear = np.sqrt(((results['Pred_Linear'] - results['Actual_DOY'])**2).mean())

print(f"\n=== KYOTO PREDICTION ERROR SUMMARY ===")
print(f"Physical Model (400-Degree Rule) RMSE: {rmse_400:.2f} days")
print(f"Statistical Fallback (Linear Reg) RMSE: {rmse_linear:.2f} days")
print(f"-> A lower RMSE means the model is more accurate.")

# --- 5. Plot ---
os.makedirs('plots', exist_ok=True)
plt.figure(figsize=(12, 6))
plt.plot(results['Year'], results['Actual_DOY'], label='Actual Bloom DOY', color='black', linewidth=2)
plt.plot(results['Year'], results['Pred_DOY_400'], label='400-Degree Rule', color='red', linestyle='--')
plt.plot(results['Year'], results['Pred_Linear'], label='Linear Regression Fallback', color='blue', linestyle=':')

plt.title('Kyoto Bloom Prediction: Physical Model vs Statistical Model')
plt.xlabel('Year')
plt.ylabel('Day of Year (DOY)')
plt.legend()
plt.tight_layout()
plt.savefig('plots/step4_physical_equation.png', dpi=300)
print("\nPlot saved to plots/step4_physical_equation.png")
