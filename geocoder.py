import googlemaps
import os
import pandas as pd
from api_config import gmaps

DEFAULT_COORDS = (6.5244, 3.3792)

def load_geocode_cache(cache_file='hospital_coordinates.csv'):
    if os.path.exists(cache_file):
        try:
            cache = pd.read_csv(cache_file, index_col='Address')
            return cache.to_dict()['Coordinates']
        except Exception as e:
            print(f"Error loading cache: {e}. Starting with empty cache.")
    return {}

def save_geocode_cache(cache, cache_file='hospital_coordinates.csv'):
    try:
        cache_df = pd.DataFrame.from_dict(cache, orient='index', columns=['Coordinates'])
        cache_df.index.name = 'Address'
        cache_df.to_csv(cache_file)
        print(f"Geocoding cache saved to {cache_file}")
    except Exception as e:
        print(f"Error saving cache: {e}")

def geocode_address(address, cache):
    if address in cache:
        coords_str = cache[address]
        if coords_str == 'None':
            return DEFAULT_COORDS
        try:
            lat, lon = map(float, coords_str.strip('()').split(','))
            return (lat, lon)
        except:
            print(f"Invalid cached coordinates for '{address}'. Re-geocoding.")
    
    try:
        full_address = f"{address}, Lagos, Nigeria"
        geocode_result = gmaps.geocode(full_address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            coords = (location['lat'], location['lng'])
            print(f"Geocoded '{address}' to {coords}")
            cache[address] = f"({coords[0]},{coords[1]})"
            return coords
        print(f"Geocoding failed for '{address}'. Using default coordinates.")
        cache[address] = 'None'
        return DEFAULT_COORDS
    except Exception as e:
        print(f"Geocoding error for '{address}': {e}. Using default coordinates.")
        cache[address] = 'None'
        return DEFAULT_COORDS