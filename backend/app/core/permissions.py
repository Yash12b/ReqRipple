from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.models.user import User
from app.models.project import Project, ProjectMember


def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Authorization header missing or invalid format.")
    return authorization.split(" ")[1]


def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise AuthenticationError("Invalid or expired access token.")

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise AuthenticationError("User not found or inactive.")
    return user


class RoleChecker:
    def __init__(self, allowed_roles: Optional[List[str]] = None):
        self.allowed_roles = [r.upper() for r in (allowed_roles or [])]

    def check(
        self,
        project_id: str,
        user: User,
        db: Session,
    ) -> ProjectMember:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )

        # Project owner has superuser rights within their project
        if project.owner_user_id == user.id:
            # Synthetic member for project owner
            owner_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.id,
            ).first()
            if not owner_member:
                owner_member = ProjectMember(
                    project_id=project_id,
                    user_id=user.id,
                    role="ADMIN",
                )
            return owner_member

        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        ).first()

        if not member:
            raise PermissionDeniedError("You are not a member of this project.")

        if self.allowed_roles and member.role.upper() not in self.allowed_roles:
            raise PermissionDeniedError(
                f"Action requires one of the following roles: {', '.join(self.allowed_roles)}. Your role is '{member.role}'."
            )

        return member


def require_project_access(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectMember:
    checker = RoleChecker(allowed_roles=None)
    return checker.check(project_id, current_user, db)


def require_project_role(*allowed_roles: str):
    checker = RoleChecker(list(allowed_roles))

    def dependency(
        project_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ProjectMember:
        return checker.check(project_id, current_user, db)

    return dependency
