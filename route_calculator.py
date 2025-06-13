from api_config import gmaps
import polyline
from datetime import datetime

DEFAULT_COORDS = (6.5244, 3.3792)

def get_driving_route(user_coords, hospital_coords, hospital_name):
    if user_coords == DEFAULT_COORDS or hospital_coords == DEFAULT_COORDS:
        print(f"Skipping route to {hospital_name}: Invalid coordinates (user: {user_coords}, hospital: {hospital_coords})")
        return None, None, None, None
    
    try:
        directions_result = gmaps.directions(
            origin=user_coords,
            destination=hospital_coords,
            mode="driving",
            departure_time=datetime.now()
        )
        if directions_result and len(directions_result) > 0:
            route = directions_result[0]['legs'][0]
            distance = route['distance']['text']
            duration = route['duration']['text']
            polyline_points = route['overview_polyline']['points']
            instructions = [step['html_instructions'] for step in route['steps']]
            return distance, duration, polyline_points, instructions
        else:
            print(f"No route found to {hospital_name}. API response: {directions_result}")
            return None, None, None, None
    except Exception as e:
        print(f"Error fetching route to {hospital_name}: {e}. Check API key or coordinates.")
        return None, None, None, None