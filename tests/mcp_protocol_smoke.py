"""Opt-in protocol smoke test; CI runs this after installing the official MCP SDK."""

import asyncio

from mcp.shared.memory import create_connected_server_and_client_session

from market_intel.mcp_server import create_mcp_server


async def verify_protocol() -> None:
    server = create_mcp_server()
    async with create_connected_server_and_client_session(server, raise_exceptions=True) as session:
        tools = await session.list_tools()
        names = {tool.name for tool in tools.tools}
        expected = {"search_sources", "get_source", "list_intents", "get_coverage"}
        if names != expected:
            raise AssertionError("Unexpected MCP tools: {}".format(sorted(names)))
        result = await session.call_tool(
            "search_sources",
            {"query": "mobile subscription conversion benchmark", "limit": 1},
        )
        if result.isError:
            raise AssertionError("MCP search_sources returned an error: {}".format(result.content))
        structured = result.structuredContent or {}
        if not structured.get("results"):
            raise AssertionError("MCP search_sources returned no structured results")


if __name__ == "__main__":
    asyncio.run(verify_protocol())
