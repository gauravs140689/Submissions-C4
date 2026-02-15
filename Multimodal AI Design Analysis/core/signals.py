from __future__ import annotations
"""Signal extraction from images: OCR, CTA heuristics, sections, palette, and contrast warnings."""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from api.schemas import CTAItem, OCRBlock, PaletteItem, SignalOutput
from core.storage import save_json, signal_path

logger = logging.getLogger(__name__)


CTA_PATTERNS = [
    r"\b(get started|start free|book demo|try now|learn more|contact sales|sign up|join now|buy now)\b",
    r"\b(request demo|talk to sales|schedule|subscribe|download)\b",
]

CLAIM_HINTS = {
    "increase",
    "faster",
    "reduce",
    "boost",
    "trusted",
    "save",
    "roi",
    "grow",
    "improve",
    "secure",
}


def _load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def _run_ocr(image: Image.Image) -> List[OCRBlock]:
    """Extract text blocks with bbox/confidence; returns empty list if OCR is unavailable."""
    try:
        import pytesseract

        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        blocks: List[OCRBlock] = []
        n = len(data.get("text", []))
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            conf_raw = data.get("conf", ["-1"] * n)[i]
            try:
                conf_val = float(conf_raw)
            except Exception:
                conf_val = -1.0

            bbox = [
                int(data["left"][i]),
                int(data["top"][i]),
                int(data["width"][i]),
                int(data["height"][i]),
            ]
            blocks.append(
                OCRBlock(
                    text=text,
                    bbox=bbox,
                    confidence=None if conf_val < 0 else max(0.0, min(1.0, conf_val / 100.0)),
                )
            )
        return blocks
    except Exception as exc:
        logger.warning("OCR failed; continuing without OCR blocks: %s", exc)
        return []


