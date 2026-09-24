from pathlib import Path
import geopandas as gpd

ROOT_DIR = Path(__file__).resolve().parent.parent
COUNTY_FILE = (
    ROOT_DIR
    / 'data'
    / 'raw'
    / 'boundaries'
    / 'counties'
    / 'tl_2025_us_county'
    / 'tl_2025_us_county.shp'
)

def load_california_counties():
    counties = gpd.read_file(COUNTY_FILE)
    california_counties = counties[counties['STATEFP'] == '06']

    #print(california_counties[['NAME', 'STATEFP', 'GEOID']])
    #print(len(california_counties))
    return california_counties


def fires_to_geodataframe(filepath):
    fires = gpd.read_file(filepath)

    #print(fires.columns)
    #print(fires[['latitude', 'longitude']].head())

    fires_gdf = gpd.GeoDataFrame(fires, geometry=gpd.points_from_xy(fires['longitude'], fires['latitude']),
                                 crs='EPSG:4326')

    #print(fires_gdf[['latitude', 'longitude', 'geometry']].head())
    #print(fires_gdf.crs)

    return fires_gdf


def assign_fires_to_counties(fires_gdf, counties_gdf):
    """"""
    counties_gdf = counties_gdf.to_crs(fires_gdf.crs)

    print(counties_gdf.crs)
    print(fires_gdf.crs)
    county_info = counties_gdf[['GEOID', 'NAME', 'geometry']]
    fires_with_counties = gpd.sjoin(fires_gdf, county_info , how='inner', predicate='within')

    print(
        fires_with_counties[
            ['latitude', 'longitude', 'NAME', 'GEOID']
        ].head(10)
    )

    print(f'Before spatial join: {len(fires_gdf)}')
    print(f'After spatial join: {len(fires_with_counties)}')
    print()
    print(fires_gdf.crs)
    print(counties_gdf.crs)

    print(fires_gdf.geometry.head())
    print(counties_gdf.geometry.head())

    print(fires_gdf.total_bounds)
    print(counties_gdf.total_bounds)

    return fires_with_counties

if __name__ == '__main__':
    counties = load_california_counties()
    fires = fires_to_geodataframe(ROOT_DIR / 'data' / 'raw' / 'firms.csv')
    fires_with_counties = assign_fires_to_counties(fires, counties)
