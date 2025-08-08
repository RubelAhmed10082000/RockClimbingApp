from datetime import timedelta, datetime
import requests

def get_7_day_weather(lat,lon):
        lat = float(lat)
        lon = float(lon)

        today = datetime.utcnow().date()
        end_date = today + timedelta(days=7)

        start_date_str = today.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m"
            f"&start_date={start_date_str}&end_date={end_date_str}"
            f"&timezone=auto"
        )

        print("Weather API URL:", url)  

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        timestamps = hourly.get("time", [])
        tempertature = hourly.get("temperature_2m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        precip = hourly.get("precipitation", [])
        wind = hourly.get("windspeed_10m", [])

        forecast = []
        for i in range(len(timestamps)):
            forecast.append({
                "time": timestamps[i],
                "temperature": tempertature[i],
                "humidity": humidity[i],
                "precipitation": precip[i],
                "windspeed": wind[i]
            })

        return forecast