from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPageResponse(BaseModel):
    id: str
    page_number: int
    text: str
    char_count: int
    word_count: int

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    file_size_bytes: int
    page_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    pages: List[DocumentPageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PassageDetailResponse(BaseModel):
    chunk_id: str
    document_id: str
    workspace_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    char_count: int
    word_count: int
    prev_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
