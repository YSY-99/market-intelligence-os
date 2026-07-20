import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .ingest import load_taxonomy, repository_file
from .router import load_knowledge_base
from .service import search_catalog


DEFAULT_KB = repository_file("data", "sources.json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-intel", description="Route research questions to trusted sources")
    parser.add_argument("--kb", default=str(DEFAULT_KB), help="Path to sources.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Recommend sources for a question")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--free-only", action="store_true")
    search.add_argument("--json", action="store_true", dest="as_json")

    inspect = subparsers.add_parser("inspect", help="Show a source record")
    inspect.add_argument("source_id")

    subparsers.add_parser("intents", help="List routing categories")
    return parser


def _print_search(query: str, results: List[dict], detected_geographies=None) -> None:
    if not results:
        if detected_geographies:
            print(
                "No suitable source found for geography {}. "
                "Add a reviewed community source for this jurisdiction.".format(
                    ", ".join(sorted(detected_geographies))
                )
            )
        else:
            print("No relevant sources found. Try a more specific question or add a community source.")
        return
    print("Query: {}".format(query))
    for index, result in enumerate(results, 1):
        source = result["source"]
        reasons = []
        if result["matched_intents"]:
            reasons.append("intent: {}".format(source["category"]))
        if result["matched_terms"]:
            reasons.append("terms: {}".format(", ".join(result["matched_terms"][:6])))
        if result["matched_routing_concepts"]:
            reasons.append("routing concepts: {}".format(", ".join(result["matched_routing_concepts"][:6])))
        if result["matched_decisions"]:
            reasons.append("decisions: {}".format(", ".join(result["matched_decisions"])))
        if result["query_geographies"]:
            reasons.append("geography: {}".format(", ".join(result["query_geographies"])))
        print("\n{}. {} — {:.1f}/100".format(index, source["company"], result["score"]))
        print("   {}".format(source["category"]))
        print("   Why: {}".format("; ".join(reasons) or "metadata relevance"))
        print("   URL: {}".format(result["recommended_url"]))
        if result["caveats"]:
            print("   Caveat: {}".format("; ".join(result["caveats"])))


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "intents":
        for category in load_taxonomy():
            print(category)
        return 0
    try:
        sources = load_knowledge_base(args.kb)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("Cannot load knowledge base: {}".format(error), file=sys.stderr)
        return 2
    if args.command == "inspect":
        source = next((item for item in sources if item["id"] == args.source_id), None)
        if source is None:
            print("Unknown source: {}".format(args.source_id), file=sys.stderr)
            return 1
        print(json.dumps(source, ensure_ascii=False, indent=2))
        return 0
    if args.limit <= 0:
        print("--limit must be a positive integer", file=sys.stderr)
        return 2
    try:
        payload = search_catalog(args.query, sources, limit=args.limit, free_only=args.free_only)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    results = payload["results"]
    detected_geographies = payload["detected_geographies"]
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_search(args.query, results, detected_geographies)
    return 0