def _dominant_palette(image: Image.Image, k: int = 5) -> List[PaletteItem]:
    """Estimate dominant colors using k-means (with a simple fallback path)."""
    arr = np.array(image)
    pixels = arr.reshape(-1, 3)

    if len(pixels) > 12000:
        idx = np.random.choice(len(pixels), 12000, replace=False)
        pixels = pixels[idx]

    try:
        from sklearn.cluster import KMeans

        model = KMeans(n_clusters=min(k, len(pixels)), random_state=42, n_init=10)
        labels = model.fit_predict(pixels)
        counts = Counter(labels)
        total = sum(counts.values())

        palette: List[PaletteItem] = []
        for label, count in counts.most_common(k):
            rgb = model.cluster_centers_[label].astype(int).tolist()
            hex_color = "#%02x%02x%02x" % tuple(rgb)
            palette.append(PaletteItem(hex=hex_color, ratio=count / total))
        return palette
    except Exception as exc:
        logger.warning("Palette extraction fallback due to: %s", exc)
        sampled = pixels[:: max(1, len(pixels) // 5)][:5]
        total = max(1, len(sampled))
        return [
            PaletteItem(hex="#%02x%02x%02x" % tuple(color.tolist()), ratio=1.0 / total)
            for color in sampled
        ]


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _luminance(rgb: Tuple[int, int, int]) -> float:
    vals = []
    for channel in rgb:
        c = channel / 255.0
        vals.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def _contrast_ratio(c1: str, c2: str) -> float:
    l1 = _luminance(_hex_to_rgb(c1))
    l2 = _luminance(_hex_to_rgb(c2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _contrast_warnings(palette: List[PaletteItem]) -> List[str]:
    """Generate approximate contrast warnings from dominant color pairs."""
    warnings: List[str] = []
    colors = [p.hex for p in palette[:4]]
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            ratio = _contrast_ratio(colors[i], colors[j])
            if ratio < 4.5:
                warnings.append(
                    f"Low approximate contrast between {colors[i]} and {colors[j]} (ratio {ratio:.2f})"
                )
    return warnings[:6]


def _detected_ctas(blocks: List[OCRBlock]) -> List[CTAItem]:
    """Find CTA-like text snippets using regex patterns over OCR text."""
    ctas: List[CTAItem] = []
    for block in blocks:
        text = block.text.lower()
        for pattern in CTA_PATTERNS:
            if re.search(pattern, text):
                ctas.append(
                    CTAItem(
                        text=block.text,
                        bbox=block.bbox,
                        type="primary" if any(x in text for x in ["start", "book", "buy", "sign"]) else "secondary",
                        confidence=block.confidence or 0.6,
                    )
                )
                break
    return ctas[:10]


def _sections_from_blocks(blocks: List[OCRBlock], image_height: int) -> List[str]:
    """Infer coarse page sections from OCR vertical position heuristics."""
    if not blocks or image_height <= 0:
        return ["hero", "content", "footer"]

    top_text = [b.text for b in blocks if b.bbox and b.bbox[1] <= image_height * 0.25]
    mid_text = [
        b.text
        for b in blocks
        if b.bbox and image_height * 0.25 < b.bbox[1] <= image_height * 0.8
    ]
    bottom_text = [b.text for b in blocks if b.bbox and b.bbox[1] > image_height * 0.8]

    sections = []
    if top_text:
        sections.append("hero")
        if any(re.search(r"\b(home|pricing|features|about|login|sign in)\b", t.lower()) for t in top_text):
            sections.append("nav")
    if mid_text:
        sections.append("content")
        if any(re.search(r"\b(form|email|name|submit|trial)\b", t.lower()) for t in mid_text):
            sections.append("form")
    if bottom_text:
        sections.append("footer")

    if not sections:
        sections = ["hero", "content"]
    return sorted(list(dict.fromkeys(sections)))


def _key_claims(blocks: List[OCRBlock]) -> List[str]:
    """Extract marketing-claim style phrases from OCR text."""
    claims: List[str] = []
    for block in blocks:
        text = block.text.strip()
        if len(text) < 8:
            continue
        words = {w.strip(".,!?").lower() for w in text.split()}
        if words & CLAIM_HINTS:
            claims.append(text)
    return claims[:8]


def _nav_items(blocks: List[OCRBlock], image_height: int) -> List[str]:
    """Approximate top navigation labels by limiting OCR to top area and short text lengths."""
    nav = []
    for block in blocks:
        if not block.bbox:
            continue
        y = block.bbox[1]
        if y > image_height * 0.2:
            continue
        text = block.text.strip()
        if 2 <= len(text) <= 20:
            nav.append(text)
    deduped = []
    seen = set()
    for item in nav:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped[:12]


def extract_signals_for_source(job_id: str, source: Dict[str, Any]) -> SignalOutput:
    """Produce and persist a SignalOutput payload for one source item."""
    image_path = source.get("image_path", "")
    source_id = source.get("source_id", "unknown")

    if not image_path or not Path(image_path).exists():
        # Keep schema stable even when a source could not be captured.
        output = SignalOutput(
            source_id=source_id,
            source_type=source.get("source_type", "upload"),
            source_ref=source.get("source_ref", ""),
            image_path=image_path,
            ocr_text_blocks=[],
            page_sections=[],
            detected_ctas=[],
            palette=[],
            contrast_warnings=["Image was unavailable for analysis"],
            key_claims=[],
            nav_items=[],
        )
        save_json(signal_path(job_id, source_id), output.model_dump())
        return output

    image = _load_image(image_path)
    width, height = image.size
    blocks = _run_ocr(image)
    palette = _dominant_palette(image)

    output = SignalOutput(
        source_id=source_id,
        source_type=source.get("source_type", "upload"),
        source_ref=source.get("source_ref", ""),
        image_path=image_path,
        ocr_text_blocks=blocks,
        page_sections=_sections_from_blocks(blocks, image_height=height),
        detected_ctas=_detected_ctas(blocks),
        palette=palette,
        contrast_warnings=_contrast_warnings(palette),
        key_claims=_key_claims(blocks),
        nav_items=_nav_items(blocks, image_height=height),
    )

    payload = output.model_dump()
    # Helpful metadata for debugging extraction quality.
    payload["image_size"] = {"width": width, "height": height}
    save_json(signal_path(job_id, source_id), payload)
    return output


def extract_signals_batch(job_id: str, sources: List[Dict[str, Any]]) -> List[SignalOutput]:
    """Run signal extraction sequentially for all ingested sources."""
    return [extract_signals_for_source(job_id, source) for source in sources]
