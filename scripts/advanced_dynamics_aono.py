import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.interpolate import UnivariateSpline
import warnings

warnings.filterwarnings('ignore')

AONO_CSV = "data/kyoto_cleaned.csv"
OUTPUT_DIR = "plots/Aono_Kyoto"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def colorline(x, y, z=None, cmap=plt.get_cmap('copper'), norm=plt.Normalize(0.0, 1.0), linewidth=3, alpha=1.0, ax=None):
    if z is None:
        z = np.linspace(0.0, 1.0, len(x))
    if not hasattr(z, "__iter__"):
        z = np.array([z])
    z = np.asarray(z)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, array=z, cmap=cmap, norm=norm, linewidth=linewidth, alpha=alpha)
    if ax is None:
        ax = plt.gca()
    ax.add_collection(lc)
    return lc

df = pd.read_csv(AONO_CSV).dropna(subset=['Year', 'DOY'])
years = df['Year'].values
doys = df['DOY'].values

plt.rcParams.update({'font.size': 12, 'axes.grid': True, 'grid.alpha': 0.3, 'figure.dpi': 150})

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle(f"Kyoto Historical Record (812-2005): Moving Equilibrium Phase-Space Dynamics\n(Advanced Model: dx/dt = -k(x - x_eq(t)))", fontsize=14, y=1.02)

# Smoothing via Spline
# 780 data points, so use a very large smoothing factor to extract multi-century trends
spline_smoothness = 100 * len(years) 
spl = UnivariateSpline(years, doys, s=spline_smoothness)
spl_deriv = spl.derivative()

# Continuous time for smooth curves
t_cont = np.linspace(years.min(), years.max(), 1000)
x_smooth = spl(t_cont)
dxdt_smooth = spl_deriv(t_cont)

# Raw derivatives (using gradient on irregularly spaced years is tricky, so we just use diff)
dxdt_raw = np.zeros_like(doys)
dxdt_raw[1:] = np.diff(doys) / np.diff(years)
dxdt_raw[0] = dxdt_raw[1] # just fill first

ax_temp, ax_phase = axes[0], axes[1]
color = "purple"
cmap_name = "viridis"

# --- Temporal Plot (x vs t) ---
ax_temp.scatter(years, doys, color=color, alpha=0.3, label='Observed (x)', s=15)
ax_temp.plot(t_cont, x_smooth, 'k-', lw=3, label='Multi-Century Moving Equilibrium $x_{eq}(t)$')
ax_temp.set_title("Long-Term Historical Bloom Date vs Year")
ax_temp.set_ylabel("Bloom Date (Day of Year)")
ax_temp.set_xlabel("Year (t)")
ax_temp.legend(loc='best')

# --- Phase Space Plot (dx/dt vs x) ---
ax_phase.axhline(0, color='gray', lw=1)
# Plot raw phase space
ax_phase.scatter(doys, dxdt_raw, color='lightgray', s=15, alpha=0.3, label='Raw noisy path', zorder=1)

# Plot smoothed phase space colored by time
cmap = plt.get_cmap(cmap_name)
norm = plt.Normalize(years.min(), years.max())
lc = colorline(x_smooth, dxdt_smooth, z=t_cont, cmap=cmap, norm=norm, linewidth=4, alpha=0.9, ax=ax_phase)

# Start and End markers
ax_phase.scatter([x_smooth[0]], [dxdt_smooth[0]], color=cmap(0.0), marker='o', s=150, edgecolor='k', zorder=5, label=f'Start ({int(years.min())})')
ax_phase.scatter([x_smooth[-1]], [dxdt_smooth[-1]], color=cmap(1.0), marker='*', s=200, edgecolor='k', zorder=5, label=f'End ({int(years.max())})')

cbar = fig.colorbar(lc, ax=ax_phase, pad=0.01)
cbar.set_label('Year (t)')

ax_phase.set_title("Phase Space: dx/dt vs x")
ax_phase.set_xlabel("Bloom Date (Day of Year)")
ax_phase.set_ylabel("dx/dt (days/year)")
ax_phase.legend(loc='upper right', fontsize=10)

pad_x = (x_smooth.max() - x_smooth.min()) * 0.5
ax_phase.set_xlim(x_smooth.min() - pad_x, x_smooth.max() + pad_x)
pad_y = (dxdt_smooth.max() - dxdt_smooth.min()) * 0.5
ax_phase.set_ylim(dxdt_smooth.min() - pad_y, dxdt_smooth.max() + pad_y)

plt.tight_layout()
fname = os.path.join(OUTPUT_DIR, "Aono_Kyoto_Advanced_Dynamics.png")
fig.savefig(fname, bbox_inches='tight')
print(f"Successfully generated Aono historical plot: {fname}")
