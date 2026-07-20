"""Public API for the Market Intelligence OS source router."""

from typing import Iterable, List, Dict

from .catalog import Catalog, load_default_sources

__version__ = "0.2.0"


def load_default_knowledge_base() -> List[Dict[str, object]]:
    """Load the repository or installed read-only source catalog."""
    return load_default_sources()


def search_sources(
    query: str,
    sources: Iterable[Dict[str, object]] = None,
    limit: int = 5,
    free_only: bool = False,
) -> List[Dict[str, object]]:
    """Return explained, ranked source recommendations for a research query."""
    return search(
        query, sources=sources, limit=limit, free_only=free_only
    )["results"]


def search(
    query: str,
    sources: Iterable[Dict[str, object]] = None,
    limit: int = 5,
    free_only: bool = False,
) -> Dict[str, object]:
    """Return a versioned search response shared with the JSON CLI."""
    return Catalog(sources).search(query, limit=limit, free_only=free_only)


__all__ = ["Catalog", "__version__", "load_default_knowledge_base", "search", "search_sources"]
