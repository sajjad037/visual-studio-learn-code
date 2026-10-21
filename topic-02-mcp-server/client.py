"""A small MCP client that connects to server.py and calls its tools."""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [tool.name for tool in tools.tools])

            result = await session.call_tool(
                "search_notes", arguments={"keyword": "backup"}
            )
            print("search_notes ->", result.content[0].text)

            result = await session.call_tool(
                "recent_notes", arguments={"limit": 2}
            )
            print("recent_notes ->", result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
