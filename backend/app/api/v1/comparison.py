from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.workspace import Workspace
from app.schemas.comparison import ComparisonRequest, ComparisonResponse
from app.services.comparison_service import comparison_service

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/compare",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    tags=["Comparison"],
)
async def compare_documents(
    workspace_id: str,
    payload: ComparisonRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compare findings across at least two documents on a topic, verifying citations per document."""
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    return await comparison_service.compare_documents(
        db=db,
        workspace_id=workspace_id,
        payload=payload,
    )
