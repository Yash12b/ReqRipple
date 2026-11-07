from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.auth import UserResponse


class RequirementVersionResponse(BaseModel):
    id: str
    requirement_id: str
    version_number: int
    title: str
    description: str
    rationale: str
    acceptance_criteria_json: List[str]
    status: str
    created_by: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    author: Optional[UserResponse] = None
    approver: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class RequirementCreate(BaseModel):
    display_id: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    requirement_type: str = Field(
        default="FUNCTIONAL",
        pattern="^(FUNCTIONAL|NON_FUNCTIONAL|BUSINESS|SECURITY|PERFORMANCE|USABILITY|REGULATORY)$",
    )
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    criticality: int = Field(default=3, ge=1, le=5)
    acceptance_criteria: List[str] = Field(default_factory=list)
    rationale: Optional[str] = Field(default="")
    owner_user_id: Optional[str] = None


class RequirementUpdate(BaseModel):
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    criticality: Optional[int] = Field(None, ge=1, le=5)
    owner_user_id: Optional[str] = None
    lifecycle_status: Optional[str] = Field(None, pattern="^(DRAFT|APPROVED|IN_REVIEW|RETIRED)$")


class RequirementResponse(BaseModel):
    id: str
    project_id: str
    graph_node_id: str
    display_id: str
    requirement_type: str
    current_version_id: Optional[str]
    priority: str
    criticality: int
    owner_user_id: Optional[str]
    lifecycle_status: str
    created_at: datetime
    updated_at: datetime
    current_version: Optional[RequirementVersionResponse] = None
    owner: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class RequirementDetailResponse(RequirementResponse):
    versions: List[RequirementVersionResponse] = Field(default_factory=list)
    incoming_edges_count: int = 0
    outgoing_edges_count: int = 0
