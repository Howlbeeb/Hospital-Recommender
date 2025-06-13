import pandas as pd
from data_loader import load_hospital_data
from geocoder import geocode_address, load_geocode_cache, save_geocode_cache
from distance_calculator import calculate_distance
from fuzzy_system import setup_fuzzy_system, compute_recommendation_score, map_preference_to_value
from route_calculator import get_driving_route
from visualizer import plot_recommendations, plot_map

def get_valid_category(prompt, default):
    valid_options = {'low', 'medium', 'high'}
    while True:
        value = input(f"{prompt} (Low/Medium/High, default {default}): ").strip().lower() or default.lower()
        if value in valid_options:
            return value.capitalize()
        print("Invalid input. Please enter Low, Medium, or High (or press Enter for default).")

def main():
    data = load_hospital_data()
    if data is None:
        return

    print(f"Loaded {len(data)} hospitals from dataset.")
    location = input("Enter your location (e.g., Ikeja, Allen Avenue): ").strip()
    user_service = input("Enter service needed (e.g., General Medicine, Surgery): ").strip()
    cost_pref_str = get_valid_category("Enter cost preference", default="Medium")
    quality_pref_str = get_valid_category("Enter quality preference", default="High")
    cost_pref = map_preference_to_value(cost_pref_str)
    quality_pref = map_preference_to_value(quality_pref_str)

    cache_file = 'hospital_coordinates.csv'
    geocode_cache = load_geocode_cache(cache_file)

    user_coords = None
    if location:
        user_coords = geocode_address(location, geocode_cache)
        if user_coords == (6.5244, 3.3792):
            print(f"Could not geocode location '{location}'. Using all hospitals without distance filter.")
        else:
            print(f"Geocoded location '{location}' to coordinates {user_coords}")
    else:
        print("No location provided. Using all hospitals without distance filter.")

    print("Geocoding hospital addresses...")
    data['Coordinates'] = data['Full Address'].apply(lambda addr: geocode_address(addr, geocode_cache))
    default_coords_count = (data['Coordinates'] == (6.5244, 3.3792)).sum()
    if default_coords_count > 0:
        print(f"Warning: {default_coords_count} hospital(s) using default coordinates. Check addresses in dataset.")
    valid_coords = data['Coordinates'].notna().sum()
    print(f"Successfully geocoded {valid_coords} hospital addresses.")

    save_geocode_cache(geocode_cache, cache_file)

    if data.empty:
        print("No hospitals available after filtering.")
        return

    if user_coords and user_coords != (6.5244, 3.3792):
        data['Distance_km'] = data['Coordinates'].apply(lambda coords: calculate_distance(user_coords, coords)[1])
        data = data[data['Distance_km'] <= 10.0]
        print(f"After 10 km filter, {len(data)} hospitals remain within 10 km of {location}.")
        if data.empty:
            print("No hospitals found within 10 km. Try a different location or broader service.")
            return

    fuzzy_system = setup_fuzzy_system()

    data['Recommendation_Score'] = data.apply(
        lambda row: compute_recommendation_score(row, user_service, cost_pref, quality_pref, user_coords, fuzzy_system),
        axis=1
    )

    recommendations = data[data['Recommendation_Score'] > 0].copy()
    print(f"Found {len(recommendations)} hospitals with non-zero recommendation scores.")

    if recommendations.empty:
        print(f"No hospitals found matching service '{user_service}'. Try a different service.")
        return

    recommendations = recommendations.sort_values(by='Recommendation_Score', ascending=False).head(3)

    print("Calculating driving routes...")
    for idx, row in recommendations.iterrows():
        distance, duration, polyline_points, instructions = get_driving_route(
            user_coords, row['Coordinates'], row['Name']
        )
        recommendations.at[idx, 'Route_Distance'] = distance
        recommendations.at[idx, 'Route_Duration'] = duration
        recommendations.at[idx, 'Polyline_Points'] = polyline_points
        recommendations.at[idx, 'Route_Instructions'] = "; ".join(instructions) if instructions else "N/A"
        if distance:
            print(f"Route to {row['Name']}: {distance}, {duration}")

    
    recommendations = recommendations[[
    'Name', 'Full Address', 'Services', 'Cost Level', 'Quality Score',
    'Recommendation_Score', 'Distance_km', 'Route_Distance', 'Route_Duration', 'Route_Instructions', 'Coordinates']]

    print("\nUser Inputs:")
    print(f"Location: {location or 'None'}")
    print(f"Service Needed: {user_service}")
    print(f"Cost Preference: {cost_pref_str}")
    print(f"Quality Preference: {quality_pref_str}")
    print("\nTop 3 Recommended Hospitals:")
    print(recommendations.drop(columns=['Coordinates', 'Route_Instructions']).to_string(index=False))

    try:
        recommendations.drop(columns=['Coordinates', 'Polyline_Points']).to_csv('recommended_hospitals.csv', index=False)
        print("\nResults saved to recommended_hospitals.csv")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

    plot_recommendations(recommendations)
    print("\nBar chart saved to hospital_recommendations.png")

    plot_map(user_coords, recommendations)
    print("\nInteractive map with routes saved to hospital_map.html")

if __name__ == "__main__":
    main()