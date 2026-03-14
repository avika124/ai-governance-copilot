"""
Master script for the Global AI Governance data pipeline.

Run: python run_pipeline.py

1. Creates tables if they don't exist
2. Fetches all EU laws → extract clauses → insert to Supabase
3. Fetches all India laws → extract clauses → insert to Supabase
4. Prints summary: X regulations fetched, Y clauses inserted, Z failed
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_client import create_tables_if_not_exist
from ingest.fetch_eu import run_fetch_eu
from ingest.fetch_india import run_fetch_india

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the full data pipeline."""
    logger.info("Starting data pipeline")

    try:
        create_tables_if_not_exist()
    except Exception as e:
        logger.error("Failed to create tables: %s", e)
        sys.exit(1)

    eu_regs, eu_clauses, eu_failed = run_fetch_eu()
    india_regs, india_clauses, india_failed = run_fetch_india()

    total_regs = eu_regs + india_regs
    total_clauses = eu_clauses + india_clauses
    total_failed = eu_failed + india_failed

    print("\n" + "=" * 50)
    print("PIPELINE SUMMARY")
    print("=" * 50)
    print(f"EU:       {eu_regs} regulations, {eu_clauses} clauses, {eu_failed} failed")
    print(f"India:    {india_regs} regulations, {india_clauses} clauses, {india_failed} failed")
    print("-" * 50)
    print(f"TOTAL:    {total_regs} regulations fetched")
    print(f"          {total_clauses} clauses inserted")
    print(f"          {total_failed} failed")
    print("=" * 50)


if __name__ == "__main__":
    main()
