"""Embedding engine wrapping sentence-transformers/all-MiniLM-L6-v2 with singleton caching."""

import logging
from typing import List, Union, Optional
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# Expected embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIMENSION = 384


class VectorEmbedder:
    _instance: Optional["VectorEmbedder"] = None
    _model = None

    def __new__(cls) -> "VectorEmbedder":
        if cls._instance is None:
            cls._instance = super(VectorEmbedder, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self) -> None:
        """Initializes SentenceTransformer model once across application lifecycle."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("SentenceTransformer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {str(e)}")
            self._model = None

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a 384-dimensional dense vector embedding for input text.
        Returns a Python list of floats for pgvector / database storage.
        """
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIMENSION

        if self._model is None:
            # Fallback deterministic normalized vector if model unavailable
            return self._deterministic_fallback_vector(text)

        vector = self._model.encode(text.strip(), normalize_embeddings=True)
        return vector.tolist()

    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generates normalized 384-dimensional embeddings for a batch of strings.
        """
        if not texts:
            return []

        if self._model is None:
            return [self._deterministic_fallback_vector(t) for t in texts]

        clean_texts = [t.strip() if t and t.strip() else "unknown" for t in texts]
        vectors = self._model.encode(
            clean_texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return vectors.tolist()

    def compute_cosine_similarity(
        self, vec_a: Union[List[float], np.ndarray], vec_b: Union[List[float], np.ndarray]
    ) -> float:
        """
        Computes the cosine similarity between two 384-dimensional vectors in range [-1.0, 1.0].
        """
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        similarity = np.dot(a, b) / (norm_a * norm_b)
        return float(np.clip(similarity, -1.0, 1.0))

    def _deterministic_fallback_vector(self, text: str) -> List[float]:
        """Deterministic reproducible unit vector used only when torch/model is offline."""
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Generate 384 pseudo-floats from hash digest
        np.random.seed(int.from_bytes(h[:4], "little"))
        vec = np.random.randn(EMBEDDING_DIMENSION).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else [0.0] * EMBEDDING_DIMENSION


# Global singleton instance
embedder = VectorEmbedder()
