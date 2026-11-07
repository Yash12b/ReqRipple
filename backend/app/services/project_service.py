from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.models.requirement import Requirement
from app.models.artifact import Artifact
from app.models.graph import TraceabilityEdge
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberCreate, ProjectMemberUpdate
from app.core.errors import EntityNotFoundError, EntityConflictError, PermissionDeniedError


class ProjectService:
    @staticmethod
    def create_project(db: Session, data: ProjectCreate, owner_id: str) -> Project:
        project = Project(
            name=data.name,
            description=data.description,
            domain=data.domain,
            owner_user_id=owner_id,
        )
        if data.settings:
            project.settings_json = data.settings

        db.add(project)
        db.flush()

        # Add owner as ADMIN member
        member = ProjectMember(
            project_id=project.id,
            user_id=owner_id,
            role="ADMIN",
        )
        db.add(member)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_user_projects(db: Session, user_id: str) -> List[Project]:
        # Return projects where user is owner or member
        projects = (
            db.query(Project)
            .outerjoin(ProjectMember, Project.id == ProjectMember.project_id)
            .filter((Project.owner_user_id == user_id) | (ProjectMember.user_id == user_id))
            .distinct()
            .order_by(Project.created_at.desc())
            .all()
        )
        return projects

    @staticmethod
    def get_project_by_id(db: Session, project_id: str) -> Project:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise EntityNotFoundError("Project", project_id)
        return project

    @staticmethod
    def get_project_detail(db: Session, project_id: str) -> dict:
        project = ProjectService.get_project_by_id(db, project_id)

        req_count = db.query(func.count(Requirement.id)).filter(Requirement.project_id == project_id).scalar() or 0
        art_count = db.query(func.count(Artifact.id)).filter(Artifact.project_id == project_id).scalar() or 0
        edge_count = (
            db.query(func.count(TraceabilityEdge.id))
            .filter(TraceabilityEdge.project_id == project_id, TraceabilityEdge.is_active.is_(True))
            .scalar()
            or 0
        )
        members_count = db.query(func.count(ProjectMember.id)).filter(ProjectMember.project_id == project_id).scalar() or 0

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "domain": project.domain,
            "owner_user_id": project.owner_user_id,
            "status": project.status,
            "settings_json": project.settings_json,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "owner": project.owner,
            "members_count": members_count,
            "requirements_count": req_count,
            "artifacts_count": art_count,
            "edges_count": edge_count,
        }

    @staticmethod
    def update_project(db: Session, project_id: str, data: ProjectUpdate) -> Project:
        project = ProjectService.get_project_by_id(db, project_id)
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        if data.domain is not None:
            project.domain = data.domain
        if data.settings is not None:
            project.settings_json = data.settings

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_members(db: Session, project_id: str) -> List[ProjectMember]:
        return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

    @staticmethod
    def add_member(db: Session, project_id: str, data: ProjectMemberCreate) -> ProjectMember:
        user = db.query(User).filter(User.email == data.user_email.lower()).first()
        if not user:
            raise EntityNotFoundError("User with email", data.user_email)

        existing = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id)
            .first()
        )
        if existing:
            raise EntityConflictError(f"User '{data.user_email}' is already a member of this project.")

        member = ProjectMember(
            project_id=project_id,
            user_id=user.id,
            role=data.role.upper(),
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def update_member_role(db: Session, project_id: str, member_id: str, data: ProjectMemberUpdate) -> ProjectMember:
        member = (
            db.query(ProjectMember)
            .filter(ProjectMember.id == member_id, ProjectMember.project_id == project_id)
            .first()
        )
        if not member:
            raise EntityNotFoundError("ProjectMember", member_id)

        project = ProjectService.get_project_by_id(db, project_id)
        if member.user_id == project.owner_user_id and data.role != "ADMIN":
            raise PermissionDeniedError("Cannot demote the project owner from ADMIN role.")

        member.role = data.role.upper()
        db.commit()
        db.refresh(member)
        return member
