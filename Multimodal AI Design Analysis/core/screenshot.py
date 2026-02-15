from __future__ import annotations
"""Playwright screenshot utility used to render public URLs into analysis images."""

import logging
import os
from pathlib import Path
from typing import Dict

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


DEFAULT_VIEWPORT = {"width": 1440, "height": 900}


def _ensure_playwright_browser_path() -> None:
    """Point Playwright to repo-local browser binaries when available.

    This avoids runtime failures when browsers are installed in `./.playwright`
    but Playwright defaults to `~/Library/Caches/ms-playwright`.
    """
    if os.getenv("PLAYWRIGHT_BROWSERS_PATH"):
        return
    local_path = Path(__file__).resolve().parents[1] / ".playwright"
    if local_path.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local_path)
        logger.info("Using local Playwright browser path: %s", local_path)


def capture_fullpage_screenshot(
    url: str,
    screenshot_path: Path,
    timeout_ms: int = 30000,
    viewport: Dict[str, int] | None = None,
) -> Dict[str, str]:
    """Capture a full page screenshot for a public URL."""
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    vp = viewport or DEFAULT_VIEWPORT
    _ensure_playwright_browser_path()

    # Sync Playwright is intentional here; callers must execute this outside async event loops.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=vp)
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
            title = page.title()
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info("Captured screenshot for %s -> %s", url, screenshot_path)
            return {
                "url": url,
                "title": title,
                "screenshot_path": str(screenshot_path),
                "status": "ok",
            }
        except PlaywrightError as exc:
            logger.exception("Playwright failed for %s", url)
            return {
                "url": url,
                "title": "",
                "screenshot_path": str(screenshot_path),
                "status": "error",
                "error": str(exc),
            }
        finally:
            context.close()
            browser.close()
