import pandas as pd
df1 = pd.read_csv('data/JMA-kaggle_dataest/sakura_first_bloom_dates.csv')
df2 = pd.read_csv('data/JMA-kaggle_dataest/sakura_full_bloom_dates.csv')
print("--- FIRST BLOOM DATA ---")
print("Columns:", list(df1.columns))
print(df1.head(3))
print("\n--- FULL BLOOM DATA ---")
print("Columns:", list(df2.columns))
print(df2.head(3))
