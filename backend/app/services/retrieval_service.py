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
        """Retrieve top-k relevant document chunks within workspace scope using pgvector or cosine similarity."""
        query = query.strip()
        if not query:
            return []

        # 1. Embed query
        raw_query_vec = embedding_service.embed_query(query)

        # 2. If PostgreSQL, attempt native pgvector vector search (<=> cosine distance operator)
        if "postgresql" in settings.DATABASE_URL:
            try:
                async with db.begin_nested():
                    dist_expr = DocumentChunk.embedding.cosine_distance(raw_query_vec)
                    stmt = (
                        select(DocumentChunk, dist_expr.label("distance"))
                        .options(selectinload(DocumentChunk.document))
                        .where(
                            DocumentChunk.workspace_id == workspace_id,
                            DocumentChunk.embedding.is_not(None),
                        )
                    )
                    if document_ids:
                        stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
                    stmt = stmt.order_by(dist_expr).limit(top_k)

                    result = await db.execute(stmt)
                    rows = result.all()
                    if rows:
                        scored_chunks = []
                        for chk, dist in rows:
                            score = round(max(0.0, 1.0 - float(dist)), 4) if dist is not None else 0.0
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
                        return scored_chunks
            except Exception as e:
                logger.warning(f"Native pgvector SQL query fallback to in-memory: {e}")

        # 3. In-memory fallback (for SQLite tests or non-vector environments)
        try:
            query_vec = np.array(raw_query_vec, dtype=np.float32)
            stmt = (
                select(DocumentChunk)
                .options(selectinload(DocumentChunk.document))
                .where(DocumentChunk.workspace_id == workspace_id)
            )
            if document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

            result = await db.execute(stmt)
            chunks = result.scalars().all()
        except Exception as e:
            logger.error(f"In-memory retrieval fallback failed: {e}")
            try:
                await db.rollback()
            except Exception:
                pass
            return []

        if not chunks:
            return []

        scored_chunks: List[RetrievedChunk] = []
        for chk in chunks:
            chk_vec = np.array(chk.get_vector(), dtype=np.float32)
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

        scored_chunks.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_chunks[:top_k]


retrieval_service = RetrievalService()
