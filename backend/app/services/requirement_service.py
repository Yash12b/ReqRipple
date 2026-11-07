import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.requirement import Requirement, RequirementVersion
from app.models.graph import GraphNode, TraceabilityEdge
from app.schemas.requirement import RequirementCreate, RequirementUpdate
from app.core.errors import EntityNotFoundError, EntityConflictError, ValidationError


class RequirementService:
    @staticmethod
    def _generate_display_id(db: Session, project_id: str) -> str:
        count = (
            db.query(func.count(Requirement.id))
            .filter(Requirement.project_id == project_id)
            .scalar()
            or 0
        )
        display_id = f"REQ-{count + 1:03d}"
        # If collision occurs, increment until available
        while (
            db.query(GraphNode)
            .filter(GraphNode.project_id == project_id, GraphNode.display_id == display_id)
            .first()
        ):
            count += 1
            display_id = f"REQ-{count + 1:03d}"
        return display_id

    @staticmethod
    def create_requirement(
        db: Session, project_id: str, data: RequirementCreate, user_id: str
    ) -> Requirement:
        # Determine display ID
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
            display_id = RequirementService._generate_display_id(db, project_id)

        # 1. Create canonical GraphNode
        graph_node = GraphNode(
            project_id=project_id,
            node_type="REQUIREMENT",
            display_id=display_id,
        )
        db.add(graph_node)
        db.flush()

        # 2. Create Requirement record
        now = datetime.now(timezone.utc)
        requirement = Requirement(
            project_id=project_id,
            graph_node_id=graph_node.id,
            display_id=display_id,
            requirement_type=data.requirement_type,
            priority=data.priority,
            criticality=data.criticality,
            owner_user_id=data.owner_user_id or user_id,
            lifecycle_status="APPROVED",
        )
        db.add(requirement)
        db.flush()

        # 3. Create initial immutable RequirementVersion (v1)
        version = RequirementVersion(
            requirement_id=requirement.id,
            version_number=1,
            title=data.title,
            description=data.description,
            rationale=data.rationale or "Initial baseline version.",
            acceptance_criteria_json=data.acceptance_criteria,
            status="APPROVED",
            created_by=user_id,
            approved_by=user_id,
            approved_at=now,
        )
        db.add(version)
        db.flush()

        # 4. Link current version
        requirement.current_version_id = version.id
        db.commit()
        db.refresh(requirement)
        return requirement

    @staticmethod
    def get_by_id(db: Session, requirement_id: str) -> Requirement:
        req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not req:
            raise EntityNotFoundError("Requirement", requirement_id)
        return req

    @staticmethod
    def get_detail(db: Session, requirement_id: str) -> dict:
        req = RequirementService.get_by_id(db, requirement_id)
        current_version = None
        if req.current_version_id:
            current_version = (
                db.query(RequirementVersion)
                .filter(RequirementVersion.id == req.current_version_id)
                .first()
            )

        versions = (
            db.query(RequirementVersion)
            .filter(RequirementVersion.requirement_id == requirement_id)
            .order_by(RequirementVersion.version_number.desc())
            .all()
        )

        incoming = (
            db.query(func.count(TraceabilityEdge.id))
            .filter(
                TraceabilityEdge.target_node_id == req.graph_node_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .scalar()
            or 0
        )
        outgoing = (
            db.query(func.count(TraceabilityEdge.id))
            .filter(
                TraceabilityEdge.source_node_id == req.graph_node_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .scalar()
            or 0
        )

        return {
            "id": req.id,
            "project_id": req.project_id,
            "graph_node_id": req.graph_node_id,
            "display_id": req.display_id,
            "requirement_type": req.requirement_type,
            "current_version_id": req.current_version_id,
            "priority": req.priority,
            "criticality": req.criticality,
            "owner_user_id": req.owner_user_id,
            "lifecycle_status": req.lifecycle_status,
            "created_at": req.created_at,
            "updated_at": req.updated_at,
            "current_version": current_version,
            "versions": versions,
            "owner": req.owner,
            "incoming_edges_count": incoming,
            "outgoing_edges_count": outgoing,
        }

    @staticmethod
    def list_requirements(
        db: Session,
        project_id: str,
        requirement_type: Optional[str] = None,
        priority: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int, int]:
        query = db.query(Requirement).filter(Requirement.project_id == project_id)

        if requirement_type:
            query = query.filter(Requirement.requirement_type == requirement_type)
        if priority:
            query = query.filter(Requirement.priority == priority)
        if lifecycle_status:
            query = query.filter(Requirement.lifecycle_status == lifecycle_status)
        if search:
            query = query.join(
                RequirementVersion, Requirement.current_version_id == RequirementVersion.id
            ).filter(
                (Requirement.display_id.ilike(f"%{search}%"))
                | (RequirementVersion.title.ilike(f"%{search}%"))
                | (RequirementVersion.description.ilike(f"%{search}%"))
            )

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        records = (
            query.order_by(Requirement.display_id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        results = []
        for req in records:
            current_version = None
            if req.current_version_id:
                current_version = (
                    db.query(RequirementVersion)
                    .filter(RequirementVersion.id == req.current_version_id)
                    .first()
                )
            results.append(
                {
                    "id": req.id,
                    "project_id": req.project_id,
                    "graph_node_id": req.graph_node_id,
                    "display_id": req.display_id,
                    "requirement_type": req.requirement_type,
                    "current_version_id": req.current_version_id,
                    "priority": req.priority,
                    "criticality": req.criticality,
                    "owner_user_id": req.owner_user_id,
                    "lifecycle_status": req.lifecycle_status,
                    "created_at": req.created_at,
                    "updated_at": req.updated_at,
                    "current_version": current_version,
                    "owner": req.owner,
                }
            )
        return results, total, total_pages

    @staticmethod
    def update_metadata(
        db: Session, requirement_id: str, data: RequirementUpdate
    ) -> Requirement:
        req = RequirementService.get_by_id(db, requirement_id)
        if data.priority is not None:
            req.priority = data.priority
        if data.criticality is not None:
            req.criticality = data.criticality
        if data.owner_user_id is not None:
            req.owner_user_id = data.owner_user_id
        if data.lifecycle_status is not None:
            req.lifecycle_status = data.lifecycle_status

        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def get_versions(db: Session, requirement_id: str) -> List[RequirementVersion]:
        RequirementService.get_by_id(db, requirement_id)
        return (
            db.query(RequirementVersion)
            .filter(RequirementVersion.requirement_id == requirement_id)
            .order_by(RequirementVersion.version_number.desc())
            .all()
        )
