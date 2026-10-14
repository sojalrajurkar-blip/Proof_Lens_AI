import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services.embedding_service import embedding_service

logger = logging.getLogger("prooflens.retrieval")


class RetrievedChunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        filename: str,
        page_number: int,
        chunk_index: int,
        content: str,
        similarity_score: float,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.filename = filename
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.content = content
        self.similarity_score = round(similarity_score, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "similarity_score": self.similarity_score,
        }


class RetrievalService:
    @staticmethod
    def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    async def retrieve(
        self,
        db: AsyncSession,
        workspace_id: str,
        query: str,
        top_k: int = settings.RETRIEVAL_TOP_K,
        document_ids: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Retrieve top-k relevant document chunks within workspace scope using cosine similarity."""
        query = query.strip()
        if not query:
            return []

        # 1. Embed query
        query_vec = np.array(embedding_service.embed_query(query), dtype=np.float32)

        # 2. Query workspace chunks with document details loaded
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.workspace_id == workspace_id)
        )
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

        result = await db.execute(stmt)
        chunks = result.scalars().all()

        if not chunks:
            return []

        # 3. Calculate similarity score for each candidate chunk
        scored_chunks: List[RetrievedChunk] = []
        for chk in chunks:
            chk_vec = np.array(chk.embedding, dtype=np.float32)
            score = self._cosine_similarity(query_vec, chk_vec)
            scored_chunks.append(
                RetrievedChunk(
                    chunk_id=chk.id,
                    document_id=chk.document_id,
                    filename=chk.document.filename if chk.document else "Unknown",
                    page_number=chk.page_number,
                    chunk_index=chk.chunk_index,
                    content=chk.content,
                    similarity_score=score,
                )
            )

        # 4. Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x.similarity_score, reverse=True)

        # 5. Return top-k
        return scored_chunks[:top_k]


retrieval_service = RetrievalService()
