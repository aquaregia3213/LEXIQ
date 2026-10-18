import math
import hashlib
from abc import ABC, abstractmethod
from typing import List

DEFAULT_EMBEDDING_DIMENSION = 1536


class BaseEmbeddingProvider(ABC):
    """Abstract base interface for embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality of embeddings."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a single vector embedding for text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of texts."""
        pass


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic semantic embedding provider.
    Produces normalized vectors of dimension `dim` based on hashed term sub-words.
    Ensures consistent, reproducible semantic vector representations in testing
    and offline environments without external API calls or large model overhead.
    """

    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIMENSION):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _normalize(self, vector: List[float]) -> List[float]:
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return [0.0] * len(vector)
        return [v / norm for v in vector]

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim

        vector = [0.0] * self._dim
        clean_text = text.lower().strip()
        words = clean_text.split()

        # Project hashed word n-grams into vector space
        for word in words:
            # Word hashing
            h_val = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h_val % self._dim
            sign = 1.0 if (h_val & 1) else -1.0
            vector[idx] += sign * 1.5

            # 3-gram character subwords for morphological similarity
            for i in range(len(word) - 2):
                gram = word[i:i+3]
                gh_val = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
                g_idx = gh_val % self._dim
                g_sign = 1.0 if (gh_val & 1) else -1.0
                vector[g_idx] += g_sign * 0.5

        return self._normalize(vector)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def create_default_embedding_provider() -> BaseEmbeddingProvider:
    """Factory resolving the active embedding provider from settings."""
    from backend.app.config import settings
    active = settings.active_ai_provider
    if active == "gemini":
        from backend.app.services.gemini_service import GeminiEmbeddingProvider
        return GeminiEmbeddingProvider()
    elif active == "deterministic":
        return DeterministicEmbeddingProvider()
    else:
        if settings.GEMINI_API_KEY:
            from backend.app.services.gemini_service import GeminiEmbeddingProvider
            return GeminiEmbeddingProvider()
        return DeterministicEmbeddingProvider()


class EmbeddingService:
    """
    Service wrapper managing application embedding generation.
    Supports switching providers dynamically based on settings.
    """

    def __init__(self, provider: Optional[BaseEmbeddingProvider] = None):
        self._custom_provider = provider

    @property
    def provider(self) -> BaseEmbeddingProvider:
        if self._custom_provider is not None:
            return self._custom_provider
        return create_default_embedding_provider()

    @provider.setter
    def provider(self, new_provider: BaseEmbeddingProvider):
        self._custom_provider = new_provider

    def get_dimension(self) -> int:
        return self.provider.dimension

    def embed_text(self, text: str) -> List[float]:
        return self.provider.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.provider.embed_batch(texts)


# Default singleton instance
_default_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Return configured EmbeddingService instance."""
    return _default_service

