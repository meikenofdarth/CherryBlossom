import pandas as pd
import numpy as np
from scipy.stats import linregress

# Load data
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

df = pd.DataFrame(data, columns=['Year', 'n']).sort_values('Year')

# Split data into Pre-Industrial (<=1850) and Modern (>1850)
df_pre = df[df['Year'] <= 1850].copy()
df_post = df[df['Year'] > 1850].copy()

def get_dynamics(df_sub):
    # Calculate forward differences
    df_sub['dt'] = df_sub['Year'].diff(periods=-1) * -1
    df_sub['dn'] = df_sub['n'].diff(periods=-1) * -1
    df_sub['dn_dt'] = df_sub['dn'] / df_sub['dt']
    
    # Drop NaNs (the last row)
    clean = df_sub.dropna()
    
    # Linear regression: dn/dt = -k * n + c
    slope, intercept, r, p, err = linregress(clean['n'], clean['dn_dt'])
    
    k = -slope
    n_eq = intercept / k
    
    # Calculate noise variance (sigma)
    clean['predicted_dn_dt'] = -k * clean['n'] + intercept
    residuals = clean['dn_dt'] - clean['predicted_dn_dt']
    sigma = np.std(residuals)
    
    return n_eq, k, sigma, len(clean)

n_eq_pre, k_pre, sigma_pre, count_pre = get_dynamics(df_pre)
n_eq_post, k_post, sigma_post, count_post = get_dynamics(df_post)

print(f"--- PRE-INDUSTRIAL BASELINE (812 AD - 1850 AD) [{count_pre} datapoints] ---")
print(f"Natural Equilibrium (n_eq): {n_eq_pre:.2f} (Day of Year)")
print(f"Restoring Force (k):        {k_pre:.4f}")
print(f"Natural Volatility (sigma): {sigma_pre:.2f} days/year\n")

print(f"--- MODERN ERA (1851 AD - Present) [{count_post} datapoints] ---")
print(f"Modern Equilibrium (n_eq):  {n_eq_post:.2f} (Day of Year)")
print(f"Restoring Force (k):        {k_post:.4f}")
print(f"Modern Volatility (sigma):  {sigma_post:.2f} days/year")

