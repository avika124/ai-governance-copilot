"""FAISS index over corpus clauses for semantic search."""

import json
import logging
from typing import Any

import numpy as np

from app.config import FAISS_INDEX_PATH, FAISS_META_PATH, PROCESSED_DIR
from app.services.database import fetch_all_clauses_for_index
from app.services.embeddings import embed_texts

logger = logging.getLogger(__name__)

_index = None
_meta: list[dict[str, Any]] = []


def _load_faiss():
    import faiss
    return faiss


def build_or_load_index(force_rebuild: bool = False) -> tuple[Any, list[dict]]:
    """
    Load FAISS index from disk or build from database.

    Returns:
        (faiss_index, metadata list per vector row)
    """
    global _index, _meta
    if _index is not None and not force_rebuild and _meta:
        return _index, _meta

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not force_rebuild and FAISS_INDEX_PATH.exists() and FAISS_META_PATH.exists():
        faiss = _load_faiss()
        _index = faiss.read_index(str(FAISS_INDEX_PATH))
        _meta = json.loads(FAISS_META_PATH.read_text(encoding="utf-8"))
        logger.info("Loaded FAISS index: %d vectors", _index.ntotal)
        return _index, _meta

    rows = fetch_all_clauses_for_index()
    if not rows:
        logger.warning("No clauses in DB; FAISS index empty")
        faiss = _load_faiss()
        dim = 384  # all-MiniLM-L6-v2
        _index = faiss.IndexFlatIP(dim)
        _meta = []
        return _index, _meta

    texts = [r["clause_text"][:2000] for r in rows]
    emb = embed_texts(texts)
    dim = emb.shape[1]
    faiss = _load_faiss()
    # Inner product on normalized vectors = cosine similarity
    index = faiss.IndexFlatIP(dim)
    index.add(emb.astype(np.float32))

    _meta = [
        {
            "clause_id": r["clause_id"],
            "regulation_id": r["regulation_id"],
            "article_number": r.get("article_number"),
            "clause_text": r["clause_text"][:1500],
            "country": r.get("country"),
            "law_name": r.get("law_name"),
        }
        for r in rows
    ]
    _index = index
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    FAISS_META_PATH.write_text(json.dumps(_meta), encoding="utf-8")
    logger.info("Built FAISS index: %d vectors", index.ntotal)
    return _index, _meta


def search_similar(query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Return top_k similar clauses with similarity score."""
    try:
        index, meta = build_or_load_index()
    except Exception as e:
        logger.warning("Could not load FAISS index: %s", e)
        return []

    if index is None or index.ntotal == 0:
        return []

    from app.services.embeddings import embed_query
    q = embed_query(query_text[:2000])
    faiss = _load_faiss()
    q = np.ascontiguousarray(q.astype(np.float32))
    scores, idxs = index.search(q, min(top_k, index.ntotal))
    out = []
    for score, i in zip(scores[0], idxs[0]):
        if i < 0:
            continue
        m = dict(meta[i])
        m["similarity"] = float(score)
        out.append(m)
    return out
