"""
Local Weather Tools — Open-Meteo API (free, no API key needed)
Replaces Gateway Lambda weather tools for local development.
"""

import json
import logging
import urllib.parse
import urllib.request
from strands import tool
from skill import skill

logger = logging.getLogger(__name__)

# Open-Meteo geocoding endpoint
_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
# Open-Meteo forecast endpoint
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _geocode(location: str) -> dict | None:
    """Resolve location name to coordinates."""
    params = urllib.parse.urlencode({"name": location, "count": 1, "language": "en"})
    url = f"{_GEOCODE_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get("results")
        if results:
            return results[0]
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
    return None


@skill(name="weather")
@tool
def get_today_weather(location: str) -> str:
    """Get current weather conditions for a location.

    Args:
        location: City name or location (e.g., 'Bangkok', 'New York', 'Tokyo')
    """
    try:
        geo = _geocode(location)
        if not geo:
            return f"Location not found: {location}"

        lat, lon = geo["latitude"], geo["longitude"]
        name = geo.get("name", location)
        country = geo.get("country", "")

        params = urllib.parse.urlencode({
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "timezone": "auto"
        })
        url = f"{_FORECAST_URL}?{params}"

        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())

        current = data.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        feels_like = current.get("apparent_temperature", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")
        weather_code = current.get("weather_code", 0)

        condition = _weather_code_to_text(weather_code)

        return (
            f"**Weather in {name}, {country}**\n\n"
            f"Condition: {condition}\n"
            f"Temperature: {temp}°C\n"
            f"Feels Like: {feels_like}°C\n"
            f"Humidity: {humidity}%\n"
            f"Wind Speed: {wind} km/h"
        )

    except Exception as e:
        logger.error(f"Weather error: {e}")
        return f"Failed to get weather for {location}: {str(e)}"


@skill(name="weather")
@tool
def get_weather_forecast(location: str, days: int = 5) -> str:
    """Get weather forecast for upcoming days.

    Args:
        location: City name or location (e.g., 'Bangkok', 'London')
        days: Number of days to forecast (1-7, default 5)
    """
    try:
        days = max(1, min(days, 7))

        geo = _geocode(location)
        if not geo:
            return f"Location not found: {location}"

        lat, lon = geo["latitude"], geo["longitude"]
        name = geo.get("name", location)
        country = geo.get("country", "")

        params = urllib.parse.urlencode({
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": days
        })
        url = f"{_FORECAST_URL}?{params}"

        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        codes = daily.get("weather_code", [])
        precip = daily.get("precipitation_probability_max", [])

        lines = [f"**{days}-Day Forecast for {name}, {country}**\n"]
        lines.append("| Date | Condition | High | Low | Rain % |")
        lines.append("|------|-----------|------|-----|--------|")

        for i in range(len(dates)):
            condition = _weather_code_to_text(codes[i] if i < len(codes) else 0)
            high = f"{max_temps[i]:.0f}°C" if i < len(max_temps) else "N/A"
            low = f"{min_temps[i]:.0f}°C" if i < len(min_temps) else "N/A"
            rain = f"{precip[i]}%" if i < len(precip) else "N/A"
            lines.append(f"| {dates[i]} | {condition} | {high} | {low} | {rain} |")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return f"Failed to get forecast for {location}: {str(e)}"


def _weather_code_to_text(code: int) -> str:
    """Convert WMO weather code to readable text."""
    codes = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤️",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Foggy 🌫️",
        48: "Icy fog 🌫️",
        51: "Light drizzle 🌦️",
        53: "Moderate drizzle 🌦️",
        55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️",
        63: "Moderate rain 🌧️",
        65: "Heavy rain 🌧️",
        71: "Slight snow ❄️",
        73: "Moderate snow ❄️",
        75: "Heavy snow ❄️",
        80: "Rain showers 🌦️",
        81: "Moderate showers 🌧️",
        82: "Violent showers ⛈️",
        95: "Thunderstorm ⛈️",
        96: "Thunderstorm + hail ⛈️",
        99: "Thunderstorm + heavy hail ⛈️",
    }
    return codes.get(code, f"Unknown ({code})")
