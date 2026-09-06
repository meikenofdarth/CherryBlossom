import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the data, skipping comment lines
data = []
with open('data/kyoto2010flower.txt', 'r') as f:
    for line in f:
        if line.startswith('#'):
            continue
        # The delimiter might be tabs or multiple spaces. Let's use string split
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                year = int(parts[0])
                if parts[1].strip() != '-' and parts[1].strip() != '':
                    doy = int(parts[1])
                    data.append((year, doy))
            except ValueError:
                pass

df = pd.DataFrame(data, columns=['Year', 'Full_Bloom_DOY'])

# Sort by year just in case
df = df.sort_values('Year')

# 1. Plot x2 (DOY) vs t (Year)
plt.figure(figsize=(12, 6))
plt.scatter(df['Year'], df['Full_Bloom_DOY'], alpha=0.5, s=10)
plt.plot(df['Year'], df['Full_Bloom_DOY'], alpha=0.2, color='gray')
plt.title('Time of Full Bloom (x2) vs Year (t) - Yasuyuki Aono Dataset (Kyoto)')
plt.xlabel('Year (t)')
plt.ylabel('Day of Year (x2)')
plt.grid(True)
plt.tight_layout()
plt.savefig('plots/Aono_Kyoto_x2_vs_t.png', dpi=300)
plt.close()

# 2. Plot dx2/dt vs x2
# dx2/dt = (x2[i+1] - x2[i]) / (t[i+1] - t[i])
df['dt'] = df['Year'].diff()
df['dx2'] = df['Full_Bloom_DOY'].diff()
df['dx2_dt'] = df['dx2'] / df['dt']

plt.figure(figsize=(10, 8))
plt.scatter(df['Full_Bloom_DOY'], df['dx2_dt'], alpha=0.5, s=10)
plt.title('dx2/dt vs Time of Full Bloom (x2) - Yasuyuki Aono Dataset (Kyoto)')
plt.xlabel('Time of Full Bloom (x2)')
plt.ylabel('dx2/dt')
plt.grid(True)
plt.axhline(0, color='red', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/Aono_Kyoto_dx2dt_vs_x2.png', dpi=300)
plt.close()

print("Plots generated: plots/Aono_Kyoto_x2_vs_t.png and plots/Aono_Kyoto_dx2dt_vs_x2.png")
