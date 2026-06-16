import os
import logging

# FastEmbed imports (if available)
try:
    from fastembed import TextEmbedding
    _fastembed = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
except Exception as e:
    logging.warning(f"FastEmbed not available: {e}")
    _fastembed = None

# sentence‑transformers fallback
try:
    from sentence_transformers import SentenceTransformer
    _st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
except Exception as e:
    logging.warning(f"sentence‑transformers not available: {e}")
    _st_model = None

def embed_text(text: str) -> list[float]:
    """Return a 768‑dim embedding for *text*.
    Prefer FastEmbed (low RAM) and fall back to sentence‑transformers.
    """
    if _fastembed:
        return list(_fastembed.embed([text]))[0].tolist()
    if _st_model:
        return _st_model.encode([text])[0].tolist()
    raise RuntimeError("No embedding backend available. Install FastEmbed or sentence‑transformers.")
