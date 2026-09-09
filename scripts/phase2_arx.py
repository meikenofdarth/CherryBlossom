import pandas as pd
import numpy as np

data_f = []
with open('data/kyoto2010flower.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                if parts[1].strip() not in ('-', ''):
                    data_f.append((int(parts[0]), int(parts[1])))
            except: pass
df_f = pd.DataFrame(data_f, columns=['Year', 'n']).set_index('Year')

data_t = []
with open('data/kyoto2010temp.txt', 'r') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split()
        if len(parts) >= 3:
            try:
                tempobs = float(parts[2])
                temp = tempobs if tempobs != -999.9 else float(parts[1])
                if temp != -999.9:
                    data_t.append((int(parts[0]), temp))
            except: pass
df_t = pd.DataFrame(data_t, columns=['Year', 'T']).set_index('Year')

df = df_f.join(df_t, how='inner').sort_index()

# We want n_t = a * n_{t-1} + b * T_t + c
df['n_prev'] = df['n'].shift(1)
df['dt_prev'] = df.index.to_series().diff(periods=1)
# Only use consecutive previous years
df = df[df['dt_prev'] == 1.0].copy()
clean = df.dropna()

X = np.column_stack((np.ones(len(clean)), clean['n_prev'], clean['T']))
y = clean['n'].values
w, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
c = w[0]; a = w[1]; b = w[2]

# The long-term equilibrium relationship (if T is constant) is n_eq = a*n_eq + b*T + c
# So n_eq = (b*T + c) / (1 - a).
# Therefore the temperature sensitivity beta is b / (1 - a)
k = 1 - a
beta = b / k

print(f"--- AUTOREGRESSIVE TEMPERATURE FORCING ---")
print(f"Autoregressive coeff (a): {a:.4f}  --> Restoring force (k) = {k:.4f}")
print(f"Direct Temp coeff (b): {b:.4f}")
print(f"Long-term Temp Sensitivity (beta): {beta:.2f} days / °C")
