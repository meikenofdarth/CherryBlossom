import pandas as pd
import requests
import time
import os

csv_path = 'data/jma_temperatures.csv'
coords_path = 'data/JMA-kaggle_dataest/station_coords_template.csv'

# Target stations. Coordinates come from the verified official JMA table.
target_sites = [
    'Aomori', 'Asahikawa', 'Yamagata', 'Kagoshima',
    'Fukuoka', 'Kyoto', 'Osaka', 'Matsue',
    'Wakkanai', 'Iwamizawa', 'Urakawa', 'Akita',
    'Nagano', 'Fukui', 'Miyazaki', 'Oita',
    'Nara', 'Kobe', 'Shizuoka', 'Kochi',
]
coords = pd.read_csv(coords_path).set_index('Site Name')
stations = {
    site: {'lat': coords.loc[site, 'Latitude'], 'lon': coords.loc[site, 'Longitude']}
    for site in target_sites
}

# Check what we already successfully downloaded
existing_df = None
completed = []
if os.path.exists(csv_path):
    existing_df = pd.read_csv(csv_path)
    if not existing_df.empty and 'Site Name' in existing_df.columns:
        completed = existing_df['Site Name'].unique().tolist()

pending_sites = [site for site in target_sites if site not in completed]
        
start_date = "1953-01-01"
end_date = "2024-12-31"

results = []

for name in pending_sites:
    coords = stations[name]
    print(f"Fetching Open-Meteo data for {name} at {coords['lat']:.4f}, {coords['lon']:.4f}...")
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