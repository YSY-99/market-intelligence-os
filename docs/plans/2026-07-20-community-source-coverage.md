# Community Source Coverage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand Market Intelligence OS with the missing primary-data domains and a validated community contribution path.

**Architecture:** Keep seed and primary-source catalogs as separate CSV inputs, merge them deterministically into one runtime JSON/JSONL knowledge base, and enrich every record with provenance, access, decision, geography, and contribution metadata. Extend the controlled taxonomy so the router can direct business questions to filings, statistics, procurement, patents, trade, reviews, regulation, talent, and local data. Community submissions use the same schema and validation pipeline but remain visibly distinguishable from reviewed seed records.

**Tech Stack:** Python 3.9 standard library, CSV, JSON/JSONL, `unittest`, CLI.

---

### Task 1: Make the catalog repository-owned and multi-file

**Files:**
- Create: `catalog/market_intelligence_sources.csv`
- Create: `catalog/public_primary_sources.csv`
- Modify: `src/market_intel/ingest.py`
- Modify: `scripts/build_kb.py`
- Test: `tests/test_ingest.py`

**Steps:**

1. Copy the existing 141-row seed catalog into `catalog/market_intelligence_sources.csv`.
2. Write failing tests for merging multiple catalogs and detecting duplicate IDs across files.
3. Add `load_catalogs(paths)` and accept multiple positional CSV paths in the build script.
4. Run `python3 -m unittest tests.test_ingest -v` and verify PASS.

### Task 2: Extend source metadata for public and community use

**Files:**
- Modify: `src/market_intel/schema.py`
- Modify: `src/market_intel/ingest.py`
- Modify: `docs/data-model.md`
- Test: `tests/test_schema.py`
- Test: `tests/test_ingest.py`

**Steps:**

1. Write failing tests for explicit authority, origin, access methods, business stages, decision types, geography, industry codes, API metadata, machine readability, restrictions, and contribution status.
2. Support optional expanded CSV columns while keeping legacy files valid.
3. Store inferred/default fields in `metadata.inferred_fields`; never present inferred values as submitted facts.
4. Validate enumerations and booleans and rerun tests.

### Task 3: Add missing source domains and routing taxonomy

**Files:**
- Modify: `config/taxonomy.json`
- Create: `catalog/public_primary_sources.csv`
- Modify: `eval/routing_queries.json`
- Test: `tests/test_router.py`

**Steps:**

1. Add categories for corporate filings, business statistics, procurement, patents/science, trade/supply chain, customer voice, regulation, talent, and local/geospatial intelligence.
2. Add the primary and public sources identified in the coverage audit, with explicit provenance and access constraints.
3. Add English and Russian routing cases for each new category.
4. Rebuild the KB and require every new evaluation scenario to pass.

### Task 4: Add a community contribution workflow

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `catalog/community_submission_template.csv`
- Create: `scripts/validate_submission.py`
- Test: `tests/test_submission.py`

**Steps:**

1. Write failing tests for valid submissions, missing required fields, duplicate source IDs, invalid URLs/enums, and unreviewed status.
2. Implement a read-only validator that checks a proposed CSV against all seed catalogs and emits a JSON report.
3. Document review criteria: provenance, legality, machine access, freshness, methodology, duplicates, and conflicts of interest.
4. Verify the template itself passes validation.

### Task 5: Document, verify, and independently audit completeness

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Create: `docs/source-coverage.md`

**Steps:**

1. Document repository-owned rebuild and community contribution commands.
2. Generate the expanded KB and coverage counts by origin/category/access method.
3. Run unit tests, JSON validation, routing evaluation, and submission validation.
4. Dispatch an independent review agent to audit completeness, missing domains, routing regressions, and contribution safety.
5. Fix all Critical/Important findings and repeat verification.

