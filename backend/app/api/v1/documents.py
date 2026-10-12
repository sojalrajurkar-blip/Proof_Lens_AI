import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.workspace import Workspace
from app.models.document import Document, DocumentPage
from app.schemas.document import DocumentResponse, DocumentDetailResponse
from app.services.storage_service import storage_service
from app.services.pdf_service import pdf_service

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, validate size and type, extract page-by-page text, and record provenance."""
    # 1. Verify workspace exists
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    # 2. Check document count limit
    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.workspace_id == workspace_id)
    )
    current_count = doc_count_result.scalar_one()
    if current_count >= settings.MAX_DOCUMENTS_PER_WORKSPACE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workspace reached document limit of {settings.MAX_DOCUMENTS_PER_WORKSPACE}.",
        )

    # 3. Validate file extension and MIME type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) are supported.",
        )

    # 4. Read file content and validate size
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 5. Generate document ID and persist PDF to local storage
    document_id = str(uuid.uuid4())
    saved_path = await storage_service.save_pdf(workspace_id, document_id, content)

    # 6. Extract page-aware text
    try:
        extraction = pdf_service.extract_text_from_bytes(content)
        doc_status = "UNSUPPORTED_SCANNED_PDF" if extraction.is_scanned else "COMPLETED"
        error_msg = "Document appears to be scanned or contains no extractable text." if extraction.is_scanned else None
    except Exception as e:
        doc_status = "FAILED"
        error_msg = str(e)
        extraction = None

    # 7. Record Document in database
    document = Document(
        id=document_id,
        workspace_id=workspace_id,
        filename=file.filename,
        file_path=saved_path,
        file_size_bytes=len(content),
        mime_type="application/pdf",
        page_count=extraction.page_count if extraction else 0,
        status=doc_status,
        error_message=error_msg,
    )
    db.add(document)

    # 8. Record DocumentPages and Chunks if extraction succeeded
    if extraction and extraction.pages and not extraction.is_scanned:
        for p in extraction.pages:
            page_record = DocumentPage(
                document_id=document_id,
                page_number=p["page_number"],
                text=p["text"],
                char_count=p["char_count"],
                word_count=p["word_count"],
            )
            db.add(page_record)

        # 9. Generate page-bound chunks and vector embeddings
        from app.services.chunking_service import chunking_service
        from app.services.embedding_service import embedding_service
        from app.models.chunk import DocumentChunk
        import json

        chunks = chunking_service.chunk_document_pages(extraction.pages)
        if chunks:
            chunk_texts = [c["content"] for c in chunks]
            vectors = embedding_service.embed_texts(chunk_texts)

            for c, vec in zip(chunks, vectors):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    workspace_id=workspace_id,
                    page_number=c["page_number"],
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    embedding_json=json.dumps(vec),
                    char_count=c["char_count"],
                    word_count=c["word_count"],
                )
                db.add(chunk_record)

    await db.commit()
    await db.refresh(document)
    return document


@router.get(
    "/workspaces/{workspace_id}/documents",
    response_model=List[DocumentResponse],
    tags=["Documents"],
)
async def list_documents(workspace_id: str, db: AsyncSession = Depends(get_db)):
    """List all documents uploaded to a workspace."""
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    result = await db.execute(
        select(Document)
        .where(Document.workspace_id == workspace_id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get(
    "/workspaces/{workspace_id}/documents/{document_id}",
    response_model=DocumentDetailResponse,
    tags=["Documents"],
)
async def get_document(
    workspace_id: str,
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get document details including page-by-page extracted text."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.workspace_id == workspace_id, Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.delete(
    "/workspaces/{workspace_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Documents"],
)
async def delete_document(
    workspace_id: str,
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document, its database records, and its physical file."""
    document = await db.get(Document, document_id)
    if not document or document.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Document not found.")

    storage_service.delete_document(workspace_id, document_id)
    await db.delete(document)
    await db.commit()
    return None
