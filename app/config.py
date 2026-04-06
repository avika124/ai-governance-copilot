"""Application configuration."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PIPELINE = PROJECT_ROOT / "data_pipeline"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FAISS_INDEX_PATH = PROCESSED_DIR / "faiss.index"
FAISS_META_PATH = PROCESSED_DIR / "faiss_meta.json"

# Load env from data_pipeline first, then project root
for env_path in (DATA_PIPELINE / ".env", PROJECT_ROOT / ".env"):
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE_URL = os.getenv("API_BASE_URL", f"http://localhost:{API_PORT}")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FAISS_SIMILARITY_THRESHOLD = 0.75
