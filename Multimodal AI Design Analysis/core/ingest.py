from __future__ import annotations
"""Input ingestion for uploads and URLs, including screenshot capture and manifest creation."""

import io
import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from PIL import Image

from core.screenshot import capture_fullpage_screenshot
from core.storage import get_job_subdir, init_job_dirs, save_json

logger = logging.getLogger(__name__)


def parse_urls(raw_urls: str | Sequence[str] | None) -> List[str]:
    """Accept comma/newline/space separated URL text and return a de-duplicated list."""
    if raw_urls is None:
        return []
    if isinstance(raw_urls, str):
        tokens = re.split(r"[\n,\s]+", raw_urls.strip())
    else:
        tokens = []
        for item in raw_urls:
            tokens.extend(re.split(r"[\n,\s]+", str(item).strip()))
    cleaned = [u for u in (t.strip() for t in tokens) if u]
    deduped: List[str] = []
    seen = set()
    for u in cleaned:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def _save_uploaded_image(job_id: str, source_id: str, filename: str, content: bytes) -> Dict[str, Any]:
    """Persist one uploaded image to runs/{job_id}/inputs."""
    ext = Path(filename).suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg"}:
        ext = ".png"

    inputs_dir = get_job_subdir(job_id, "inputs")
    dest = inputs_dir / f"{source_id}{ext}"

    image = Image.open(io.BytesIO(content)).convert("RGB")
    image.save(dest)

    return {
        "source_id": source_id,
        "source_type": "upload",
        "source_ref": filename,
        "image_path": str(dest),
    }


def _save_url_screenshot(job_id: str, source_id: str, url: str) -> Dict[str, Any]:
    """Capture and persist one URL screenshot to runs/{job_id}/screenshots."""
    shots_dir = get_job_subdir(job_id, "screenshots")
    dest = shots_dir / f"{source_id}.png"

    meta = capture_fullpage_screenshot(url=url, screenshot_path=dest)
    return {
        "source_id": source_id,
        "source_type": "url",
        "source_ref": url,
        "image_path": meta.get("screenshot_path", str(dest)),
        "capture_status": meta.get("status", "error"),
        "capture_error": meta.get("error"),
        "title": meta.get("title", ""),
    }


def ingest_assets(
    job_id: str,
    uploaded_images: Iterable[Tuple[str, bytes]] | None,
    urls: Sequence[str] | None,
    context: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Create job folders, ingest all assets, and write a normalized input manifest."""
    init_job_dirs(job_id)
    items: List[Dict[str, Any]] = []

    if uploaded_images:
        for idx, (filename, content) in enumerate(uploaded_images, start=1):
            source_id = f"upload_{idx:03d}"
            try:
                items.append(_save_uploaded_image(job_id, source_id, filename, content))
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to ingest image %s", filename)
                items.append(
                    {
                        "source_id": source_id,
                        "source_type": "upload",
                        "source_ref": filename,
                        "image_path": "",
                        "capture_status": "error",
                        "capture_error": str(exc),
                    }
                )

    if urls:
        start = len(items) + 1
        for idx, url in enumerate(urls, start=start):
            source_id = f"url_{idx:03d}"
            items.append(_save_url_screenshot(job_id, source_id, url))

    manifest = {
        "job_id": job_id,
        "context": context or {},
        "items": items,
    }
    save_json(get_job_subdir(job_id, "inputs") / "manifest.json", manifest)
    return items
