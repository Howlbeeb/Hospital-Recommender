from flask import Flask,send_file, request, jsonify
from data_loader import load_hospital_data
from geocoder import geocode_address, load_geocode_cache, save_geocode_cache
from fuzzy_system import setup_fuzzy_system, compute_recommendation_score, map_preference_to_value
from route_calculator import get_driving_route
import pandas as pd

app = Flask(__name__)

@app.route('/')
def serve_frontend():
    return send_file('index.html')

# Existing /get_recommendations route remains unchanged
@app.route('/get_recommendations', methods=['GET'])
def get_recommendations():
    # Extract query parameters
    location = request.args.get('location', '').strip()
    service = request.args.get('service', '').strip()
    cost_pref_str = request.args.get('cost_pref', 'Medium').strip().capitalize()
    quality_pref_str = request.args.get('quality_pref', 'High').strip().capitalize()

    # Validate inputs
    if not service:
        return jsonify({'error': 'Service parameter is required.'}), 400

    valid_categories = {'Low', 'Medium', 'High'}
    if cost_pref_str not in valid_categories:
        return jsonify({'error': 'Invalid cost preference. Use Low, Medium, or High.'}), 400
    if quality_pref_str not in valid_categories:
        return jsonify({'error': 'Invalid quality preference. Use Low, Medium, or High.'}), 400

    # Map preferences to numerical values
    cost_pref = map_preference_to_value(cost_pref_str)
    quality_pref = map_preference_to_value(quality_pref_str)

    # Load hospital data
    data = load_hospital_data()
    if data is None:
        return jsonify({'error': 'Failed to load hospital data.'}), 500

    # Load geocoding cache
    cache_file = 'hospital_coordinates.csv'
    geocode_cache = load_geocode_cache(cache_file)

    # Geocode user location
    user_coords = None
    if location:
        user_coords = geocode_address(location, geocode_cache)
        if user_coords == (6.5244, 3.3792):
            print(f"Could not geocode location '{location}'. Using all hospitals without distance filter.")
        else:
            print(f"Geocoded location '{location}' to coordinates {user_coords}")
    else:
        print("No location provided. Using all hospitals without distance filter.")

    # Geocode hospital addresses
    print("Geocoding hospital addresses...")
    data['Coordinates'] = data['Full Address'].apply(lambda addr: geocode_address(addr, geocode_cache))
    default_coords_count = (data['Coordinates'] == (6.5244, 3.3792)).sum()
    if default_coords_count > 0:
        print(f"Warning: {default_coords_count} hospital(s) using default coordinates. Check addresses in dataset.")
    valid_coords = data['Coordinates'].notna().sum()
    print(f"Successfully geocoded {valid_coords} hospital addresses.")

    # Save geocoding cache
    save_geocode_cache(geocode_cache, cache_file)

    if data.empty:
        return jsonify({'error': 'No hospitals available after filtering.'}), 404

    # Apply distance filter if user location is valid
    if user_coords and user_coords != (6.5244, 3.3792):
        data['Distance_km'] = data['Coordinates'].apply(lambda coords: calculate_distance(user_coords, coords)[1])
        data = data[data['Distance_km'] <= 10.0]
        if data.empty:
            return jsonify({'error': 'No hospitals found within 10 km of the provided location.'}), 404

    # Initialize fuzzy logic system
    fuzzy_system = setup_fuzzy_system()

    # Compute recommendation scores
    data['Recommendation_Score'] = data.apply(
        lambda row: compute_recommendation_score(row, service, cost_pref, quality_pref, user_coords, fuzzy_system),
        axis=1
    )

    # Filter hospitals with non-zero scores
    recommendations = data[data['Recommendation_Score'] > 0].copy()
    if recommendations.empty:
        return jsonify({'error': f"No hospitals found matching service '{service}'."}), 404

    # Get top 3 recommendations
    recommendations = recommendations.sort_values(by='Recommendation_Score', ascending=False).head(3)

    # Calculate driving routes
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

    # Prepare response
    response_data = recommendations[[
        'Name', 'Full Address', 'Services', 'Cost Level', 'Quality Score',
        'User Rating', 'Recommendation_Score', 'Route_Distance', 'Route_Duration', 'Route_Instructions'
    ]].to_dict(orient='records')

    return jsonify({
        'user_inputs': {
            'location': location or 'None',
            'service': service,
            'cost_preference': cost_pref_str,
            'quality_preference': quality_pref_str
        },
        'recommendations': response_data
    }), 200

if __name__ == '__main__':
    app.run(debug=True)