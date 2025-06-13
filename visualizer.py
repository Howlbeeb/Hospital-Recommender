import matplotlib.pyplot as plt
import folium
import polyline

def plot_recommendations(recommendations):
    if recommendations.empty:
        print("No recommendations to plot.")
        return
    plt.figure(figsize=(10, 6))
    plt.bar(recommendations['Name'], recommendations['Recommendation_Score'], color='skyblue')
    plt.xlabel('Hospital Name')
    plt.ylabel('Recommendation Score')
    plt.title('Top 3 Recommended Hospitals')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('hospital_recommendations.png')
    plt.close()

def plot_map(user_coords, recommendations):
    if recommendations.empty:
        print("No hospitals to display on the map.")
        return
    
    map_center = user_coords if user_coords else (6.5244, 3.3792)
    m = folium.Map(location=map_center, zoom_start=11.5)

    if user_coords:
        folium.Marker(
            location=user_coords,
            popup="Your Location",
            icon=folium.Icon(color='red', icon='user')
        ).add_to(m)
    
    colors = ['blue', 'green', 'purple']
    for idx, row in recommendations.iterrows():
        coords = row.get('Coordinates')
        if coords:
            folium.Marker(
                location=coords,
                popup=(
                    f"{row['Name']}<br>"
                    f"Services: {row['Services']}<br>"
                    f"Recommendation Score: {row['Recommendation_Score']:.2f}<br>"
                    f"Distance: {row.get('Route_Distance', 'N/A')}<br>"
                    f"Duration: {row.get('Route_Duration', 'N/A')}"
                ),
                icon=folium.Icon(color='blue', icon='hospital')
            ).add_to(m)
            
            if user_coords and row.get('Polyline_Points'):
                try:
                    decoded_points = polyline.decode(row['Polyline_Points'])
                    folium.PolyLine(
                        locations=decoded_points,
                        color=colors[idx % len(colors)],
                        weight=5,
                        opacity=0.7,
                        popup=(
                            f"Route to {row['Name']}<br>"
                            f"Distance: {row.get('Route_Distance', 'N/A')}<br>"
                            f"Duration: {row.get('Route_Duration', 'N/A')}"
                        )
                    ).add_to(m)
                except Exception as e:
                    print(f"Error plotting route to {row['Name']}: {e}")

    m.save('hospital_map.html')