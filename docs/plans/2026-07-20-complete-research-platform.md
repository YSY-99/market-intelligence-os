# Market Intelligence OS: Complete Research Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the source catalog into a public, evidence-first system that can route business questions, safely retrieve permitted public or private material, and produce reproducible analyses with citations.

**Architecture:** Keep a dependency-light Python domain core and place CLI, MCP, HTTP, and web interfaces around the same typed application services. Store sources, documents, research projects, claims, and evidence as versioned records; make every conclusion traceable to an immutable snapshot. Treat retrieval as an untrusted boundary with explicit network, licensing, privacy, and prompt-injection controls.

**Tech Stack:** Python 3.9+, official MCP Python SDK (optional extra), JSON Schema, SQLite for local state, stdlib HTTP/security primitives, unittest, GitHub Actions; later FastAPI/PostgreSQL/object storage and a small accessible web client.

---

## Definition of 10/10

The project earns a 10/10 product-readiness score only when a new user can install it, connect an AI client, add permitted sources or documents, run an idea/business question, inspect cited evidence, reproduce the result, and understand its uncertainty without trusting hidden agent behavior. The hosted edition must additionally pass security, privacy, accessibility, reliability, and operational gates.

## Task 1: Stable application facade and read-only MCP server

**Files:**
- Create: `src/market_intel/catalog.py`
- Create: `src/market_intel/mcp_server.py`
- Create: `tests/test_catalog.py`
- Create: `tests/test_mcp_server.py`
- Create: `docs/mcp.md`
- Modify: `src/market_intel/__init__.py`
- Modify: `src/market_intel/cli.py`
- Modify: `pyproject.toml`
- Modify: `README.md`

**Step 1:** Write failing tests for `get_source`, `list_intents`, `get_coverage`, input bounds, stable response envelopes, and import behavior without the optional MCP SDK.

**Step 2:** Implement the dependency-free catalog facade and reuse it from the public Python API and CLI.

**Step 3:** Add an optional `mcp` dependency group and `market-intel-mcp` entry point using the official SDK's `FastMCP`. Register read-only tools: `search_sources`, `get_source`, `list_intents`, and `get_coverage`.

**Step 4:** Document local installation and configuration for MCP clients. Make network transports opt-in; default to stdio.

**Step 5:** Run `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py`.

**Step 6:** Commit: `feat: add read-only MCP research tools`.

## Task 2: Research project workspace and reproducible manifests

**Files:**
- Create: `src/market_intel/workspace.py`
- Create: `schemas/research-project.schema.json`
- Create: `schemas/research-run.schema.json`
- Create: `tests/test_workspace.py`
- Create: `docs/research-workspaces.md`
- Modify: `src/market_intel/cli.py`
- Modify: `src/market_intel/mcp_server.py`

**Step 1:** Test safe project identifiers, atomic writes, schema versions, timestamps, user questions, selected sources, and immutable run manifests.

**Step 2:** Implement a filesystem workspace with explicit root selection and no ambient home-directory writes.

**Step 3:** Add CLI commands to create/show projects and record a routing run. Add MCP tools only for an explicitly configured workspace.

**Step 4:** Validate all persisted records against schemas and document backup/export behavior.

**Step 5:** Run unit and repository checks.

**Step 6:** Commit: `feat: add reproducible research workspaces`.

## Task 3: Document registry, rights, and provenance

**Files:**
- Create: `src/market_intel/documents.py`
- Create: `src/market_intel/rights.py`
- Create: `schemas/document.schema.json`
- Create: `schemas/source-snapshot.schema.json`
- Create: `tests/test_documents.py`
- Create: `tests/test_rights.py`
- Create: `docs/data-rights.md`
- Modify: `LICENSE-DATA`

**Step 1:** Test records for canonical URL, publisher, publication/access dates, content type, language, geography, checksum, license, robots/terms note, and retention policy.

**Step 2:** Implement an append-only document registry and content-addressed snapshot metadata. Never commit third-party document bodies to the public repository.

**Step 3:** Implement rights decisions: metadata-only, retrievable, cacheable, user-private, expired, and blocked.

**Step 4:** Add provenance validation and exportable attribution manifests.

