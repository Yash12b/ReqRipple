from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.auth import UserResponse

VALID_RELATION_TYPES = (
    "^(IMPLEMENTED_BY|SPECIFIED_BY|REALISED_AS|DEPENDS_ON|EXPOSES|"
    "CONSUMED_BY|USES|VERIFIED_BY|DOCUMENTED_BY|DEPLOYED_IN|CONSTRAINED_BY|DERIVED_FROM)$"
)


class GraphNodeResponse(BaseModel):
    id: str
    project_id: str
    node_type: str  # REQUIREMENT, ARTIFACT
    display_id: str
    title: str = ""
    entity_id: str = ""  # requirement_id or artifact_id
    sub_type: str = ""  # requirement_type or artifact_type
    criticality: int = 3
    status: str = "ACTIVE"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TraceabilityEdgeCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    relation_type: str = Field(default="DEPENDS_ON", pattern=VALID_RELATION_TYPES)
    propagation_enabled: bool = True
    relationship_strength: float = Field(default=1.0, ge=0.0, le=1.0)
    confirmation_status: str = Field(
        default="CONFIRMED", pattern="^(CONFIRMED|SUGGESTED|NEEDS_REVIEW)$"
    )
    notes: Optional[str] = Field(default="", max_length=1000)


class TraceabilityEdgeUpdate(BaseModel):
    relation_type: Optional[str] = Field(None, pattern=VALID_RELATION_TYPES)
    propagation_enabled: Optional[bool] = None
    relationship_strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    confirmation_status: Optional[str] = Field(None, pattern="^(CONFIRMED|SUGGESTED|NEEDS_REVIEW)$")
    notes: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class TraceabilityEdgeResponse(BaseModel):
    id: str
    project_id: str
    source_node_id: str
    target_node_id: str
    source_display_id: Optional[str] = None
    target_display_id: Optional[str] = None
    relation_type: str
    propagation_enabled: bool
    relationship_strength: float
    confirmation_status: str
    notes: str
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class GraphResponse(BaseModel):
    nodes: List[GraphNodeResponse]
    edges: List[TraceabilityEdgeResponse]
