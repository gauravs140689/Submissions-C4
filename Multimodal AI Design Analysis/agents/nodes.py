from __future__ import annotations
"""LangGraph node implementations for ingestion, analysis agents, merge, and report composition."""

from collections import Counter
import hashlib
import itertools
import re
from typing import Any, Dict, List, TypedDict

from api.schemas import (
    AgentIssueBundle,
    Component,
    Confidence,
    ExecutiveSnapshot,
    Impact,
    Issue,
    Severity,
    SourceScoreCard,
)
from agents.models import get_model_wrapper
from agents.prompts import (
    ACCESSIBILITY_PROMPT,
    MARKET_PATTERN_PROMPT,
    UX_CRITIQUE_PROMPT,
    VISUAL_ANALYSIS_PROMPT,
)
from core.ingest import ingest_assets
from core.reporting import build_report, build_ticket_payloads, report_to_markdown
from core.signals import extract_signals_batch
from rag.retriever import retrieve


class GraphState(TypedDict, total=False):
    """Shared mutable state passed from one graph node to the next."""
    job_id: str
    context: Dict[str, Any]
    uploaded_images: List[Dict[str, Any]]
    urls: List[str]
    sources: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    rag_snippets: List[Dict[str, Any]]
    visual_bundle: Dict[str, Any]
    ux_bundle: Dict[str, Any]
    market_bundle: Dict[str, Any]
    accessibility_bundle: Dict[str, Any]
    merged_issues: List[Dict[str, Any]]
    report_json: Dict[str, Any]
    report_md: str
    action_items: List[Dict[str, Any]]
    ticket_payloads: Dict[str, Any]


def _mk_issue_id(seed: str) -> str:
    """Create stable short ids so repeated runs produce deterministic issue identifiers."""
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:10]


def _short_quote(text: str, max_words: int = 25) -> str:
    """Trim citation quotes to the project requirement of short snippets."""
    words = text.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).strip() + " ..."


def _citations(snippets: List[Dict[str, Any]], max_items: int = 2) -> List[str]:
    return [s["snippet_id"] for s in snippets[:max_items]]


def _issue(
    title: str,
    issue: str,
    evidence: str,
    principle: str,
    impact: Impact,
    severity: Severity,
    fix: str,
    acceptance_criteria: List[str],
    confidence: Confidence,
    references: List[str],
    component: Component,
) -> Issue:
    """Helper to build Issue objects with consistent id construction."""
    return Issue(
        id=_mk_issue_id(f"{title}|{component.value}|{severity.value}|{issue}"),
        title=title,
        issue=issue,
        evidence=evidence,
        principle=principle,
        impact=impact,
        severity=severity,
        fix=fix,
        acceptance_criteria=acceptance_criteria,
        confidence=confidence,
        references=references,
        component=component,
    )


def ingest_node(state: GraphState) -> GraphState:
    """Normalize raw input blobs and URL list into stored source artifacts."""
    uploaded = []
    for item in state.get("uploaded_images", []):
        uploaded.append((item["filename"], item["content"]))

    sources = ingest_assets(
        job_id=state["job_id"],
        uploaded_images=uploaded,
        urls=state.get("urls", []),
        context=state.get("context", {}),
    )
    return {"sources": sources}


def signals_node(state: GraphState) -> GraphState:
    """Extract structured signals for each ingested image/screenshot."""
    signals = extract_signals_batch(state["job_id"], state.get("sources", []))
    return {"signals": [s.model_dump() for s in signals]}


def rag_prepare_node(state: GraphState) -> GraphState:
    """Build retrieval query from context and attach KB snippets for citation-aware reasoning."""
    context = state.get("context", {})
    query = " ".join(
        [
            str(context.get("industry_category", "")),
            str(context.get("target_audience", "")),
            str(context.get("primary_conversion_goal", "")),
            "landing page ux conversion accessibility",
        ]
    ).strip()
    snippets = retrieve(query=query or "landing page design analysis", k=8, filters={"platform": "web"})
    rag_snippets = [
        {
            "snippet_id": s.snippet_id,
            "quote": _short_quote(s.text),
            "source": s.source,
            "category": s.category,
            "text": s.text,
        }
        for s in snippets
    ]
    return {"rag_snippets": rag_snippets}


