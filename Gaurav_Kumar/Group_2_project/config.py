"""
config.py
=========
Central configuration hub for the Multi-Agent Deep Researcher.

WHY THIS EXISTS:
    Instead of scattering magic strings and constants across files,
    we put ALL configuration in one place. This means:
    - You change a model name once, it updates everywhere.
    - API keys are loaded safely from .env, never hardcoded.
    - Junior devs can understand the whole system just by reading this file.

USAGE:
    from config import settings
    print(settings.DEFAULT_MODEL)
"""

import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file FIRST, before anything else tries to read env vars
load_dotenv()

# ─────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Available Models on OpenRouter
# ─────────────────────────────────────────────
AVAILABLE_MODELS: dict[str, str] = {
    "GPT-4o Mini (Fast)":               "openai/gpt-4o-mini",
    "Gemini 2.0 Flash (Free)":          "google/gemini-2.0-flash-exp:free",
    "DeepSeek V3 (Free)":               "deepseek/deepseek-chat:free",
    "Llama 3.1 8B (Free)":              "meta-llama/llama-3.1-8b-instruct:free",
    "Qwen 2.5 72B (Free)":              "qwen/qwen-2.5-72b-instruct:free",
    "Claude 3.5 Haiku (Cheapest)":      "anthropic/claude-3.5-haiku",
    "Claude 3.5 Sonnet (Balanced)":     "anthropic/claude-3.5-sonnet",
}


@dataclass
class Settings:
    """
    All application settings, loaded from environment variables.

    Attributes:
        OPENROUTER_API_KEY: API key for OpenRouter LLM access.
        TAVILY_API_KEY: API key for Tavily web search.
        DEFAULT_MODEL: OpenRouter model string to use by default.
        OPENROUTER_BASE_URL: Base URL for OpenRouter's OpenAI-compatible API.
        MAX_SEARCH_RESULTS: How many web results to fetch per query.
        MAX_TOKENS: Max tokens for each LLM response.
        TEMPERATURE: LLM temperature (0 = deterministic, 1 = creative).
        REQUEST_TIMEOUT: Seconds before an LLM/API call times out.
        DEBUG_LLM: If True, log full LLM prompts and responses.
        CHROMA_PERSIST_DIR: Where ChromaDB stores its files.
        PDF_OUTPUT_DIR: Where generated PDFs are saved.
        MAX_ITERATIONS: Max reflection loop iterations.
        QUALITY_THRESHOLD: Minimum quality score (0-100) to accept report.
        MAX_SUB_QUERIES: Max sub-queries the decomposer can generate.
    """

    # ── API Keys (loaded from .env) ──────────────────────────
    OPENROUTER_API_KEY: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    TAVILY_API_KEY: str = field(
        default_factory=lambda: os.getenv("TAVILY_API_KEY", "")
    )

    # ── LLM Settings ─────────────────────────────────────────
    DEFAULT_MODEL: str = field(
        default_factory=lambda: os.getenv(
            "DEFAULT_MODEL", "google/gemini-2.0-flash-exp:free"
        )
    )
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.2
    REQUEST_TIMEOUT: int = 90

    # ── Search Settings ──────────────────────────────────────
    MAX_SEARCH_RESULTS: int = 6

    # ── Orchestration Settings ───────────────────────────────
    MAX_ITERATIONS: int = 2          # Max reflection loops
    QUALITY_THRESHOLD: float = 65.0  # Min quality to accept (0-100)
    MAX_SUB_QUERIES: int = 5         # Max decomposed sub-queries

    # ── Debug Settings ───────────────────────────────────────
    DEBUG_LLM: bool = field(
        default_factory=lambda: os.getenv("DEBUG_LLM", "false").lower() == "true"
    )

    # ── Storage Paths ────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = ".chroma"
    PDF_OUTPUT_DIR: str = "outputs"

    # ── Available Models (for UI dropdown) ───────────────────
    AVAILABLE_MODELS: dict = field(default_factory=lambda: AVAILABLE_MODELS)

    def validate(self) -> None:
        """
        Check that required API keys are present.

        Raises:
            ValueError: If any required API key is missing.
        """
        missing: list[str] = []
        if not self.OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY")
        if not self.TAVILY_API_KEY:
            missing.append("TAVILY_API_KEY")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please copy .env.example to .env and fill in your API keys."
            )

    def __post_init__(self) -> None:
        """Create output directories if they don't exist."""
        os.makedirs(self.PDF_OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)
        logger.info("Configuration loaded successfully.")


# ─────────────────────────────────────────────
# Singleton Settings Instance
# ─────────────────────────────────────────────
settings = Settings()
