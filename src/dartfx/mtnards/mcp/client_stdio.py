import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # Define server parameters
    server_params = StdioServerParameters(
        command="python",  # Adjust if using a different interpreter
        args=["server.py"],  # Replace with your server script
        env=None,  # Add environment variables if needed
    )

    # Establish stdio connection
    async with stdio_client(server_params) as (read, write):
        # Initialize client session
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            response = await session.list_tools()
            print("Available tools:")
            for tool in response.tools:
                print(f"- {tool.name}: {tool.description}")

            # List available resources
            response = await session.list_resources()
            print("Available resources:")
            for resource in response.resources:
                print(f"- {resource.name}: {resource.description}")

            # List available resource templates
            response = await session.list_resource_templates()
            print("Available resource templates:")
            for template in response.resourceTemplates:
                print(f"- {template.name}: {template.description}")

            # Example: Call a tool named 'add' with parameters
            # tool_name = "add"
            # params = {"a": 5, "b": 3}
            # result = await session.call_tool(tool_name, params)
            # print(result)

            results = await session.read_resource("mtnards://catalog")
            print("Catalogs:")
            for catalog in results:
                print(f"- {catalog}")


# Run the async main function
asyncio.run(main())
