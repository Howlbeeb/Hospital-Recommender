import numpy as np
from geopy.distance import geodesic

def calculate_distance(user_coords, hospital_coords, scale=2.0):
    if user_coords is None or hospital_coords is None:
        return 0.0, float('inf')
    try:
        distance = geodesic(user_coords, hospital_coords).km
        proximity_score = np.exp(-distance / scale)
        return proximity_score, distance
    except Exception as e:
        print(f"Distance calculation error: {e}")
        return 0.0, float('inf')