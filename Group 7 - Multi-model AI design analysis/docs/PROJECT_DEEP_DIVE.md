# Multimodal AI Design Analysis Suite: Full Product + Technical Deep Dive

This document is the authoritative handoff for product and engineering contributors.
It reflects the latest implementation in this repository.

## 1) Product Purpose
The application audits web landing page quality from:
- Uploaded screenshots/images
- Live website URLs (captured via Playwright)

It produces:
- `report.json` (structured machine-readable report)
- `report.md` (human-readable report)
- `action_items.json` (flattened backlog)
- Jira/GitHub ticket payload JSON
- Optional n8n push for downstream automation

## 2) Core Product Behavior
Users can:
- Upload multiple PNG/JPG/JPEG images
- Paste one or more URLs
- Provide context fields:
  - industry/category
  - target audience
  - primary conversion goal
  - brand tone
  - benchmark mode (`startup`, `enterprise`, `brand-led`)
- Trigger analysis in `auto`, `sync`, or `async` mode
- View results in Streamlit and download artifacts
- Send completed reports to n8n

## 3) Current Repository Structure

```text
app_streamlit/
  Home.py
  utils.py
  pages/
    1_Analyze.py
    2_Results.py

api/
  main.py
  schemas.py

core/
  ingest.py
  screenshot.py
  signals.py
  reporting.py
  storage.py

rag/
  index_kb.py
  lancedb_store.py
  retriever.py

agents/
  prompts.py
  models.py
  graph.py
  nodes.py

kb/
  landing_page_best_practices.md
  ux_heuristics.md
  accessibility_checklist.md
  conversion_copy_patterns.md

workflows/
  n8n_workflow.json

docs/
  STEP_BY_STEP_EXECUTION.md
  PROJECT_DEEP_DIVE.md
```

## 4) Runtime Architecture (End-to-End)
1. User submits analysis request from Streamlit or API.
2. API creates a `job_id` (UUID) and initializes `runs/{job_id}/...` artifacts.
3. LangGraph pipeline runs:
   - ingestion
   - signal extraction
   - RAG preparation
   - parallel agent analysis
   - merge/dedupe
   - report composition
4. Outputs persist to filesystem.
5. Results are fetched via `GET /result/{job_id}`.
6. Optional webhook push sends result payload to n8n.

## 5) Job Artifact Layout

```text
runs/{job_id}/
  inputs/
    manifest.json
  screenshots/
    url_###.png
  signals/
    source_id.json
  outputs/
    report.json
    report.md
    action_items.json
  ticket_payloads/
    jira_issues.json
    github_issues.json
  job_status.json
```

Why this design works:
- full traceability
- easy debugging per stage
- deterministic retrieval of completed jobs

## 6) API Surface
Implemented in `api/main.py` with schemas in `api/schemas.py`.

### `POST /analyze`
Multipart fields:
- `images`
- `urls`
- `context_json`
- `mode` (`auto`, `sync`, `async`)

Behavior:
- `sync`: runs in threadpool (safe for sync Playwright calls)
- `async`: background task execution
- `auto`: sync for small jobs, async for larger jobs

### `GET /result/{job_id}`
Returns status and completed payloads.
Statuses:
- `missing`, `queued`, `running`, `failed`, `completed`

### `GET /jobs/recent?limit=20`
Returns recent job list used by Streamlit Results page.
Payload per job:
- `job_id`, `status`, `detail`, `updated_at`

### `POST /webhook/n8n`
Pushes completed result to n8n webhook.
Webhook source:
- request `webhook_url` override OR
- env `N8N_WEBHOOK_URL`

## 7) LangGraph Design
Implemented in `agents/graph.py` and `agents/nodes.py`.

### Current graph topology
- `ingest_node`
- `signals_node`
- `rag_prepare_node`
- parallel fan-out:
  - `visual_analysis_agent_node`
  - `ux_critique_agent_node`
  - `market_patterns_agent_node`
  - `accessibility_agent_node`
- fan-in:
  - `merge_dedupe_node`
- `report_compose_node`

### Important implementation detail
Nodes return only their updated keys (not full state dict), which avoids concurrent state update collisions in the parallel stage.

## 8) Agent Node Responsibilities
- `ingest_node`: normalize uploads/URLs and persist input artifacts
- `signals_node`: compute OCR/palette/CTA/sections/nav/claims signals
- `rag_prepare_node`: retrieve top KB snippets and attach citations
- `visual_analysis_agent_node`: hierarchy, CTA prominence, contrast, nav cues
- `ux_critique_agent_node`: value proposition clarity and cognitive load
- `market_patterns_agent_node`: trust/social-proof and risk-reversal patterns
- `accessibility_agent_node`: contrast/readability a11y concerns
- `merge_dedupe_node`: dedupe by title+component and keep highest severity
- `report_compose_node`: compose snapshot, summary, backlog, comparison, tickets

## 9) Multimodal Model Layer
Implemented in `agents/models.py`.

Current model strategy (OpenRouter):
- primary: `openai/gpt-4.1-mini`
- secondary fallback: `google/gemini-2.5-flash`

If model calls fail or API key is missing:
- system falls back to OCR/signal-only critique

