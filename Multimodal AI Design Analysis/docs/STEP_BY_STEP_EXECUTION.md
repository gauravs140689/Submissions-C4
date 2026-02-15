# Step-by-Step Execution Guide

This document explains how the **Multimodal AI Design Analysis Suite** executes a request end-to-end, with practical examples.

## 1) User submits input
You can start from either:
- Streamlit UI (`app_streamlit/pages/1_Analyze.py`)
- API directly (`POST /analyze`)

Supported inputs:
- Image files (`png`, `jpg`, `jpeg`)
- URL list (one or many)
- Optional context: industry, audience, conversion goal, tone, notes

Example (API request):
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "urls=https://example.com" \
  -F "mode=sync" \
  -F 'context_json={"industry_category":"SaaS","target_audience":"Founders","primary_conversion_goal":"Book demo"}'
```

Example response:
```json
{
  "job_id": "ef651208-2cd1-42dd-ad86-35132caa672c",
  "status": "completed",
  "mode": "sync",
  "result_available": true,
  "detail": "Pipeline completed"
}
```

## 2) API decides execution mode
File: `api/main.py`

Mode behavior:
- `sync`: runs pipeline in threadpool (safe for Playwright sync API)
- `async`: queued in FastAPI background task
- `auto`: sync for small jobs, async for larger jobs

Job status is written to:
- `runs/{job_id}/job_status.json`

Example status payload:
```json
{
  "job_id": "ef651208-2cd1-42dd-ad86-35132caa672c",
  "status": "running",
  "detail": "Pipeline started (first run can take longer while models load)",
  "updated_at": "2026-02-14T14:30:40.000000+00:00"
}
```

## 3) LangGraph pipeline starts
File: `agents/graph.py`

Order:
1. `ingest_node`
2. `signals_node`
3. `rag_prepare_node`
4. Parallel fan-out:
   - `visual_analysis_agent_node`
   - `ux_critique_agent_node`
   - `market_patterns_agent_node`
   - `accessibility_agent_node`
5. `merge_dedupe_node`
6. `report_compose_node`

## 4) Ingestion stage
File: `core/ingest.py`

Actions:
- Creates per-job directories under `runs/{job_id}/`
- Saves uploaded files to `inputs/`
- Captures URL screenshots to `screenshots/` via Playwright
- Writes `inputs/manifest.json`

Example manifest:
```json
{
  "job_id": "ef651208-2cd1-42dd-ad86-35132caa672c",
  "context": {"industry_category":"SaaS"},
  "items": [
    {
      "source_id": "url_001",
      "source_type": "url",
      "source_ref": "https://example.com",
      "image_path": "runs/ef651208-2cd1-42dd-ad86-35132caa672c/screenshots/url_001.png",
      "capture_status": "ok",
      "title": "Example Domain"
    }
  ]
}
```

## 5) Signal extraction stage
File: `core/signals.py`

For each source image, the app extracts:
- `ocr_text_blocks`
- `page_sections`
- `detected_ctas`
- `palette`
- `contrast_warnings`
- `key_claims`
- `nav_items`

Saved to:
- `runs/{job_id}/signals/{source_id}.json`

Example (truncated):
```json
{
  "source_id": "url_001",
  "source_type": "url",
  "ocr_text_blocks": [],
  "page_sections": ["hero", "content", "footer"],
  "detected_ctas": [],
  "palette": [{"hex":"#f5f5f5","ratio":0.33}],
  "contrast_warnings": ["Low approximate contrast between #aaaaaa and #ffffff (ratio 2.10)"]
}
```

## 6) RAG preparation stage
Files:
- `rag/index_kb.py` (one-time indexing)
- `rag/lancedb_store.py`
- `rag/retriever.py`

Flow:
- KB markdown files in `kb/` are chunked and embedded into LanceDB
- Query is built from user context + landing-page analysis intent
- Top snippets are attached to graph state as citations

Example snippet in state:
```json
{
  "snippet_id": "landing_page_best_practices-001",
  "quote": "State the primary value proposition in one concise headline.",
  "source": "landing_page_best_practices.md",
  "category": "landing_page"
}
```

## 7) Parallel agent analysis stage
Files:
- `agents/nodes.py`
- `agents/models.py`
- `agents/prompts.py`

All 4 agents run in parallel after RAG prep:
- Visual analysis agent
- UX critique agent
- Market patterns agent
- Accessibility agent

Each agent outputs strict `Issue` JSON objects with fields like:
- `title`, `issue`, `evidence`, `principle`, `impact`, `severity`, `fix`, `acceptance_criteria`, `references`, `component`

Example issue:
```json
{
  "id": "6804e1cb37",
  "title": "Primary CTA not obvious",
  "issue": "No clear primary call-to-action was detected in visible content.",
  "impact": "conversion",
  "severity": "high",
  "fix": "Add a single primary CTA button in hero with action-led text and high visual prominence.",
  "acceptance_criteria": [
    "Hero section includes one primary CTA",
    "CTA text uses explicit action verb"
  ],
  "references": ["landing_page_best_practices-001"],
  "component": "cta"
}
```

## 8) Merge, dedupe, and report composition
Files:
- `agents/nodes.py` (`merge_dedupe_node`, `report_compose_node`)
- `core/reporting.py`

Actions:
- Deduplicate similar issues
- Sort by severity/impact
- Build report summary + quick wins + backlog + comparison
- Render markdown report
- Build Jira/GitHub ticket payloads

## 9) Output persistence
Saved under `runs/{job_id}/`:
- `outputs/report.json`
- `outputs/report.md`
- `outputs/action_items.json`
- `ticket_payloads/jira_issues.json`
- `ticket_payloads/github_issues.json`

Example command:
```bash
find runs/ef651208-2cd1-42dd-ad86-35132caa672c -maxdepth 3 -type f | sort
```

## 10) Result retrieval
API endpoint:
- `GET /result/{job_id}`

Example:
```bash
curl -s http://127.0.0.1:8000/result/ef651208-2cd1-42dd-ad86-35132caa672c
```

The Streamlit Results page (`app_streamlit/pages/2_Results.py`) uses this endpoint to:
- Show status
- Render markdown
- Show action items table
- Enable JSON/MD downloads

## 11) Optional n8n automation
Options:
- Streamlit "Send to n8n" button
- API helper: `POST /webhook/n8n`

n8n flow (`workflows/n8n_workflow.json`):
1. Receives `job_id` or report payload
2. Fetches result if needed
3. Sends email summary
4. Optionally creates Jira/GitHub tickets

## 12) Troubleshooting quick checks
Check job progress:
```bash
cat runs/<job_id>/job_status.json
```

Check result availability:
```bash
curl -s http://127.0.0.1:8000/result/<job_id>
```

Check server health:
```bash
curl -s http://127.0.0.1:8000/health
```

If job seems slow on first run:
- Initial model downloads/warm-up can add delay
- OCR may be skipped if local Tesseract is not installed
- Report still completes with fallback paths
