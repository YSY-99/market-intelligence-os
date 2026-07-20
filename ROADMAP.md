# Roadmap

Market Intelligence OS will evolve from a source router into a complete, evidence-based research system for people and AI agents.

## v0.2 — Read-only MCP

Status: released in v0.2.0.

- `search_sources`
- `get_source`
- `list_intents`
- `get_coverage`
- shared response schemas and error handling with the CLI/Python API
- MCP integration documentation and automated protocol tests

Success means an MCP-compatible AI client can install the project locally and discover the best sources without knowing the repository internals.

## v0.3 — Documents and safe retrieval

- report and document registry;
- HTML, PDF, CSV, JSON, and approved API adapters;
- SSRF-safe networking, redirect/IP validation, size/time/MIME limits, and rate controls;
- retrieval timestamps, content hashes, provenance, rights status, and raw-artifact references;
- no connector enabled until its access and reuse policy is reviewed.

Success means the system can collect permitted public evidence reproducibly without treating fetched content as trusted instructions.

## v0.4 — Evidence and idea analysis

- research-question decomposition;
- market, competitor, pricing, customer, regulation, and risk workflows;
- claim-level citations and PDF page references;
- evidence confidence, contradictions, limitations, and explicit insufficient-evidence results;
- private user documents stored separately from the public catalog.

Success means a person can submit a business idea and receive a structured, traceable analysis rather than only a list of links.

## v1.0 — Public research service

- web interface and hosted API;
- projects, saved research, refresh jobs, and exports;
- authentication, quotas, moderation, privacy, deletion, and abuse controls;
- monitoring and source freshness checks;
- broad multilingual/industry/geography evaluation with citation-quality metrics.

Success means non-technical users and AI agents can run reliable research while every material conclusion remains traceable to current evidence.
