from __future__ import annotations
"""Model wrappers used by agents for multimodal reasoning and tracing configuration."""

import base64
from functools import lru_cache
import logging
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


@dataclass
class VisionResult:
    """Normalized response shape from model wrapper to downstream agents."""
    summary: str
    model_id: str
    mode: str


class MultimodalModelWrapper:
    """Unified wrapper for vision analysis through OpenRouter with graceful fallbacks."""

    def __init__(self) -> None:
        # Keep old MM_* env names as compatibility fallback for existing setups.
        self.primary_model_id = os.getenv("OR_PRIMARY_MODEL") or os.getenv("MM_MODEL_ID") or "openai/gpt-4.1-mini"
        self.secondary_model_id = (
            os.getenv("OR_SECONDARY_MODEL") or os.getenv("MM_FALLBACK_MODEL_ID") or "google/gemini-2.5-flash"
        )
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        self.timeout_seconds = int(os.getenv("OR_TIMEOUT_SECONDS", "90"))
        self.max_tokens = int(os.getenv("OR_MAX_TOKENS", "300"))
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost")
        self.app_title = os.getenv("OPENROUTER_APP_TITLE", "Multimodal AI Design Analysis Suite")
        self.mode = "openrouter"

        if self.api_key:
            logger.info(
                "OpenRouter multimodal wrapper active (primary=%s, secondary=%s)",
                self.primary_model_id,
                self.secondary_model_id,
            )
        else:
            logger.warning("OPENROUTER_API_KEY missing; vision model path disabled and OCR/text fallback will be used.")

    def _headers(self) -> Dict[str, str]:
        """Build OpenRouter headers, including optional attribution headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.http_referer,
            "X-Title": self.app_title,
        }

    def _image_as_data_url(self, image_path: str) -> Optional[str]:
        """Encode local image into a data URL accepted by vision chat-completions APIs."""
        path = Path(image_path)
        if not path.exists():
            return None
        mime, _ = mimetypes.guess_type(path.name)
        mime = mime or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"

    def _extract_content(self, payload: Dict[str, object]) -> str:
        """Normalize OpenRouter response content across string/list formats."""
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content") if isinstance(message, dict) else ""
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if isinstance(text, str):
                        parts.append(text.strip())
            return " ".join(part for part in parts if part).strip()
        return ""

    def _call_model(self, model_id: str, prompt: str, image_data_url: str) -> str:
        """Call OpenRouter chat completion for image+text analysis."""
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return self._extract_content(response.json())

    def analyze(self, image_path: str, prompt: str) -> VisionResult:
        """Run image analysis with primary/fallback OpenRouter models."""
        if not self.api_key:
            return VisionResult(
                summary="OPENROUTER_API_KEY missing; using OCR/text-only critique.",
                model_id="none",
                mode="disabled",
            )
        image_data_url = self._image_as_data_url(image_path)
        if not image_data_url:
            return VisionResult(
                summary="Image unavailable for vision model; using OCR/text-only critique.",
                model_id="none",
                mode="disabled",
            )

        try:
            primary = self._call_model(self.primary_model_id, prompt, image_data_url)
            if primary:
                return VisionResult(summary=primary, model_id=self.primary_model_id, mode="openrouter-primary")
            raise ValueError("Primary model returned empty content.")
        except Exception as exc:
            logger.warning("Primary OpenRouter model failed (%s): %s", self.primary_model_id, exc)

        try:
            secondary = self._call_model(self.secondary_model_id, prompt, image_data_url)
            if secondary:
                return VisionResult(summary=secondary, model_id=self.secondary_model_id, mode="openrouter-secondary")
            raise ValueError("Secondary model returned empty content.")
        except Exception as exc:
            logger.warning("Secondary OpenRouter model failed (%s): %s", self.secondary_model_id, exc)
            return VisionResult(
                summary="Vision inference failed on primary and secondary models; used OCR/text fallback.",
                model_id="none",
                mode="fallback",
            )


def get_langsmith_config() -> Dict[str, str]:
    """Enable LangSmith tracing only when API key is configured."""
    if os.getenv("LANGSMITH_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_PROJECT", "multimodal-design-suite")
        return {
            "enabled": "true",
            "project": os.getenv("LANGCHAIN_PROJECT", "multimodal-design-suite"),
        }
    return {"enabled": "false"}


@lru_cache(maxsize=1)
def get_model_wrapper() -> MultimodalModelWrapper:
    """Process-level singleton wrapper to avoid reloading large model artifacts per request."""
    return MultimodalModelWrapper()
