import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)  # REQUIREMENT, ARTIFACT
    display_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("project_id", "display_id", name="uq_graph_nodes_project_display_id"),
    )

    # Relationships
    project = relationship("Project", back_populates="graph_nodes")
    requirement = relationship("Requirement", back_populates="graph_node", uselist=False)
    artifact = relationship("Artifact", back_populates="graph_node", uselist=False)

    outgoing_edges = relationship(
        "TraceabilityEdge",
        foreign_keys="[TraceabilityEdge.source_node_id]",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    incoming_edges = relationship(
        "TraceabilityEdge",
        foreign_keys="[TraceabilityEdge.target_node_id]",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )


class TraceabilityEdge(Base):
    __tablename__ = "traceability_edges"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), default="DEPENDS_ON", nullable=False
    )
    propagation_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    relationship_strength: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    confirmation_status: Mapped[str] = mapped_column(
        String(50), default="CONFIRMED", nullable=False
    )  # CONFIRMED, SUGGESTED, NEEDS_REVIEW
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
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
        Index("ix_traceability_edges_project_active", "project_id", "is_active"),
        Index("ix_traceability_edges_source_target", "source_node_id", "target_node_id"),
    )

    project = relationship("Project", back_populates="traceability_edges")
    source_node = relationship("GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("GraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
    creator = relationship("User", foreign_keys=[created_by])