def visual_analysis_agent_node(state: GraphState) -> GraphState:
    """Visual/layout-focused issue generation using signals plus optional vision-model summary."""
    wrapper = get_model_wrapper()
    snippets = state.get("rag_snippets", [])
    issues: List[Issue] = []

    for signal in state.get("signals", []):
        vision = wrapper.analyze(signal.get("image_path", ""), VISUAL_ANALYSIS_PROMPT)
        ctas = signal.get("detected_ctas", [])
        warnings = signal.get("contrast_warnings", [])
        sections = signal.get("page_sections", [])

        if not ctas:
            issues.append(
                _issue(
                    title="Primary CTA not obvious",
                    issue="No clear primary call-to-action was detected in visible content.",
                    evidence="OCR and CTA heuristics did not find a strong conversion action.",
                    principle="Landing pages should provide one dominant next step above the fold.",
                    impact=Impact.conversion,
                    severity=Severity.high,
                    fix="Add a single primary CTA button in hero with action-led text and high visual prominence.",
                    acceptance_criteria=[
                        "Hero section includes one primary CTA",
                        "CTA text uses explicit action verb",
                        "CTA is visually distinguishable from secondary actions",
                    ],
                    confidence=Confidence.med,
                    references=_citations(snippets),
                    component=Component.cta,
                )
            )
        elif len(ctas) > 3:
            issues.append(
                _issue(
                    title="Too many competing CTAs",
                    issue="Multiple CTA options may split user attention and reduce completion rates.",
                    evidence=f"Detected approximately {len(ctas)} CTA-like labels.",
                    principle="Choice overload in critical moments reduces decision confidence.",
                    impact=Impact.clarity,
                    severity=Severity.medium,
                    fix="Prioritize one primary CTA and demote others to secondary links or lower sections.",
                    acceptance_criteria=[
                        "Only one primary CTA in hero",
                        "Secondary CTAs are visually quieter",
                    ],
                    confidence=Confidence.med,
                    references=_citations(snippets),
                    component=Component.cta,
                )
            )

        if warnings:
            issues.append(
                _issue(
                    title="Potential low-contrast visual pairings",
                    issue="Detected palette combinations may fail readability in key UI elements.",
                    evidence=warnings[0],
                    principle="Text and interactive controls need readable contrast across devices.",
                    impact=Impact.a11y,
                    severity=Severity.medium,
                    fix="Adjust foreground/background combinations to meet at least WCAG AA contrast targets.",
                    acceptance_criteria=[
                        "Primary text contrast >= 4.5:1",
                        "Large text and CTA labels pass >= 3:1",
                    ],
                    confidence=Confidence.med,
                    references=_citations(snippets),
                    component=Component.visual,
                )
            )

        if "nav" not in sections:
            issues.append(
                _issue(
                    title="Navigation affordance unclear",
                    issue="Top-level navigation structure is not evident from visible content.",
                    evidence="Section detection did not confidently identify a nav band.",
                    principle="Visitors should quickly orient and explore trust-building pages.",
                    impact=Impact.trust,
                    severity=Severity.low,
                    fix="Add concise top navigation with essential links and consistent placement.",
                    acceptance_criteria=[
                        "Top nav is visible on desktop",
                        "Navigation labels are concise and scannable",
                    ],
                    confidence=Confidence.low,
                    references=_citations(snippets),
                    component=Component.nav,
                )
            )

        if vision.summary and "clutter" in vision.summary.lower():
            issues.append(
                _issue(
                    title="Visual hierarchy appears cluttered",
                    issue="Elements may compete for attention, reducing comprehension speed.",
                    evidence=_short_quote(vision.summary),
                    principle="Clear hierarchy improves scanning and goal completion.",
                    impact=Impact.clarity,
                    severity=Severity.medium,
                    fix="Increase spacing, reduce competing styles, and emphasize one core message path.",
                    acceptance_criteria=[
                        "Hero has one dominant headline",
                        "Primary CTA is top visual priority",
                        "Secondary content uses lighter emphasis",
                    ],
                    confidence=Confidence.low,
                    references=_citations(snippets),
                    component=Component.layout,
                )
            )

    bundle = AgentIssueBundle(agent_name="visual_analysis_agent", issues=issues)
    return {"visual_bundle": bundle.model_dump()}


