import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # USER_STORY, ACCEPTANCE_CRITERIA, DESIGN_COMPONENT, MODULE_SERVICE, API_ENDPOINT, DATABASE_ENTITY, UI_SCREEN, TEST_CASE, DOCUMENTATION, DEPLOYMENT_CONFIG
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    criticality: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1 to 5
    owner_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE", nullable=False
    )  # DRAFT, ACTIVE, DEPRECATED, ARCHIVED
    estimated_effort_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=True)
    external_reference: Mapped[str] = mapped_column(String(255), nullable=True)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("project_id", "display_id", name="uq_artifacts_project_display_id"),
    )

    # Relationships
    project = relationship("Project", back_populates="artifacts")
    graph_node = relationship("GraphNode", back_populates="artifact")
    owner = relationship("User", foreign_keys=[owner_user_id])
    impact_results = relationship("ImpactResult", back_populates="artifact", cascade="all, delete-orphan")
    test_executions = relationship("TestExecution", back_populates="artifact", cascade="all, delete-orphan")