**Step 5:** Commit: `feat: add document provenance and rights registry`.

## Task 4: Safe retrieval boundary

**Files:**
- Create: `src/market_intel/retrieval/policy.py`
- Create: `src/market_intel/retrieval/http.py`
- Create: `src/market_intel/retrieval/limits.py`
- Create: `tests/test_retrieval_policy.py`
- Create: `tests/test_retrieval_http.py`
- Create: `docs/security/retrieval-threat-model.md`

**Step 1:** Test rejection of non-HTTP schemes, credentials in URLs, localhost, private/link-local/reserved IPs, DNS rebinding, unsafe redirects, oversized bodies, disallowed MIME types, decompression bombs, and excessive timeouts.

**Step 2:** Implement URL normalization, DNS/IP validation on every hop, bounded streaming, content sniffing, retry budgets, and per-host rate limits.

**Step 3:** Treat fetched text as untrusted data. Preserve it separately from system instructions and mark prompt-injection indicators without executing embedded instructions.

**Step 4:** Test only against local deterministic fixtures; keep live-network tests opt-in.

**Step 5:** Commit: `feat: add policy-controlled document retrieval`.

## Task 5: Extraction, normalization, and evidence index

**Files:**
- Create: `src/market_intel/extractors/base.py`
- Create: `src/market_intel/extractors/html.py`
- Create: `src/market_intel/extractors/pdf.py`
- Create: `src/market_intel/extractors/tabular.py`
- Create: `src/market_intel/evidence.py`
- Create: `schemas/evidence-chunk.schema.json`
- Create: `tests/fixtures/documents/`
- Create: `tests/test_extractors.py`
- Create: `tests/test_evidence.py`

**Step 1:** Define normalized blocks with stable locator, page/section/table coordinates, content hash, extraction warnings, and source snapshot ID.

**Step 2:** Implement HTML, PDF, CSV, and JSON extractors behind one interface. Make heavyweight parsers optional extras.

**Step 3:** Build deterministic lexical retrieval first, then an optional embedding index with recorded model/version and rebuild support.

**Step 4:** Add golden extraction fixtures and multilingual retrieval evaluations.

**Step 5:** Commit: `feat: build traceable evidence index`.

## Task 6: Claim ledger and evidence-first synthesis

**Files:**
- Create: `src/market_intel/claims.py`
- Create: `src/market_intel/citations.py`
- Create: `src/market_intel/synthesis.py`
- Create: `schemas/claim.schema.json`
- Create: `schemas/analysis.schema.json`
- Create: `tests/test_claims.py`
- Create: `tests/test_citations.py`
- Create: `tests/test_synthesis.py`

**Step 1:** Test claim-to-evidence links, quote bounds, citation locators, primary/secondary source classification, freshness, independence, contradiction flags, and calibrated confidence.

**Step 2:** Implement a claim ledger where unsupported material claims fail validation rather than silently appearing in a report.

**Step 3:** Add deterministic citation rendering and an evidence appendix. Keep model-generated prose outside the trusted evidence layer.

**Step 4:** Add abstention and coverage-gap responses for insufficient or conflicting evidence.

**Step 5:** Commit: `feat: add cited claim ledger and synthesis`.

## Task 7: Business and idea analysis workflows

**Files:**
- Create: `src/market_intel/workflows/idea.py`
- Create: `src/market_intel/workflows/market.py`
- Create: `src/market_intel/workflows/competitors.py`
- Create: `src/market_intel/workflows/pricing.py`
- Create: `src/market_intel/workflows/regulation.py`
- Create: `config/workflows.json`
- Create: `schemas/research-brief.schema.json`
- Create: `tests/test_workflows.py`
- Create: `docs/analysis-methodology.md`

**Step 1:** Define question decomposition into customer/problem, market, alternatives, demand signals, unit economics, distribution, regulatory risk, execution risk, and disconfirming evidence.

**Step 2:** Route each sub-question by intent, geography, freshness, source authority, source independence, access, and evidence type.

**Step 3:** Produce a structured brief with assumptions, findings, counter-evidence, unknowns, suggested experiments, citations, and reproducibility manifest.

**Step 4:** Add benchmark cases with human-reviewed expected source classes and minimum evidence requirements.

