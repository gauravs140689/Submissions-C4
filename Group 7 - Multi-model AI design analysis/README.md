# Multimodal AI Design Analysis Suite

Multimodal landing-page audit app for designers and PMs.
It analyzes URLs and uploaded images, grounds findings with a local RAG KB, and returns structured outputs in Streamlit and API.

## Current Highlights
- Input modes:
  - URL(s) -> full-page screenshots via Playwright
  - Image upload(s) (`png`, `jpg`, `jpeg`)
- Analysis stack:
  - OCR + visual heuristics (CTA, sections, palette/contrast, claims, nav)
  - RAG grounding from local KB (LanceDB)
  - LangGraph multi-agent critique (parallel agent stage)
  - OpenRouter multimodal assist
- Scoring:
  - `heuristic_score` (quality estimate)
  - `confidence_score` (reliability estimate)
  - benchmark-calibrated scoring mode: `startup`, `enterprise`, `brand-led`
- UX flow:
  - No manual job ID copy/paste required
  - Results page has recent jobs picker + cache-aware loading
- Automation:
  - Send report to n8n for email summary workflow

## Project Structure

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
  retriever.py
  lancedb_store.py

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

runs/
  {job_id}/...
```

## Model Configuration (OpenRouter)
Configured in `agents/models.py`.

- Primary model (default): `openai/gpt-4.1-mini`
- Secondary fallback (default): `google/gemini-2.5-flash`
- If model calls fail or key is missing, pipeline continues with OCR/signal heuristics.

## Environment Variables
Create env file:

```bash
cp .env.example .env
```

Set at least:
- `OPENROUTER_API_KEY`

Main variables:
- `API_BASE_URL` (Streamlit -> API)
- `N8N_WEBHOOK_URL` (optional default webhook)
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`)
- `OR_PRIMARY_MODEL`
- `OR_SECONDARY_MODEL`
- `OR_TIMEOUT_SECONDS`
- `OR_MAX_TOKENS`
- `OPENROUTER_HTTP_REFERER`
- `OPENROUTER_APP_TITLE`
- `LANGSMITH_API_KEY` (optional)

## Local Runbook
1. Install dependencies:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

2. Install OCR binary (recommended):
- Install `tesseract` on your machine.

3. Index KB into LanceDB:

```bash
PYTHONPATH=. python rag/index_kb.py
```

4. Start API:

```bash
PYTHONPATH=. uvicorn api.main:app --reload --port 8000
```

5. Start Streamlit:

```bash
API_BASE_URL=http://127.0.0.1:8000 PYTHONPATH=. streamlit run app_streamlit/Home.py
```

## Colab-Friendly Runbook (Dev/Experiment)

```bash
!pip install -r requirements.txt
!python -m playwright install chromium
!apt-get update && apt-get install -y tesseract-ocr
!PYTHONPATH=. python rag/index_kb.py
```

Run services:

```bash
# API
!nohup PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

# Streamlit
!nohup API_BASE_URL=http://127.0.0.1:8000 PYTHONPATH=. streamlit run app_streamlit/Home.py --server.port 8501 --server.headless true > st.log 2>&1 &
```

Use ngrok/cloudflared if external access is needed.

## API Contract

### `POST /analyze`
Multipart form fields:
- `images`: file list
- `urls`: newline/comma-separated URLs
- `context_json`: JSON string
- `mode`: `auto|sync|async`

Recommended context keys:
- `industry_category`
- `target_audience`
- `primary_conversion_goal`
- `brand_tone`
- `benchmark_mode` (`startup|enterprise|brand-led`)

Response:

```json
{
  "job_id": "uuid",
  "status": "queued|running|completed|failed",
  "mode": "sync|async",
  "result_available": false,
  "detail": "Use GET /result/{job_id} to poll"
}
```

### `GET /result/{job_id}`
Returns status and completed outputs (`report`, `report_md`, `action_items`) when ready.

### `GET /jobs/recent?limit=20`
Returns recent jobs for Results-page navigation.

### `POST /webhook/n8n`
Body:

```json
{
  "job_id": "uuid",
  "webhook_url": "https://optional-override"
}
```

## Output Artifacts
Per run:

```text
runs/{job_id}/
  outputs/
    report.json
    report.md
    action_items.json
  ticket_payloads/
    jira_issues.json
    github_issues.json
```

`report.json` includes `executive_snapshot` with:
- `benchmark_mode`
- `heuristic_score`
- `confidence_score`
- per-source scorecards (`good_things`, `could_improve`)

## Scoring Semantics
- `heuristic_score`: quality estimate from detected design signals and benchmark-mode weights.
- `confidence_score`: reliability estimate based on extraction coverage/quality.
- Contrast penalties are capped and heuristic score is confidence-aware (damped toward neutral when confidence is low).

## RAG + KB
- KB source files are in `kb/`.
- Indexer (`rag/index_kb.py`) chunks + embeds into LanceDB.
- Retriever injects relevant snippets into agent reasoning and report citations.

## n8n Integration
- Workflow blueprint: `workflows/n8n_workflow.json`
- Typical flow:
  1. Webhook trigger
  2. Optional fetch `/result/{job_id}`
  3. Send summary email
  4. Optional ticket creation branch if configured

## Safety Notes
- Designed for publicly accessible pages.
- Do not target authenticated/private pages.
- Keep timeouts/rate polite.
- Never hardcode secrets; use env vars.

## Schema Check

```bash
PYTHONPATH=. pytest -q
```

## Known Limitations
- OCR quality depends on screenshot clarity and installed Tesseract.
- Contrast checks are heuristic (not full DOM WCAG audit).
- Heuristic scoring is decision-support, not absolute ground truth.
