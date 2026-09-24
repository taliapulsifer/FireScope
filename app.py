import folium

from src.geography import (
    load_california_counties,
    fires_to_geodataframe,
    assign_fires_to_counties, ROOT_DIR
)
from src.fire_boundaries import (
    fetch_fire_boundaries,
    extract_kml,
    load_fire_footprints,
    filter_california_footprints
)

counties = load_california_counties()
fires = fires_to_geodataframe('data/raw/firms.csv')
fires_counties = assign_fires_to_counties(fires, counties)
boundary_data = fetch_fire_boundaries()
boundary_path = extract_kml(boundary_data)
footprints = load_fire_footprints(boundary_path)
california_footprints = filter_california_footprints(
    footprints,
    counties
)

fire_map = folium.Map(location=[37.2, -119.5], zoom_start=6)

folium.GeoJson(
    counties,
    name='California Counties',

    style_function=lambda feature: {
        'fillColor': 'transparent',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0
    },

    highlight_function=lambda feature: {
        'fillColor': 'yellow',
        'color': 'black',
        'weight': 3,
        'fillOpacity': 0.4
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['NAME'],
        aliases=['County:']
    )
).add_to(fire_map)


folium.GeoJson(
    california_footprints,
    name='VIIRS Detection Footprints',
    style_function=lambda feature: {
        'fillColor': 'red',
        'color': 'red',
        'weight': 1,
        'fillOpacity': 0.25
    }
).add_to(fire_map)


for row, fire in fires_counties.iterrows():
    tooltip = (
        f"{fire['NAME']} County<br>"
        f"FRP: {fire['frp']}<br>"
        f"Confidence: {fire['confidence']}<br>"
        f"Detected: {fire['acq_date']} {fire['acq_time']}"
    )

    folium.CircleMarker(
        location=[fire['latitude'], fire['longitude']],
        radius=5,
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.7,
        tooltip=tooltip
    ).add_to(fire_map)


folium.LayerControl().add_to(fire_map)
fire_map.save('firescope_map.html')