def ux_critique_agent_node(state: GraphState) -> GraphState:
    """Heuristic UX critique for proposition clarity and navigation load."""
    snippets = state.get("rag_snippets", [])
    issues: List[Issue] = []

    for signal in state.get("signals", []):
        key_claims = signal.get("key_claims", [])
        nav_items = signal.get("nav_items", [])

        if not key_claims:
            quote = snippets[0]["quote"] if snippets else "No supporting KB quote available."
            issues.append(
                _issue(
                    title="Value proposition not explicit",
                    issue="Core user benefit is not clearly stated in extracted above-fold copy.",
                    evidence=f"Limited claim extraction. KB: '{quote}'",
                    principle="Users should understand outcome and audience fit in seconds.",
                    impact=Impact.clarity,
                    severity=Severity.high,
                    fix="Rewrite hero headline/subheadline to name audience, outcome, and differentiator.",
                    acceptance_criteria=[
                        "Hero headline names outcome",
                        "Subheadline states audience and time-to-value",
                        "Primary CTA aligns with stated outcome",
                    ],
                    confidence=Confidence.med,
                    references=_citations(snippets),
                    component=Component.hero,
                )
            )

        if len(nav_items) > 7:
            issues.append(
                _issue(
                    title="Navigation may overload first-time visitors",
                    issue="Too many top-level options can reduce directional clarity.",
                    evidence=f"Detected roughly {len(nav_items)} nav-like labels.",
                    principle="Progressive disclosure improves cognitive load on entry pages.",
                    impact=Impact.clarity,
                    severity=Severity.low,
                    fix="Limit top-level nav to essential destinations and move secondary links to footer.",
                    acceptance_criteria=[
                        "Primary nav has <= 6 top links",
                        "Secondary links moved to footer",
                    ],
                    confidence=Confidence.low,
                    references=_citations(snippets),
                    component=Component.nav,
                )
            )

    bundle = AgentIssueBundle(agent_name="ux_critique_agent", issues=issues)
    return {"ux_bundle": bundle.model_dump()}


def market_patterns_agent_node(state: GraphState) -> GraphState:
    """Conversion-pattern analysis for trust signals and risk-reversal copy."""
    snippets = state.get("rag_snippets", [])
    issues: List[Issue] = []
    social_proof_terms = {"trusted", "customers", "reviews", "teams", "companies", "testimonials", "logos"}

    for signal in state.get("signals", []):
        ocr_words = " ".join(block.get("text", "") for block in signal.get("ocr_text_blocks", [])).lower()
        has_social_proof = any(term in ocr_words for term in social_proof_terms)

        if not has_social_proof:
            issues.append(
                _issue(
                    title="Social proof signals are weak",
                    issue="The page does not clearly show credibility markers near decision points.",
                    evidence="OCR did not find common social-proof cues (testimonials/logos/trust numbers).",
                    principle="Credibility cues reduce perceived risk before conversion.",
                    impact=Impact.trust,
                    severity=Severity.medium,
                    fix="Add customer logos, testimonial snippets, or quantified outcomes near CTA sections.",
                    acceptance_criteria=[
                        "At least one social-proof block appears above fold or near primary CTA",
                        "Proof includes verifiable customer or metric detail",
                    ],
                    confidence=Confidence.med,
                    references=_citations(snippets),
                    component=Component.content,
                )
            )

        if "free" not in ocr_words and "trial" not in ocr_words and "demo" not in ocr_words:
            issues.append(
                _issue(
                    title="Risk-reversal copy is missing",
                    issue="Users may hesitate when there is no low-risk next step language.",
                    evidence="No 'free trial', 'demo', or similar reassurance terms were extracted.",
                    principle="Lowering perceived commitment improves click-through and form starts.",
                    impact=Impact.conversion,
                    severity=Severity.medium,
                    fix="Include risk-reversal microcopy near CTA (e.g., no credit card, cancel anytime, free demo).",
                    acceptance_criteria=[
                        "Primary CTA includes risk-reversal support text",
                        "Microcopy is visible on desktop and mobile",
                    ],
                    confidence=Confidence.med,
                    references=_citations(snippets),
                    component=Component.cta,
                )
            )

    bundle = AgentIssueBundle(agent_name="market_patterns_agent", issues=issues)
    return {"market_bundle": bundle.model_dump()}


