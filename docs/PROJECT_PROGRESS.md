# Global AI Governance Copilot — Project Progress (2-Pager)

**Date:** March 2024 | **Repo:** github.com/avika124/ai-governance-copilot

---

## Page 1: What Has Been Done

### Data Pipeline (Complete)

A Python pipeline ingests EU and India laws, extracts clause-level text, and stores it in Supabase (PostgreSQL).

| Metric | Value |
|--------|-------|
| Regulations | 23 (13 EU, 10 India) |
| Clauses | ~5,147 |
| Failed | 2 India laws (404) |

**EU:** GDPR, ePrivacy, Cybersecurity Act, NIS2, AI Act, DSA, DMA, Data Act, Product Liability, Consumer Rights, DORA, Working Time, Platform Work.

**India:** DPDP Act, IT Act, BNS, BNSS, Consumer Protection, Competition, RBI, SEBI, Industrial Relations, Code on Wages, Clinical Establishments.

### Annotation Prep (Complete)

Clauses exported for Label Studio with three labels: **risk_type**, **actor_type**, **obligation_type**.

### Version Control

Project on GitHub; `.env` excluded; pipeline and annotation prep committed.

---

## Page 2: How We Did It

### Architecture

**Stack:** Python, requests, BeautifulSoup, PyMuPDF, spaCy, psycopg2, Supabase.

**Flow:** `config.py` → `fetch_eu.py` / `fetch_india.py` → `extract_clauses.py` → `db_client.py` → Supabase.

### EU Ingestion

- **Source:** EUR-Lex HTML (`eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:...`)
- **Method:** requests + BeautifulSoup; regex splits on "Article X"
- **Fallback:** PyMuPDF if HTML fails

### India Ingestion

- **Source:** legislative.gov.in PDFs
- **Method:** requests.Session with `Referer: https://legislative.gov.in/`, homepage visit for cookies, direct PDF GET
- **Parsing:** PyMuPDF extracts text; regex splits on "Section X"

### Clause Extraction

- **Tool:** spaCy `en_core_web_sm`
- **Rules:** Skip <30 chars, numbers, headers; UUID4 per clause; batch insert (50)

### Database (Supabase)

**regulations:** regulation_id, country, law_name, law_category, law_type, year, source_url, raw_text  
**clauses:** clause_id, regulation_id, article_number, clause_text, char_count

### Annotation Export

`python -m annotate.prepare_labelstudio [limit]` → `annotated/labelstudio_import.json`  
Config: `LABELSTUDIO_CONFIG.xml`

### Run Commands

```bash
cd data_pipeline && pip install -r requirements.txt && python -m spacy download en_core_web_sm
cp .env.example .env  # SUPABASE_DB_URL
python run_pipeline.py
python -m annotate.prepare_labelstudio 500
```

### Next Steps (Not Built)

Model training (DeBERTa, FAISS) | Agent pipeline (LangChain) | FastAPI | Streamlit UI
