#!/usr/bin/env python3
import os
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_intel.router import validate_source_record  # noqa: E402
from market_intel.schema_contract import validate_json_schema  # noqa: E402
from market_intel.service import search_catalog  # noqa: E402
CATALOGS = [
    "catalog/market_intelligence_sources.csv",
    "catalog/public_primary_sources.csv",
    "catalog/global_public_sources.csv",
    "catalog/community_reviewed_sources.csv",
]
EXPECTED_SEED_CATALOGS = set(CATALOGS[:3])


def run(*args: str) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment.setdefault("PYTHONPYCACHEPREFIX", str(Path(tempfile.gettempdir()) / "market-intel-pycache"))
    subprocess.run([sys.executable, *args], cwd=str(ROOT), env=environment, check=True)


def main() -> int:
    with (ROOT / "config" / "seed_catalog_hashes.json").open(encoding="utf-8") as handle:
        seed_hashes = json.load(handle)
    if set(seed_hashes) != EXPECTED_SEED_CATALOGS:
        raise SystemExit("Seed hash manifest must contain exactly the three frozen seed catalogs")
    for relative_path, expected in seed_hashes.items():
        if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
            raise SystemExit("Invalid SHA-256 in seed manifest: {}".format(relative_path))
        actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(
                "Frozen seed catalog changed: {}. New sources belong in "
                "catalog/community_reviewed_sources.csv; governance approval is required "
                "to update the seed manifest.".format(relative_path)
            )
    with (ROOT / "schemas" / "source.schema.json").open(encoding="utf-8") as handle:
        schema = json.load(handle)
    with (ROOT / "data" / "sources.json").open(encoding="utf-8") as handle:
        sources = json.load(handle)
    for index, source in enumerate(sources):
        validate_source_record(source, index)
        validate_json_schema(source, schema, ROOT / "schemas", "$[{}]".format(index))
    with (ROOT / "schemas" / "search-response.schema.json").open(encoding="utf-8") as handle:
        response_schema = json.load(handle)
    response = search_catalog("subscription retention", sources, limit=1)
    validate_json_schema(response, response_schema, ROOT / "schemas")
    missing_response = set(response_schema["required"]).difference(response)
    if missing_response or response.get("api_version") != "0.1" or response.get("kb_schema_version") != "1.0":
        raise SystemExit("Search response does not satisfy search-response.schema.json")
    run("-m", "unittest", "discover", "-s", "tests", "-v")
    run("scripts/evaluate_router.py")
    run("scripts/validate_submission.py", "catalog/community_submission_template.csv")
    with tempfile.TemporaryDirectory() as temp_dir:
        run("scripts/build_kb.py", *CATALOGS, "--output-dir", temp_dir)
        for name in ("sources.json", "sources.jsonl"):
            generated = Path(temp_dir, name).read_bytes()
            committed = Path(ROOT, "data", name).read_bytes()
            if generated != committed:
                raise SystemExit("Generated data/{} is stale; rebuild the knowledge base".format(name))
    run("-m", "compileall", "-q", "src", "scripts", "tests")
    print("Repository checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
