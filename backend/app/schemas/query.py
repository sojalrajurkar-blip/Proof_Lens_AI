from typing import List, Optional
from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question or search query.")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of passages to retrieve.")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document filter.")


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    similarity_score: float


class RetrievalResponse(BaseModel):
    query: str
    workspace_id: str
    total_retrieved: int
    chunks: List[RetrievedChunkResponse]
