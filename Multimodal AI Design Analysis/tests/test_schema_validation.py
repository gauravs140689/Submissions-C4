from __future__ import annotations
"""Minimal schema regression test to ensure report payloads remain structurally valid."""

from datetime import datetime, timezone

from api.schemas import (
    Confidence,
    Component,
    ExecutiveSnapshot,
    Impact,
    Issue,
    Report,
    Severity,
    SourceScoreCard,
    validate_report_payload,
)


def test_issue_and_report_schema_validation() -> None:
    # Build one representative issue and ensure report validation accepts it.
    issue = Issue(
        id="abc123",
        title="Test issue",
        issue="Some problem",
        evidence="Observed issue evidence",
        principle="A UX principle",
        impact=Impact.conversion,
        severity=Severity.high,
        fix="Specific fix",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        confidence=Confidence.med,
        references=["snippet-001"],
        component=Component.hero,
    )

    report = Report(
        job_id="job-1",
        created_at=datetime.now(timezone.utc),
        context={"industry_category": "SaaS"},
        analyzed_sources=[{"source_id": "upload_001", "source_type": "upload", "source_ref": "sample.png"}],
        executive_snapshot=ExecutiveSnapshot(
            headline="7.6/10 heuristic (7.1/10 confidence) - Competitive baseline.",
            overall_score=7.6,
            heuristic_score=7.6,
            confidence_score=7.1,
            benchmark_mode="startup",
            overall_rating="Strong with clear optimization headroom",
            top_strengths=["CTA structure is focused"],
            top_improvements=["Fix contrast issues for accessibility compliance"],
            source_scorecards=[
                SourceScoreCard(
                    source_id="upload_001",
                    source_type="upload",
                    source_ref="sample.png",
                    score=7.6,
                    heuristic_score=7.6,
                    confidence_score=7.1,
                    grade="B",
                    good_things=["CTA structure is focused"],
                    could_improve=["Fix contrast issues for accessibility compliance"],
                )
            ],
        ),
        executive_summary="Summary",
        quick_wins=["Improve CTA contrast"],
        prioritized_backlog=[issue],
        citations={"snippet-001": "Keep value proposition clear above fold."},
    )

    validate_report_payload(report.model_dump(mode="json"))
