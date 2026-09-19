import pandas as pd
import requests
import time
import os

coords_file = 'data/JMA-kaggle_dataest/station_coords_template.csv'

if not os.path.exists(coords_file):
    print(f"Error: {coords_file} not found.")
    exit()

df = pd.read_csv(coords_file)

def get_coords(city_name):
    # Try looking for the meteorological station first, then just the city
    search_queries = [
        f"{city_name} Meteorological Observatory, Japan",
        f"{city_name}, Japan"
    ]
    
    headers = {'User-Agent': 'SakuraBloomResearch/1.0'}
    
    for query in search_queries:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': query, 'format': 'json', 'limit': 1}
        try:
            response = requests.get(url, params=params, headers=headers)
            data = response.json()
            if data:
                # Return rounded latitude and longitude
                return round(float(data[0]['lat']), 4), round(float(data[0]['lon']), 4)
        except Exception as e:
            print(f"  API error for {query}: {e}")
        
        # Required 1-second delay to be polite to the free OpenStreetMap API
        time.sleep(1.2) 
        
    return None, None

print(f"Fetching coordinates for {len(df)} stations...")

for idx, row in df.iterrows():
    # Only fetch if the latitude is missing
    if pd.isna(row['Latitude']) or str(row['Latitude']).strip() == '':
        site = row['Site Name']
        
        # Fix known Kaggle dataset typo
        site_query = 'Shionomisaki' if site == 'Shiomizumaki' else site
            
        print(f"[{idx+1}/{len(df)}] Geocoding {site}...")
        lat, lon = get_coords(site_query)
        
        if lat and lon:
            df.at[idx, 'Latitude'] = lat
            df.at[idx, 'Longitude'] = lon
        else:
            print(f"  -> Could not find coordinates for {site}")

# Save the filled data back to the CSV
df.to_csv(coords_file, index=False)
print(f"\nDone! Updated coordinates saved to {coords_file}.")