Environment variables:
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OR_PRIMARY_MODEL`
- `OR_SECONDARY_MODEL`
- `OR_TIMEOUT_SECONDS`
- `OR_MAX_TOKENS`
- `OPENROUTER_HTTP_REFERER`
- `OPENROUTER_APP_TITLE`

## 10) Screenshot Capture Reliability
Implemented in `core/screenshot.py`.

Current fix:
- Automatically points Playwright to repo-local `.playwright` binaries when available via `PLAYWRIGHT_BROWSERS_PATH`.

Why this matters:
- Prevents executable path mismatch failures between local cached browsers and project-local installs.

## 11) Signal Extraction Engine
Implemented in `core/signals.py`.

Per-source signal payload includes:
- `ocr_text_blocks`
- `page_sections`
- `detected_ctas`
- `palette`
- `contrast_warnings`
- `key_claims`
- `nav_items`

Fallback behavior:
- extraction continues even if OCR is unavailable
- safe defaults preserve schema validity

## 12) RAG Design and KB Linkage

### Why RAG exists
RAG grounds findings in curated standards rather than raw heuristics alone.

### KB files
- `kb/landing_page_best_practices.md`
- `kb/ux_heuristics.md`
- `kb/accessibility_checklist.md`
- `kb/conversion_copy_patterns.md`

These are now upgraded to AI SaaS-oriented standards (prompt-first UX, trust systems, enterprise signals, conversion copy rigor).

### Indexing
- Script: `rag/index_kb.py`
- Chunks KB content, enriches metadata, and stores vectors in LanceDB
- Embedding model: `BAAI/bge-small-en-v1.5`

### Retrieval usage at runtime
- `rag_prepare_node` forms query from context
- retrieves top snippets
- attaches `snippet_id` references to issues
- `report.md` and `report.json` include citations

## 13) Report Composition and Scoring (Latest)
Implemented in `agents/nodes.py` and `core/reporting.py`.

### Executive Snapshot (top of report)
`report.executive_snapshot` includes:
- `headline`
- `benchmark_mode`
- `heuristic_score` (0-10)
- `confidence_score` (0-10)
- `overall_score` (legacy alias)
- `overall_rating`
- `top_strengths`
- `top_improvements`
- `source_scorecards` per design

### Per-source scorecard
Each source includes:
- `heuristic_score`
- `confidence_score`
- `score` (legacy alias)
- `grade`
- `good_things`
- `could_improve`

### Benchmark mode calibration
Supported modes:
- `startup`
- `enterprise`
- `brand-led`

Each mode applies different scoring weights for:
- CTA strictness
- trust/risk expectations
- enterprise readiness
- contrast penalties

### Contrast penalty cap
Contrast impact is now capped to avoid unrealistic score collapse.

### Confidence-aware damping
Final heuristic score is pulled toward neutral baseline when confidence is low, reducing over-penalization from uncertain detection.

## 14) Streamlit UX (Latest)

### Analyze page (`app_streamlit/pages/1_Analyze.py`)
- collects inputs + context + benchmark mode
- submits job
- keeps `job_history` in session
- optional auto-open Results after submit

### Results page (`app_streamlit/pages/2_Results.py`)
No manual job ID paste required:
- recent jobs dropdown (from API + session history)
- refresh selected job
- cached result reuse
- refresh job list action
- markdown + JSON + action table + n8n send

## 15) n8n Workflow Role
Defined in `workflows/n8n_workflow.json`.

Typical flow:
1. Webhook receives `job_id` or full payload
2. Fetches `GET /result/{job_id}` if needed
3. Sends summary email
4. Optional branch to create Jira/GitHub issues
5. Skips ticket branches gracefully when creds are missing

## 16) Observability and Error Handling
- Per-job status tracking in `job_status.json`
- API status/error propagation to clients
- persisted intermediate artifacts for debugging
- optional LangSmith tracing via env key

Common latency sources:
- first-run model warmup
- OCR quality dependency
- JS-heavy pages in Playwright capture

## 17) Known Limitations
- agent outputs are still largely deterministic heuristics
- contrast checks are heuristic, not full DOM WCAG audits
- no dedicated distributed queue backend (Redis/Celery)
- progress is status-based, not stage-streamed live telemetry

## 18) Recommended Next Enhancements
1. Stage-level progress states in API status (`capturing`, `signals`, `rag`, `agents`, `reporting`).
2. "RAG Debug" panel in Results to show retrieved snippet text and source files.
3. Optional stricter LLM-structured issue generation per agent with repair parser.
4. Comparison dashboard with trend tracking across repeated runs.
5. SLA and closure tracking for generated action items.

## 19) Quick Start (Current)

```bash
# 1) install deps
pip install -r requirements.txt
python -m playwright install chromium

# 2) index KB
PYTHONPATH=. python -m rag.index_kb

# 3) start API
PYTHONPATH=. uvicorn api.main:app --reload --port 8000

# 4) start Streamlit
API_BASE_URL=http://127.0.0.1:8000 PYTHONPATH=. streamlit run app_streamlit/Home.py
```

## 20) Fast Read Order for New Contributors
1. `agents/graph.py`
2. `agents/nodes.py`
3. `api/main.py`
4. `core/signals.py`
5. `core/reporting.py`
6. `rag/lancedb_store.py`
7. `app_streamlit/pages/1_Analyze.py`
8. `app_streamlit/pages/2_Results.py`
9. `workflows/n8n_workflow.json`

That sequence gives full understanding of orchestration, contracts, scoring, and UX behavior.
