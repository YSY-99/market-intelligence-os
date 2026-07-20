# Python API v0.1

The supported read-only API is intentionally small:

```python
from market_intel import load_default_knowledge_base, search, search_sources

sources = load_default_knowledge_base()
results = search_sources("subscription retention benchmark", sources, limit=5)
response = search("subscription retention benchmark", sources, limit=5)
```

`search_sources` returns the same explained ranking used by the CLI. Each result contains the source record, total score, score breakdown, matched intent/terms/decisions, geography, recommended URL, and caveats. Network retrieval and the proposed MCP `research` tool are not part of v0.1.

The package version is independent from `schema_version` inside every source record. Breaking record changes require a schema-version change and migration notes.
