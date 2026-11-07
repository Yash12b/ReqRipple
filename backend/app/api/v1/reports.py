import csv
import io
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.dashboard_service import DashboardService
from app.services.impact_analysis_service import ImpactAnalysisService
from app.core.permissions import get_current_user, require_project_access
from app.models.user import User

router = APIRouter(tags=["Dashboard & Reports"])


@router.get("/projects/{project_id}/dashboard", response_model=Dict[str, Any])
def get_dashboard(
    project_id: str,
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return DashboardService.get_project_dashboard(db, project_id)


@router.get("/projects/{project_id}/change-debt", response_model=Dict[str, Any])
def get_change_debt(
    project_id: str,
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return DashboardService.get_change_debt(db, project_id)


@router.get("/projects/{project_id}/volatility", response_model=List[Dict[str, Any]])
def get_volatility(
    project_id: str,
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    return DashboardService.get_volatility(db, project_id)


@router.get("/impact-analyses/{analysis_id}/export.csv")
def export_impact_csv(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = ImpactAnalysisService.get_analysis_detail(db, analysis_id)
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Artifact ID",
        "Artifact Title",
        "Artifact Type",
        "Shortest Distance",
        "Path Strength",
        "Criticality Factor",
        "Proximity Factor",
        "Verification Gap Factor",
        "Impact Priority Score",
        "Priority Band",
        "Disposition",
    ])

    for r in detail.get("results", []):
        writer.writerow([
            r.get("artifact_display_id", ""),
            r.get("artifact_title", ""),
            r.get("artifact_type", ""),
            r.get("shortest_distance", 1),
            r.get("path_strength", 1.0),
            r.get("criticality_factor", 1.0),
            r.get("proximity_factor", 1.0),
            r.get("verification_gap_factor", 1.0),
            r.get("impact_score", 0),
            r.get("priority_band", "LOW"),
            r.get("disposition", "UPDATE_REQUIRED"),
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=impact_report_{analysis_id[:8]}.csv"},
    )
