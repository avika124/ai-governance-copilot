"""
Reset script - clears all regulations and clauses so pipeline can re-run fresh.
Run this once before re-running run_pipeline.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_client import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM clauses;")
        cur.execute("DELETE FROM regulations;")
        conn.commit()
    print("✅ Cleared all clauses and regulations. Ready to re-run pipeline.")
except Exception as e:
    conn.rollback()
    print(f"❌ Failed: {e}")
finally:
    conn.close()
