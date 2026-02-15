from __future__ import annotations
"""HTTP utility helpers used by Streamlit pages to talk to FastAPI endpoints."""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")


def submit_analysis(
    urls: List[str],
    context: Dict[str, Any],
    files: List[Tuple[str, bytes]],
    mode: str = "auto",
) -> Dict[str, Any]:
    """Submit files/URLs/context to POST /analyze."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/analyze"

    multipart_files = []
    for filename, content in files:
        multipart_files.append(("images", (filename, content, "application/octet-stream")))

    payload = {
        "urls": "\n".join(urls),
        "context_json": json.dumps(context),
        "mode": mode,
    }

    response = requests.post(endpoint, data=payload, files=multipart_files, timeout=180)
    response.raise_for_status()
    return response.json()


def get_result(job_id: str) -> Dict[str, Any]:
    """Fetch current status or completed payload from GET /result/{job_id}."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/result/{job_id}"
    response = requests.get(endpoint, timeout=60)
    response.raise_for_status()
    return response.json()


def get_recent_jobs(limit: int = 20) -> Dict[str, Any]:
    """Fetch recent jobs list from API for no-copy Results navigation."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/jobs/recent"
    response = requests.get(endpoint, params={"limit": limit}, timeout=60)
    response.raise_for_status()
    return response.json()


def send_to_n8n(job_id: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Trigger backend helper that forwards a completed report payload to n8n."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/webhook/n8n"
    body = {"job_id": job_id}
    chosen_url = webhook_url or N8N_WEBHOOK_URL
    if chosen_url:
        body["webhook_url"] = chosen_url

    response = requests.post(endpoint, json=body, timeout=60)
    response.raise_for_status()
    return response.json()


def send_email_report(job_id: str, to_email: Optional[str] = None) -> Dict[str, Any]:
    """Send analysis report via email through the FastAPI /send-email endpoint."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/send-email"
    body: Dict[str, Any] = {"job_id": job_id}
    if to_email:
        body["to_email"] = to_email

    response = requests.post(endpoint, json=body, timeout=60)
    response.raise_for_status()
    return response.json()


def create_tickets(job_id: str, providers: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create GitHub/Jira tickets for blocker/high severity issues."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/create-tickets"
    body: Dict[str, Any] = {"job_id": job_id}
    if providers:
        body["providers"] = providers

    response = requests.post(endpoint, json=body, timeout=60)
    response.raise_for_status()
    return response.json()
