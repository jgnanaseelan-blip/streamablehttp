from typing import Any
import httpx
import logging
from fastmcp import FastMCP

# -----------------------------
# Logging Configuration
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("weather", stateless_http=True)

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""

    logger.info(f"Calling NWS API: {url}")
    print(f"[DEBUG] Calling NWS API: {url}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()

            logger.info("API request successful")
            print("[DEBUG] API request successful")

            return response.json()

        except Exception as e:
            logger.error(f"NWS API request failed: {e}")
            print(f"[ERROR] NWS API request failed: {e}")
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""

    props = feature["properties"]

    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


# -----------------------------
# TOOL 1
# -----------------------------
@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state."""

    logger.info(f"TOOL INVOKED: get_alerts | state={state}")
    print(f"[TOOL INVOKED] get_alerts with state={state}")

    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        logger.warning("No alert data returned")
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        logger.info("No active alerts found")
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]

    logger.info(f"Returning {len(alerts)} alerts")

    return "\n---\n".join(alerts)


# -----------------------------
# TOOL 2
# -----------------------------
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location."""

    logger.info(f"TOOL INVOKED: get_forecast | lat={latitude} lon={longitude}")
    print(f"[TOOL INVOKED] get_forecast lat={latitude} lon={longitude}")

    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        logger.error("Unable to fetch forecast grid data")
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]

    logger.info(f"Forecast endpoint: {forecast_url}")

    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        logger.error("Unable to fetch detailed forecast")
        return "Unable to fetch detailed forecast."

    periods = forecast_data["properties"]["periods"]

    forecasts = []

    for period in periods[:5]:
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    logger.info("Returning forecast response")

    return "\n---\n".join(forecasts)


# -----------------------------
# SERVER START
# -----------------------------
if __name__ == "__main__":

    import os

    port = int(os.getenv('MCP_HTTP_PORT', '8080'))
    host = os.getenv('MCP_HTTP_HOST', '127.0.0.1')

    logger.info("Starting MCP Weather Server")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")

    print("=== MCP WEATHER SERVER STARTED ===")

    mcp.run(
        transport='streamable-http',
        port=port,
        host=host
    )
