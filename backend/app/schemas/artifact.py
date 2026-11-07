from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.auth import UserResponse

VALID_ARTIFACT_TYPES = (
    "^(USER_STORY|ACCEPTANCE_CRITERIA|DESIGN_COMPONENT|MODULE_SERVICE|"
    "API_ENDPOINT|DATABASE_ENTITY|UI_SCREEN|TEST_CASE|DOCUMENTATION|"
    "DEPLOYMENT_CONFIG|PROJECT_TASK)$"
)


class ArtifactCreate(BaseModel):
    display_id: Optional[str] = Field(None, max_length=100)
    artifact_type: str = Field(..., pattern=VALID_ARTIFACT_TYPES)
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(default="", max_length=5000)
    criticality: int = Field(default=3, ge=1, le=5)
    owner_user_id: Optional[str] = None
    estimated_effort_hours: Optional[float] = Field(default=0.0, ge=0.0)
    external_reference: Optional[str] = Field(None, max_length=255)


class ArtifactUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    criticality: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = Field(None, pattern="^(DRAFT|ACTIVE|DEPRECATED|ARCHIVED)$")
    owner_user_id: Optional[str] = None
    estimated_effort_hours: Optional[float] = Field(None, ge=0.0)
    external_reference: Optional[str] = Field(None, max_length=255)


class ArtifactResponse(BaseModel):
    id: str
    project_id: str
    graph_node_id: str
    display_id: str
    artifact_type: str
    title: str
    description: str
    criticality: int
    owner_user_id: Optional[str]
    status: str
    estimated_effort_hours: Optional[float]
    external_reference: Optional[str]
    last_reviewed_at: Optional[datetime]
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    owner: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ArtifactDetailResponse(ArtifactResponse):
    incoming_edges_count: int = 0
    outgoing_edges_count: int = 0