def accessibility_agent_node(state: GraphState) -> GraphState:
    """Accessibility-focused pass based on contrast/readability heuristics."""
    snippets = state.get("rag_snippets", [])
    issues: List[Issue] = []

    for signal in state.get("signals", []):
        warnings = signal.get("contrast_warnings", [])
        blocks = signal.get("ocr_text_blocks", [])
        long_texts = [b.get("text", "") for b in blocks if len(b.get("text", "")) > 90]

        if warnings:
            issues.append(
                _issue(
                    title="Potential WCAG contrast non-compliance",
                    issue="Color contrast may be insufficient for normal text in key regions.",
                    evidence=warnings[0],
                    principle="WCAG 2.x AA expects sufficient contrast for readable text.",
                    impact=Impact.a11y,
                    severity=Severity.high,
                    fix="Rebalance palette and tokenized color roles for text and interactive controls.",
                    acceptance_criteria=[
                        "Body text contrast >= 4.5:1",
                        "Button label contrast >= 4.5:1",
                        "Design tokens document updated values",
                    ],
                    confidence=Confidence.med,
                    references=_citations(snippets),
                    component=Component.visual,
                )
            )

        if long_texts:
            issues.append(
                _issue(
                    title="Readable copy blocks may be too dense",
                    issue="Long uninterrupted copy can reduce readability and accessibility for scanning.",
                    evidence=_short_quote(long_texts[0]),
                    principle="Short paragraphs and headings improve readability and assistive navigation.",
                    impact=Impact.a11y,
                    severity=Severity.low,
                    fix="Break dense copy into short paragraphs with descriptive subheadings and bullet lists.",
                    acceptance_criteria=[
                        "Long sections are split into smaller chunks",
                        "Section headings describe user outcome",
                    ],
                    confidence=Confidence.low,
                    references=_citations(snippets),
                    component=Component.content,
                )
            )

    bundle = AgentIssueBundle(agent_name="accessibility_agent", issues=issues)
    return {"accessibility_bundle": bundle.model_dump()}


def merge_dedupe_node(state: GraphState) -> GraphState:
    """Merge agent outputs and deduplicate semantically similar issues by title+component."""
    all_issue_dicts = list(
        itertools.chain(
            state.get("visual_bundle", {}).get("issues", []),
            state.get("ux_bundle", {}).get("issues", []),
            state.get("market_bundle", {}).get("issues", []),
            state.get("accessibility_bundle", {}).get("issues", []),
        )
    )

    merged: Dict[str, Dict[str, Any]] = {}
    severity_rank = {"blocker": 0, "high": 1, "medium": 2, "low": 3}

    for issue in all_issue_dicts:
        key = f"{issue['title'].lower()}::{issue['component']}"
        current = merged.get(key)
        if not current:
            merged[key] = issue
            continue
        if severity_rank[issue["severity"]] < severity_rank[current["severity"]]:
            merged[key] = issue

    return {"merged_issues": list(merged.values())}


