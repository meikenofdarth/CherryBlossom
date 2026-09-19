import pandas as pd
import requests
import time
import os

csv_path = 'data/jma_temperatures.csv'

# Target stations and their coordinates
stations = {
    'Aomori': {'lat': 40.8246, 'lon': 140.7406},
    'Asahikawa': {'lat': 43.7706, 'lon': 142.3649},
    'Yamagata': {'lat': 38.2404, 'lon': 140.3633},
    'Kagoshima': {'lat': 31.5601, 'lon': 130.5581},
    'Fukuoka': {'lat': 33.5819, 'lon': 130.3253},
    'Kyoto': {'lat': 35.0116, 'lon': 135.7681},
    'Osaka': {'lat': 34.6937, 'lon': 135.5023},
    'Matsue': {'lat': 35.4681, 'lon': 133.0483}
}

# Check what we already successfully downloaded
existing_df = None
completed = []
if os.path.exists(csv_path):
    existing_df = pd.read_csv(csv_path)
    if not existing_df.empty and 'Site Name' in existing_df.columns:
        completed = existing_df['Site Name'].unique().tolist()
        
start_date = "1953-01-01"
end_date = "2024-12-31"

results = []

for name, coords in stations.items():
    if name in completed:
        print(f"Skipping {name} (already downloaded).")
        continue
        
    print(f"Fetching Open-Meteo data for {name}...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": coords['lat'],
        "longitude": coords['lon'],
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean",
        "timezone": "Asia/Tokyo"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'daily' not in data:
            print(f"  -> Error API Response: {data.get('reason', data)}")
            print("  -> Waiting 10 seconds before next attempt...")
            time.sleep(10)
            continue
            
        df = pd.DataFrame({
            'Date': pd.to_datetime(data['daily']['time']),
            'Temp': data['daily']['temperature_2m_mean']
        })
        
        df = df.dropna(subset=['Temp'])
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df = df[df['Month'].isin([2, 3])]
        
        monthly_avg = df.groupby(['Year', 'Month'])['Temp'].mean().reset_index()
        pivot = monthly_avg.pivot(index='Year', columns='Month', values='Temp').reset_index()
        
        if 2 in pivot.columns and 3 in pivot.columns:
            pivot = pivot[['Year', 2, 3]]
            pivot.columns = ['Year', 'Feb_Temp', 'Mar_Temp']
            pivot['Site Name'] = name
            results.append(pivot)
            print(f"  -> Success: {len(pivot)} years of data retrieved.")
        
    except Exception as e:
        print(f"  -> Error fetching {name}: {e}")
        
    print("  -> Waiting 10 seconds to respect API limits...")
    time.sleep(10) 

if results:
    new_df = pd.concat(results, ignore_index=True)
    if existing_df is not None and not existing_df.empty:
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        final_df = new_df
        
    final_df.to_csv(csv_path, index=False)
    print(f"\nSaved combined temperature data to {csv_path}!")
else:
    print("\nNo new data was retrieved.")