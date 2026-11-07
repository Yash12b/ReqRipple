import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Requirement(Base):
    __tablename__ = "requirements"

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
    requirement_type: Mapped[str] = mapped_column(
        String(50), default="FUNCTIONAL", nullable=False
    )  # FUNCTIONAL, NON_FUNCTIONAL, BUSINESS, SECURITY, PERFORMANCE, USABILITY, REGULATORY
    current_version_id: Mapped[str] = mapped_column(
        String(36), nullable=True
    )  # Reference to current active RequirementVersion
    priority: Mapped[str] = mapped_column(
        String(50), default="MEDIUM", nullable=False
    )  # LOW, MEDIUM, HIGH, CRITICAL
    criticality: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1 to 5
    owner_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    lifecycle_status: Mapped[str] = mapped_column(
        String(50), default="APPROVED", nullable=False
    )  # DRAFT, APPROVED, IN_REVIEW, RETIRED
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
        UniqueConstraint("project_id", "display_id", name="uq_requirements_project_display_id"),
    )

    # Relationships
    project = relationship("Project", back_populates="requirements")
    graph_node = relationship("GraphNode", back_populates="requirement")
    owner = relationship("User", foreign_keys=[owner_user_id])
    versions = relationship(
        "RequirementVersion",
        foreign_keys="[RequirementVersion.requirement_id]",
        back_populates="requirement",
        cascade="all, delete-orphan",
        order_by="RequirementVersion.version_number.desc()",
    )
    change_requests = relationship("ChangeRequest", back_populates="requirement", cascade="all, delete-orphan")


class RequirementVersion(Base):
    __tablename__ = "requirement_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    requirement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="", nullable=False)
    acceptance_criteria_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="APPROVED", nullable=False
    )  # DRAFT, APPROVED, RETIRED
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("requirement_id", "version_number", name="uq_req_version_req_num"),
    )

    requirement = relationship("Requirement", foreign_keys=[requirement_id], back_populates="versions")
    author = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
