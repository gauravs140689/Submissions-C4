from __future__ import annotations
"""FastAPI entrypoint for analysis jobs, result polling, and n8n webhook delivery."""

import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

from agents.graph import run_analysis_pipeline
from api.schemas import AnalyzeResponse, ResultResponse, WebhookRequest
from api.tickets import create_github_issues, create_jira_issues
from core.ingest import parse_urls
from core.storage import get_job_status, list_recent_jobs, output_path, set_job_status

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Single API app used by both Streamlit and n8n.
app = FastAPI(title="Multimodal AI Design Analysis Suite API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_context(context_json: Optional[str]) -> Dict[str, Any]:
    """Parse optional JSON context from multipart forms into a dict."""
    if not context_json:
        return {}
    try:
        return json.loads(context_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid context_json: {exc}") from exc


def _load_result_files(job_id: str) -> Dict[str, Any]:
    """Load persisted output artifacts for a completed job."""
    report_json_path = output_path(job_id, "report.json")
    report_md_path = output_path(job_id, "report.md")
    action_items_path = output_path(job_id, "action_items.json")

    if not report_json_path.exists():
        raise FileNotFoundError("report.json not found")

    report = json.loads(report_json_path.read_text(encoding="utf-8"))
    report_md = report_md_path.read_text(encoding="utf-8") if report_md_path.exists() else ""
    action_payload = json.loads(action_items_path.read_text(encoding="utf-8")) if action_items_path.exists() else {}
    action_items = action_payload.get("action_items", [])

    return {"report": report, "report_md": report_md, "action_items": action_items}


def _run_job(job_id: str, urls: List[str], uploaded_images: List[Dict[str, Any]], context: Dict[str, Any]) -> None:
    """Run the full pipeline and persist failure details in job status if it errors."""
    try:
        run_analysis_pipeline(job_id=job_id, urls=urls, uploaded_images=uploaded_images, context=context)
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Job %s failed", job_id)
        set_job_status(job_id, "failed", detail=str(exc))


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs/recent")
def jobs_recent(limit: int = 20) -> Dict[str, Any]:
    """List recently updated jobs so UI can offer click-to-open history."""
    safe_limit = max(1, min(limit, 100))
    return {"jobs": list_recent_jobs(limit=safe_limit)}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    background_tasks: BackgroundTasks,
    urls: Optional[str] = Form(default=None),
    context_json: Optional[str] = Form(default=None),
    mode: str = Form(default="auto"),
    images: List[UploadFile] = File(default=[]),
):
    # Normalize all incoming user inputs into one request payload.
    url_list = parse_urls(urls)
    context = _parse_context(context_json)

    uploads: List[Dict[str, Any]] = []
    for file in images:
        content = await file.read()
        uploads.append({"filename": file.filename or "upload.png", "content": content})

    if not url_list and not uploads:
        raise HTTPException(status_code=400, detail="Provide at least one image or URL")

    job_id = str(uuid4())
    total_inputs = len(url_list) + len(uploads)

    chosen_mode = mode
    if chosen_mode not in {"auto", "sync", "async"}:
        raise HTTPException(status_code=400, detail="mode must be one of: auto, sync, async")

    if chosen_mode == "auto":
        # Small jobs are faster to run inline; larger jobs are queued in background.
        chosen_mode = "sync" if total_inputs <= 2 else "async"

    if chosen_mode == "sync":
        # Run in threadpool so sync Playwright code does not execute inside the async event loop.
        set_job_status(job_id, "queued", detail="Running synchronously")
        await run_in_threadpool(_run_job, job_id, url_list, uploads, context)
        status = get_job_status(job_id).get("status", "failed")
        return AnalyzeResponse(
            job_id=job_id,
            status=status if status in {"completed", "failed"} else "completed",
            mode="sync",
            result_available=status == "completed",
            detail=get_job_status(job_id).get("detail"),
        )

    set_job_status(job_id, "queued", detail="Queued for background execution")
    # FastAPI will execute this after returning HTTP response.
    background_tasks.add_task(_run_job, job_id, url_list, uploads, context)

    return AnalyzeResponse(
        job_id=job_id,
        status="queued",
        mode="async",
        result_available=False,
        detail="Use GET /result/{job_id} to poll",
    )


@app.get("/result/{job_id}", response_model=ResultResponse)
def result(job_id: str):
    """Poll current state, and return report payload once completed."""
    status_payload = get_job_status(job_id)
    status = status_payload.get("status", "missing")

    if status == "missing":
        return ResultResponse(job_id=job_id, status="missing", error="job_id not found")

    if status in {"queued", "running"}:
        return ResultResponse(job_id=job_id, status=status, error=status_payload.get("detail"))

    if status == "failed":
        return ResultResponse(job_id=job_id, status="failed", error=status_payload.get("detail"))

    try:
        result_payload = _load_result_files(job_id)
    except Exception as exc:
        return ResultResponse(job_id=job_id, status="failed", error=str(exc))

    return ResultResponse(
        job_id=job_id,
        status="completed",
        report=result_payload["report"],
        report_md=result_payload["report_md"],
        action_items=result_payload["action_items"],
    )


class EmailRequest(BaseModel):
    job_id: str
    to_email: Optional[str] = None


def _build_email_body(job_id: str, result_payload: Dict[str, Any]) -> str:
    """Build a readable plain-text email body from analysis results."""
    report = result_payload.get("report", {})
    snapshot = report.get("executive_snapshot", {})
    action_items = result_payload.get("action_items", [])

    headline = snapshot.get("headline", "Analysis complete")
    score = snapshot.get("heuristic_score", "N/A")
    confidence = snapshot.get("confidence_score", "N/A")
    strengths = "\n".join(f"  ✅ {s}" for s in snapshot.get("top_strengths", []))
    improvements = "\n".join(f"  ⚠️ {s}" for s in snapshot.get("top_improvements", []))
    top5 = "\n".join(
        f"  {i+1}. [{(item.get('severity','') ).upper()}] {item.get('title','Untitled')}"
        for i, item in enumerate(action_items[:5])
    )

    return (
        f"Design Analysis Report\n"
        f"========================\n\n"
        f"Job ID: {job_id}\n"
        f"Score: {score}/10 (Confidence: {confidence}/10)\n"
        f"{headline}\n\n"
        f"--- Top 5 Issues ---\n{top5 or '  No issues detected'}\n\n"
        f"--- Strengths ---\n{strengths or '  None detected'}\n\n"
        f"--- Improvements Needed ---\n{improvements or '  None detected'}\n\n"
        f"Total issues found: {len(action_items)}\n"
        f"---\nGenerated by Multimodal AI Design Analysis Suite"
    )


@app.post("/send-email")
def send_email(payload: EmailRequest):
    """Send the analysis report via email using SMTP (Gmail)."""
    status = get_job_status(payload.job_id).get("status")
    if status != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {status}")

    result_payload = _load_result_files(payload.job_id)

    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    from_email = os.getenv("EMAIL_FROM", smtp_user)
    to_email = payload.to_email or os.getenv("REPORT_EMAIL_TO", from_email)

    if not smtp_user or not smtp_pass:
        raise HTTPException(status_code=500, detail="SMTP credentials not configured. Set SMTP_USER and SMTP_PASS in .env")

    report = result_payload.get("report", {})
    snapshot = report.get("executive_snapshot", {})
    score = snapshot.get("heuristic_score", "N/A")
    subject = f"Design Analysis Report - {score}/10 - Job {payload.job_id[:8]}"

    body_text = _build_email_body(payload.job_id, result_payload)
    report_md = result_payload.get("report_md", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    if report_md:
        msg.attach(MIMEText(f"<pre>{report_md}</pre>", "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
        return {"status": "sent", "job_id": payload.job_id, "to_email": to_email}
    except smtplib.SMTPException as exc:
        raise HTTPException(status_code=502, detail=f"SMTP error: {exc}") from exc


class TicketRequest(BaseModel):
    job_id: str
    providers: List[str] = ["github", "jira"]  # which providers to create tickets on


@app.post("/create-tickets")
def create_tickets(payload: TicketRequest):
    """Create GitHub/Jira tickets for blocker/high severity issues from a completed job."""
    status = get_job_status(payload.job_id).get("status")
    if status != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {status}")

    result_payload = _load_result_files(payload.job_id)
    action_items = result_payload.get("action_items", [])
    results: Dict[str, Any] = {"job_id": payload.job_id}

    if "github" in payload.providers:
        results["github"] = create_github_issues(action_items, payload.job_id)

    if "jira" in payload.providers:
        results["jira"] = create_jira_issues(action_items, payload.job_id)

    return results


@app.post("/webhook/n8n")
def webhook_n8n(payload: WebhookRequest):
    """Push completed report payload to a caller-provided or env-configured n8n webhook."""
    status = get_job_status(payload.job_id).get("status")
    if status != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed. Current status: {status}")

    result_payload = _load_result_files(payload.job_id)
    webhook_url = str(payload.webhook_url) if payload.webhook_url else os.getenv("N8N_WEBHOOK_URL")
    if not webhook_url:
        return {
            "status": "skipped",
            "reason": "No webhook URL set. Provide webhook_url or N8N_WEBHOOK_URL env.",
            "job_id": payload.job_id,
        }

    body = {
        "job_id": payload.job_id,
        "report": result_payload["report"],
        "report_md": result_payload["report_md"],
        "action_items": result_payload["action_items"],
    }

    try:
        response = requests.post(webhook_url, json=body, timeout=60)
        response.raise_for_status()
        # n8n responds with the workflow output (email + ticket results)
        try:
            n8n_body = response.json()
        except Exception:
            n8n_body = {}
        return {
            "status": "sent",
            "job_id": payload.job_id,
            "webhook_url": webhook_url,
            "response_status": response.status_code,
            "n8n_response": n8n_body,
        }
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Failed to call n8n webhook: {exc}") from exc
