# Market Intelligence OS Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local, inspectable market-intelligence source router that converts the existing CSV into a normalized knowledge base and recommends the best sources for a natural-language research question.

**Architecture:** A deterministic ingestion pipeline converts the source catalog into versioned JSON records with normalized metadata and generated search terms. A dependency-free Python router scores every source by intent, topic, category, authority, freshness, and access preference, then exposes the result through a CLI. The first release routes users to sources; later releases can add live web retrieval, report indexing, embeddings, and an MCP adapter without changing the core record schema.

**Tech Stack:** Python 3.9 standard library, JSON/JSONL, `unittest`, `argparse`.

---

### Task 1: Define the canonical source schema and taxonomy

**Files:**
- Create: `config/taxonomy.json`
- Create: `src/market_intel/schema.py`
- Test: `tests/test_schema.py`

**Step 1: Write the failing tests**

Cover deterministic slug generation, semicolon-list parsing, priority-to-authority defaults, ISO date validation, and rejection of records missing company or URLs.

**Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_schema -v`

Expected: FAIL because `market_intel.schema` does not exist.

**Step 3: Implement the schema helpers**

Implement a JSON-serializable source record with these stable fields:

```python
{
    "schema_version": "1.0",
    "id": "revenuecat",
    "company": "RevenueCat",
    "category": "Subscription & Web2App",
    "subcategory": "Subscription infrastructure / benchmarks",
    "description": "...",
    "best_for": ["subscription apps", "paywalls"],
    "topics": ["subscriptions", "paywall", "retention"],
    "keywords": ["subscription", "conversion"],
    "synonyms": [],
    "source_type": "Subscription infrastructure / benchmarks",
    "content_formats": ["annual report"],
    "access": {"raw": "Freemium / gated report", "free": True, "paid": True, "gated": True},
    "urls": {"website": "...", "research": "...", "blog": "..."},
    "flagship_resources": [{"title": "State of Subscription Apps", "url": "..."}],
    "priority": "high",
    "authority_score": 9.0,
    "last_verified": "2026-07-20",
    "notes": "...",
    "search_examples": [],
    "example_prompts": [],
    "when_not_to_use": [],
    "related_sources": []
}
```

Keep generated/inferred fields distinguishable in the ingestion metadata so they can be reviewed later.

**Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tests.test_schema -v`

Expected: PASS.

### Task 2: Build deterministic CSV ingestion

**Files:**
- Create: `src/market_intel/ingest.py`
- Create: `scripts/build_kb.py`
- Test: `tests/test_ingest.py`
- Create: `data/.gitkeep`

**Step 1: Write failing fixture-based tests**

Test column mapping, URL preservation, topic extraction, access-model normalization, stable output ordering, and duplicate-ID detection.

**Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_ingest -v`

Expected: FAIL because ingestion is missing.

**Step 3: Implement ingestion**

Read UTF-8/UTF-8-BOM CSV using `csv.DictReader`, validate required columns, map each row to the canonical schema, and write both:

- `data/sources.json` for human review;
- `data/sources.jsonl` for streaming/indexing integrations.

Derive topic terms only from controlled category rules plus `Best_For`; do not fabricate company facts.

**Step 4: Build the knowledge base**

Run:

```bash
PYTHONPATH=src python3 scripts/build_kb.py \
  /Users/yahen/Downloads/market_intelligence_sources.csv \
  --output-dir data
```

Expected: 141 valid records and an ingestion summary with no duplicates.

**Step 5: Run tests**

Run: `python3 -m unittest tests.test_ingest -v`

Expected: PASS.

### Task 3: Implement query understanding and source ranking

**Files:**
- Create: `src/market_intel/router.py`
- Test: `tests/test_router.py`

**Step 1: Write failing routing tests**

Test at least these intents:

```python
"benchmark conversion for mobile subscriptions" -> RevenueCat near the top
"AI industry trends and investment" -> AI/technology and VC research sources
"consumer search behavior" -> consumer/trend research sources
"competitor website traffic" -> web/competitive intelligence sources
```

Also test `--free-only`, recency preference, deterministic tie-breaking, and score explanations.

**Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_router -v`

Expected: FAIL because router is missing.

**Step 3: Implement transparent weighted ranking**

Use normalized tokens and phrases. Score with explicit components:

```text
intent/category match     0..35
topic/best-for match      0..30
description/title match   0..15
authority                 0..10
priority                  0..5
freshness                 0..5
```

Return `matched_terms`, `matched_intents`, `score_breakdown`, recommended URL, and caveats. A score must always be explainable and reproducible.

**Step 4: Run tests**

Run: `python3 -m unittest tests.test_router -v`

Expected: PASS.

### Task 4: Expose the router as a local CLI

**Files:**
- Create: `src/market_intel/cli.py`
- Create: `src/market_intel/__init__.py`
- Create: `src/market_intel/__main__.py`
- Test: `tests/test_cli.py`

**Step 1: Write failing CLI tests**

Test text and JSON output, result limit, free-only filter, missing KB error, and UTF-8/Russian queries.

**Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_cli -v`

Expected: FAIL because CLI is missing.

**Step 3: Implement commands**

```bash
PYTHONPATH=src python3 -m market_intel search "subscription conversion benchmark" --limit 5
PYTHONPATH=src python3 -m market_intel search "AI consumer trends" --json
PYTHONPATH=src python3 -m market_intel inspect revenuecat
PYTHONPATH=src python3 -m market_intel intents
```

Text output should show why each source was selected; JSON output should be suitable for Claude/Codex/automation consumption.

**Step 4: Run tests**

Run: `python3 -m unittest tests.test_cli -v`

Expected: PASS.

### Task 5: Document operation and extension points

**Files:**
- Create: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/data-model.md`

**Step 1: Document the working loop**

Explain: edit CSV -> rebuild KB -> inspect validation report -> query router. Include copy-paste commands and example outputs.

**Step 2: Document boundaries**

State clearly that v0.1 recommends sources but does not yet crawl pages or claim to answer from their contents.

**Step 3: Document the next phases**

Describe compatible extensions:

1. report registry and scheduled freshness checks;
2. live retrieval adapters per source;
3. full-text/embedding index with citations;
4. thin MCP server exposing `search_sources`, `get_source`, and later `research`;
5. evaluation set with expected sources and ranking metrics.

**Step 4: Run the complete verification suite**

Run:

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/build_kb.py /Users/yahen/Downloads/market_intelligence_sources.csv --output-dir data
PYTHONPATH=src python3 -m market_intel search "mobile subscription retention benchmark" --limit 5
```

Expected: all tests pass; build reports 141 sources; CLI returns explained recommendations.

