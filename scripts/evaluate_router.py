#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from market_intel.router import load_knowledge_base, route_query


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate top-1 source routing")
    parser.add_argument("--kb", default="data/sources.json")
    parser.add_argument("--queries", default="eval/routing_queries.json")
    args = parser.parse_args()
    sources = load_knowledge_base(args.kb)
    with Path(args.queries).open(encoding="utf-8") as handle:
        cases = json.load(handle)
    passed = 0
    for case in cases:
        result_limit = 10 if (
            case.get("expected_categories_in_top") or case.get("expected_sources_in_top")
        ) else 1
        results = route_query(case["query"], sources, limit=result_limit)
        result = results[0] if results else None
        actual_category = result["source"]["category"] if result else None
        actual_source = result["source"]["id"] if result else None
        if case.get("expected_no_results"):
            category_ok = not results
        elif case.get("expected_categories_in_top"):
            actual_categories = {item["source"]["category"] for item in results}
            category_ok = set(case["expected_categories_in_top"]).issubset(actual_categories)
        else:
            category_ok = actual_category == case["expected_category"]
        source_ok = not case.get("expected_source") or actual_source == case["expected_source"]
        if case.get("expected_sources_in_top"):
            actual_sources = {item["source"]["id"] for item in results}
            source_ok = set(case["expected_sources_in_top"]).issubset(actual_sources)
        ok = category_ok and source_ok
        passed += int(ok)
        print("{} | {} | {}".format("PASS" if ok else "FAIL", case["query"], actual_source or "no-result"))
    print("\nTop-1 routing: {}/{} ({:.1f}%)".format(passed, len(cases), passed / len(cases) * 100))
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
