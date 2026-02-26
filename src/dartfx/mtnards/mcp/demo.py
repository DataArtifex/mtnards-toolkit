# server.py
import logging
import sys

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr
)
logger = logging.getLogger(__name__)
logger.info("Starting MCP server...")
sys.stderr.flush()


# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
