import httpx

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
    "get_weather": get_weather
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
    }
]
