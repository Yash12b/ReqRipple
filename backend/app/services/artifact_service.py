import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.artifact import Artifact
from app.models.graph import GraphNode, TraceabilityEdge
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate
from app.core.errors import EntityNotFoundError, EntityConflictError

TYPE_PREFIX_MAP = {
    "USER_STORY": "US",
    "ACCEPTANCE_CRITERIA": "AC",
    "DESIGN_COMPONENT": "DES",
    "MODULE_SERVICE": "MOD",
    "API_ENDPOINT": "API",
    "DATABASE_ENTITY": "DB",
    "UI_SCREEN": "UI",
    "TEST_CASE": "TEST",
    "DOCUMENTATION": "DOC",
    "DEPLOYMENT_CONFIG": "DEP",
    "PROJECT_TASK": "TASK",
}


class ArtifactService:
    @staticmethod
    def _generate_display_id(db: Session, project_id: str, artifact_type: str) -> str:
        prefix = TYPE_PREFIX_MAP.get(artifact_type, "ART")
        count = (
            db.query(func.count(Artifact.id))
            .filter(Artifact.project_id == project_id, Artifact.artifact_type == artifact_type)
            .scalar()
            or 0
        )
        display_id = f"{prefix}-{count + 1:03d}"
        while (
            db.query(GraphNode)
            .filter(GraphNode.project_id == project_id, GraphNode.display_id == display_id)
            .first()
        ):
            count += 1
            display_id = f"{prefix}-{count + 1:03d}"
        return display_id

    @staticmethod
    def create_artifact(
        db: Session, project_id: str, data: ArtifactCreate, user_id: str
    ) -> Artifact:
        display_id = data.display_id.strip() if data.display_id else None
        if display_id:
            existing_node = (
                db.query(GraphNode)
                .filter(GraphNode.project_id == project_id, GraphNode.display_id == display_id)
                .first()
            )
            if existing_node:
                raise EntityConflictError(
                    f"A node with display ID '{display_id}' already exists in this project."
                )
        else:
            display_id = ArtifactService._generate_display_id(db, project_id, data.artifact_type)

        # 1. Create canonical GraphNode
        graph_node = GraphNode(
            project_id=project_id,
            node_type="ARTIFACT",
            display_id=display_id,
        )
        db.add(graph_node)
        db.flush()

        # 2. Create Artifact record
        artifact = Artifact(
            project_id=project_id,
            graph_node_id=graph_node.id,
            display_id=display_id,
            artifact_type=data.artifact_type,
            title=data.title,
            description=data.description or "",
            criticality=data.criticality,
            owner_user_id=data.owner_user_id or user_id,
            status="ACTIVE",
            estimated_effort_hours=data.estimated_effort_hours or 0.0,
            external_reference=data.external_reference,
            last_reviewed_at=datetime.now(timezone.utc),
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact

    @staticmethod
    def get_by_id(db: Session, artifact_id: str) -> Artifact:
        art = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        if not art:
            raise EntityNotFoundError("Artifact", artifact_id)
        return art

    @staticmethod
    def get_detail(db: Session, artifact_id: str) -> dict:
        art = ArtifactService.get_by_id(db, artifact_id)
        incoming = (
            db.query(func.count(TraceabilityEdge.id))
            .filter(
                TraceabilityEdge.target_node_id == art.graph_node_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .scalar()
            or 0
        )
        outgoing = (
            db.query(func.count(TraceabilityEdge.id))
            .filter(
                TraceabilityEdge.source_node_id == art.graph_node_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .scalar()
            or 0
        )
        return {
            "id": art.id,
            "project_id": art.project_id,
            "graph_node_id": art.graph_node_id,
            "display_id": art.display_id,
            "artifact_type": art.artifact_type,
            "title": art.title,
            "description": art.description,
            "criticality": art.criticality,
            "owner_user_id": art.owner_user_id,
            "status": art.status,
            "estimated_effort_hours": art.estimated_effort_hours,
            "external_reference": art.external_reference,
            "last_reviewed_at": art.last_reviewed_at,
            "archived_at": art.archived_at,
            "created_at": art.created_at,
            "updated_at": art.updated_at,
            "owner": art.owner,
            "incoming_edges_count": incoming,
            "outgoing_edges_count": outgoing,
        }

    @staticmethod
    def list_artifacts(
        db: Session,
        project_id: str,
        artifact_type: Optional[str] = None,
        criticality: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Artifact], int, int]:
        query = db.query(Artifact).filter(Artifact.project_id == project_id)

        if artifact_type:
            query = query.filter(Artifact.artifact_type == artifact_type)
        if criticality:
            query = query.filter(Artifact.criticality == criticality)
        if status:
            query = query.filter(Artifact.status == status)
        if search:
            query = query.filter(
                (Artifact.display_id.ilike(f"%{search}%"))
                | (Artifact.title.ilike(f"%{search}%"))
                | (Artifact.description.ilike(f"%{search}%"))
            )

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        items = (
            query.order_by(Artifact.display_id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total, total_pages

    @staticmethod
    def update_artifact(db: Session, artifact_id: str, data: ArtifactUpdate) -> Artifact:
        art = ArtifactService.get_by_id(db, artifact_id)
        if data.title is not None:
            art.title = data.title
        if data.description is not None:
            art.description = data.description
        if data.criticality is not None:
            art.criticality = data.criticality
        if data.status is not None:
            art.status = data.status
            if data.status == "ARCHIVED":
                art.archived_at = datetime.now(timezone.utc)
        if data.owner_user_id is not None:
            art.owner_user_id = data.owner_user_id
        if data.estimated_effort_hours is not None:
            art.estimated_effort_hours = data.estimated_effort_hours
        if data.external_reference is not None:
            art.external_reference = data.external_reference

        db.commit()
        db.refresh(art)
        return art
