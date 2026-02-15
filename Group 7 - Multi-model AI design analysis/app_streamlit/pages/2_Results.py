from __future__ import annotations
"""Streamlit page for loading a completed job, rendering report, and exporting artifacts."""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

try:
    from app_streamlit.utils import get_recent_jobs, get_result, send_to_n8n
except ModuleNotFoundError:
    # Some Streamlit runtimes execute page files without project root on sys.path.
    # Add repository root so `app_streamlit.*` imports work consistently.
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app_streamlit.utils import get_recent_jobs, get_result, send_to_n8n

st.title("Results")

if "job_history" not in st.session_state:
    st.session_state["job_history"] = []
if "latest_job_id" not in st.session_state:
    st.session_state["latest_job_id"] = ""
if "result_cache" not in st.session_state:
    st.session_state["result_cache"] = {}

api_jobs: List[Dict[str, Any]] = []
try:
    api_jobs = get_recent_jobs(limit=30).get("jobs", [])
except Exception:
    # Results page remains usable via session history even if API list call fails.
    api_jobs = []

job_meta: Dict[str, Dict[str, Any]] = {j["job_id"]: j for j in api_jobs if j.get("job_id")}
for jid in st.session_state.get("job_history", []):
    job_meta.setdefault(jid, {"job_id": jid, "status": "unknown"})
if st.session_state.get("latest_job_id"):
    jid = st.session_state["latest_job_id"]
    job_meta.setdefault(jid, {"job_id": jid, "status": "unknown"})

job_options = sorted(
    job_meta.keys(),
    key=lambda x: job_meta.get(x, {}).get("updated_at", ""),
    reverse=True,
)

def _job_label(job_id: str) -> str:
    meta = job_meta.get(job_id, {})
    status = meta.get("status", "unknown")
    ts = meta.get("updated_at", "")
    suffix = f" | {ts.replace('T', ' ')[:19]}" if ts else ""
    return f"{job_id}  ({status}){suffix}"

if not job_options:
    st.caption("No jobs found yet. Run analysis from Analyze page first.")
    st.stop()

default_job_id = st.session_state.get("latest_job_id") or job_options[0]
default_idx = job_options.index(default_job_id) if default_job_id in job_options else 0
job_id = st.selectbox(
    "Recent Jobs",
    options=job_options,
    index=default_idx,
    format_func=_job_label,
)
st.session_state["latest_job_id"] = job_id

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    fetch_clicked = st.button("Refresh Selected Job", use_container_width=True)
with col2:
    use_cached = st.button("Use Cached Result", use_container_width=True)
with col3:
    refresh_list = st.button("Refresh Job List", use_container_width=True)
if refresh_list:
    st.rerun()

result: Dict[str, Any] = {}
result_cache = st.session_state.get("result_cache", {})
if use_cached and job_id in result_cache:
    # Avoid an API call when user wants to inspect data already stored in this browser session.
    result = result_cache[job_id]
elif not fetch_clicked and job_id in result_cache:
    result = result_cache[job_id]
elif fetch_clicked or job_id:
    try:
        with st.spinner("Loading result..."):
            result = get_result(job_id)
            st.session_state["latest_result"] = result
            result_cache[job_id] = result
            st.session_state["result_cache"] = result_cache
            history = st.session_state.get("job_history", [])
            if job_id in history:
                history.remove(job_id)
            history.insert(0, job_id)
            st.session_state["job_history"] = history[:30]
    except Exception as exc:
        st.error(f"Failed to fetch result: {exc}")

if not result:
    st.caption("Select a job and refresh.")
    st.stop()

status = result.get("status", "unknown")
st.write(f"Status: `{status}`")

if status in {"queued", "running"}:
    # Show backend detail so users can distinguish normal warm-up from real failures.
    detail = result.get("error")
    if detail:
        st.info(f"Job is still processing. Detail: {detail}")
    else:
        st.info("Job is still processing. Refresh in a moment.")
    st.caption("Tip: click Fetch Result again after a few seconds to refresh status.")
    st.stop()
if status == "failed":
    st.error(result.get("error", "Analysis failed"))
    st.stop()
if status == "missing":
    st.error("Job not found")
    st.stop()

report = result.get("report", {})
report_md = result.get("report_md", "")
action_items: List[Dict[str, Any]] = result.get("action_items", [])

