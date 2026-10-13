from typing import List, Optional
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Payload for submitting a question to a workspace."""
    question: str = Field(..., min_length=2, max_length=1500, description="The user's question to be answered from workspace evidence.")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of candidate chunks to retrieve.")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document IDs to restrict evidence search.")
    similarity_threshold: Optional[float] = Field(default=None, description="Optional custom minimum cosine similarity threshold.")


class ValidatedCitation(BaseModel):
    """Server-verified citation directly mapped to a database DocumentChunk."""
    chunk_id: str = Field(..., description="Unique ID of the cited chunk.")
    document_id: str = Field(..., description="ID of the document containing the passage.")
    filename: str = Field(..., description="Server-derived original filename.")
    page_number: int = Field(..., description="Server-derived 1-based page number.")
    chunk_index: int = Field(..., description="Index of the chunk on the page.")
    excerpt: str = Field(..., description="Verbatim excerpt from the source chunk.")
    similarity_score: float = Field(..., description="Cosine similarity score of the chunk to the query.")


class GroundedAnswerResponse(BaseModel):
    """Structured response containing synthesized answer, citations, and status."""
    question: str
    workspace_id: str
    status: str = Field(..., description="'ANSWERED', 'INSUFFICIENT_EVIDENCE', or 'ERROR'.")
    answer: str
    citations: List[ValidatedCitation] = Field(default_factory=list)
    total_retrieved: int = Field(..., description="Number of candidate passages retrieved.")
    validated_citations_count: int = Field(..., description="Number of verified citations supporting the answer.")
    model_used: str = Field(..., description="Name of the generation model or provider used.")
    abstention_reason: Optional[str] = Field(default=None, description="Detailed reason if the system abstained from answering.")


class LLMAnswerOutput(BaseModel):
    """Strict JSON schema enforced on the LLM output."""
    status: str = Field(..., description="Must be 'ANSWERED' if direct evidence exists in passages, or 'INSUFFICIENT_EVIDENCE' if evidence is missing or partial.")
    answer: str = Field(..., description="Grounded answer synthesized strictly from the provided passages, or a clear explanation of what fact is missing.")
    cited_chunk_ids: List[str] = Field(default_factory=list, description="List of Passage IDs that directly provide evidence for the answer.")
