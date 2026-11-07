import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.change_request import ChangeRequest, ImpactAnalysis
from app.models.requirement import Requirement
from app.schemas.change_request import ChangeRequestCreate, ChangeRequestUpdate
from app.services.diff_service import DiffService
from app.domain.workflows.change_state_machine import ChangeStateMachine
from app.core.errors import EntityNotFoundError, ValidationError


class ChangeRequestService:
    @staticmethod
    def create_change_request(
        db: Session,
        project_id: str,
        data: ChangeRequestCreate,
        user_id: str,
    ) -> ChangeRequest:
        req = (
            db.query(Requirement)
            .filter(Requirement.id == data.requirement_id, Requirement.project_id == project_id)
            .first()
        )
        if not req:
            raise EntityNotFoundError("Requirement in project", data.requirement_id)

        cr = ChangeRequest(
            project_id=project_id,
            requirement_id=data.requirement_id,
            requester_user_id=user_id,
            title=data.title,
            reason=data.reason,
            business_justification=data.business_justification or "",
            urgency=data.urgency,
            proposed_fields_json=data.proposed_fields,
            status="SUBMITTED",
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(cr)
        db.commit()
        db.refresh(cr)

        # Automatically compute field-level diffs upon creation
        DiffService.compute_and_store_diffs(db, cr)

        return cr

    @staticmethod
    def get_by_id(db: Session, change_request_id: str) -> ChangeRequest:
        cr = db.query(ChangeRequest).filter(ChangeRequest.id == change_request_id).first()
        if not cr:
            raise EntityNotFoundError("ChangeRequest", change_request_id)
        return cr

    @staticmethod
    def get_detail(db: Session, change_request_id: str) -> dict:
        cr = ChangeRequestService.get_by_id(db, change_request_id)
        diffs = DiffService.get_diffs(db, change_request_id)
        latest_analysis = (
            db.query(ImpactAnalysis)
            .filter(
                ImpactAnalysis.change_request_id == change_request_id,
                ImpactAnalysis.is_preview.is_(False),
            )
            .order_by(ImpactAnalysis.created_at.desc())
            .first()
        )

        analysis_data = None
        if latest_analysis:
            from app.services.impact_analysis_service import ImpactAnalysisService
            analysis_data = ImpactAnalysisService.get_analysis_detail(db, latest_analysis.id)

        return {
            "id": cr.id,
            "project_id": cr.project_id,
            "requirement_id": cr.requirement_id,
            "requester_user_id": cr.requester_user_id,
            "title": cr.title,
            "reason": cr.reason,
            "business_justification": cr.business_justification,
            "urgency": cr.urgency,
            "proposed_fields_json": cr.proposed_fields_json,
            "status": cr.status,
            "submitted_at": cr.submitted_at,
            "decided_at": cr.decided_at,
            "decided_by": cr.decided_by,
            "decision_rationale": cr.decision_rationale,
            "created_at": cr.created_at,
            "updated_at": cr.updated_at,
            "requester": cr.requester,
            "decider": cr.decider,
            "diffs": diffs,
            "latest_analysis": analysis_data,
        }

    @staticmethod
    def list_change_requests(
        db: Session,
        project_id: str,
        status: Optional[str] = None,
        urgency: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ChangeRequest], int, int]:
        query = db.query(ChangeRequest).filter(ChangeRequest.project_id == project_id)

        if status:
            query = query.filter(ChangeRequest.status == status)
        if urgency:
            query = query.filter(ChangeRequest.urgency == urgency)

        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        items = (
            query.order_by(ChangeRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total, total_pages

    @staticmethod
    def submit_draft(db: Session, change_request_id: str) -> ChangeRequest:
        cr = ChangeRequestService.get_by_id(db, change_request_id)
        ChangeStateMachine.validate_transition(cr.status, "SUBMITTED")
        cr.status = "SUBMITTED"
        cr.submitted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(cr)
        DiffService.compute_and_store_diffs(db, cr)
        return cr
