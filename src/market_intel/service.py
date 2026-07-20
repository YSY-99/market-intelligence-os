from typing import Dict, Iterable

from .router import (
    detect_decision_types,
    detect_geographies,
    detect_intents,
    route_query,
    validate_source_record,
)


API_VERSION = "0.1"
RANKING_VERSION = "lexical-v1"


def search_catalog(
    query: str,
    sources: Iterable[Dict[str, object]],
    limit: int = 5,
    free_only: bool = False,
) -> Dict[str, object]:
    """Return the versioned response envelope shared by Python and CLI clients."""
    catalog = list(sources)
    for index, source in enumerate(catalog):
        validate_source_record(source, index)
    intents = detect_intents(query)
    decisions = sorted(detect_decision_types(query))
    geographies = sorted(detect_geographies(
        query, allow_lowercase_codes=bool(intents or decisions)
    ))
    results = route_query(query, catalog, limit=limit, free_only=free_only)
    return {
        "api_version": API_VERSION,
        "kb_schema_version": "1.0",
        "ranking_version": RANKING_VERSION,
        "query": query,
        "detected_intents": intents,
        "detected_decisions": decisions,
        "detected_geographies": geographies,
        "coverage_gap": not results,
        "warnings": [
            "Source authority may be an editorial proxy; verify material claims against methodology and primary evidence."
        ],
        "results": results,
    }
