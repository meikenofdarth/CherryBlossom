import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline
from matplotlib.collections import LineCollection
import warnings
warnings.filterwarnings('ignore')

AONO_CSV = "data/kyoto_cleaned.csv"
OUTPUT_DIR = "plots/Phase2_Theoretical"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------
# Mathematical Model
# -----------------
def theoretical_x(t, E0, beta, A, period, phi, k):
    """
    Steady-state solution to: dx/dt = -k(x(t) - E(t))
    where E(t) = E0 - beta*t + A*sin(omega*t + phi)
    and omega = 2*pi / period.
    """
    omega = 2 * np.pi / period
    
    # Linear drift component
    linear_part = E0 + (beta / k) - beta * t
    
    # Oscillating limit cycle component (attenuated and phase-shifted)
    amplitude_attenuation = k / np.sqrt(k**2 + omega**2)
    phase_lag = np.arctan(omega / k)
    oscillation_part = A * amplitude_attenuation * np.sin(omega * t + phi - phase_lag)
    
    return linear_part + oscillation_part

def theoretical_E(t, E0, beta, A, period, phi):
    """ The environmental driving force E(t) """
    omega = 2 * np.pi / period
    return E0 - beta * t + A * np.sin(omega * t + phi)

def colorline(x, y, z=None, cmap=plt.get_cmap('copper'), norm=plt.Normalize(0.0, 1.0), linewidth=3, alpha=1.0, ax=None):
    if z is None: z = np.linspace(0.0, 1.0, len(x))
    if not hasattr(z, "__iter__"): z = np.array([z])
    z = np.asarray(z)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, array=z, cmap=cmap, norm=norm, linewidth=linewidth, alpha=alpha)
    if ax is None: ax = plt.gca()
    ax.add_collection(lc)
    return lc

# -----------------
# Data Loading & Fitting
# -----------------
df = pd.read_csv(AONO_CSV).dropna(subset=['Year', 'DOY'])
years = df['Year'].values
doys = df['DOY'].values

# Normalize time to start at 0 for numeric stability in fitting
t_norm = years - years.min()

# Initial guess for parameters: E0, beta, A, period, phi, k
# E0 ~ mean DOY (~105)
# beta ~ small warming trend (e.g. 0.01 days/year)
# A ~ 5 days amplitude
# period ~ 200 years (multi-century cycle)
# phi ~ 0
# k ~ 0.5 (fast adaptation)
initial_guess = [105.0, 0.01, 5.0, 200.0, 0.0, 0.5]

# Bounds to keep physics realistic
# E0: [90, 120]
# beta: [-0.05, 0.05] (allow cooling or warming)
# A: [0, 20] (amplitude in days)
# period: [30, 800] (decadal to multi-century)
# phi: [-pi, pi]
# k: [0.01, 5.0] (adaptation rate)
bounds = (
    [90.0, -0.05, 0.0, 30.0, -np.pi, 0.01],
    [120.0, 0.05, 20.0, 800.0, np.pi, 5.0]
)

print("Running theoretical optimization (Curve Fit)...")
popt, pcov = curve_fit(theoretical_x, t_norm, doys, p0=initial_guess, bounds=bounds)

E0_fit, beta_fit, A_fit, period_fit, phi_fit, k_fit = popt
print("\n--- Optimized Physical Parameters ---")
print(f"E0 (Base Equilibrium) = {E0_fit:.2f} DOY")
print(f"Beta (Warming Trend)  = {beta_fit:.4f} days/year")
print(f"A (Climate Amp)       = {A_fit:.2f} days")
print(f"T (Climate Period)    = {period_fit:.1f} years")
print(f"k (Biol. Adaptation)  = {k_fit:.3f}")

# -----------------
# Plotting
# -----------------
t_cont = np.linspace(t_norm.min(), t_norm.max(), 1000)
years_cont = t_cont + years.min()

# Compute theoretical trajectories
x_sim = theoretical_x(t_cont, *popt)
E_sim = theoretical_E(t_cont, E0_fit, beta_fit, A_fit, period_fit, phi_fit)

# Theoretical derivative (dx/dt = -k(x - E))
dxdt_sim = -k_fit * (x_sim - E_sim)

plt.rcParams.update({'font.size': 12, 'axes.grid': True, 'grid.alpha': 0.3, 'figure.dpi': 150})
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle(f"Phase 2: Theoretical Driven-Equilibrium Model Fit (Kyoto Aono)\nEquation: dx/dt = -k(x - E(t))", fontsize=14, y=1.02)

# --- Temporal Plot ---
ax_temp = axes[0]
ax_temp.scatter(years, doys, color="purple", alpha=0.2, s=15, label='Historical Data')
ax_temp.plot(years_cont, E_sim, 'r--', lw=2, label='Fitted Environment E(t)', alpha=0.7)
ax_temp.plot(years_cont, x_sim, 'k-', lw=3, label='Theoretical Bloom x(t)')
ax_temp.set_title("Temporal Dynamics")
ax_temp.set_ylabel("Bloom Date (Day of Year)")
ax_temp.set_xlabel("Year")
ax_temp.legend(loc='lower left', fontsize=10)

# --- Phase Space Plot ---
ax_phase = axes[1]
ax_phase.axhline(0, color='gray', lw=1)

# We use the empirical spline's dx/dt just for the background reference
spl = UnivariateSpline(years, doys, s=100*len(years))
x_empirical = spl(years_cont)
dxdt_empirical = spl.derivative()(years_cont)
ax_phase.plot(x_empirical, dxdt_empirical, color='lightgray', lw=2, label='Empirical Spline', zorder=1)

# Plot theoretical phase space
cmap = plt.get_cmap("viridis")
norm = plt.Normalize(years.min(), years.max())
lc = colorline(x_sim, dxdt_sim, z=years_cont, cmap=cmap, norm=norm, linewidth=4, alpha=0.9, ax=ax_phase)
cbar = fig.colorbar(lc, ax=ax_phase, pad=0.01)
cbar.set_label('Year')

ax_phase.set_title("Theoretical Phase Space (dx/dt vs x)")
ax_phase.set_xlabel("Bloom Date (Day of Year)")
ax_phase.set_ylabel("Theoretical dx/dt (days/year)")
ax_phase.legend(loc='upper right', fontsize=10)

pad_x = (x_sim.max() - x_sim.min()) * 0.5
ax_phase.set_xlim(x_sim.min() - pad_x, x_sim.max() + pad_x)
pad_y = (dxdt_sim.max() - dxdt_sim.min()) * 0.5
ax_phase.set_ylim(dxdt_sim.min() - pad_y, dxdt_sim.max() + pad_y)

plt.tight_layout()
fname = os.path.join(OUTPUT_DIR, "Phase2_Theoretical_Fit_Aono.png")
fig.savefig(fname, bbox_inches='tight')
print(f"Successfully generated Phase 2 Plot: {fname}")
