from __future__ import annotations
"""Streamlit page for submitting analysis jobs and polling initial completion state."""

from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple

import streamlit as st

try:
    from app_streamlit.utils import get_result, submit_analysis
except ModuleNotFoundError:
    # Some Streamlit runtimes execute page files without project root on sys.path.
    # Add repository root so `app_streamlit.*` imports work consistently.
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app_streamlit.utils import get_result, submit_analysis

st.title("Analyze")
st.caption("Upload screenshots and/or paste landing page URLs.")

if "latest_job_id" not in st.session_state:
    # Session key is reused by Results page to pre-fill last submitted job id.
    st.session_state["latest_job_id"] = ""
if "job_history" not in st.session_state:
    # In-session history avoids manual copy/paste between pages.
    st.session_state["job_history"] = []

with st.form("analyze_form"):
    uploads = st.file_uploader(
        "Upload image files (PNG/JPG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    urls_text = st.text_area(
        "Landing page URLs (one per line or comma separated)",
        height=120,
        placeholder="https://example.com\nhttps://example.org",
    )

    st.markdown("### Context")
    industry = st.text_input("Industry / Category", placeholder="SaaS, fintech, ecommerce...")
    audience = st.text_input("Target Audience", placeholder="Founders, SMB marketers, enterprise buyers...")
    goal = st.text_input("Primary Conversion Goal", placeholder="Book demo, signup, start trial...")
    tone = st.text_input("Brand Tone (optional)", placeholder="Trusted, playful, premium...")
    benchmark_mode = st.selectbox(
        "Benchmark Mode",
        options=["startup", "enterprise", "brand-led"],
        index=0,
        help="Calibrates scoring expectations by website strategy/maturity.",
    )
    extra = st.text_area("Extra Notes (optional)", height=80)

    mode = st.selectbox("Execution Mode", ["auto", "sync", "async"], index=0)
    auto_open_results = st.checkbox("Auto-open Results after submit", value=True)
    submitted = st.form_submit_button("Analyze", use_container_width=True)

if submitted:
    # Convert textarea input and uploaded files to API payload format.
    url_list = [u.strip() for u in urls_text.replace(",", "\n").splitlines() if u.strip()]
    file_payloads: List[Tuple[str, bytes]] = []
    for upload in uploads or []:
        file_payloads.append((upload.name, upload.getvalue()))

    context: Dict[str, str] = {
        "industry_category": industry,
        "target_audience": audience,
        "primary_conversion_goal": goal,
        "brand_tone": tone,
        "benchmark_mode": benchmark_mode,
        "extra_notes": extra,
    }

    if not url_list and not file_payloads:
        st.error("Provide at least one URL or image.")
    else:
        try:
            with st.spinner("Submitting analysis request..."):
                response = submit_analysis(urls=url_list, context=context, files=file_payloads, mode=mode)

            job_id = response["job_id"]
            st.session_state["latest_job_id"] = job_id
            history = st.session_state.get("job_history", [])
            if job_id in history:
                history.remove(job_id)
            history.insert(0, job_id)
            st.session_state["job_history"] = history[:30]
            st.success(f"Job created: {job_id}")

            status = response.get("status")
            st.write(f"Initial status: `{status}` | mode: `{response.get('mode')}`")

            if status in {"queued", "running"}:
                st.info("Polling for completion...")
                progress = st.progress(0)
                # Lightweight polling loop for immediate user feedback on fresh jobs.
                for idx in range(1, 31):
                    time.sleep(2)
                    result = get_result(job_id)
                    progress.progress(min(idx / 30, 1.0))
                    if result.get("status") == "completed":
                        st.session_state["latest_result"] = result
                        st.success("Analysis completed. Open Results page.")
                        break
                    if result.get("status") == "failed":
                        st.error(f"Analysis failed: {result.get('error')}")
                        break
                else:
                    st.warning("Still running. Open Results page and refresh later.")
                    if auto_open_results:
                        st.switch_page("pages/2_Results.py")
            elif status == "completed":
                st.session_state["latest_result"] = get_result(job_id)
                st.success("Analysis completed. Open Results page.")
                if auto_open_results:
                    st.switch_page("pages/2_Results.py")
            else:
                st.error(f"Analysis failed: {response.get('detail', 'unknown error')}")

        except Exception as exc:
            st.error(f"Could not submit analysis: {exc}")

st.divider()
st.markdown("### Last Job")
if st.session_state.get("latest_job_id"):
    st.code(st.session_state["latest_job_id"])
    st.page_link("pages/2_Results.py", label="Open Results", icon="📊")
else:
    st.caption("No job submitted in this session yet.")
