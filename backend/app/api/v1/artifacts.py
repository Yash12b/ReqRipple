from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactUpdate,
    ArtifactResponse,
    ArtifactDetailResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.artifact_service import ArtifactService
from app.core.permissions import get_current_user, require_project_access, require_project_role
from app.models.user import User

router = APIRouter(tags=["Artifacts"])


@router.get("/projects/{project_id}/artifacts", response_model=PaginatedResponse[ArtifactResponse])
def list_artifacts(
    project_id: str,
    artifact_type: Optional[str] = Query(None),
    criticality: Optional[int] = Query(None, ge=1, le=5),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    items, total, total_pages = ArtifactService.list_artifacts(
        db,
        project_id,
        artifact_type=artifact_type,
        criticality=criticality,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/projects/{project_id}/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_artifact(
    project_id: str,
    data: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    _=Depends(require_project_role("ADMIN", "ANALYST", "DEVELOPER", "TESTER")),
    db: Session = Depends(get_db),
):
    return ArtifactService.create_artifact(db, project_id, data, current_user.id)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetailResponse)
def get_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = ArtifactService.get_detail(db, artifact_id)
    require_project_access(detail["project_id"], current_user, db)
    return detail


@router.patch("/artifacts/{artifact_id}", response_model=ArtifactResponse)
def update_artifact(
    artifact_id: str,
    data: ArtifactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    art = ArtifactService.get_by_id(db, artifact_id)
    require_project_role("ADMIN", "ANALYST", "DEVELOPER", "TESTER")(art.project_id, current_user, db)
    return ArtifactService.update_artifact(db, artifact_id, data)
