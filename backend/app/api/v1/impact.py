from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.change_request import (
    ImpactAnalysisResponse,
    ImpactResultResponse,
    ImpactResultDispositionUpdate,
    RemediationActionCreate,
    RemediationActionUpdate,
    RemediationActionResponse,
    TestExecutionCreate,
    TestExecutionResponse,
)
from app.services.impact_analysis_service import ImpactAnalysisService
from app.services.review_service import ReviewService
from app.services.remediation_service import RemediationService
from app.core.permissions import get_current_user, require_project_access, require_project_role
from app.models.user import User

router = APIRouter(tags=["Impact Analysis & Remediation"])


@router.get(
    "/impact-analyses/{analysis_id}",
    response_model=ImpactAnalysisResponse,
)
def get_impact_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ImpactAnalysisService.get_analysis_detail(db, analysis_id)


@router.post(
    "/impact-results/{impact_result_id}/disposition",
    response_model=ImpactResultResponse,
)
def record_disposition(
    impact_result_id: str,
    data: ImpactResultDispositionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = ReviewService.update_disposition(
        db,
        impact_result_id,
        disposition=data.disposition,
        rationale=data.review_rationale,
        user_id=current_user.id,
    )
    return res


@router.post(
    "/impact-results/{impact_result_id}/actions",
    response_model=RemediationActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_remediation_action(
    impact_result_id: str,
    data: RemediationActionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RemediationService.create_action(db, impact_result_id, data)


@router.patch(
    "/remediation-actions/{action_id}",
    response_model=RemediationActionResponse,
)
def update_remediation_action(
    action_id: str,
    data: RemediationActionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RemediationService.update_action(db, action_id, data)


@router.post(
    "/artifacts/{artifact_id}/test-executions",
    response_model=TestExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_test_execution(
    artifact_id: str,
    data: TestExecutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RemediationService.record_test_execution(
        db, artifact_id, data, current_user.id
    )
