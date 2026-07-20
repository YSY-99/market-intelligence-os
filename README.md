# Market Intelligence OS

Market Intelligence OS is an open, explainable router for business research. Give it a market question or product idea, and it recommends the most relevant public and analytical sources, explains why they fit, and returns source links in human-readable or JSON form.

Version `0.2` is the routing and MCP foundation. It helps people and AI agents decide **where to research**; it does not yet download third-party documents or generate a complete evidence-backed market report.

## What it provides

- 213 source records across 36 business-research categories;
- English and Russian query routing;
- geography-aware recommendations and safe coverage gaps;
- explainable scoring by intent, topic, decision type, authority proxy, and metadata;
- installable CLI, public Python API, and read-only MCP server;
- JSON and JSONL knowledge-base formats for AI agents;
- community source submissions with editorial review and provenance controls;
- reproducible builds, JSON Schemas, and CI for Python 3.9–3.13.

## Quick start

```bash
git clone https://github.com/YSY-99/market-intelligence-os.git
cd market-intelligence-os
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

market-intel search "mobile subscription conversion benchmark" --limit 5
market-intel search "government procurement Germany" --limit 5 --json
```

Use the Python API:

```python
from market_intel import search

response = search("AI industry trends and investment", limit=5)
for result in response["results"]:
    print(result["source"]["company"], result["recommended_url"])
```

See [the API guide](docs/api.md) and [the runnable example](examples/search_sources.py).

Connect an AI client through MCP (Python 3.10+):

```bash
python -m pip install -e '.[mcp]'
market-intel-mcp
```

See [the MCP guide](docs/mcp.md) for client configuration, available tools, and safety limits.

## Repository contents

All project content is stored as regular files and directories:

| Path | Purpose |
|---|---|
| `catalog/` | Human-editable CSV source catalogs and the community template |
| `config/` | Routing taxonomy, geography rules, decision types, and frozen seed hashes |
| `data/` | Generated `sources.json` and `sources.jsonl` knowledge base |
| `src/market_intel/` | Python routing engine, validation, CLI, and public API |
| `schemas/` | Machine-readable source and search-response contracts |
| `scripts/` | Build, validation, evaluation, and repository quality commands |
| `tests/` | Unit and regression tests |
| `eval/` | Golden routing queries |
| `docs/` | Architecture, governance, data model, security, and implementation plans |
| `.github/` | CI, issue forms, PR template, and CODEOWNERS |

The ZIP and TAR files displayed on a GitHub Release page are generated automatically by GitHub from the tagged source tree. They are download formats, not archive files committed inside this repository.

## How it works

1. CSV catalogs remain the editable source of truth.
2. The build process validates and normalizes records into JSON/JSONL.
3. The router detects research intent, decision type, and geography.
4. It ranks compatible sources and returns explanations, caveats, and URLs.
5. The user or an AI agent performs the actual research against those sources.

Rebuild the knowledge base:

```bash
PYTHONPATH=src python3 scripts/build_kb.py \
  catalog/market_intelligence_sources.csv \
  catalog/public_primary_sources.csv \
  catalog/global_public_sources.csv \
  catalog/community_reviewed_sources.csv \
  --output-dir data
```

Run the complete quality gate:

```bash
python3 scripts/check_repository.py
```

The current regression suite passes 53/53 routing scenarios.

## Contributing sources

New sources never enter production automatically. Start with `catalog/community_submission_template.csv`, keep the contribution status as `pending`, and validate it:

```bash
PYTHONPATH=src python3 scripts/validate_submission.py path/to/proposal.csv
```

Source provenance, geography, access restrictions, rights metadata, and reviewer independence are required. See [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Roadmap

Our next development sequence is:

1. Reproducible research workspaces and run manifests.
2. A report/document registry with publication dates, provenance, and hashes.
3. Safe HTML/PDF/API retrieval with licensing controls and citation-ready artifacts.
4. Evidence extraction, source comparison, and claim-level citations.
5. A complete idea-analysis workflow and, later, a public web service.

See [ROADMAP.md](ROADMAP.md) for release goals and acceptance criteria.

## Current limitations

- All source connectors are currently disabled (`not_implemented`).
- The system does not fetch or redistribute linked content.
- Some legacy catalog records still require rights, geography, and methodology enrichment.
- An empty license field or `review_required` is not permission to scrape or reuse a source.
- Material business decisions must be verified against current primary evidence and methodology.

## License

- Software: [Apache License 2.0](LICENSE).
- Original catalog metadata: [Creative Commons Attribution 4.0 International](LICENSE-DATA).
- Third-party reports, APIs, websites, datasets, and trademarks remain under their owners' terms; see [NOTICE](NOTICE).

## Documentation

- [Architecture](docs/architecture.md)
- [Data model](docs/data-model.md)
- [API](docs/api.md)
- [Source coverage](docs/source-coverage.md)
- [Threat model](docs/threat-model.md)
- [Security policy](SECURITY.md)
- [Governance](GOVERNANCE.md)
