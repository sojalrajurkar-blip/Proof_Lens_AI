from abc import ABC, abstractmethod
from typing import List
import hashlib
import numpy as np
from app.config import settings


class BaseEmbeddingProvider(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text passages."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Embed a single query."""
        pass


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini embedding provider using the official google-genai SDK."""

    def __init__(self, api_key: str = settings.GEMINI_API_KEY, model: str = settings.GEMINI_EMBEDDING_MODEL):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env.")
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings: List[List[float]] = []
        # Batch in groups of 16 to respect payload limits
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.models.embed_content(
                model=self.model,
                contents=batch,
            )
            for emb in response.embeddings:
                embeddings.append(list(emb.values))
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=[query],
        )
        return list(response.embeddings[0].values)


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic 768-dimensional mock embedding provider for tests and offline development."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def _generate_vector(self, text: str) -> List[float]:
        # Generate a repeatable pseudo-random normalized vector from md5 hash
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._generate_vector(query)
