import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Native pgvector column (3072 dimensions matching gemini-embedding-001)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(3072), nullable=True)

    # JSON-serialized list of floats (backward compatibility & portable fallback)
    embedding_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    char_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    document = relationship("Document", back_populates="chunks")

    def get_vector(self) -> List[float]:
        """Return embedding vector as float list, checking native vector first then json."""
        if self.embedding is not None:
            return [float(x) for x in self.embedding]
        if self.embedding_json:
            return json.loads(self.embedding_json)
        return []
