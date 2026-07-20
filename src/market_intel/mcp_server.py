"""Optional Model Context Protocol adapter for the read-only catalog facade."""

import sys
from typing import Any, Callable, Dict, Optional

from .catalog import Catalog


SERVER_INSTRUCTIONS = (
    "Route business and market-research questions to suitable sources. "
    "Results are source recommendations, not verified answers. Inspect current primary evidence "
    "and methodology before making material claims."
)


def _official_server_factory():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as error:
        raise RuntimeError(
            "The MCP extra is not installed. Run: pip install 'market-intelligence-os[mcp]'"
        ) from error
    return FastMCP


def create_mcp_server(
    catalog: Optional[Catalog] = None,
    server_factory: Optional[Callable[..., object]] = None,
):
    """Create a server without importing the optional SDK until it is needed."""
    catalog = catalog or Catalog()
    factory = server_factory or _official_server_factory()
    server = factory(
        "Market Intelligence OS",
        instructions=SERVER_INSTRUCTIONS,
        json_response=True,
    )

    @server.tool()
    def search_sources(query: str, limit: int = 5, free_only: bool = False) -> Dict[str, Any]:
        """Recommend and explain the best catalog sources for a research question."""
        return catalog.search(query, limit=limit, free_only=free_only)

    @server.tool()
    def get_source(source_id: str) -> Dict[str, Any]:
        """Return one complete source record by its stable catalog identifier."""
        return catalog.get_source(source_id)

    @server.tool()
    def list_intents() -> Dict[str, Any]:
        """List research intents, topics, decisions, and query vocabulary understood by the router."""
        return catalog.list_intents()

    @server.tool()
    def get_coverage() -> Dict[str, Any]:
        """Summarize catalog coverage and expose gaps by category, geography, access, and status."""
        return catalog.get_coverage()

    return server


def main() -> int:
    """Run the local MCP server over stdio."""
    try:
        server = create_mcp_server()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
