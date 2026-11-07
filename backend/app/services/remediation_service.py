from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.change_request import (
    ChangeRequest,
    ImpactAnalysis,
    ImpactResult,
    RemediationAction,
    TestExecution,
)
from app.models.artifact import Artifact
from app.schemas.change_request import RemediationActionCreate, RemediationActionUpdate, TestExecutionCreate
from app.domain.workflows.closure_rules import ClosureRules
from app.domain.workflows.change_state_machine import ChangeStateMachine
from app.core.errors import EntityNotFoundError, ValidationError


class RemediationService:
    @staticmethod
    def create_action(
        db: Session,
        impact_result_id: str,
        data: RemediationActionCreate,
    ) -> RemediationAction:
        res = db.query(ImpactResult).filter(ImpactResult.id == impact_result_id).first()
        if not res:
            raise EntityNotFoundError("ImpactResult", impact_result_id)

        action = RemediationAction(
            impact_result_id=impact_result_id,
            title=data.title,
            action_type=data.action_type,
            description=data.description or "",
            assigned_to=data.assigned_to,
            due_date=data.due_date,
            status="OPEN",
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def update_action(
        db: Session,
        action_id: str,
        data: RemediationActionUpdate,
    ) -> RemediationAction:
        action = db.query(RemediationAction).filter(RemediationAction.id == action_id).first()
        if not action:
            raise EntityNotFoundError("RemediationAction", action_id)

        if data.title is not None:
            action.title = data.title
        if data.description is not None:
            action.description = data.description
        if data.assigned_to is not None:
            action.assigned_to = data.assigned_to
        if data.due_date is not None:
            action.due_date = data.due_date
        if data.status is not None:
            action.status = data.status
            if data.status in ("DONE", "WAIVED"):
                action.completed_at = datetime.now(timezone.utc)
        if data.completion_notes is not None:
            action.completion_notes = data.completion_notes
        if data.evidence_reference is not None:
            action.evidence_reference = data.evidence_reference

        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def record_test_execution(
        db: Session,
        artifact_id: str,
        data: TestExecutionCreate,
        user_id: str,
    ) -> TestExecution:
        art = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        if not art:
            raise EntityNotFoundError("Artifact", artifact_id)
        if art.artifact_type != "TEST_CASE":
            raise ValidationError(
                f"Test executions can only be recorded against TEST_CASE artifacts, but artifact '{art.display_id}' has type '{art.artifact_type}'."
            )

        test_exec = TestExecution(
            artifact_id=artifact_id,
            change_request_id=data.change_request_id,
            executed_by=user_id,
            result=data.result,
            notes=data.notes or "",
            evidence_reference=data.evidence_reference,
            executed_at=datetime.now(timezone.utc),
        )
        db.add(test_exec)
        db.commit()
        db.refresh(test_exec)
        return test_exec

    @staticmethod
    def check_closure(db: Session, change_request_id: str) -> Tuple[bool, List[str]]:
        cr = db.query(ChangeRequest).filter(ChangeRequest.id == change_request_id).first()
        if not cr:
            raise EntityNotFoundError("ChangeRequest", change_request_id)

        analysis = (
            db.query(ImpactAnalysis)
            .filter(
                ImpactAnalysis.change_request_id == cr.id,
                ImpactAnalysis.is_preview.is_(False),
            )
            .first()
        )
        if not analysis:
            return False, ["No approved impact analysis snapshot exists for this change request."]

        results = (
            db.query(ImpactResult)
            .filter(ImpactResult.impact_analysis_id == analysis.id)
            .all()
        )
        res_dicts = [
            {"id": r.id, "artifact_id": r.artifact_id, "disposition": r.disposition}
            for r in results
        ]

        result_ids = [r.id for r in results]
        actions = (
            db.query(RemediationAction)
            .filter(RemediationAction.impact_result_id.in_(result_ids))
            .all()
        )
        act_dicts = [{"id": a.id, "status": a.status} for a in actions]

        test_execs = (
            db.query(TestExecution)
            .filter(TestExecution.change_request_id == cr.id)
            .all()
        )
        test_dicts = [
            {"id": t.id, "artifact_id": t.artifact_id, "result": t.result}
            for t in test_execs
        ]

        return ClosureRules.evaluate_closure_conditions(res_dicts, act_dicts, test_dicts)

    @staticmethod
    def close_change_request(db: Session, change_request_id: str) -> ChangeRequest:
        cr = db.query(ChangeRequest).filter(ChangeRequest.id == change_request_id).first()
        if not cr:
            raise EntityNotFoundError("ChangeRequest", change_request_id)

        can_close, reasons = RemediationService.check_closure(db, change_request_id)
        if not can_close:
            raise ValidationError(
                f"Change request cannot be closed due to unmet conditions: {'; '.join(reasons)}"
            )

        ChangeStateMachine.validate_transition(cr.status, "CLOSED")
        cr.status = "CLOSED"
        db.commit()
        db.refresh(cr)
        return cr
