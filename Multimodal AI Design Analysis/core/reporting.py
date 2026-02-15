from __future__ import annotations
"""Report composition utilities: sorting, markdown rendering, persistence, and ticket payload shaping."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from api.schemas import ExecutiveSnapshot, Issue, Report, validate_report_payload
from core.storage import get_job_subdir, output_path, save_json, save_text

SEVERITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
IMPACT_ORDER = {"conversion": 0, "trust": 1, "clarity": 2, "a11y": 3}


def sort_issues(issues: List[Issue]) -> List[Issue]:
    """Sort by severity first, then impact, then title for deterministic ordering."""
    return sorted(
        issues,
        key=lambda issue: (
            SEVERITY_ORDER.get(issue.severity.value, 99),
            IMPACT_ORDER.get(issue.impact.value, 99),
            issue.title.lower(),
        ),
    )


def report_to_markdown(report: Report) -> str:
    """Render a human-readable markdown summary from structured Report data."""
    severity_counts = Counter(issue.severity.value for issue in report.prioritized_backlog)
    snapshot = report.executive_snapshot
    lines = [
        f"# Multimodal AI Design Analysis Report ({report.job_id})",
        "",
        f"Generated: {report.created_at.isoformat()}",
        "",
        "## Executive Snapshot",
        f"**{snapshot.headline}**",
        "",
        f"- Benchmark Mode: **{snapshot.benchmark_mode}**",
        f"- Heuristic Score: **{snapshot.heuristic_score:.1f}/10**",
        f"- Confidence Score: **{snapshot.confidence_score:.1f}/10**",
        f"- Overall Score (legacy): **{snapshot.overall_score:.1f}/10**",
        f"- Overall Rating: **{snapshot.overall_rating}**",
    ]

    if snapshot.top_strengths:
        lines.append("- Top Strengths:")
        for item in snapshot.top_strengths:
            lines.append(f"  - {item}")

    if snapshot.top_improvements:
        lines.append("- Top Improvement Opportunities:")
        for item in snapshot.top_improvements:
            lines.append(f"  - {item}")

    if snapshot.source_scorecards:
        lines.extend(["", "### Source Scorecards"])
        for card in snapshot.source_scorecards:
            lines.extend(
                [
                    f"- **{card.source_ref}** ({card.source_type})",
                    f"  - Heuristic: **{card.heuristic_score:.1f}/10** | Confidence: **{card.confidence_score:.1f}/10** ({card.grade})",
                ]
            )
            if card.good_things:
                lines.append(f"  - Good: {', '.join(card.good_things[:3])}")
            if card.could_improve:
                lines.append(f"  - Improve: {', '.join(card.could_improve[:3])}")

    lines.extend(
        [
            "",
        "## Executive Summary",
        report.executive_summary,
        "",
        "## Severity Snapshot",
        f"- Blocker: {severity_counts.get('blocker', 0)}",
        f"- High: {severity_counts.get('high', 0)}",
        f"- Medium: {severity_counts.get('medium', 0)}",
        f"- Low: {severity_counts.get('low', 0)}",
        "",
        "## Quick Wins",
        ]
    )

    if report.quick_wins:
        for item in report.quick_wins:
            lines.append(f"- {item}")
    else:
        lines.append("- No immediate quick wins were detected.")

    if report.comparison:
        lines.extend(
            [
                "",
                "## Comparison",
                f"Recommendation: {report.comparison.recommendation}",
                "",
                "Tradeoffs:",
            ]
        )
        for t in report.comparison.tradeoffs:
            lines.append(f"- {t}")

    lines.extend(["", "## Prioritized Backlog"])
    for idx, issue in enumerate(report.prioritized_backlog, start=1):
        lines.extend(
            [
                f"### {idx}. [{issue.severity.value.upper()}] {issue.title}",
                f"- Component: {issue.component.value}",
                f"- Impact: {issue.impact.value}",
                f"- Confidence: {issue.confidence.value}",
                f"- Issue: {issue.issue}",
                f"- Evidence: {issue.evidence}",
                f"- Principle: {issue.principle}",
                f"- Fix: {issue.fix}",
                "- Acceptance Criteria:",
            ]
        )
        for ac in issue.acceptance_criteria:
            lines.append(f"  - {ac}")
        if issue.references:
            lines.append(f"- KB References: {', '.join(issue.references)}")
        lines.append("")

    if report.citations:
        lines.extend(["## KB Citations", ""])
        for snippet_id, quote in report.citations.items():
            lines.append(f"- {snippet_id}: \"{quote}\"")

    return "\n".join(lines)


def build_ticket_payloads(issues: List[Issue], context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Transform issues into provider-specific payload shapes for Jira and GitHub."""
    jira_payloads: List[Dict[str, Any]] = []
    github_payloads: List[Dict[str, Any]] = []

    for issue in issues:
        if issue.severity.value not in {"blocker", "high", "medium", "low"}:
            continue

        jira_payloads.append(
            {
                "summary": f"[{issue.severity.value.upper()}] {issue.title}",
                "description": (
                    f"Issue: {issue.issue}\n\n"
                    f"Evidence: {issue.evidence}\n\n"
                    f"Principle: {issue.principle}\n\n"
                    f"Fix: {issue.fix}\n\n"
                    f"Acceptance Criteria:\n- " + "\n- ".join(issue.acceptance_criteria)
                ),
                "labels": ["design-audit", issue.component.value, issue.impact.value, issue.severity.value],
                "priority_hint": issue.severity.value,
            }
        )

        github_payloads.append(
            {
                "title": f"[{issue.severity.value.upper()}] {issue.title}",
                "body": (
                    f"## Issue\n{issue.issue}\n\n"
                    f"## Evidence\n{issue.evidence}\n\n"
                    f"## Principle\n{issue.principle}\n\n"
                    f"## Proposed Fix\n{issue.fix}\n\n"
                    f"## Acceptance Criteria\n- " + "\n- ".join(issue.acceptance_criteria)
                ),
                "labels": ["design-audit", issue.component.value, issue.severity.value],
            }
        )

    return {"jira_issues": jira_payloads, "github_issues": github_payloads}


