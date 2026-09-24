from src.weather import fetch_weather

weather = fetch_weather(
    latitude=38.5816,
    longitude=-121.4944,
    start_date='2025-07-01',
    end_date='2025-07-01'
)

print(weather.keys())
print(weather['hourly'].keys())

print(weather['hourly']['time'][:5])
print(weather['hourly']['temperature_2m'][:5])