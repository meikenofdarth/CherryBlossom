import pandas as pd
import matplotlib.pyplot as plt

# 1. Load Bloom Data
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

# 2. Load Temperature Data
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
                temp = tempobs if tempobs != -999.9 else temprec
                if temp != -999.9:
                    temp_data.append((year, temp))
            except ValueError: pass
df_temp = pd.DataFrame(temp_data, columns=['Year', 'Temp_March']).set_index('Year')

# 3. Merge and Clean
# We will use an inner join so we only keep years where we have both bloom date and temperature.
df_clean = df_flower.join(df_temp, how='inner').sort_index()

# Save the cleaned dataset for future steps
df_clean.to_csv('data/kyoto_cleaned.csv')

# 4. Basic Plots
# Plot A: DOY vs Year
plt.figure(figsize=(10, 5))
plt.scatter(df_clean.index, df_clean['DOY'], alpha=0.5, s=15, color='purple')
plt.title('Cherry Blossom Full Bloom DOY vs Year (Kyoto)')
plt.xlabel('Year')
plt.ylabel('Day of Year (DOY)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/step1_doy_vs_year.png', dpi=300)
plt.close()

# Plot B: Distribution of DOY
plt.figure(figsize=(8, 5))
plt.hist(df_clean['DOY'], bins=30, color='pink', edgecolor='black', alpha=0.7)
plt.title('Distribution of Full Bloom DOY')
plt.xlabel('Day of Year (DOY)')
plt.ylabel('Frequency (Years)')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plots/step1_doy_distribution.png', dpi=300)
plt.close()

# 5. Summary Printout
print("--- STEP 1 SUMMARY ---")
print(f"Total years with both Bloom DOY and Temperature data: {len(df_clean)}")
print(f"Time range: {df_clean.index.min()} AD to {df_clean.index.max()} AD")
print(f"Average Bloom DOY: {df_clean['DOY'].mean():.2f}")
print(f"Average March Temp: {df_clean['Temp_March'].mean():.2f} °C")
