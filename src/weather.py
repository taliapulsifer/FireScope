import requests

METEO_URL = 'https://archive-api.open-meteo.com/v1/archive'

def fetch_weather(latitude, longitude, start_date, end_date):
    """Request historical weather data from Open-Meteo."""
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date,
        'hourly': [
            'temperature_2m',
            'relative_humidity_2m',
            'precipitation',
            'wind_speed_10m',
            'wind_gusts_10m',
            'soil_moisture_0_to_7cm',
            'vapour_pressure_deficit'
        ],
        'timezone': 'auto',
    }
    response = requests.get(METEO_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()