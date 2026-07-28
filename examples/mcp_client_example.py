

"""MCP client example: connect to the YTAI MCP server and call tools.



This example demonstrates how to connect to the MCP server from a Python

client using the MCP Python SDK. It launches the server as a subprocess,

lists available tools, and calls the search tool.



Prerequisites:

    pip install mcp



Usage:

    python examples/mcp_client_example.py

"""



import sys

from pathlib import Path



if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))





def main():

    try:

        from mcp import ClientSession, StdioServerParameters

        from mcp.client.stdio import stdio_client

    except ImportError:

        print("The 'mcp' package is required to run this example.")

        print("Install it with: pip install mcp")

        sys.exit(1)



    import asyncio



    project_root = str(Path(__file__).resolve().parent.parent)



    server_params = StdioServerParameters(

        command="python",

        args=["-m", "mcp.server"],

        cwd=project_root,

    )



    async def run():

        async with stdio_client(server_params) as (read_stream, write_stream):

            async with ClientSession(read_stream, write_stream) as session:

                await session.initialize()





                tools = await session.list_tools()

                print("Available tools:")

                for tool in tools.tools:

                    print(f"  {tool.name}: {tool.description}")

                print()





                result = await session.call_tool(

                    "search_videos",

                    arguments={"query": "python tutorial", "limit": 5},

                )



                print("Search results:")

                for content in result.content:

                    if hasattr(content, "text"):

                        print(content.text)



    asyncio.run(run())





if __name__ == "__main__":

    main()