def persist_outputs(
    job_id: str,
    report_payload: Dict[str, Any],
    report_md: str,
    action_items: List[Dict[str, Any]],
    ticket_payloads: Dict[str, List[Dict[str, Any]]],
) -> Tuple[Path, Path, Path]:
    """Validate and persist all primary output files for a job."""
    validate_report_payload(report_payload)

    report_json_path = output_path(job_id, "report.json")
    report_md_path = output_path(job_id, "report.md")
    action_items_path = output_path(job_id, "action_items.json")

    save_json(report_json_path, report_payload)
    save_text(report_md_path, report_md)
    save_json(action_items_path, {"job_id": job_id, "action_items": action_items})

    tickets_dir = get_job_subdir(job_id, "ticket_payloads")
    save_json(tickets_dir / "jira_issues.json", {"issues": ticket_payloads.get("jira_issues", [])})
    save_json(tickets_dir / "github_issues.json", {"issues": ticket_payloads.get("github_issues", [])})

    return report_json_path, report_md_path, action_items_path


def build_report(
    job_id: str,
    context: Dict[str, Any],
    analyzed_sources: List[Dict[str, Any]],
    executive_snapshot: ExecutiveSnapshot | Dict[str, Any],
    executive_summary: str,
    quick_wins: List[str],
    prioritized_backlog: List[Issue],
    comparison: Dict[str, Any] | None,
    citations: Dict[str, str],
) -> Report:
    """Construct the canonical Report model before markdown conversion and persistence."""
    return Report(
        job_id=job_id,
        created_at=datetime.now(timezone.utc),
        context=context,
        analyzed_sources=analyzed_sources,
        executive_snapshot=executive_snapshot,
        executive_summary=executive_summary,
        quick_wins=quick_wins,
        prioritized_backlog=sort_issues(prioritized_backlog),
        comparison=comparison,
        citations=citations,
    )
