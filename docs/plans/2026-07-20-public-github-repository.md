# Public GitHub Repository Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn Market Intelligence OS into a reproducible, installable, community-governed public GitHub repository.

**Architecture:** Keep the dependency-free routing core and repository-owned catalogs as the source of truth. Add standard Python packaging, deterministic validation in CI, GitHub contribution workflows, public governance/security documentation, and stable library-facing functions without implementing network retrieval yet.

**Tech Stack:** Python 3.9+, unittest, argparse, GitHub Actions, CSV/JSON/JSONL.

---

### Task 1: Package metadata and installation

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Modify: `README.md`
- Test: `tests/test_package.py`

1. Add a failing test for package version and console entry point behavior.
2. Run `PYTHONPATH=src python3 -m unittest tests.test_package -v` and verify failure.
3. Add PEP 621 metadata, Python version classifiers, project URLs, package discovery, and `market-intel` entry point.
4. Document clone, editable install, CLI usage, and supported Python versions without machine-specific paths.
5. Run the test and `python3 -m pip install -e . --no-deps` in an isolated temporary target.

### Task 2: Deterministic quality gate

**Files:**
- Create: `scripts/check_repository.py`
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Test: `tests/test_repository.py`

1. Add tests that verify generated JSON/JSONL are reproducible from all trusted catalogs.
2. Implement one repository check that runs unit tests, routing evaluation, template validation, compilation, and generated-data comparison.
3. Add a GitHub Actions matrix for Python 3.9–3.13 with least-privilege permissions and dependency-free execution.
4. Document the single local quality command.
5. Run the complete gate and expect exit code 0.

### Task 3: GitHub community workflow

**Files:**
- Create: `.github/ISSUE_TEMPLATE/source_submission.yml`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/CODEOWNERS`
- Create: `CODE_OF_CONDUCT.md`
- Modify: `CONTRIBUTING.md`

1. Add structured source and bug issue forms.
2. Add a PR checklist covering tests, provenance, geography, licensing, and generated artifacts.
3. Add a placeholder CODEOWNERS entry that must be replaced with the future GitHub organization/team.
4. Add a contributor covenant and explain the editorial review lifecycle.
5. Validate YAML syntax and repository links.

### Task 4: Security, provenance, and release policy

**Files:**
- Create: `SECURITY.md`
- Create: `docs/threat-model.md`
- Create: `CHANGELOG.md`
- Create: `CITATION.cff`
- Create: `docs/release-checklist.md`
- Modify: `docs/architecture.md`

1. Document private vulnerability reporting and supported versions.
2. Document trust boundaries for submissions, generated data, URLs, future retrieval, personal data, and licenses.
3. Add a changelog and citation metadata for v0.1.0.
4. Add a reproducible release checklist with tags and generated-data verification.
5. Review documentation for claims that exceed current connector/retrieval capability.

### Task 5: Public API and examples

**Files:**
- Create: `examples/search_sources.py`
- Create: `docs/api.md`
- Modify: `src/market_intel/__init__.py`
- Test: `tests/test_public_api.py`

1. Add a failing import/use test for the supported public Python API.
2. Export stable read-only functions for loading the bundled repository KB and routing queries.
3. Add a minimal example and API contract documentation.
4. Run unit tests and the example.
5. Record MCP/retrieval as explicitly out of scope for v0.1 rather than presenting it as implemented.

### Task 6: License decision and final audit

**Files:**
- Create after owner approval: `LICENSE`
- Create after owner approval: `LICENSE-DATA`
- Modify: `README.md`

1. Confirm the code and metadata licenses with the repository owner.
2. Add exact license texts and clarify that third-party source content remains under publisher terms.
3. Run the repository quality gate.
4. Request an independent code/repository review.
5. Initialize the first clean commit only after the owner approves repository name, GitHub owner, and license.
