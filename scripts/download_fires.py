from pathlib import Path
from src.firms import fetch_fires, save_raw_data

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT_DIR / 'data' / 'raw'

DATA_SOURCE = 'VIIRS_NOAA20_NRT'
CALIFORNIA_BOUNDS = '-124.48,32.53,-114.13,42.01'

data = fetch_fires(DATA_SOURCE, CALIFORNIA_BOUNDS, 1) # w, s, e, n

filepath = save_raw_data(data, filepath=RAW_DATA_DIR / 'firms.csv')

print(f'FIRMS data saved to {filepath}')