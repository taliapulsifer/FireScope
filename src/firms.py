import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FIRMS_MAP_KEY = os.getenv('FIRMS_MAP_KEY')

if not FIRMS_MAP_KEY:
    raise ValueError('FIRMS_MAP_KEY environment variable is not set')


def fetch_fires(data_source, geo_area, num_days):
    """Request fire detection data from NASA FIRMS"""
    base_url = 'https://firms.modaps.eosdis.nasa.gov/api/area/csv'
    url = f'{base_url}/{FIRMS_MAP_KEY}/{data_source}/{geo_area}/{num_days}'
    response = requests.get(url, timeout=30)

    response.raise_for_status()

    return response.text


def save_raw_data(data, filepath):
    """Save an unmodified FIRMS response"""
    filepath = Path(filepath)

    filepath.parent.mkdir(parents=True, exist_ok=True) #Create this directory and any missing parent directories. If it
    # already exits, don't throw any errors

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(data)

    return filepath
