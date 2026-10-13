from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.workspace import Workspace
from app.schemas.query import RetrievalRequest, RetrievalResponse, RetrievedChunkResponse
from app.schemas.qa import QuestionRequest, GroundedAnswerResponse
from app.services.retrieval_service import retrieval_service
from app.services.qa_service import qa_service

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/retrieve",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    tags=["Retrieval"],
)
async def retrieve_passages(
    workspace_id: str,
    payload: RetrievalRequest,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve relevant document passages within a workspace using semantic similarity."""
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    retrieved = await retrieval_service.retrieve(
        db=db,
        workspace_id=workspace_id,
        query=payload.query,
        top_k=payload.top_k,
        document_ids=payload.document_ids,
    )

    chunk_responses = [
        RetrievedChunkResponse(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            page_number=c.page_number,
            chunk_index=c.chunk_index,
            content=c.content,
            similarity_score=c.similarity_score,
        )
        for c in retrieved
    ]

    return RetrievalResponse(
        query=payload.query,
        workspace_id=workspace_id,
        total_retrieved=len(chunk_responses),
        chunks=chunk_responses,
    )


@router.post(
    "/workspaces/{workspace_id}/ask",
    response_model=GroundedAnswerResponse,
    status_code=status.HTTP_200_OK,
    tags=["Q&A"],
)
async def ask_question(
    workspace_id: str,
    payload: QuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Answer a user question strictly grounded in retrieved workspace documents, with server-validated citations and abstention."""
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    return await qa_service.answer_question(
        db=db,
        workspace_id=workspace_id,
        payload=payload,
    )
