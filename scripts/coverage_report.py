#!/usr/bin/env python3
import argparse
import json
from collections import Counter, defaultdict

from market_intel.router import load_knowledge_base


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize knowledge-base source coverage")
    parser.add_argument("--kb", default="data/sources.json")
    args = parser.parse_args()
    sources = load_knowledge_base(args.kb)
    category_geographies = defaultdict(set)
    for source in sources:
        for geography in source["geographies"] or ["UNSPECIFIED"]:
            category_geographies[source["category"]].add(geography)
    category_publishers = Counter(source["category"] for source in sources)
    report = {
        "sources": len(sources),
        "categories": dict(sorted(Counter(source["category"] for source in sources).items())),
        "data_origins": dict(sorted(Counter(source["data_origin"] for source in sources).items())),
        "access_methods": dict(sorted(Counter(
            method for source in sources for method in source["access_methods"]
        ).items())),
        "decision_types": dict(sorted(Counter(
            decision for source in sources for decision in source["decision_types"]
        ).items())),
        "contribution_statuses": dict(sorted(Counter(
            source["contribution"]["status"] for source in sources
        ).items())),
        "connector_statuses": dict(sorted(Counter(
            source["integration"]["connector_status"] for source in sources
        ).items())),
        "languages": dict(sorted(Counter(
            language for source in sources for language in source["languages"]
        ).items())),
        "verification_statuses": dict(sorted(Counter(
            source["verification"]["status"] for source in sources
        ).items())),
        "industry_codes": dict(sorted(Counter(
            code for source in sources for code in source["industry_codes"]
        ).items())),
        "category_geography_coverage": {
            category: sorted(geographies)
            for category, geographies in sorted(category_geographies.items())
        },
        "fragile_categories": sorted(
            category for category, count in category_publishers.items() if count < 3
        ),
        "single_publisher_categories": sorted(
            category for category in category_publishers
            if len({source["publisher"] for source in sources if source["category"] == category}) == 1
        ),
        "machine_readable": {
            "yes": sum(source["machine_readable"] is True for source in sources),
            "no": sum(source["machine_readable"] is False for source in sources),
            "unspecified": sum(source["machine_readable"] is None for source in sources),
        },
        "metadata_backlog": {
            "unspecified_origin": sum(source["data_origin"] == "unspecified" for source in sources),
            "missing_geography": sum(not source["geographies"] for source in sources),
            "missing_restrictions": sum(not source["terms_or_scraping_restrictions"] for source in sources),
            "missing_license": sum(not source["license"] for source in sources),
            "missing_api_docs_for_api_sources": sum(
                "api" in source["access_methods"] and not source["integration"]["api_docs_url"]
                for source in sources
            ),
            "inferred_provenance": sum(
                "contribution.provenance_url" in source["metadata"]["inferred_fields"]
                for source in sources
            ),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
