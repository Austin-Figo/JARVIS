"""Live atmospheric weather data module for JARVIS."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict


def get_weather(location: str = "") -> Dict[str, Any]:
    """Fetch current real-time atmospheric weather data."""
    clean_loc = location.strip()
    encoded = urllib.parse.quote(clean_loc) if clean_loc else ""
    url = f"https://wttr.in/{encoded}?format=j1"

    # Also check if OpenWeather key is present in settings
    try:
        config_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
        with config_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
            owm_key = cfg.get("weatherKey", "")
            if owm_key and "•" not in owm_key and clean_loc:
                owm_url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded}&appid={owm_key}&units=metric"
                req = urllib.request.Request(owm_url, headers={"User-Agent": "JARVIS/3.7"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    city = data.get("name", clean_loc)
                    temp = data.get("main", {}).get("temp", 0)
                    desc = data.get("weather", [{}])[0].get("description", "Clear").title()
                    humidity = data.get("main", {}).get("humidity", 0)
                    wind = data.get("wind", {}).get("speed", 0)
                    msg = f"Weather in {city}: {desc}, {temp}°C, Humidity: {humidity}%, Wind: {wind} m/s."
                    return {
                        "ok": True,
                        "message": msg,
                        "action": "weather",
                        "data": {"city": city, "temp_c": temp, "condition": desc, "humidity": humidity, "wind_speed": wind},
                    }
    except Exception:
        pass

    # Free zero-configuration live weather fallback via wttr.in
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            curr = data.get("current_condition", [{}])[0]
            nearest = data.get("nearest_area", [{}])[0]
            city = nearest.get("areaName", [{}])[0].get("value", clean_loc or "Current Location")
            temp = curr.get("temp_C", "N/A")
            desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear").strip()
            humidity = curr.get("humidity", "N/A")
            wind = curr.get("windspeedKmph", "N/A")

            msg = f"Weather in {city}: {desc}, {temp}°C, Humidity: {humidity}%, Wind: {wind} km/h."
            return {
                "ok": True,
                "message": msg,
                "action": "weather",
                "data": {"city": city, "temp_c": temp, "condition": desc, "humidity": humidity, "wind_kmph": wind},
            }
    except Exception as e:
        return {
            "ok": True,
            "message": f"Unable to fetch atmospheric telemetry: {e}. Opening Windows Weather.",
            "action": "weather",
            "data": {},
        }

