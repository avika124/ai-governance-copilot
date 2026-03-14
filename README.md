# Global AI Governance Copilot

An agentic AI system that analyzes draft AI policy text, finds gaps vs global standards, detects cross-border regulatory conflicts, and generates policy improvement recommendations.

**Phase 1:** EU + India only.

## Tech Stack

- **Backend:** Python + FastAPI
- **NLP:** HuggingFace Transformers (DeBERTa, all-MiniLM-L6-v2)
- **Vector Search:** FAISS
- **Agent:** LangChain
- **MLOps:** MLflow
- **Frontend:** Streamlit
- **Database:** SQLite (dev) / PostgreSQL (prod)

## Setup

```bash
cd ai-governance-copilot
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
```

## Data Pipeline

```bash
cd data_pipeline
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
# Edit .env: SUPABASE_DB_URL=postgresql://...

python run_pipeline.py
```

Fetches EU laws from EUR-Lex and India laws from legislative.gov.in. Stores regulations and clauses in Supabase.

## Project Structure

```
ai-governance-copilot/
├── data_pipeline/        # Data ingestion (EU + India → Supabase)
│   ├── config.py         # Law sources and URLs
│   ├── db_client.py      # Supabase connection
│   ├── run_pipeline.py   # Master script
│   └── ingest/            # fetch_eu, fetch_india, extract_clauses
├── data/
├── scripts/
├── db/
└── ...
```

## License

MIT
