from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.workspace import Workspace
from app.schemas.document import WorkspaceCreate, WorkspaceResponse

router = APIRouter()


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201, tags=["Workspaces"])
async def create_workspace(payload: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new research/document workspace."""
    workspace = Workspace(name=payload.name)
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("/workspaces", response_model=List[WorkspaceResponse], tags=["Workspaces"])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    """List all available workspaces."""
    result = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return result.scalars().all()


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse, tags=["Workspaces"])
async def get_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    """Get workspace by ID."""
    workspace = await db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return workspace
