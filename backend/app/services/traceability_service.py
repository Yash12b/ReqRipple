from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.graph import GraphNode, TraceabilityEdge
from app.models.requirement import Requirement, RequirementVersion
from app.models.artifact import Artifact
from app.schemas.graph import TraceabilityEdgeCreate, TraceabilityEdgeUpdate
from app.core.errors import EntityNotFoundError, EntityConflictError, ValidationError

DEFAULT_STRENGTHS = {
    "IMPLEMENTED_BY": 1.00,
    "REALISED_AS": 0.95,
    "VERIFIED_BY": 0.95,
    "DEPENDS_ON": 0.90,
    "EXPOSES": 0.85,
    "CONSUMED_BY": 0.85,
    "USES": 0.80,
    "SPECIFIED_BY": 0.90,
    "CONSTRAINED_BY": 0.90,
    "DOCUMENTED_BY": 0.60,
    "DERIVED_FROM": 0.90,
    "DEPLOYED_IN": 0.70,
}


class TraceabilityService:
    @staticmethod
    def create_edge(
        db: Session, project_id: str, data: TraceabilityEdgeCreate, user_id: str
    ) -> TraceabilityEdge:
        if data.source_node_id == data.target_node_id:
            raise ValidationError("Self-referencing edges are not permitted.")

        # Verify source node exists and belongs to the project
        source_node = (
            db.query(GraphNode)
            .filter(GraphNode.id == data.source_node_id, GraphNode.project_id == project_id)
            .first()
        )
        if not source_node:
            raise EntityNotFoundError("Source GraphNode in project", data.source_node_id)

        # Verify target node exists and belongs to the project
        target_node = (
            db.query(GraphNode)
            .filter(GraphNode.id == data.target_node_id, GraphNode.project_id == project_id)
            .first()
        )
        if not target_node:
            raise EntityNotFoundError("Target GraphNode in project", data.target_node_id)

        # Check for existing active edge
        existing = (
            db.query(TraceabilityEdge)
            .filter(
                TraceabilityEdge.project_id == project_id,
                TraceabilityEdge.source_node_id == data.source_node_id,
                TraceabilityEdge.target_node_id == data.target_node_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .first()
        )
        if existing:
            raise EntityConflictError(
                f"An active relationship already exists between '{source_node.display_id}' and '{target_node.display_id}'."
            )

        # Use default strength if default value 1.0 was passed and relation_type has specific default
        strength = data.relationship_strength
        if strength == 1.0 and data.relation_type in DEFAULT_STRENGTHS:
            strength = DEFAULT_STRENGTHS[data.relation_type]

        edge = TraceabilityEdge(
            project_id=project_id,
            source_node_id=data.source_node_id,
            target_node_id=data.target_node_id,
            relation_type=data.relation_type,
            propagation_enabled=data.propagation_enabled,
            relationship_strength=strength,
            confirmation_status=data.confirmation_status,
            notes=data.notes or "",
            created_by=user_id,
            is_active=True,
        )
        db.add(edge)
        db.commit()
        db.refresh(edge)
        return edge

    @staticmethod
    def get_edge_by_id(db: Session, edge_id: str) -> TraceabilityEdge:
        edge = db.query(TraceabilityEdge).filter(TraceabilityEdge.id == edge_id).first()
        if not edge:
            raise EntityNotFoundError("TraceabilityEdge", edge_id)
        return edge

    @staticmethod
    def update_edge(
        db: Session, edge_id: str, data: TraceabilityEdgeUpdate
    ) -> TraceabilityEdge:
        edge = TraceabilityService.get_edge_by_id(db, edge_id)
        if data.relation_type is not None:
            edge.relation_type = data.relation_type
        if data.propagation_enabled is not None:
            edge.propagation_enabled = data.propagation_enabled
        if data.relationship_strength is not None:
            edge.relationship_strength = data.relationship_strength
        if data.confirmation_status is not None:
            edge.confirmation_status = data.confirmation_status
        if data.notes is not None:
            edge.notes = data.notes
        if data.is_active is not None:
            edge.is_active = data.is_active

        db.commit()
        db.refresh(edge)
        return edge

    @staticmethod
    def deactivate_edge(db: Session, edge_id: str) -> TraceabilityEdge:
        edge = TraceabilityService.get_edge_by_id(db, edge_id)
        edge.is_active = False
        db.commit()
        db.refresh(edge)
        return edge

    @staticmethod
    def get_project_graph(db: Session, project_id: str) -> dict:
        nodes = db.query(GraphNode).filter(GraphNode.project_id == project_id).all()
        edges = (
            db.query(TraceabilityEdge)
            .filter(
                TraceabilityEdge.project_id == project_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .all()
        )

        # Preload requirement details
        reqs = db.query(Requirement).filter(Requirement.project_id == project_id).all()
        req_map = {r.graph_node_id: r for r in reqs}
        req_versions = (
            db.query(RequirementVersion)
            .filter(
                RequirementVersion.id.in_(
                    [r.current_version_id for r in reqs if r.current_version_id]
                )
            )
            .all()
        )
        version_map = {v.id: v for v in req_versions}

        # Preload artifact details
        arts = db.query(Artifact).filter(Artifact.project_id == project_id).all()
        art_map = {a.graph_node_id: a for a in arts}

        # Build node responses
        node_responses = []
        node_display_map = {}
        for n in nodes:
            node_display_map[n.id] = n.display_id
            title = ""
            entity_id = ""
            sub_type = ""
            criticality = 3
            status = "ACTIVE"

            if n.node_type == "REQUIREMENT" and n.id in req_map:
                req = req_map[n.id]
                entity_id = req.id
                sub_type = req.requirement_type
                criticality = req.criticality
                status = req.lifecycle_status
                if req.current_version_id and req.current_version_id in version_map:
                    title = version_map[req.current_version_id].title
            elif n.node_type == "ARTIFACT" and n.id in art_map:
                art = art_map[n.id]
                entity_id = art.id
                sub_type = art.artifact_type
                criticality = art.criticality
                status = art.status
                title = art.title

            node_responses.append(
                {
                    "id": n.id,
                    "project_id": n.project_id,
                    "node_type": n.node_type,
                    "display_id": n.display_id,
                    "title": title,
                    "entity_id": entity_id,
                    "sub_type": sub_type,
                    "criticality": criticality,
                    "status": status,
                    "created_at": n.created_at,
                }
            )

        edge_responses = []
        for e in edges:
            edge_responses.append(
                {
                    "id": e.id,
                    "project_id": e.project_id,
                    "source_node_id": e.source_node_id,
                    "target_node_id": e.target_node_id,
                    "source_display_id": node_display_map.get(e.source_node_id, ""),
                    "target_display_id": node_display_map.get(e.target_node_id, ""),
                    "relation_type": e.relation_type,
                    "propagation_enabled": e.propagation_enabled,
                    "relationship_strength": e.relationship_strength,
                    "confirmation_status": e.confirmation_status,
                    "notes": e.notes,
                    "is_active": e.is_active,
                    "created_by": e.created_by,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                    "creator": e.creator,
                }
            )

        return {"nodes": node_responses, "edges": edge_responses}

    @staticmethod
    def get_traceability_health(db: Session, project_id: str) -> dict:
        requirements = db.query(Requirement).filter(Requirement.project_id == project_id).all()
        artifacts = db.query(Artifact).filter(Artifact.project_id == project_id).all()
        active_edges = (
            db.query(TraceabilityEdge)
            .filter(
                TraceabilityEdge.project_id == project_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .all()
        )

        req_node_ids = {r.graph_node_id for r in requirements}
        art_node_ids = {a.graph_node_id for a in artifacts}

        # Outgoing edges from requirements
        req_impl_links = set()
        req_verify_links = set()
        for e in active_edges:
            if e.source_node_id in req_node_ids:
                if e.relation_type in ("IMPLEMENTED_BY", "REALISED_AS"):
                    req_impl_links.add(e.source_node_id)
                elif e.relation_type == "VERIFIED_BY":
                    req_verify_links.add(e.source_node_id)

        # Connected artifact nodes
        connected_artifacts = set()
        for e in active_edges:
            if e.source_node_id in art_node_ids:
                connected_artifacts.add(e.source_node_id)
            if e.target_node_id in art_node_ids:
                connected_artifacts.add(e.target_node_id)

        orphan_artifacts = [
            {"id": a.id, "display_id": a.display_id, "title": a.title, "type": a.artifact_type}
            for a in artifacts
            if a.graph_node_id not in connected_artifacts
        ]

        # Critical artifacts (criticality >= 4) with no linked test case
        tested_artifacts = set()
        test_case_nodes = {a.graph_node_id for a in artifacts if a.artifact_type == "TEST_CASE"}
        for e in active_edges:
            if e.relation_type == "VERIFIED_BY" or e.target_node_id in test_case_nodes:
                tested_artifacts.add(e.source_node_id)

        critical_untested = [
            {"id": a.id, "display_id": a.display_id, "title": a.title, "criticality": a.criticality}
            for a in artifacts
            if a.criticality >= 4
            and a.artifact_type != "TEST_CASE"
            and a.graph_node_id not in tested_artifacts
        ]

        unconfirmed_edges = [
            e.id for e in active_edges if e.confirmation_status in ("SUGGESTED", "NEEDS_REVIEW")
        ]

        total_reqs = len(requirements)
        return {
            "total_requirements": total_reqs,
            "requirements_with_implementation": len(req_impl_links),
            "requirements_with_verification": len(req_verify_links),
            "total_artifacts": len(artifacts),
            "orphan_artifacts_count": len(orphan_artifacts),
            "orphan_artifacts": orphan_artifacts,
            "critical_untested_count": len(critical_untested),
            "critical_untested": critical_untested,
            "unconfirmed_edges_count": len(unconfirmed_edges),
            "total_active_edges": len(active_edges),
        }
