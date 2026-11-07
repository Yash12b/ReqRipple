from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.graph import (
    TraceabilityEdgeCreate,
    TraceabilityEdgeUpdate,
    TraceabilityEdgeResponse,
    GraphResponse,
)
from app.services.traceability_service import TraceabilityService
from app.core.permissions import get_current_user, require_project_access, require_project_role
from app.models.user import User

router = APIRouter(tags=["Traceability"])


@router.get("/projects/{project_id}/graph", response_model=GraphResponse)
def get_project_graph(
    project_id: str,
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return TraceabilityService.get_project_graph(db, project_id)


@router.post(
    "/projects/{project_id}/edges",
    response_model=TraceabilityEdgeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_traceability_edge(
    project_id: str,
    data: TraceabilityEdgeCreate,
    current_user: User = Depends(get_current_user),
    _=Depends(require_project_role("ADMIN", "ANALYST")),
    db: Session = Depends(get_db),
):
    edge = TraceabilityService.create_edge(db, project_id, data, current_user.id)
    # Reload with display details
    graph = TraceabilityService.get_project_graph(db, project_id)
    matched = next((e for e in graph["edges"] if e["id"] == edge.id), None)
    return matched or edge


@router.patch("/edges/{edge_id}", response_model=TraceabilityEdgeResponse)
def update_traceability_edge(
    edge_id: str,
    data: TraceabilityEdgeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    edge = TraceabilityService.get_edge_by_id(db, edge_id)
    require_project_role("ADMIN", "ANALYST")(edge.project_id, current_user, db)
    updated = TraceabilityService.update_edge(db, edge_id, data)
    graph = TraceabilityService.get_project_graph(db, updated.project_id)
    matched = next((e for e in graph["edges"] if e["id"] == updated.id), None)
    return matched or updated


@router.delete("/edges/{edge_id}", response_model=TraceabilityEdgeResponse)
def deactivate_traceability_edge(
    edge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    edge = TraceabilityService.get_edge_by_id(db, edge_id)
    require_project_role("ADMIN", "ANALYST")(edge.project_id, current_user, db)
    deactivated = TraceabilityService.deactivate_edge(db, edge_id)
    return deactivated


@router.get("/projects/{project_id}/traceability-health", response_model=Dict[str, Any])
def get_traceability_health(
    project_id: str,
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return TraceabilityService.get_traceability_health(db, project_id)
