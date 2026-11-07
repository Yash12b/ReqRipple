from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.auth import UserResponse


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str = Field(default="", max_length=2000)
    domain: str = Field(default="General", max_length=100)
    settings: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    domain: Optional[str] = Field(None, max_length=100)
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    owner_user_id: str
    status: str
    settings_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberCreate(BaseModel):
    user_email: str
    role: str = Field(default="ANALYST", pattern="^(ADMIN|ANALYST|DEVELOPER|TESTER|APPROVER|VIEWER)$")


class ProjectMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(ADMIN|ANALYST|DEVELOPER|TESTER|APPROVER|VIEWER)$")


class ProjectMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    joined_at: datetime
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    owner: Optional[UserResponse] = None
    members_count: int = 0
    requirements_count: int = 0
    artifacts_count: int = 0
    edges_count: int = 0
