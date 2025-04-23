import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession

async def main():
    # Connect to the MCP server using SSE transport
    async with sse_client("http://127.0.0.1:6277") as (reader, writer):
        # Initialize the client session
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            # List available tools
            tools_response = await session.list_tools()
            print("Available tools:")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")

            # Example: Call a tool named 'add' with parameters
            tool_name = "add"
            params = {"a": 5, "b": 3}
            result = await session.call_tool(tool_name, params)
            print(f"\nResult from tool '{tool_name}': {result.result}")

# Run the async main function
asyncio.run(main())