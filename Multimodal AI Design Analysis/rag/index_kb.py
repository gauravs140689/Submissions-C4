from __future__ import annotations
"""CLI utility to chunk markdown KB files and index them into LanceDB."""

import argparse
from pathlib import Path
from typing import Dict, List

from rag.lancedb_store import LanceKBStore


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> List[str]:
    """Chunk long markdown text into overlapping pieces suitable for embeddings."""
    clean = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not clean:
        return []

    paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}".strip()
            continue

        if current:
            chunks.append(current)
        if len(para) <= max_chars:
            current = para
        else:
            start = 0
            while start < len(para):
                end = min(len(para), start + max_chars)
                piece = para[start:end].strip()
                if piece:
                    chunks.append(piece)
                if end >= len(para):
                    break
                start = max(0, end - overlap)
            current = ""

    if current:
        chunks.append(current)
    return chunks


def infer_category(filename: str) -> str:
    """Infer a coarse category from filename to support retrieval filtering."""
    name = filename.lower()
    if "accessibility" in name:
        return "accessibility"
    if "heuristic" in name:
        return "ux"
    if "copy" in name or "conversion" in name:
        return "copywriting"
    if "landing" in name:
        return "landing_page"
    return "general"


def build_documents(kb_dir: Path) -> List[Dict[str, str]]:
    """Convert markdown files into chunk dictionaries with stable snippet ids."""
    docs: List[Dict[str, str]] = []
    for md_file in sorted(kb_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        chunks = chunk_text(content)
        category = infer_category(md_file.name)
        for idx, chunk in enumerate(chunks, start=1):
            docs.append(
                {
                    "snippet_id": f"{md_file.stem}-{idx:03d}",
                    "text": chunk,
                    "source": md_file.name,
                    "category": category,
                    "domain": "landing-page",
                    "platform": "web",
                }
            )
    return docs


def main() -> None:
    """Parse CLI args, index KB content, and print insertion count."""
    parser = argparse.ArgumentParser(description="Index markdown KB into LanceDB")
    parser.add_argument("--kb_dir", default="kb", help="Directory containing KB markdown files")
    parser.add_argument("--db_path", default="lancedb", help="LanceDB directory")
    parser.add_argument("--table", default="kb_chunks", help="LanceDB table name")
    parser.add_argument("--embed_model", default="BAAI/bge-small-en-v1.5", help="Embedding model")
    args = parser.parse_args()

    kb_path = Path(args.kb_dir)
    kb_path.mkdir(parents=True, exist_ok=True)

    store = LanceKBStore(
        db_path=args.db_path,
        table_name=args.table,
        embedding_model=args.embed_model,
    )
    docs = build_documents(kb_path)
    inserted = store.add_documents(docs)
    print(f"Indexed {inserted} chunks from {kb_path}")


if __name__ == "__main__":
    main()
