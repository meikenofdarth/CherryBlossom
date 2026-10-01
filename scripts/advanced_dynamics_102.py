import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.collections import LineCollection
from scipy.interpolate import UnivariateSpline
from datetime import date, timedelta
import warnings

# Suppress warnings for splines on small data
warnings.filterwarnings('ignore')

# Configuration
FIRST_BLOOM_CSV = "data/JMA-kaggle_dataest/sakura_first_bloom_dates.csv"
FULL_BLOOM_CSV = "data/JMA-kaggle_dataest/sakura_full_bloom_dates.csv"
OUTPUT_DIR = "plots/JMA-102_cities_plots/advanced_dynamics"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------
# Utility Functions
# -----------------
def get_year_columns(df):
    return [c for c in df.columns if c.strip().isdigit()]

def normalized_doy(dt_obj):
    if pd.isna(dt_obj): return np.nan
    m, d = dt_obj.month, dt_obj.day
    if m == 2 and d == 29: return 59.5
    return date(2001, m, d).timetuple().tm_yday

def extract_station_series(df, station_name, year_cols):
    match = df.loc[df['Site Name'] == station_name]
    if match.empty: return np.array([]), np.array([])
    row = match.iloc[0]
    
    years, doys = [], []
    for yc in year_cols:
        raw = row[yc]
        if pd.isna(raw) or raw == '': continue
        dt_obj = pd.to_datetime(raw, errors='coerce')
        if pd.isna(dt_obj): continue
        years.append(int(yc))
        doys.append(normalized_doy(dt_obj))
        
    years = np.array(years, dtype=int)
    doys = np.array(doys, dtype=float)
    order = np.argsort(years)
    return years[order], doys[order]

def doy_formatter():
    base = date(2001, 1, 1)
    def _fmt(y, _pos):
        try:
            d = base + timedelta(days=float(y) - 1)
            return d.strftime('%b %d')
        except (OverflowError, ValueError):
            return ''
    return FuncFormatter(_fmt)

def safe_stub(name):
    return re.sub(r'[^A-Za-z0-9_-]+', '_', name).strip('_')

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

# -----------------
# Main Processing
# -----------------
df1 = pd.read_csv(FIRST_BLOOM_CSV)
df2 = pd.read_csv(FULL_BLOOM_CSV)

stations = df1['Site Name'].tolist()
year_cols = get_year_columns(df1)

plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3, 'figure.dpi': 150})

count = 0
for idx, station in enumerate(stations, start=1):
    y1, d1 = extract_station_series(df1, station, year_cols)
    y2, d2 = extract_station_series(df2, station, year_cols)
    
    # We need at least 10 data points to do meaningful spline smoothing
    if len(y1) < 10 or len(y2) < 10:
        continue
        
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"{station}: Moving Equilibrium Phase-Space Dynamics\n(Advanced Model: dx/dt = -k(x - x_eq(t)))", fontsize=14, y=0.98)
    
    # Process First Bloom (Top Row) and Full Bloom (Bottom Row)
    datasets = [
        (axes[0,0], axes[0,1], y1, d1, "First Bloom (x1)", "tab:pink", "winter"),
        (axes[1,0], axes[1,1], y2, d2, "Full Bloom (x2)", "tab:red", "autumn")
    ]
    
    for ax_temp, ax_phase, years, doys, label, color, cmap_name in datasets:
        # 1. Smoothing via Spline (High smoothing factor to act as moving equilibrium x_eq(t))
        spline_smoothness = 25 * len(years) 
        try:
            spl = UnivariateSpline(years, doys, s=spline_smoothness)
            spl_deriv = spl.derivative()
        except:
            ax_temp.text(0.5, 0.5, "Spline Failed", ha='center', va='center')
            continue
            
        # Continuous time for smooth curves
        t_cont = np.linspace(years.min(), years.max(), 500)
        x_smooth = spl(t_cont)
        dxdt_smooth = spl_deriv(t_cont)
        
        # Raw derivatives
        dxdt_raw = np.gradient(doys, years)
        
        # --- Temporal Plot (x vs t) ---
        ax_temp.scatter(years, doys, color=color, alpha=0.5, label='Observed (x)', s=20)
        ax_temp.plot(t_cont, x_smooth, 'k-', lw=2, label='Moving Equilibrium $x_{eq}(t)$')
        ax_temp.set_title(f"{label}: Raw Data + Moving Equilibrium")
        ax_temp.set_ylabel(f"{label} (Calendar Day)")
        ax_temp.set_xlabel("Year (t)")
        ax_temp.yaxis.set_major_formatter(doy_formatter())
        ax_temp.legend(loc='best')
        
        # --- Phase Space Plot (dx/dt vs x) ---
        ax_phase.axhline(0, color='gray', lw=1)
        # Plot raw phase space (light gray)
        ax_phase.scatter(doys, dxdt_raw, color='lightgray', s=20, label='Raw noisy path', zorder=1)
        
        # Plot smoothed phase space (Elliptical Limit Cycle) colored by time
        cmap = plt.get_cmap(cmap_name)
        norm = plt.Normalize(years.min(), years.max())
        lc = colorline(x_smooth, dxdt_smooth, z=t_cont, cmap=cmap, norm=norm, linewidth=3, alpha=0.8, ax=ax_phase)
        
        # Add a star at the start and end of the smooth path
        ax_phase.scatter([x_smooth[0]], [dxdt_smooth[0]], color=cmap(0.0), marker='o', s=100, edgecolor='k', zorder=5, label=f'Start ({years.min()})')
        ax_phase.scatter([x_smooth[-1]], [dxdt_smooth[-1]], color=cmap(1.0), marker='*', s=150, edgecolor='k', zorder=5, label=f'End ({years.max()})')
        
        cbar = fig.colorbar(lc, ax=ax_phase, pad=0.01)
        cbar.set_label('Year (t)')
        
        ax_phase.set_title(f"{label}: Phase Space dx/dt vs x")
        ax_phase.set_xlabel(f"{label} (Calendar Day)")
        ax_phase.set_ylabel("dx/dt (days/year)")
        ax_phase.xaxis.set_major_formatter(doy_formatter())
        ax_phase.legend(loc='upper left', fontsize=8)
        
        # Keep limits tight to highlight the ellipse
        pad_x = (x_smooth.max() - x_smooth.min()) * 0.5
        ax_phase.set_xlim(x_smooth.min() - pad_x, x_smooth.max() + pad_x)
        pad_y = (dxdt_smooth.max() - dxdt_smooth.min()) * 0.5
        ax_phase.set_ylim(dxdt_smooth.min() - pad_y, dxdt_smooth.max() + pad_y)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    fname = os.path.join(OUTPUT_DIR, f"{idx:03d}_{safe_stub(station)}_advanced.png")
    fig.savefig(fname)
    plt.close(fig)
    count += 1
    
    if count % 10 == 0:
        print(f"Processed {count} stations...")

print(f"Successfully generated {count} advanced dynamical plots in {OUTPUT_DIR}")