st.subheader("Markdown Report")
st.markdown(report_md if report_md else "No markdown report available")

st.subheader("Downloads")
report_json_str = json.dumps(report, indent=2)
action_items_str = json.dumps(action_items, indent=2)

c1, c2, c3 = st.columns(3)
with c1:
    st.download_button(
        "Download report.md",
        data=report_md,
        file_name=f"{job_id}_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
with c2:
    st.download_button(
        "Download report.json",
        data=report_json_str,
        file_name=f"{job_id}_report.json",
        mime="application/json",
        use_container_width=True,
    )
with c3:
    st.download_button(
        "Download action_items.json",
        data=action_items_str,
        file_name=f"{job_id}_action_items.json",
        mime="application/json",
        use_container_width=True,
    )

st.subheader("Action Items")
if action_items:
    # Dataframe view makes filtering by severity/component easy for triage.
    df = pd.DataFrame(action_items)
    sev_options = sorted(df["severity"].dropna().unique().tolist()) if "severity" in df else []
    comp_options = sorted(df["component"].dropna().unique().tolist()) if "component" in df else []

    f1, f2 = st.columns(2)
    with f1:
        selected_sev = st.multiselect("Filter severity", options=sev_options, default=sev_options)
    with f2:
        selected_comp = st.multiselect("Filter component", options=comp_options, default=comp_options)

    filtered = df.copy()
    if selected_sev:
        filtered = filtered[filtered["severity"].isin(selected_sev)]
    if selected_comp:
        filtered = filtered[filtered["component"].isin(selected_comp)]

    show_cols = [
        c
        for c in ["id", "severity", "component", "title", "impact", "confidence", "fix", "references"]
        if c in filtered.columns
    ]
    st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)
else:
    st.caption("No action items available.")

st.subheader("🚀 Send to n8n (Email + GitHub + Jira)")
st.caption(
    "One click triggers the n8n workflow which will: "
    "**① Email the report** → **② Create GitHub issues** → **③ Create Jira bugs** "
    "(for blocker/high severity items)."
)
high_count = sum(1 for item in action_items if item.get("severity", "").lower() in {"blocker", "high"})
st.info(f"📊 {len(action_items)} total issues · {high_count} blocker/high → tickets will be created for these.")

if st.button("⚡ Send to n8n", use_container_width=True, type="primary"):
    if not job_id:
        st.error("Select a job first.")
    else:
        try:
            with st.spinner("Sending to n8n → Email + GitHub + Jira..."):
                resp = send_to_n8n(job_id=job_id)
            n8n_resp = resp.get("n8n_response", resp)
            st.success("✅ n8n workflow completed!")

            # --- Email result ---
            email_data = n8n_resp.get("email", {})
            email_status = email_data.get("status", "unknown")
            if email_status == "sent":
                st.success(f"📧 Email sent to {email_data.get('to_email', 'recipient')}")
            else:
                st.warning(f"📧 Email: {email_status}")

            # --- GitHub issues with links ---
            tickets = n8n_resp.get("tickets", {})
            gh = tickets.get("github", n8n_resp.get("github", {}))
            gh_created = gh.get("created", 0)
            if gh_created:
                st.success(f"🐙 GitHub: {gh_created} issue(s) created")
                for iss in gh.get("issues", []):
                    url = iss.get("url") or iss.get("html_url", "")
                    title = iss.get("title", "")
                    number = iss.get("number", "")
                    st.markdown(f"- [#{number} — {title}]({url})")
            else:
                st.info(f"🐙 GitHub: {gh.get('status', 'n/a')}")

            # --- Jira bugs with links ---
            jr = tickets.get("jira", n8n_resp.get("jira", {}))
            jr_created = jr.get("created", 0)
            if jr_created:
                st.success(f"🎫 Jira: {jr_created} bug(s) created")
                for iss in jr.get("issues", []):
                    url = iss.get("url", "")
                    key = iss.get("key", "")
                    summary = iss.get("summary", "")
                    st.markdown(f"- [{key} — {summary}]({url})")
            else:
                st.info(f"🎫 Jira: {jr.get('status', 'n/a')}")

            with st.expander("Full n8n response"):
                st.json(resp)
        except Exception as exc:
            st.error(f"Failed to send to n8n: {exc}")

st.subheader("JSON Viewer")
st.json(report)
