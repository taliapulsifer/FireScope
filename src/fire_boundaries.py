from io import BytesIO
from itertools import count

import geopandas as gpd
import pandas as pd
import requests
from pathlib import Path
import zipfile
from src.geography import load_california_counties

ROOT_DIR = Path(__file__).resolve().parent.parent
BOUNDARY_DATA_DIR = ROOT_DIR / 'data' / 'raw' / 'fire_boundaries'

FIRE_FOOTPRINT_URL = "https://firms.modaps.eosdis.nasa.gov/api/kml_fire_footprints"


def fetch_fire_boundaries():
    region = "usa_contiguous_and_hawaii"
    date_span = "24h"
    sensor = "noaa-20-viirs-c2"

    url = f"{FIRE_FOOTPRINT_URL}/{region}/{date_span}/{sensor}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Returns a zipped KML, not JSON
    return response.content


def extract_kml(data):
    BOUNDARY_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(BytesIO(data)) as zip_file:
        kml_files = [
            filename
            for filename in zip_file.namelist()
            if filename.endswith('.kml')
        ]

        kml_filename = kml_files[0]
        kml_data = zip_file.read(kml_filename)

        output_path = BOUNDARY_DATA_DIR / 'fire_footprints.kml'

        with open(output_path, 'wb') as file:
            file.write(kml_data)

        return output_path


def load_fire_footprints(filepath):
    layers = [
        '375m Fire Detection Footprints (Last 0 to 6hrs)',
        '375m Fire Detection Footprints (Last 6 to 12hrs)',
        '375m Fire Detection Footprints (Last 12 to 24hrs)'
    ]

    footprints = []

    for layer in layers:
        layer_gdf = gpd.read_file(
            filepath,
            layer=layer
        )

        footprints.append(layer_gdf)

    #crs is Coordinate Reference System
    combined = gpd.GeoDataFrame(pd.concat(footprints, ignore_index=True),
                                crs=footprints[0].crs)
    return combined

def filter_california_footprints(footprints, counties):
    counties = counties.to_crs(footprints.crs)
    california = counties.dissolve()

    california_footprints = gpd.sjoin(footprints, california[['geometry']], how='inner', predicate='intersects')
    return california_footprints


if __name__ == "__main__":
    data = fetch_fire_boundaries()
    filepath = extract_kml(data)

    footprints = load_fire_footprints(filepath)

    counties = load_california_counties()

    california_footprints = filter_california_footprints(
        footprints,
        counties
    )

    print(f"All footprints: {len(footprints)}")
    print(f"California footprints: {len(california_footprints)}")