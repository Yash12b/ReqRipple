from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse,
)
from app.services.project_service import ProjectService
from app.core.permissions import get_current_user, require_project_access, require_project_role
from app.models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectResponse])
def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService.get_user_projects(db, current_user.id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService.create_project(db, data, current_user.id)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return ProjectService.get_project_detail(db, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    _=Depends(require_project_role("ADMIN")),
    db: Session = Depends(get_db),
):
    return ProjectService.update_project(db, project_id, data)


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def get_project_members(
    project_id: str,
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return ProjectService.get_members(db, project_id)


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: str,
    data: ProjectMemberCreate,
    _=Depends(require_project_role("ADMIN")),
    db: Session = Depends(get_db),
):
    return ProjectService.add_member(db, project_id, data)


@router.patch("/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
def update_member_role(
    project_id: str,
    member_id: str,
    data: ProjectMemberUpdate,
    _=Depends(require_project_role("ADMIN")),
    db: Session = Depends(get_db),
):
    return ProjectService.update_member_role(db, project_id, member_id, data)