**Step 5:** Commit: `feat: add evidence-first business analysis workflows`.

## Task 8: Community contribution and source-quality lifecycle

**Files:**
- Create: `src/market_intel/quality.py`
- Create: `schemas/source-review.schema.json`
- Create: `data/reviews/README.md`
- Create: `.github/ISSUE_TEMPLATE/source.yml`
- Create: `.github/workflows/source-review.yml`
- Create: `tests/test_quality.py`
- Modify: `CONTRIBUTING.md`

**Step 1:** Replace opaque authority numbers with a review rubric: publisher identity, methodology transparency, primary data, sample quality, recency, independence, correction policy, and access stability.

**Step 2:** Record reviewer, date, evidence, conflicts, and next review date. Keep community submissions quarantined until validation and review pass.

**Step 3:** Add duplicate detection, broken-link reports, staleness budgets, and coverage dashboards by geography/industry/decision type.

**Step 4:** Commit: `feat: add auditable source quality lifecycle`.

## Task 9: Public HTTP API and private data plane

**Files:**
- Create: `src/market_intel/http_api/`
- Create: `deploy/compose.yaml`
- Create: `docs/api.md`
- Create: `docs/privacy.md`
- Create: `docs/security/authentication.md`
- Create: `tests/integration/test_http_api.py`

**Step 1:** Specify OpenAPI endpoints and stable error envelopes for catalogs, projects, documents, analyses, exports, and health.

**Step 2:** Add authenticated tenant isolation, least-privilege service roles, encrypted secrets, upload malware checks, deletion/export, quotas, audit logs, and idempotency keys.

**Step 3:** Separate public catalog metadata from private user documents in storage, indexing, caches, logs, backups, and model-provider requests.

**Step 4:** Add migration, backup/restore, disaster recovery, and abuse/rate-limit integration tests.

**Step 5:** Commit: `feat: add secure multi-tenant research API`.

## Task 10: Accessible web application

**Files:**
- Create: `web/`
- Create: `docs/product/user-journeys.md`
- Create: `tests/e2e/`

**Step 1:** Implement onboarding, project creation, source/document addition, query composition, live progress, evidence inspection, citation navigation, export, and deletion.

**Step 2:** Meet WCAG 2.2 AA, keyboard and screen-reader support, responsive layouts, localization, plain-language errors, and explicit cost/privacy controls.

**Step 3:** Add browser tests for the complete first-user journey and critical failure states.

**Step 4:** Commit: `feat: add accessible research workspace UI`.

## Task 11: Evaluation, security, and operations gates

**Files:**
- Create: `evals/`
- Create: `docs/operations/slo.md`
- Create: `docs/operations/runbooks/`
- Create: `SECURITY.md`
- Create: `.github/workflows/security.yml`
- Create: `.github/workflows/release.yml`
- Modify: `.github/workflows/ci.yml`

**Step 1:** Add routing recall, evidence precision, citation correctness, freshness, contradiction, abstention, multilingual, latency, and cost datasets with regression thresholds.

**Step 2:** Add dependency review, secret scanning, static analysis, SBOM, signed releases/provenance, container scanning, and scheduled security tests.

**Step 3:** Define SLOs, tracing/metrics/log redaction, alerts, incident response, rollback, capacity, and cost budgets.

**Step 4:** Commission independent security/privacy review and public methodology review before declaring v1.0.

**Step 5:** Commit: `chore: enforce v1 production readiness gates`.

## Task 12: Release and 10/10 acceptance audit

**Files:**
- Create: `docs/acceptance/ten-out-of-ten.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `ROADMAP.md`

**Step 1:** Run clean-machine installation tests for CLI, Python, MCP, local workspace, hosted API, and web onboarding.

**Step 2:** Run the complete evaluation and security suites and publish versioned results with known limitations.

**Step 3:** Verify licenses, attributions, contributor governance, privacy requests, backups, incident drills, accessibility, and reproducibility.

**Step 4:** Mark 10/10 only when every acceptance check has evidence and an owner; otherwise publish the actual score and remaining gaps.

**Step 5:** Tag and sign v1.0.0 and publish packages, images, documentation, migration notes, and support policy.
