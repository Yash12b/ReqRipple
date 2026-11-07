from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.change_request import (
    ChangeRequestCreate,
    ChangeRequestResponse,
    ChangeRequestDetailResponse,
    ChangeRequestDiffResponse,
    ChangeDecisionRequest,
    ImpactAnalysisResponse,
    SimulationResponse,
    ClosureCheckResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.change_request_service import ChangeRequestService
from app.services.diff_service import DiffService
from app.services.impact_analysis_service import ImpactAnalysisService
from app.services.review_service import ReviewService
from app.services.remediation_service import RemediationService
from app.core.permissions import get_current_user, require_project_access, require_project_role
from app.models.user import User

router = APIRouter(tags=["Change Requests"])


@router.get(
    "/projects/{project_id}/change-requests",
    response_model=PaginatedResponse[ChangeRequestResponse],
)
def list_change_requests(
    project_id: str,
    status: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(require_project_access),
    db: Session = Depends(get_db),
):
    items, total, total_pages = ChangeRequestService.list_change_requests(
        db, project_id, status=status, urgency=urgency, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/projects/{project_id}/change-requests",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_change_request(
    project_id: str,
    data: ChangeRequestCreate,
    current_user: User = Depends(get_current_user),
    _=Depends(require_project_role("ADMIN", "ANALYST")),
    db: Session = Depends(get_db),
):
    return ChangeRequestService.create_change_request(
        db, project_id, data, current_user.id
    )


@router.get(
    "/change-requests/{change_request_id}",
    response_model=ChangeRequestDetailResponse,
)
def get_change_request(
    change_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = ChangeRequestService.get_detail(db, change_request_id)
    require_project_access(detail["project_id"], current_user, db)
    return detail


@router.get(
    "/change-requests/{change_request_id}/diff",
    response_model=List[ChangeRequestDiffResponse],
)
def get_change_request_diff(
    change_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_access(cr.project_id, current_user, db)
    return DiffService.get_diffs(db, change_request_id)


@router.post(
    "/change-requests/{change_request_id}/analyse",
    response_model=ImpactAnalysisResponse,
)
def run_impact_analysis(
    change_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_role("ADMIN", "ANALYST")(cr.project_id, current_user, db)
    return ImpactAnalysisService.run_analysis(
        db, change_request_id, current_user.id, is_preview=False
    )


@router.post(
    "/change-requests/{change_request_id}/simulate",
    response_model=SimulationResponse,
)
def run_what_if_simulation(
    change_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_access(cr.project_id, current_user, db)
    return ImpactAnalysisService.run_analysis(
        db, change_request_id, current_user.id, is_preview=True
    )


@router.post(
    "/change-requests/{change_request_id}/approve",
    response_model=ChangeRequestResponse,
)
def approve_change_request(
    change_request_id: str,
    data: ChangeDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_role("ADMIN", "APPROVER")(cr.project_id, current_user, db)
    return ReviewService.approve_change_request(
        db, change_request_id, current_user.id, data.rationale
    )


@router.post(
    "/change-requests/{change_request_id}/reject",
    response_model=ChangeRequestResponse,
)
def reject_change_request(
    change_request_id: str,
    data: ChangeDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_role("ADMIN", "APPROVER")(cr.project_id, current_user, db)
    return ReviewService.reject_change_request(
        db, change_request_id, current_user.id, data.rationale
    )


@router.post(
    "/change-requests/{change_request_id}/defer",
    response_model=ChangeRequestResponse,
)
def defer_change_request(
    change_request_id: str,
    data: ChangeDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_role("ADMIN", "APPROVER")(cr.project_id, current_user, db)
    return ReviewService.defer_change_request(
        db, change_request_id, current_user.id, data.rationale
    )


@router.get(
    "/change-requests/{change_request_id}/closure-check",
    response_model=ClosureCheckResponse,
)
def check_closure(
    change_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_access(cr.project_id, current_user, db)
    can_close, reasons = RemediationService.check_closure(db, change_request_id)
    return ClosureCheckResponse(can_close=can_close, blocking_reasons=reasons)


@router.post(
    "/change-requests/{change_request_id}/close",
    response_model=ChangeRequestResponse,
)
def close_change_request(
    change_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cr = ChangeRequestService.get_by_id(db, change_request_id)
    require_project_role("ADMIN", "APPROVER")(cr.project_id, current_user, db)
    return RemediationService.close_change_request(db, change_request_id)
