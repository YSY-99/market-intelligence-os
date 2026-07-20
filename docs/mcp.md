# MCP integration

Market Intelligence OS exposes its source router to AI clients through four read-only Model Context Protocol tools:

- `search_sources` ranks sources for a question and explains every result;
- `get_source` returns one full catalog record by stable ID;
- `list_intents` describes the router's research vocabulary;
- `get_coverage` summarizes categories, geographies, access models, connector status, and verification status.

These tools recommend where to research. They do not fetch third-party pages, execute instructions found in content, or claim that a linked source proves an answer.

## Install and run

The official stable MCP Python SDK currently requires Python 3.10 or newer. The repository pins stable SDK version `1.28.1` because the forthcoming v2 line has a breaking API. The core CLI and Python library continue to support Python 3.9 without MCP.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[mcp]'
market-intel-mcp
```

The server uses standard input/output by default, so it can run as a local subprocess without opening a network port. Configure an MCP client with the executable inside the virtual environment:

```json
{
  "mcpServers": {
    "market-intelligence": {
      "command": "/absolute/path/to/.venv/bin/market-intel-mcp"
    }
  }
}
```

Restart the client and ask it to list the server tools. A useful first call is `search_sources` with `query` set to `mobile subscription conversion benchmark` and `limit` set to `5`.

## Safety and limits

- Queries must contain 1–2,000 characters.
- Result limits must be between 1 and 20.
- Source IDs must contain 1–128 characters.
- The server is read-only and does not persist user questions.
- All outputs use the same versioned contracts as the Python API.
- Streamable HTTP is intentionally not enabled yet; authentication and tenant isolation are required before network deployment.
