# Global AI Governance Copilot

An agentic system that analyzes draft AI policy text against EU and India legal corpora: **coverage gaps**, **cross-border conflict signals**, and **policy option cards** (minimal / moderate / strict).

---

## Architecture

| Layer | Technology |
|--------|------------|
| Data | Supabase (PostgreSQL), ~5k+ clauses |
| Embeddings & search | `sentence-transformers/all-MiniLM-L6-v2`, FAISS (IndexFlatIP) |
| Classification | Keyword-based risk / actor / obligation tags (extensible to fine-tuned models) |
| API | FastAPI |
| UI | Streamlit |
| Reports | PDF (ReportLab) |

**Pipeline:** `parse_clauses` → `classify_clauses` → `check_coverage` → `detect_conflicts` → `generate_recommendations`

---

## Quick start

### 1. Environment

```bash
cd ai-governance-copilot
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set `SUPABASE_DB_URL` in `data_pipeline/.env` (or project `.env`).

### 2. Data pipeline (first time / refresh corpus)

```bash
cd data_pipeline
python run_pipeline.py
```

### 3. API server

From **project root**:

```bash
export PYTHONPATH=.
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

- Docs: http://127.0.0.1:8000/docs  
- `POST /analyze` — full analysis  
- `GET /regulations`, `GET /clauses/{regulation_id}`, `GET /reports/{id}`, `GET /conflicts`

### 4. Streamlit UI

```bash
export PYTHONPATH=.
streamlit run app/ui/app.py
```

Open the URL shown (default http://localhost:8501). Set **API base URL** in the sidebar if the API is not on `http://127.0.0.1:8000`.

---

## Project layout

```
ai-governance-copilot/
├── app/
│   ├── agent/           # pipeline, coverage_checker, conflict_detector, recommender, classifier
│   ├── api/main.py      # FastAPI
│   ├── services/        # database, embeddings, faiss_index
│   ├── ui/app.py        # Streamlit
│   └── utils/pdf_report.py
├── data_pipeline/       # Ingestion → Supabase
├── data/processed/      # FAISS index (generated)
└── docs/
```

---

## Workflow diagram

Open in a browser: [`docs/workflow.html`](docs/workflow.html) — Mermaid flowchart of the data pipeline, agent, API, and UI.

## GitHub

https://github.com/avika124/ai-governance-copilot

---

## License

MIT
