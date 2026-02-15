from __future__ import annotations
"""LangGraph workflow assembly and top-level pipeline execution entrypoint."""

import logging
from functools import lru_cache
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from agents.models import get_langsmith_config
from agents.nodes import (
    GraphState,
    accessibility_agent_node,
    ingest_node,
    market_patterns_agent_node,
    merge_dedupe_node,
    rag_prepare_node,
    report_compose_node,
    signals_node,
    ux_critique_agent_node,
    visual_analysis_agent_node,
)
from core.reporting import persist_outputs
from core.storage import set_job_status

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def build_graph():
    """Build and compile the deterministic node sequence used for every analysis job."""
    get_langsmith_config()

    graph = StateGraph(GraphState)
    graph.add_node("ingest_node", ingest_node)
    graph.add_node("signals_node", signals_node)
    graph.add_node("rag_prepare_node", rag_prepare_node)
    graph.add_node("visual_analysis_agent_node", visual_analysis_agent_node)
    graph.add_node("ux_critique_agent_node", ux_critique_agent_node)
    graph.add_node("market_patterns_agent_node", market_patterns_agent_node)
    graph.add_node("accessibility_agent_node", accessibility_agent_node)
    graph.add_node("merge_dedupe_node", merge_dedupe_node)
    graph.add_node("report_compose_node", report_compose_node)

    graph.set_entry_point("ingest_node")
    graph.add_edge("ingest_node", "signals_node")
    graph.add_edge("signals_node", "rag_prepare_node")
    # Fan out: these agents operate on shared read-only state and write separate bundle keys.
    graph.add_edge("rag_prepare_node", "visual_analysis_agent_node")
    graph.add_edge("rag_prepare_node", "ux_critique_agent_node")
    graph.add_edge("rag_prepare_node", "market_patterns_agent_node")
    graph.add_edge("rag_prepare_node", "accessibility_agent_node")
    # Fan in: merge runs after all agent bundles are produced.
    graph.add_edge("visual_analysis_agent_node", "merge_dedupe_node")
    graph.add_edge("ux_critique_agent_node", "merge_dedupe_node")
    graph.add_edge("market_patterns_agent_node", "merge_dedupe_node")
    graph.add_edge("accessibility_agent_node", "merge_dedupe_node")
    graph.add_edge("merge_dedupe_node", "report_compose_node")
    graph.add_edge("report_compose_node", END)

    return graph.compile()


def run_analysis_pipeline(
    job_id: str,
    urls: List[str],
    uploaded_images: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Run full graph, persist outputs, and return API-ready payload."""
    set_job_status(job_id, "running", detail="Pipeline started (first run can take longer while models load)")
    app = build_graph()

    try:
        # GraphState is passed as one dict; each node appends/updates its own keys.
        final_state = app.invoke(
            {
                "job_id": job_id,
                "urls": urls,
                "uploaded_images": uploaded_images,
                "context": context,
            }
        )

        report_json = final_state["report_json"]
        report_md = final_state["report_md"]
        action_items = final_state["action_items"]
        ticket_payloads = final_state["ticket_payloads"]

        persist_outputs(
            job_id=job_id,
            report_payload=report_json,
            report_md=report_md,
            action_items=action_items,
            ticket_payloads=ticket_payloads,
        )
        set_job_status(job_id, "completed", detail="Pipeline completed")

        return {
            "job_id": job_id,
            "status": "completed",
            "report": report_json,
            "report_md": report_md,
            "action_items": action_items,
            "ticket_payloads": ticket_payloads,
        }
    except Exception as exc:
        logger.exception("Pipeline failed for job %s", job_id)
        set_job_status(job_id, "failed", detail=str(exc))
        raise
