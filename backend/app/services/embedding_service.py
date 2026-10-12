import logging
from typing import List
from app.config import settings
from app.core.ai_provider import BaseEmbeddingProvider, GeminiEmbeddingProvider, MockEmbeddingProvider

logger = logging.getLogger("prooflens.embedding")


class EmbeddingService:
    def __init__(self, provider: BaseEmbeddingProvider | None = None):
        if provider is not None:
            self.provider = provider
        elif settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() and not settings.GEMINI_API_KEY.startswith("your_"):
            try:
                self.provider = GeminiEmbeddingProvider()
                logger.info("Using GeminiEmbeddingProvider (text-embedding-004)")
            except Exception as e:
                logger.warning(f"Could not initialize GeminiEmbeddingProvider: {e}. Falling back to MockEmbeddingProvider.")
                self.provider = MockEmbeddingProvider()
        else:
            logger.info("No valid GEMINI_API_KEY found. Initializing MockEmbeddingProvider for offline/testing mode.")
            self.provider = MockEmbeddingProvider()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.provider.embed_texts(texts)

    def embed_query(self, query: str) -> List[float]:
        return self.provider.embed_query(query)


embedding_service = EmbeddingService()
