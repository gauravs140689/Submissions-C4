from __future__ import annotations
"""Thin retrieval facade with cached store initialization."""

from functools import lru_cache
from typing import Dict, List, Optional

from rag.lancedb_store import KBSnippet, get_default_store


@lru_cache(maxsize=1)
def _store():
    # Store creation can be expensive; cache it per process.
    return get_default_store()


def retrieve(query: str, k: int = 5, filters: Optional[Dict[str, str]] = None) -> List[KBSnippet]:
    """Retrieve top-k snippets for a query with optional metadata filters."""
    return _store().retrieve(query=query, k=k, filters=filters or {})
