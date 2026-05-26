import httpx
from datetime import datetime
import pytz
from typing import Annotated
from pydantic import Field
from mcp.server.fastmcp import FastMCP
import sys

print("Loading agent-tools...", file=sys.stderr)
# Create the MCP server instance
mcp = FastMCP("agent-tools")

@mcp.tool()
async def get_current_time(
    timezone: Annotated[
        str,
        Field(description="The timezone to get the time for, e.g. 'UTC', 'America/New_York', 'Asia/Kolkata'. Default is 'UTC'.")
    ] = "UTC"
) -> dict:
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


@mcp.tool()
async def get_weather(
    location: Annotated[
        str,
        Field(description="The city and state, e.g. San Francisco, CA")
    ]
) -> dict:
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


# Dynamically construct AVAILABLE_TOOLS and TOOL_DEFINITIONS from the MCP registry
# for backwards compatibility with the FastAPI / ReAct agent client.
AVAILABLE_TOOLS = {
    name: tool.fn for name, tool in mcp._tool_manager._tools.items()
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description.strip() if tool.description else "",
            "parameters": tool.parameters,
        }
    }
    for tool in mcp._tool_manager._tools.values()
]
