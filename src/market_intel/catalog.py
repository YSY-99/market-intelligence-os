"""Dependency-free application facade shared by CLI, Python, and MCP clients."""

from collections import Counter
from copy import deepcopy
from typing import Dict, Iterable, List, Optional

from .ingest import load_taxonomy, repository_file
from .router import load_knowledge_base, validate_source_record
from .service import API_VERSION, search_catalog


MAX_QUERY_CHARACTERS = 2000
MAX_SEARCH_RESULTS = 20
MAX_SOURCE_ID_CHARACTERS = 128


def load_default_sources() -> List[Dict[str, object]]:
    """Load the repository or installed read-only source catalog."""
    return load_knowledge_base(repository_file("data", "sources.json"))


class Catalog:
    """Validated, read-only source catalog with stable response envelopes."""

    def __init__(
        self,
        sources: Optional[Iterable[Dict[str, object]]] = None,
        taxonomy: Optional[Dict[str, object]] = None,
    ) -> None:
        self._sources = deepcopy(list(sources) if sources is not None else load_default_sources())
        self._taxonomy = taxonomy or load_taxonomy()
        self._by_id = {}
        for index, source in enumerate(self._sources):
            validate_source_record(source, index)
            source_id = source["id"]
            if source_id in self._by_id:
                raise ValueError("Duplicate source id: {}".format(source_id))
            self._by_id[source_id] = source

    @property
    def sources(self) -> List[Dict[str, object]]:
        """Return a shallow copy so callers cannot change catalog membership."""
        return deepcopy(self._sources)

    def search(self, query: str, limit: int = 5, free_only: bool = False) -> Dict[str, object]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if len(query) > MAX_QUERY_CHARACTERS:
            raise ValueError("query must not exceed {} characters".format(MAX_QUERY_CHARACTERS))
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_SEARCH_RESULTS:
            raise ValueError("limit must be between 1 and {}".format(MAX_SEARCH_RESULTS))
        if not isinstance(free_only, bool):
            raise ValueError("free_only must be a boolean")
        return deepcopy(search_catalog(query, self._sources, limit=limit, free_only=free_only))

    def get_source(self, source_id: str) -> Dict[str, object]:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if len(source_id) > MAX_SOURCE_ID_CHARACTERS:
            raise ValueError("source_id must not exceed {} characters".format(MAX_SOURCE_ID_CHARACTERS))
        source = self._by_id.get(source_id)
        return {
            "api_version": API_VERSION,
            "source_id": source_id,
            "found": source is not None,
            "source": deepcopy(source),
        }

    def list_intents(self) -> Dict[str, object]:
        intents = []
        for name, rule in self._taxonomy.items():
            intents.append({
                "name": name,
                "topics": list(rule.get("topics", [])),
                "decision_types": list(rule.get("decision_types", [])),
                "query_terms": list(rule.get("query_terms", [])),
            })
        return {"api_version": API_VERSION, "total": len(intents), "intents": intents}

    def get_coverage(self) -> Dict[str, object]:
        categories = Counter(source["category"] for source in self._sources)
        geographies = Counter(
            geography
            for source in self._sources
            for geography in source.get("geographies", [])
        )
        connectors = Counter(
            source.get("integration", {}).get("connector_status", "unspecified")
            for source in self._sources
        )
        verification = Counter(
            source.get("verification", {}).get("status", "unspecified")
            for source in self._sources
        )
        access_models = Counter()
        for source in self._sources:
            access = source.get("access", {})
            for access_type in ("free", "paid", "freemium"):
                if access.get(access_type):
                    access_models[access_type] += 1
        return {
            "api_version": API_VERSION,
            "total_sources": len(self._sources),
            "categories": dict(sorted(categories.items())),
            "geographies": dict(sorted(geographies.items())),
            "access_models": dict(sorted(access_models.items())),
            "connector_statuses": dict(sorted(connectors.items())),
            "verification_statuses": dict(sorted(verification.items())),
        }
