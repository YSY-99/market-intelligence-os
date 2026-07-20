"""Public API for the Market Intelligence OS source router."""

from typing import Iterable, List, Dict

from .ingest import repository_file
from .router import load_knowledge_base
from .service import search_catalog

__version__ = "0.1.0"


def load_default_knowledge_base() -> List[Dict[str, object]]:
    """Load the repository or installed read-only source catalog."""
    return load_knowledge_base(repository_file("data", "sources.json"))


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
    catalog = list(sources) if sources is not None else load_default_knowledge_base()
    return search_catalog(query, catalog, limit=limit, free_only=free_only)


__all__ = ["__version__", "load_default_knowledge_base", "search", "search_sources"]
