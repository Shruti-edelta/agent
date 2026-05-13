import httpx
from datetime import datetime
import pytz

async def get_current_time(timezone: str = "UTC"):
    """
    Get the current date and time for a given timezone.
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return {
            "timezone": timezone,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "iso_format": now.isoformat()
        }
    except Exception as e:
        # Fallback to local time if timezone is invalid
        now = datetime.now()
        return {
            "error": f"Invalid timezone '{timezone}', returning system time instead.",
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "iso_format": now.isoformat()
        }


async def get_weather(location: str):
    """
    Fetch real-time weather information for a given location using wttr.in.
    """
    try:
        # wttr.in/?format=j1 returns JSON data
        url = f"https://wttr.in/{location}?format=j1"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            current = data['current_condition'][0]
            temp_c = current['temp_C']
            weather_desc = current['weatherDesc'][0]['value']
            humidity = current['humidity']
            wind_speed = current['windspeedKmph']
            
            return {
                "location": location,
                "temperature": f"{temp_c}°C",
                "condition": weather_desc,
                "humidity": f"{humidity}%",
                "wind_speed": f"{wind_speed} km/h"
            }
    except Exception as e:
        return {"error": f"Could not fetch weather for {location}: {str(e)}"}

# Map of tool names to functions for easy lookup
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "get_current_time": get_current_time
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time for a specific timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The timezone to get the time for, e.g. 'UTC', 'America/New_York', 'Asia/Kolkata'. Default is 'UTC'.",
                    },
                },
            },
        },
    }
]
