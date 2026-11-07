from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.requirement import (
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
    RequirementDetailResponse,
    RequirementVersionResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.requirement_service import RequirementService
from app.core.permissions import get_current_user, require_project_access, require_project_role
from app.models.user import User

router = APIRouter(tags=["Requirements"])


@router.get("/projects/{project_id}/requirements", response_model=PaginatedResponse[RequirementResponse])
def list_requirements(
    project_id: str,
    requirement_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    lifecycle_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    items, total, total_pages = RequirementService.list_requirements(
        db,
        project_id,
        requirement_type=requirement_type,
        priority=priority,
        lifecycle_status=lifecycle_status,
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
    "/projects/{project_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement(
    project_id: str,
    data: RequirementCreate,
    current_user: User = Depends(get_current_user),
    _=Depends(require_project_role("ADMIN", "ANALYST")),
    db: Session = Depends(get_db),
):
    req = RequirementService.create_requirement(db, project_id, data, current_user.id)
    return RequirementService.get_detail(db, req.id)


@router.get("/requirements/{requirement_id}", response_model=RequirementDetailResponse)
def get_requirement(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = RequirementService.get_detail(db, requirement_id)
    # Validate membership for project
    require_project_access(detail["project_id"], current_user, db)
    return detail


@router.patch("/requirements/{requirement_id}", response_model=RequirementResponse)
def update_requirement_metadata(
    requirement_id: str,
    data: RequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = RequirementService.get_by_id(db, requirement_id)
    require_project_role("ADMIN", "ANALYST")(req.project_id, current_user, db)
    updated = RequirementService.update_metadata(db, requirement_id, data)
    return RequirementService.get_detail(db, updated.id)


@router.get("/requirements/{requirement_id}/versions", response_model=List[RequirementVersionResponse])
def get_requirement_versions(
    requirement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = RequirementService.get_by_id(db, requirement_id)
    require_project_access(req.project_id, current_user, db)
    return RequirementService.get_versions(db, requirement_id)
