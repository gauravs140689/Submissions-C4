from __future__ import annotations
"""Filesystem helpers for per-job artifacts and lightweight job status tracking."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

RUNS_ROOT = Path(os.getenv("RUNS_DIR", "runs"))


def ensure_dir(path: Path) -> Path:
    """Create directory if missing and return the same path for fluent usage."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_runs_root() -> Path:
    return ensure_dir(RUNS_ROOT)


def get_job_dir(job_id: str) -> Path:
    return ensure_dir(ensure_runs_root() / job_id)


def get_job_subdir(job_id: str, name: str) -> Path:
    return ensure_dir(get_job_dir(job_id) / name)


def init_job_dirs(job_id: str) -> Dict[str, Path]:
    """Create the standard runs/{job_id} sub-folder structure used by the pipeline."""
    base = get_job_dir(job_id)
    paths = {
        "base": base,
        "inputs": ensure_dir(base / "inputs"),
        "screenshots": ensure_dir(base / "screenshots"),
        "signals": ensure_dir(base / "signals"),
        "outputs": ensure_dir(base / "outputs"),
        "ticket_payloads": ensure_dir(base / "ticket_payloads"),
    }
    return paths


def status_path(job_id: str) -> Path:
    return get_job_dir(job_id) / "job_status.json"


def set_job_status(job_id: str, status: str, detail: Optional[str] = None) -> None:
    """Write current job status so UI/API polling can reflect pipeline progress."""
    payload = {
        "job_id": job_id,
        "status": status,
        "detail": detail,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json(status_path(job_id), payload)


def get_job_status(job_id: str) -> Dict[str, Any]:
    """Return last-known status; missing jobs return a synthetic 'missing' status."""
    path = status_path(job_id)
    if not path.exists():
        return {"job_id": job_id, "status": "missing", "detail": None}
    return load_json(path)


def list_recent_jobs(limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent jobs from runs/ sorted by status update time descending."""
    ensure_runs_root()
    jobs: List[Dict[str, Any]] = []

    for job_dir in RUNS_ROOT.iterdir():
        if not job_dir.is_dir():
            continue
        job_id = job_dir.name
        status = get_job_status(job_id)
        updated_at = status.get("updated_at")
        if not updated_at:
            # Fall back to filesystem timestamp if status file is missing.
            updated_at = datetime.fromtimestamp(job_dir.stat().st_mtime, tz=timezone.utc).isoformat()
        jobs.append(
            {
                "job_id": job_id,
                "status": status.get("status", "unknown"),
                "detail": status.get("detail"),
                "updated_at": updated_at,
            }
        )

    jobs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return jobs[: max(1, limit)]


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    """Persist JSON with consistent indentation and ASCII-safe encoding."""
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def output_path(job_id: str, filename: str) -> Path:
    """Build path to runs/{job_id}/outputs/{filename}."""
    return get_job_subdir(job_id, "outputs") / filename


def signal_path(job_id: str, source_id: str) -> Path:
    return get_job_subdir(job_id, "signals") / f"{source_id}.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
