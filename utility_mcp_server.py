from fastmcp import FastMCP
import pytz
import os
import datetime
from tavily import TavilyClient
from typing import Dict, List
import shutil
import logging

from dotenv import load_dotenv
load_dotenv()
# -----------------------------------------------------
# Logging Setup
# -----------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------
# Configuration
# -----------------------------------------------------

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is not set")

tavily_client = TavilyClient(TAVILY_API_KEY)


# -----------------------------------------------------
# MCP Server
# -----------------------------------------------------

mcp = FastMCP(
    name="Utility Tools MCP Server",
    port=8000
)


# -----------------------------------------------------
# Web Search Tool
# -----------------------------------------------------

@mcp.tool()
def web_search(query: str) -> List[Dict]:

    logger.info(f"web_search invoked | query={query}")

    try:
        response = tavily_client.search(query=query)

        results = []

        for item in response.get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content")
            })

        logger.info(f"web_search completed | results={len(results)}")

        return results

    except Exception as e:
        logger.error(f"web_search failed | error={str(e)}")
        return [{"error": str(e)}]


# -----------------------------------------------------
# Current Date Time Tool
# -----------------------------------------------------

@mcp.tool()
def current_datetime(timezone: str = "UTC") -> str:

    logger.info(f"current_datetime invoked | timezone={timezone}")

    try:
        tz = pytz.timezone(timezone)
        now = datetime.datetime.now(tz)

        result = now.strftime("%Y-%m-%d %H:%M:%S %Z")

        logger.info(f"current_datetime result | {result}")

        return result

    except pytz.exceptions.UnknownTimeZoneError:
        logger.error(f"Unknown timezone | {timezone}")
        return f"Error: Unknown timezone '{timezone}'"


# -----------------------------------------------------
# Disk Space Tool
# -----------------------------------------------------

@mcp.tool()
def get_disk_space(path: str = "/") -> Dict:

    logger.info(f"get_disk_space invoked | path={path}")

    try:
        total, used, free = shutil.disk_usage(path)

        result = {
            "path": path,
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free
        }

        logger.info(f"get_disk_space completed | free={free}")

        return result

    except Exception as e:
        logger.error(f"get_disk_space failed | error={str(e)}")
        return {"error": str(e)}


# -----------------------------------------------------
# Run MCP Server
# -----------------------------------------------------

if __name__ == "__main__":

    logger.info("Starting MCP Server on port 8080")

    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8080
    )
