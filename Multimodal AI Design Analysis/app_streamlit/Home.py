from __future__ import annotations
"""Streamlit landing page introducing the suite and linking to analysis workflow pages."""

import streamlit as st

st.set_page_config(page_title="Multimodal AI Design Analysis Suite", page_icon="🧪", layout="wide")

st.title("Multimodal AI Design Analysis Suite")
st.caption("Landing page design analysis from screenshots, uploads, and URLs.")

with st.container(border=True):
    st.markdown(
        """
This application analyzes web landing pages for design quality using:
- URL screenshot capture (Playwright) and image uploads
- OCR + visual signal extraction
- OpenRouter multimodal analysis (primary + fallback model strategy)
- RAG retrieval from the local AI SaaS UX/design KB
- LangGraph multi-agent critique workflow (parallel agent execution)

Use **Analyze** to submit URLs/images and context.  
Then open **Results** to review scoring, findings, and exports.
"""
    )

st.subheader("What You Get")
st.markdown(
    """
- Executive Snapshot with:
  - `heuristic_score`
  - `confidence_score`
  - benchmark-calibrated rating (`startup`, `enterprise`, `brand-led`)
- Per-design scorecards (good things + improvement opportunities)
- Prioritized action backlog (severity/component/impact)
- Downloadable artifacts:
  - `report.md`
  - `report.json`
  - `action_items.json`
"""
)

st.subheader("Automation")
st.markdown(
    """
- Send completed reports to n8n from Results page
- n8n sends email summaries to stakeholders
"""
)
