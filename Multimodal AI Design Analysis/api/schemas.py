from __future__ import annotations
"""Shared Pydantic schemas for API IO, pipeline state payloads, and report validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, ValidationError, model_validator


class Severity(str, Enum):
    """Priority level used for sorting and ticket creation."""
    blocker = "blocker"
    high = "high"
    medium = "medium"
    low = "low"


class Confidence(str, Enum):
    low = "low"
    med = "med"
    high = "high"


class Impact(str, Enum):
    conversion = "conversion"
    trust = "trust"
    clarity = "clarity"
    a11y = "a11y"


class Component(str, Enum):
    hero = "hero"
    nav = "nav"
    cta = "cta"
    form = "form"
    footer = "footer"
    content = "content"
    layout = "layout"
    mobile = "mobile"
    visual = "visual"
    global_component = "global"


class OCRBlock(BaseModel):
    """Single OCR text element with optional bounding box and confidence."""
    text: str
    bbox: Optional[List[int]] = None
    confidence: Optional[float] = None


class CTAItem(BaseModel):
    text: str
    bbox: Optional[List[int]] = None
    type: Literal["primary", "secondary"] = "secondary"
    confidence: float = 0.5


class PaletteItem(BaseModel):
    hex: str
    ratio: float = Field(..., ge=0.0, le=1.0)


class SignalOutput(BaseModel):
    """Structured design signals extracted from a single source image/screenshot."""
    source_id: str
    source_type: Literal["upload", "url"]
    source_ref: str
    image_path: str
    ocr_text_blocks: List[OCRBlock] = Field(default_factory=list)
    page_sections: List[str] = Field(default_factory=list)
    detected_ctas: List[CTAItem] = Field(default_factory=list)
    palette: List[PaletteItem] = Field(default_factory=list)
    contrast_warnings: List[str] = Field(default_factory=list)
    key_claims: List[str] = Field(default_factory=list)
    nav_items: List[str] = Field(default_factory=list)


class Issue(BaseModel):
    """Canonical issue schema produced by all analysis agents."""
    id: str
    title: str
    issue: str
    evidence: str
    principle: str
    impact: Impact
    severity: Severity
    fix: str
    acceptance_criteria: List[str]
    confidence: Confidence
    references: List[str] = Field(default_factory=list)
    component: Component = Component.global_component


class AgentIssueBundle(BaseModel):
    agent_name: str
    issues: List[Issue] = Field(default_factory=list)


class ComparisonSummary(BaseModel):
    recommendation: str = ""
    tradeoffs: List[str] = Field(default_factory=list)


class SourceScoreCard(BaseModel):
    """Per-source score and summary used for top-of-report comparison views."""
    source_id: str
    source_type: Literal["upload", "url"]
    source_ref: str
    score: float = Field(..., ge=0.0, le=10.0)
    heuristic_score: float = Field(..., ge=0.0, le=10.0)
    confidence_score: float = Field(..., ge=0.0, le=10.0)
    grade: str
    good_things: List[str] = Field(default_factory=list)
    could_improve: List[str] = Field(default_factory=list)


class ExecutiveSnapshot(BaseModel):
    """Catchy top section summarizing overall quality and immediate action themes."""
    headline: str
    overall_score: float = Field(..., ge=0.0, le=10.0)
    heuristic_score: float = Field(..., ge=0.0, le=10.0)
    confidence_score: float = Field(..., ge=0.0, le=10.0)
    benchmark_mode: Literal["startup", "enterprise", "brand-led"] = "startup"
    overall_rating: str
    top_strengths: List[str] = Field(default_factory=list)
    top_improvements: List[str] = Field(default_factory=list)
    source_scorecards: List[SourceScoreCard] = Field(default_factory=list)


class Report(BaseModel):
    """Top-level machine-readable report saved to report.json."""
    job_id: str
    created_at: datetime
    context: Dict[str, Any] = Field(default_factory=dict)
    analyzed_sources: List[Dict[str, Any]] = Field(default_factory=list)
    executive_snapshot: ExecutiveSnapshot
    executive_summary: str
    quick_wins: List[str] = Field(default_factory=list)
    prioritized_backlog: List[Issue] = Field(default_factory=list)
    comparison: Optional[ComparisonSummary] = None
    citations: Dict[str, str] = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    """Response returned by POST /analyze."""
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    mode: Literal["sync", "async"]
    result_available: bool = False
    detail: Optional[str] = None


class ResultResponse(BaseModel):
    """Response returned by GET /result/{job_id}."""
    job_id: str
    status: Literal["queued", "running", "completed", "failed", "missing"]
    report: Optional[Report] = None
    report_md: Optional[str] = None
    action_items: List[Issue] = Field(default_factory=list)
    error: Optional[str] = None


class AnalyzeContext(BaseModel):
    industry_category: Optional[str] = None
    target_audience: Optional[str] = None
    primary_conversion_goal: Optional[str] = None
    brand_tone: Optional[str] = None
    benchmark_mode: Optional[Literal["startup", "enterprise", "brand-led"]] = "startup"
    extra_notes: Optional[str] = None


class AnalyzeFormPayload(BaseModel):
    urls: List[HttpUrl] = Field(default_factory=list)
    context: AnalyzeContext = Field(default_factory=AnalyzeContext)
    batch_name: Optional[str] = None


class WebhookRequest(BaseModel):
    job_id: str
    webhook_url: Optional[HttpUrl] = None


class TicketPayloadBundle(BaseModel):
    jira_issues: List[Dict[str, Any]] = Field(default_factory=list)
    github_issues: List[Dict[str, Any]] = Field(default_factory=list)


class ValidatePayload(BaseModel):
    """Guard model used before persisting report artifacts."""
    report: Report

    @model_validator(mode="after")
    def check_backlog_not_empty(self) -> "ValidatePayload":
        if not self.report.prioritized_backlog:
            raise ValueError("prioritized_backlog must contain at least one issue")
        return self


def validate_report_payload(report_payload: Dict[str, Any]) -> None:
    """Raise ValueError if final report payload violates schema constraints."""
    try:
        ValidatePayload(report=report_payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid report payload: {exc}") from exc
