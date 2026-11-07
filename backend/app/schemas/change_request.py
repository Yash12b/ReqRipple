from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.auth import UserResponse


class ChangeRequestCreate(BaseModel):
    requirement_id: str
    title: str = Field(..., min_length=3, max_length=255)
    reason: str = Field(..., min_length=5)
    business_justification: Optional[str] = Field(default="")
    urgency: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    proposed_fields: Dict[str, Any] = Field(
        ...,
        description="Dictionary of proposed field modifications e.g. {'description': '...', 'acceptance_criteria': [...]}",
    )


class ChangeRequestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    reason: Optional[str] = None
    business_justification: Optional[str] = None
    urgency: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    proposed_fields: Optional[Dict[str, Any]] = None


class ChangeRequestDiffResponse(BaseModel):
    id: str
    change_request_id: str
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    diff_type: str
    change_category: str

    model_config = ConfigDict(from_attributes=True)


class ChangeDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVE|REJECT|DEFER)$")
    rationale: Optional[str] = Field(
        default="", description="Mandatory for REJECT and DEFER decisions."
    )


class ImpactResultDispositionUpdate(BaseModel):
    disposition: str = Field(
        ...,
        pattern="^(UPDATE_REQUIRED|RETEST_REQUIRED|REVIEW_NO_CHANGE|NOT_APPLICABLE|RISK_ACCEPTED)$",
    )
    review_rationale: Optional[str] = Field(
        default="",
        description="Mandatory when marking NOT_APPLICABLE or RISK_ACCEPTED.",
    )


class RemediationActionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    action_type: str = Field(default="UPDATE", pattern="^(UPDATE|RETEST|REVIEW|DOCUMENT)$")
    description: Optional[str] = Field(default="")
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class RemediationActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(OPEN|IN_PROGRESS|BLOCKED|DONE|WAIVED)$")
    completion_notes: Optional[str] = None
    evidence_reference: Optional[str] = None


class RemediationActionResponse(BaseModel):
    id: str
    impact_result_id: str
    title: str
    action_type: str
    description: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    completion_notes: str = ""
    evidence_reference: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    assignee: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TestExecutionCreate(BaseModel):
    change_request_id: Optional[str] = None
    result: str = Field(..., pattern="^(NOT_RUN|PASSED|FAILED|BLOCKED)$")
    notes: Optional[str] = Field(default="")
    evidence_reference: Optional[str] = None


class TestExecutionResponse(BaseModel):
    id: str
    artifact_id: str
    change_request_id: Optional[str] = None
    result: str
    notes: str = ""
    evidence_reference: Optional[str] = None
    executed_at: datetime
    executor: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ImpactResultResponse(BaseModel):
    id: Optional[str] = None
    impact_analysis_id: Optional[str] = None
    artifact_id: str
    artifact_display_id: Optional[str] = None
    artifact_title: Optional[str] = None
    artifact_type: Optional[str] = None
    shortest_distance: int
    path_strength: float
    criticality_factor: float
    proximity_factor: float
    verification_gap_factor: float
    impact_score: int
    priority_band: str
    explanation_paths_json: List[List[Dict[str, Any]]] = Field(default_factory=list)
    warning_flags_json: List[str] = Field(default_factory=list)
    disposition: str = "UPDATE_REQUIRED"
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_rationale: Optional[str] = None
    reviewer: Optional[UserResponse] = None
    actions: List[RemediationActionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ImpactAnalysisResponse(BaseModel):
    id: str
    change_request_id: str
    source_requirement_version_id: Optional[str] = None
    algorithm_version: str = "1.0.0"
    scoring_weights_json: Dict[str, float] = Field(default_factory=dict)
    summary_json: Dict[str, Any] = Field(default_factory=dict)
    is_preview: bool = False
    created_by: Optional[str] = None
    created_at: datetime
    results: List[ImpactResultResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ChangeRequestResponse(BaseModel):
    id: str
    project_id: str
    requirement_id: str
    requester_user_id: Optional[str] = None
    title: str
    reason: str
    business_justification: str = ""
    urgency: str
    proposed_fields_json: Dict[str, Any]
    status: str
    submitted_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_rationale: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    requester: Optional[UserResponse] = None
    decider: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ChangeRequestDetailResponse(ChangeRequestResponse):
    diffs: List[ChangeRequestDiffResponse] = Field(default_factory=list)
    latest_analysis: Optional[ImpactAnalysisResponse] = None


class ClosureCheckResponse(BaseModel):
    can_close: bool
    blocking_reasons: List[str] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    change_request_id: str
    is_preview: bool = True
    summary: Dict[str, Any]
    diffs: List[Dict[str, Any]]
    results: List[ImpactResultResponse]
    warnings: List[str] = Field(default_factory=list)