def _comparison_summary(signals: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """Generate simple comparative recommendation when multiple designs are analyzed."""
    if len(signals) < 2:
        return None

    scored = []
    for sig in signals:
        score = 0
        score += min(3, len(sig.get("detected_ctas", [])))
        score += min(3, len(sig.get("key_claims", [])))
        score += 2 if "hero" in sig.get("page_sections", []) else 0
        score -= len(sig.get("contrast_warnings", []))
        scored.append((sig["source_id"], score))

    scored.sort(key=lambda x: x[1], reverse=True)
    best = scored[0][0]
    worst = scored[-1][0]
    tradeoffs = [
        f"{best} shows stronger conversion cues (CTA + claims) than {worst}.",
        "Lower-contrast palettes correlate with weaker accessibility confidence.",
        "Designs with explicit nav and social proof tend to score better on trust.",
    ]
    return {
        "recommendation": f"Prioritize the structure used in {best}, then apply accessibility fixes before rollout.",
        "tradeoffs": tradeoffs,
    }


def _score_to_grade(score: float) -> str:
    """Map normalized 0-10 scores to human-friendly grade labels."""
    if score >= 9.0:
        return "A"
    if score >= 8.0:
        return "B+"
    if score >= 7.0:
        return "B"
    if score >= 6.0:
        return "C+"
    if score >= 5.0:
        return "C"
    return "D"


def _normalize_benchmark_mode(value: Any) -> str:
    """Normalize benchmark mode input from context into one supported label."""
    raw = str(value or "startup").strip().lower().replace("_", "-")
    if raw == "enterprise":
        return "enterprise"
    if raw in {"brand", "brand-led", "brand led", "brand-first", "brandfirst"}:
        return "brand-led"
    return "startup"


def _benchmark_weights(mode: str) -> Dict[str, float]:
    """Return scoring weights calibrated for different product/site strategies."""
    if mode == "enterprise":
        return {
            "base": 6.8,
            "cta_good": 0.7,
            "cta_missing": 0.8,
            "cta_overload": 0.4,
            "claims_good": 0.8,
            "claims_missing": 1.0,
            "hero_good": 0.5,
            "hero_missing": 0.6,
            "nav_good": 0.4,
            "nav_overload": 0.4,
            "nav_missing": 0.5,
            "contrast_penalty_per_warning": 0.4,
            "contrast_penalty_cap": 0.8,
            "contrast_good": 0.2,
            "social_good": 0.8,
            "social_missing": 1.0,
            "risk_good": 0.4,
            "risk_missing": 0.5,
            "enterprise_good": 0.9,
            "enterprise_missing": 0.9,
        }
    if mode == "brand-led":
        return {
            "base": 7.2,
            "cta_good": 0.5,
            "cta_missing": 0.4,
            "cta_overload": 0.2,
            "claims_good": 0.7,
            "claims_missing": 0.7,
            "hero_good": 0.8,
            "hero_missing": 0.5,
            "nav_good": 0.3,
            "nav_overload": 0.2,
            "nav_missing": 0.1,
            "contrast_penalty_per_warning": 0.3,
            "contrast_penalty_cap": 0.7,
            "contrast_good": 0.2,
            "social_good": 0.5,
            "social_missing": 0.2,
            "risk_good": 0.2,
            "risk_missing": 0.0,
            "enterprise_good": 0.2,
            "enterprise_missing": 0.0,
        }
    # startup baseline
    return {
        "base": 7.0,
        "cta_good": 0.9,
        "cta_missing": 1.0,
        "cta_overload": 0.5,
        "claims_good": 0.9,
        "claims_missing": 0.9,
        "hero_good": 0.7,
        "hero_missing": 0.5,
        "nav_good": 0.2,
        "nav_overload": 0.2,
        "nav_missing": 0.0,
        "contrast_penalty_per_warning": 0.3,
        "contrast_penalty_cap": 0.6,
        "contrast_good": 0.2,
        "social_good": 0.5,
        "social_missing": 0.2,
        "risk_good": 0.5,
        "risk_missing": 0.2,
        "enterprise_good": 0.2,
        "enterprise_missing": 0.0,
    }


def _estimate_confidence_score(signal: Dict[str, Any], source_type: str) -> float:
    """Estimate confidence based on richness/coverage of extracted signals."""
    score = 4.5
    ocr_count = len(signal.get("ocr_text_blocks", []))
    section_count = len(signal.get("page_sections", []))

    if ocr_count >= 25:
        score += 2.0
    elif ocr_count >= 10:
        score += 1.2
    elif ocr_count >= 4:
        score += 0.5
    else:
        score -= 0.8

    if section_count >= 3:
        score += 0.8
    elif section_count >= 1:
        score += 0.3
    else:
        score -= 0.3

    if signal.get("key_claims"):
        score += 0.7
    if signal.get("detected_ctas"):
        score += 0.5
    if signal.get("nav_items"):
        score += 0.4
    if signal.get("palette"):
        score += 0.2
    if source_type == "url":
        score += 0.3

    return round(max(1.0, min(10.0, score)), 1)


def _overall_rating(heuristic_score: float, confidence_score: float) -> str:
    """Narrative rating used in the catchy top-level report headline."""
    if heuristic_score >= 8.5:
        rating = "Excellent foundation"
    elif heuristic_score >= 7.0:
        rating = "Strong with clear optimization headroom"
    elif heuristic_score >= 5.5:
        rating = "Promising but needs targeted improvements"
    else:
        rating = "Needs major redesign attention"

    if confidence_score < 4.5:
        return f"{rating} (low-confidence estimate)"
    return rating


def _quality_band(heuristic_score: float, confidence_score: float) -> str:
    """Human-readable quality band combining quality and confidence dimensions."""
    if heuristic_score >= 8.0 and confidence_score >= 7.0:
        return "High confidence, high quality"
    if heuristic_score >= 7.0:
        return "Competitive baseline"
    if heuristic_score >= 5.5:
        return "Improvement required before scaling"
    return "At-risk conversion baseline"


def _build_executive_snapshot(
    sources: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
    issues: List[Issue],
    context: Dict[str, Any] | None = None,
) -> ExecutiveSnapshot:
    """Build an at-a-glance scorecard for each analyzed source and an overall headline."""
    source_by_id = {s.get("source_id"): s for s in sources}
    cards: List[SourceScoreCard] = []
    strengths_all: List[str] = []
    improvements_all: List[str] = []
    benchmark_mode = _normalize_benchmark_mode((context or {}).get("benchmark_mode", "startup"))
    weights = _benchmark_weights(benchmark_mode)
    social_terms = {"trusted", "customers", "testimonials", "logos", "reviews", "case study", "case studies"}
    risk_terms = {"free", "trial", "demo", "no credit card", "cancel anytime", "start free"}
    enterprise_terms = {
        "soc 2",
        "soc2",
        "iso 27001",
        "sso",
        "scim",
        "audit log",
        "governance",
        "dpa",
        "gdpr",
        "hipaa",
    }

    for signal in signals:
        source_id = signal.get("source_id", "unknown")
        source_meta = source_by_id.get(source_id, {})
        source_type = source_meta.get("source_type", signal.get("source_type", "upload"))
        heuristic_score = weights["base"]
        confidence_score = _estimate_confidence_score(signal, source_type)
        ctas = signal.get("detected_ctas", [])
        claims = signal.get("key_claims", [])
        sections = signal.get("page_sections", [])
        nav_items = signal.get("nav_items", [])
        warnings = signal.get("contrast_warnings", [])
        ocr_words = " ".join(block.get("text", "") for block in signal.get("ocr_text_blocks", [])).lower()

        good: List[str] = []
        improve: List[str] = []

        if 1 <= len(ctas) <= 3:
            heuristic_score += weights["cta_good"]
            good.append("CTA structure is focused")
        elif len(ctas) == 0:
            heuristic_score -= weights["cta_missing"]
            improve.append("Make one primary CTA obvious above the fold")
        else:
            heuristic_score -= weights["cta_overload"]
            improve.append("Reduce competing CTA choices in primary viewport")

        if claims:
            heuristic_score += weights["claims_good"]
            good.append("Value proposition signals are present")
        else:
            heuristic_score -= weights["claims_missing"]
            improve.append("Clarify outcome-driven value proposition in hero copy")

        if "hero" in sections:
            heuristic_score += weights["hero_good"]
            good.append("Hero structure appears discoverable")
        else:
            heuristic_score -= weights["hero_missing"]
            improve.append("Strengthen above-the-fold message hierarchy")

        if "nav" in sections or (1 <= len(nav_items) <= 6):
            heuristic_score += weights["nav_good"]
            good.append("Navigation cues are reasonably discoverable")
        elif len(nav_items) > 7:
            heuristic_score -= weights["nav_overload"]
            improve.append("Simplify top navigation options")
        else:
            heuristic_score -= weights["nav_missing"]

        if warnings:
            contrast_penalty = min(
                weights["contrast_penalty_cap"],
                len(warnings) * weights["contrast_penalty_per_warning"],
            )
            heuristic_score -= contrast_penalty
            improve.append("Fix contrast issues for accessibility compliance")
        else:
            heuristic_score += weights["contrast_good"]
            good.append("No major contrast warnings were detected")

        if any(term in ocr_words for term in social_terms):
            heuristic_score += weights["social_good"]
            good.append("Trust/social-proof signals are visible")
        else:
            heuristic_score -= weights["social_missing"]
            improve.append("Add concrete social proof near key conversion points")

        if any(term in ocr_words for term in risk_terms):
            heuristic_score += weights["risk_good"]
            good.append("Risk-reversal language is present")
        else:
            heuristic_score -= weights["risk_missing"]
            if weights["risk_missing"] > 0:
                improve.append("Add low-risk CTA microcopy (trial/demo/no credit card)")

        has_enterprise_signals = any(term in ocr_words for term in enterprise_terms)
        if has_enterprise_signals:
            heuristic_score += weights["enterprise_good"]
            if benchmark_mode == "enterprise":
                good.append("Enterprise readiness signals are visible")
        else:
            heuristic_score -= weights["enterprise_missing"]
            if benchmark_mode == "enterprise":
                improve.append("Add enterprise signals (security/compliance/SSO/governance)")

        # Confidence-aware damping:
        # low-confidence runs should not over-penalize or over-reward aggressively.
        neutral_score = weights["base"]
        confidence_factor = confidence_score / 10.0
        heuristic_score = neutral_score + ((heuristic_score - neutral_score) * confidence_factor)
        heuristic_score = round(max(0.0, min(10.0, heuristic_score)), 1)
        strengths_all.extend(good)
        improvements_all.extend(improve)

        cards.append(
            SourceScoreCard(
                source_id=source_id,
                source_type=source_type,
                source_ref=source_meta.get("source_ref", signal.get("source_ref", source_id)),
                score=heuristic_score,  # legacy alias retained for compatibility
                heuristic_score=heuristic_score,
                confidence_score=confidence_score,
                grade=_score_to_grade(heuristic_score),
                good_things=good[:5] if good else ["Baseline structure is present"],
                could_improve=improve[:5] if improve else ["No major opportunities identified by current heuristics"],
            )
        )

    if not cards:
        cards = [
            SourceScoreCard(
                source_id="none",
                source_type="upload",
                source_ref="No sources analyzed",
                score=5.0,
                heuristic_score=5.0,
                confidence_score=3.0,
                grade="C",
                good_things=["Pipeline executed successfully"],
                could_improve=["Provide at least one URL/image for richer analysis"],
            )
        ]

    heuristic_score = round(sum(card.heuristic_score for card in cards) / len(cards), 1)
    confidence_score = round(sum(card.confidence_score for card in cards) / len(cards), 1)
    rating = _overall_rating(heuristic_score, confidence_score)

    sev_counts = Counter(issue.severity.value for issue in issues)
    top_strengths = [item for item, _ in Counter(strengths_all).most_common(3)] or [
        "Core layout baseline is detectable",
        "Conversion path can be improved with focused experiments",
    ]
    top_improvements = [item for item, _ in Counter(improvements_all).most_common(3)] or [
        "No major improvement clusters were detected",
    ]

    blocker_high = sev_counts.get("blocker", 0) + sev_counts.get("high", 0)
    headline = (
        f"{heuristic_score:.1f}/10 heuristic ({confidence_score:.1f}/10 confidence) - "
        f"{_quality_band(heuristic_score, confidence_score)}. "
        f"Detected {blocker_high} blocker/high issue(s) across {len(cards)} design(s)."
    )

    return ExecutiveSnapshot(
        headline=headline,
        overall_score=heuristic_score,  # legacy alias retained for compatibility
        heuristic_score=heuristic_score,
        confidence_score=confidence_score,
        benchmark_mode=benchmark_mode,
        overall_rating=rating,
        top_strengths=top_strengths,
        top_improvements=top_improvements,
        source_scorecards=sorted(cards, key=lambda c: c.heuristic_score, reverse=True),
    )


def report_compose_node(state: GraphState) -> GraphState:
    """Compose final report payloads, markdown, and ticket-ready action lists."""
    issues = [Issue.model_validate(item) for item in state.get("merged_issues", [])]
    snippets = state.get("rag_snippets", [])
    citations = {item["snippet_id"]: item["quote"] for item in snippets[:8]}

    if not issues:
        # Keep downstream contracts valid even when heuristics found nothing actionable.
        issues = [
            _issue(
                title="No significant issues detected",
                issue="The heuristic pipeline found limited actionable problems.",
                evidence="Fallback generated when issue list is empty.",
                principle="Human review is recommended to validate assumptions.",
                impact=Impact.clarity,
                severity=Severity.low,
                fix="Run a manual pass and include additional screenshots for state-based flows.",
                acceptance_criteria=["Manual reviewer confirms no blocker/high issues"],
                confidence=Confidence.low,
                references=[],
                component=Component.global_component,
            )
        ]

    severe = [i for i in issues if i.severity.value in {"blocker", "high"}]
    executive_summary = (
        f"Analyzed {len(state.get('signals', []))} design(s). "
        f"Detected {len(issues)} issues, including {len(severe)} blocker/high items. "
        "Top themes: CTA clarity, messaging specificity, trust signals, and accessibility readiness."
    )

    quick_wins = [
        issue.fix for issue in issues if issue.severity.value in {"blocker", "high", "medium"}
    ][:5]

    executive_snapshot = _build_executive_snapshot(
        sources=state.get("sources", []),
        signals=state.get("signals", []),
        issues=issues,
        context=state.get("context", {}),
    )

    report = build_report(
        job_id=state["job_id"],
        context=state.get("context", {}),
        analyzed_sources=[
            {
                "source_id": s.get("source_id"),
                "source_type": s.get("source_type"),
                "source_ref": s.get("source_ref"),
            }
            for s in state.get("sources", [])
        ],
        executive_snapshot=executive_snapshot,
        executive_summary=executive_summary,
        quick_wins=quick_wins,
        prioritized_backlog=issues,
        comparison=_comparison_summary(state.get("signals", [])),
        citations=citations,
    )

    report_md = report_to_markdown(report)
    ticket_payloads = build_ticket_payloads(issues, state.get("context", {}))

    return {
        "report_json": report.model_dump(mode="json"),
        "report_md": report_md,
        "action_items": [issue.model_dump(mode="json") for issue in report.prioritized_backlog],
        "ticket_payloads": ticket_payloads,
    }
