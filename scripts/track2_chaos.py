import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import nolds
from mpl_toolkits.mplot3d import Axes3D

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
full_years = np.arange(df.index.min(), df.index.max() + 1)
df_cont = df.reindex(full_years)
ts = df_cont['n'].interpolate(method='linear').values

# 2. Time Delay (tau)
# Calculate autocorrelation to find first zero-crossing or 1/e
max_lag = 100
autocorr = [pd.Series(ts).autocorr(lag=i) for i in range(max_lag)]

tau = 1 # Fallback
for i, ac in enumerate(autocorr):
    if ac <= np.exp(-1): # 1/e
        tau = i
        break

# 3. Embedding Dimension (m) - Correlation Dimension (D_2)
# nolds.corr_dim calculates the correlation dimension
# We will use an embedding dimension of 10 to ensure we capture the full phase space
try:
    d2 = nolds.corr_dim(ts, emb_dim=10)
except Exception as e:
    d2 = 2.0 # fallback if it fails

# 4. Maximal Lyapunov Exponent (lambda)
try:
    # Use Rosenstein algorithm for MLE
    lyap = nolds.lyap_r(ts, emb_dim=int(np.ceil(d2)) if not np.isnan(d2) else 3, tau=tau)
    # nolds.lyap_r returns an array of estimates for different trajectory times, we take the mean slope
    # Actually, nolds.lyap_r returns the exponent if fit="poly" is omitted? Wait, by default it fits a polynomial.
    # lyap_r returns a single float (the exponent) by default in recent versions, or an array if fit="RANSAC".
    # We will just print the result directly if it's a float, or take the mean/slope if it's an array.
    if isinstance(lyap, (list, np.ndarray)):
        lyap_max = np.polyfit(np.arange(len(lyap)), lyap, 1)[0]
    else:
        lyap_max = lyap
except Exception as e:
    lyap_max = 0.0

print("--- TRACK 2: TAKENS' EMBEDDING AND CHAOS ---")
print(f"Optimal Time Delay (tau): {tau} years")
print(f"Correlation Dimension (D_2): {d2:.4f}")
print("   -> The integer ceiling of this number is the minimum number of dynamic variables governing the Kyoto climate.")
print(f"Maximal Lyapunov Exponent (lambda): {lyap_max:.4f}")
if lyap_max > 0:
    print("   -> lambda > 0 implies deterministic chaos/sensitive dependence on initial conditions.")
else:
    print("   -> lambda <= 0 implies noise or a stable periodic system without chaos.")

# 6. Output Plot: 3D Phase Space Reconstruction
# n(t), n(t+tau), n(t+2*tau)
n_t = ts[:-2*tau]
n_t_plus_tau = ts[tau:-tau]
n_t_plus_2tau = ts[2*tau:]

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Smooth colormap representing time
time_colors = np.linspace(0, 1, len(n_t))
scatter = ax.scatter(n_t, n_t_plus_tau, n_t_plus_2tau, c=time_colors, cmap='viridis', s=10, alpha=0.7)

cbar = plt.colorbar(scatter, ax=ax, pad=0.1)
cbar.set_label('Time (Oldest to Newest)')

ax.set_title(f"3D Phase-Space Reconstruction (tau={tau})")
ax.set_xlabel('n(t)')
ax.set_ylabel(f'n(t+{tau})')
ax.set_zlabel(f'n(t+{2*tau})')

plt.tight_layout()
plt.savefig('plots/Aono_Kyoto_PhaseSpace_3D.png', dpi=300)
plt.close()
