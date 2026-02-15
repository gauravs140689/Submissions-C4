from __future__ import annotations
"""GitHub and Jira ticket creation helpers for blocker/high severity design issues."""

import logging
import os
from base64 import b64encode
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SEVERITY_LABELS = {"blocker", "high"}


def _filter_high_severity(action_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return only blocker/high severity issues worth creating tickets for."""
    return [
        item for item in action_items
        if (item.get("severity", "").lower()) in SEVERITY_LABELS
    ]


def _issue_body(item: Dict[str, Any], job_id: str) -> str:
    """Build a markdown body for a single issue ticket."""
    return (
        f"**Severity:** {item.get('severity', 'N/A')}\n"
        f"**Component:** {item.get('component', 'N/A')}\n"
        f"**Impact:** {item.get('impact', 'N/A')}\n"
        f"**Confidence:** {item.get('confidence', 'N/A')}\n\n"
        f"## Issue\n{item.get('issue', item.get('title', ''))}\n\n"
        f"## Evidence\n{item.get('evidence', 'N/A')}\n\n"
        f"## Principle\n{item.get('principle', 'N/A')}\n\n"
        f"## Suggested Fix\n{item.get('fix', 'N/A')}\n\n"
        f"## Acceptance Criteria\n"
        + "\n".join(f"- {ac}" for ac in item.get("acceptance_criteria", []))
        + f"\n\n---\n*Auto-generated from job `{job_id}` by Design Analysis Suite*"
    )


# ── GitHub ────────────────────────────────────────────────────────────────────

def create_github_issues(
    action_items: List[Dict[str, Any]],
    job_id: str,
    repo: str | None = None,
    token: str | None = None,
) -> Dict[str, Any]:
    """Create GitHub issues for blocker/high severity items. Returns summary."""
    repo = repo or os.getenv("GITHUB_REPO", "")
    token = token or os.getenv("GITHUB_TOKEN", "")
    if not repo or not token:
        return {"status": "skipped", "reason": "GITHUB_REPO or GITHUB_TOKEN not set"}

    high_items = _filter_high_severity(action_items)
    if not high_items:
        return {"status": "ok", "created": 0, "message": "No blocker/high issues to file"}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    created: List[Dict[str, Any]] = []
    errors: List[str] = []

    for item in high_items:
        title = f"[{item.get('severity', '').upper()}] {item.get('title', 'Design Issue')}"
        body = _issue_body(item, job_id)
        labels = [
            f"severity:{item.get('severity', 'high')}",
            f"component:{item.get('component', 'general')}",
            "design-analysis",
        ]
        payload = {"title": title, "body": body, "labels": labels}

        try:
            resp = requests.post(
                f"https://api.github.com/repos/{repo}/issues",
                json=payload, headers=headers, timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            created.append({"number": data["number"], "url": data["html_url"], "title": title})
        except requests.RequestException as exc:
            errors.append(f"{title}: {exc}")

    return {
        "status": "ok" if not errors else "partial",
        "created": len(created),
        "issues": created,
        "errors": errors,
    }


# ── Jira ──────────────────────────────────────────────────────────────────────

_SEVERITY_TO_PRIORITY = {"blocker": "Highest", "high": "High"}


def create_jira_issues(
    action_items: List[Dict[str, Any]],
    job_id: str,
    jira_url: str | None = None,
    jira_email: str | None = None,
    jira_token: str | None = None,
    project_key: str | None = None,
) -> Dict[str, Any]:
    """Create Jira bugs for blocker/high severity items. Returns summary."""
    jira_url = (jira_url or os.getenv("JIRA_URL", "")).rstrip("/")
    jira_email = jira_email or os.getenv("JIRA_EMAIL", "")
    jira_token = jira_token or os.getenv("JIRA_API_TOKEN", "")
    project_key = project_key or os.getenv("JIRA_PROJECT_KEY", "")

    if not all([jira_url, jira_email, jira_token, project_key]):
        return {"status": "skipped", "reason": "Jira credentials not fully configured"}

    high_items = _filter_high_severity(action_items)
    if not high_items:
        return {"status": "ok", "created": 0, "message": "No blocker/high issues to file"}

    auth = b64encode(f"{jira_email}:{jira_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
    }
    created: List[Dict[str, Any]] = []
    errors: List[str] = []

    for item in high_items:
        summary = f"[{item.get('severity', '').upper()}] {item.get('title', 'Design Issue')}"
        description = (
            f"*Severity:* {item.get('severity', 'N/A')}\n"
            f"*Component:* {item.get('component', 'N/A')}\n"
            f"*Impact:* {item.get('impact', 'N/A')}\n\n"
            f"h3. Issue\n{item.get('issue', item.get('title', ''))}\n\n"
            f"h3. Evidence\n{item.get('evidence', 'N/A')}\n\n"
            f"h3. Suggested Fix\n{item.get('fix', 'N/A')}\n\n"
            f"h3. Acceptance Criteria\n"
            + "\n".join(f"* {ac}" for ac in item.get("acceptance_criteria", []))
            + f"\n\n----\n_Auto-generated from job {job_id}_"
        )

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": "Bug"},
                "labels": ["design-analysis", item.get("component", "general")],
            }
        }

        try:
            resp = requests.post(
                f"{jira_url}/rest/api/3/issue",
                json=payload, headers=headers, timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            issue_key = data.get("key", "")
            created.append({
                "key": issue_key,
                "url": f"{jira_url}/browse/{issue_key}",
                "summary": summary,
            })
        except requests.RequestException as exc:
            errors.append(f"{summary}: {exc}")

    return {
        "status": "ok" if not errors else "partial",
        "created": len(created),
        "issues": created,
        "errors": errors,
    }
