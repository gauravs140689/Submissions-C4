from __future__ import annotations
"""LanceDB-backed KB store with sentence-transformer embeddings and filtered retrieval."""

import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import lancedb
import pyarrow as pa
from sentence_transformers import SentenceTransformer


@dataclass
class KBSnippet:
    """Retrieval return shape used by agent nodes and report citations."""
    snippet_id: str
    text: str
    source: str
    category: str
    domain: Optional[str] = None
    platform: Optional[str] = None


class LanceKBStore:
    """Small wrapper around LanceDB table creation, indexing, and nearest-neighbor search."""
    def __init__(
        self,
        db_path: str | Path = "lancedb",
        table_name: str = "kb_chunks",
        embedding_model: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        self.db_path = str(db_path)
        self.table_name = table_name
        self.db = lancedb.connect(self.db_path)
        self.embedder = SentenceTransformer(embedding_model)
        self.dim = int(self.embedder.get_sentence_embedding_dimension())
        self.table = self._ensure_table()

    def _ensure_table(self):
        """Open existing table or create it with a fixed schema."""
        schema = pa.schema(
            [
                pa.field("snippet_id", pa.string()),
                pa.field("text", pa.string()),
                pa.field("source", pa.string()),
                pa.field("category", pa.string()),
                pa.field("domain", pa.string()),
                pa.field("platform", pa.string()),
                pa.field("embedding", pa.list_(pa.float32(), self.dim)),
            ]
        )

        if self.table_name in self.db.table_names():
            return self.db.open_table(self.table_name)
        return self.db.create_table(self.table_name, schema=schema)

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Embed and insert KB chunks into LanceDB."""
        if not documents:
            return 0
        texts = [doc["text"] for doc in documents]
        vectors = self.embedder.encode(texts, normalize_embeddings=True).tolist()

        rows = []
        for doc, vec in zip(documents, vectors):
            rows.append(
                {
                    "snippet_id": doc.get("snippet_id") or str(uuid.uuid4()),
                    "text": doc["text"],
                    "source": doc.get("source", "unknown"),
                    "category": doc.get("category", "general"),
                    "domain": doc.get("domain"),
                    "platform": doc.get("platform"),
                    "embedding": [float(x) for x in vec],
                }
            )
        self.table.add(rows)
        return len(rows)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[KBSnippet]:
        """Vector search with optional domain/category/platform filters."""
        vector = self.embedder.encode([query], normalize_embeddings=True)[0].tolist()
        search = self.table.search(vector).limit(k)

        if filters:
            clauses = []
            for key in ["domain", "category", "platform"]:
                value = filters.get(key)
                if value:
                    clauses.append(f"{key} = '{value}'")
            if clauses:
                search = search.where(" AND ".join(clauses))

        rows = search.to_list()
        snippets: List[KBSnippet] = []
        for row in rows:
            snippets.append(
                KBSnippet(
                    snippet_id=row["snippet_id"],
                    text=row["text"],
                    source=row["source"],
                    category=row["category"],
                    domain=row.get("domain"),
                    platform=row.get("platform"),
                )
            )
        return snippets


def get_default_store() -> LanceKBStore:
    """Create store instance from environment overrides used in local/colab runs."""
    db_path = os.getenv("LANCEDB_PATH", "lancedb")
    table_name = os.getenv("LANCEDB_TABLE", "kb_chunks")
    embedding_model = os.getenv("EMBED_MODEL_ID", "BAAI/bge-small-en-v1.5")
    return LanceKBStore(db_path=db_path, table_name=table_name, embedding_model=embedding_model)
