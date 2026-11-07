import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requester_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    business_justification: Mapped[str] = mapped_column(Text, default="", nullable=False)
    urgency: Mapped[str] = mapped_column(
        String(50), default="MEDIUM", nullable=False
    )  # LOW, MEDIUM, HIGH, CRITICAL
    proposed_fields_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="DRAFT", nullable=False, index=True
    )  # DRAFT, SUBMITTED, ANALYSIS_READY, IN_REVIEW, APPROVED, REJECTED, DEFERRED, IMPLEMENTING, VERIFICATION_PENDING, CLOSED, CANCELLED
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision_rationale: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project")
    requirement = relationship("Requirement", back_populates="change_requests")
    requester = relationship("User", foreign_keys=[requester_user_id])
    decider = relationship("User", foreign_keys=[decided_by])
    diffs = relationship("ChangeRequestDiff", back_populates="change_request", cascade="all, delete-orphan")
    impact_analyses = relationship(
        "ImpactAnalysis", back_populates="change_request", cascade="all, delete-orphan"
    )
    test_executions = relationship(
        "TestExecution", back_populates="change_request", cascade="all, delete-orphan"
    )


class ChangeRequestDiff(Base):
    __tablename__ = "change_request_diffs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    change_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("change_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text, nullable=True)
    diff_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ADDED, REMOVED, MODIFIED, UNCHANGED
    change_category: Mapped[str] = mapped_column(
        String(100), default="FUNCTIONAL_SCOPE_CHANGE", nullable=False
    )

    change_request = relationship("ChangeRequest", back_populates="diffs")


class ImpactAnalysis(Base):
    __tablename__ = "impact_analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    change_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("change_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_requirement_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirement_versions.id", ondelete="SET NULL"), nullable=True
    )
    graph_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    scoring_weights_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    change_request = relationship("ChangeRequest", back_populates="impact_analyses")
    source_version = relationship("RequirementVersion")
    creator = relationship("User")
    results = relationship("ImpactResult", back_populates="analysis", cascade="all, delete-orphan")


class ImpactResult(Base):
    __tablename__ = "impact_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    impact_analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shortest_distance: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    path_strength: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    criticality_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    proximity_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    verification_gap_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    impact_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 to 100
    priority_band: Mapped[str] = mapped_column(
        String(50), default="MEDIUM", nullable=False
    )  # LOW, MEDIUM, HIGH, CRITICAL
    explanation_paths_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    warning_flags_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    disposition: Mapped[str] = mapped_column(
        String(50), default="UPDATE_REQUIRED", nullable=False
    )  # UPDATE_REQUIRED, RETEST_REQUIRED, REVIEW_NO_CHANGE, NOT_APPLICABLE, RISK_ACCEPTED
    reviewed_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    review_rationale: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("impact_analysis_id", "artifact_id", name="uq_impact_analysis_artifact"),
    )

    analysis = relationship("ImpactAnalysis", back_populates="results")
    artifact = relationship("Artifact", back_populates="impact_results")
    reviewer = relationship("User")
    actions = relationship("RemediationAction", back_populates="impact_result", cascade="all, delete-orphan")


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    impact_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("impact_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(
        String(50), default="UPDATE", nullable=False
    )  # UPDATE, RETEST, REVIEW, DOCUMENT
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assigned_to: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="OPEN", nullable=False, index=True
    )  # OPEN, IN_PROGRESS, BLOCKED, DONE, WAIVED
    completion_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    impact_result = relationship("ImpactResult", back_populates="actions")
    assignee = relationship("User", foreign_keys=[assigned_to])


class TestExecution(Base):
    __tablename__ = "test_executions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    change_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("change_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    executed_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    result: Mapped[str] = mapped_column(
        String(50), default="NOT_RUN", nullable=False
    )  # NOT_RUN, PASSED, FAILED, BLOCKED
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    artifact = relationship("Artifact", back_populates="test_executions")
    change_request = relationship("ChangeRequest", back_populates="test_executions")
    executor = relationship("User", foreign_keys=[executed_by])
