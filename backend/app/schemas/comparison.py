from typing import List
from pydantic import BaseModel, Field
from app.schemas.qa import ValidatedCitation


class ComparisonRequest(BaseModel):
    """Payload for comparing findings across multiple documents on a topic."""
    topic: str = Field(..., min_length=3, max_length=1500, description="The topic or question to compare across documents.")
    document_ids: List[str] = Field(..., min_length=2, max_length=10, description="List of at least two document IDs to compare.")
    top_k_per_document: int = Field(default=3, ge=1, le=10, description="Number of candidate chunks to retrieve per document.")


class DocumentFinding(BaseModel):
    """Evidence finding extracted from a single document along with its supporting citations."""
    document_id: str
    filename: str
    status: str = Field(..., description="'FINDING_EXTRACTED' or 'INSUFFICIENT_EVIDENCE'")
    finding: str = Field(..., description="Summary of what this document states about the topic.")
    citations: List[ValidatedCitation] = Field(default_factory=list)


class ComparisonSynthesis(BaseModel):
    """Synthesis of the comparative relationship across the documents' claims."""
    relationship: str = Field(
        ...,
        description="'AGREEMENT', 'DIFFERENCE', 'CONTRADICTION', or 'INSUFFICIENT_EVIDENCE'"
    )
    summary: str = Field(..., description="Synthesis explaining how the documents relate to each other on the topic.")
    scope_warnings: List[str] = Field(
        default_factory=list,
        description="Warnings regarding differences in definitions, scopes, or non-comparable contexts."
    )


class ComparisonResponse(BaseModel):
    """Structured response for cross-document comparison."""
    workspace_id: str
    topic: str
    status: str = Field(..., description="'COMPLETED', 'PARTIAL', or 'INSUFFICIENT_EVIDENCE'")
    findings: List[DocumentFinding]
    synthesis: ComparisonSynthesis
    model_used: str


class LLMComparisonFindingItem(BaseModel):
    """Per-document finding schema returned by LLM."""
    document_id: str = Field(description="ID of the document.")
    status: str = Field(description="Must be 'FINDING_EXTRACTED' or 'INSUFFICIENT_EVIDENCE'.")
    finding: str = Field(description="Summary of facts extracted from this document's passages, or reason for missing evidence.")
    cited_chunk_ids: List[str] = Field(default_factory=list, description="Passage IDs directly supporting this finding.")


class LLMComparisonOutput(BaseModel):
    """Strict JSON schema enforced on Gemini for cross-document comparison synthesis."""
    findings: List[LLMComparisonFindingItem]
    relationship: str = Field(
        description="Must be 'AGREEMENT', 'DIFFERENCE', 'CONTRADICTION', or 'INSUFFICIENT_EVIDENCE'."
    )
    summary: str = Field(description="Synthesis comparing the documents' findings.")
    scope_warnings: List[str] = Field(
        default_factory=list,
        description="Explicit warnings if documents discuss different scopes, definitions, or contexts rather than contradicting."
    )
