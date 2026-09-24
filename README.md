FireScope is an interactive geospatial wildfire monitoring and risk-analysis project focused on California. It combines satellite fire detections, geospatial data, weather data, and machine learning to explore current fire activity and environmental fire risk.

## Current Features

- Retrieves near-real-time thermal detections from NASA FIRMS
- Maps VIIRS fire detections across California
- Associates detections with California counties using GeoPandas spatial joins
- Retrieves and displays VIIRS 375 m detection footprints
- Interactive Folium map with county boundaries and fire detection information
- Retrieves historical weather data from Open-Meteo

## Tech Stack

- Python
- GeoPandas
- Folium
- Pandas
- NASA FIRMS API
- Open-Meteo API
- U.S. Census TIGER/Line geographic data

## In Progress

FireScope is currently under development. Planned features include:

- Historical wildfire and weather dataset construction
- Machine-learning-based relative fire-risk estimation
- Model feature explanations
- Parallelized data collection and processing
- Interactive Streamlit dashboard
- Deployment as a web application

## Data Sources

FireScope currently uses:

- **NASA FIRMS** — VIIRS satellite thermal detections and detection footprints
- **Open-Meteo** — historical weather observations
- **U.S. Census Bureau TIGER/Line** — California county boundaries

## Disclaimer

NASA FIRMS detections represent satellite-observed thermal anomalies and should not be interpreted as confirmed wildfire perimeters. FireScope is an educational and portfolio project and is not intended for emergency or operational wildfire decision-making.