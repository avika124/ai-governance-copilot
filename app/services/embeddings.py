"""Sentence-transformer embedding singleton."""

from functools import lru_cache
from typing import List

import numpy as np

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Return L2-normalized embeddings (n, dim)."""
    model = _get_model()
    emb = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(emb, dtype=np.float32)


def embed_query(text: str) -> np.ndarray:
    """Single query embedding, shape (1, dim)."""
    return embed_texts([text])
