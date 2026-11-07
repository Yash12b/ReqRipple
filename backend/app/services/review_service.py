from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.change_request import (
    ChangeRequest,
    ImpactAnalysis,
    ImpactResult,
    RemediationAction,
)
from app.models.requirement import Requirement, RequirementVersion
from app.domain.workflows.change_state_machine import ChangeStateMachine
from app.core.errors import EntityNotFoundError, ValidationError, PermissionDeniedError


class ReviewService:
    @staticmethod
    def approve_change_request(
        db: Session,
        change_request_id: str,
        user_id: str,
        rationale: str = "",
    ) -> ChangeRequest:
        cr = db.query(ChangeRequest).filter(ChangeRequest.id == change_request_id).first()
        if not cr:
            raise EntityNotFoundError("ChangeRequest", change_request_id)

        # Verify impact analysis exists
        analysis = (
            db.query(ImpactAnalysis)
            .filter(
                ImpactAnalysis.change_request_id == cr.id,
                ImpactAnalysis.is_preview.is_(False),
            )
            .first()
        )
        if not analysis:
            raise ValidationError(
                "An impact analysis must be performed before approving a change request."
            )

        # Validate workflow transition
        ChangeStateMachine.validate_transition(cr.status, "APPROVED")

        req = db.query(Requirement).filter(Requirement.id == cr.requirement_id).first()
        if not req:
            raise EntityNotFoundError("Requirement", cr.requirement_id)

        now = datetime.now(timezone.utc)

        # 1. Determine next version number
        latest_version = (
            db.query(RequirementVersion)
            .filter(RequirementVersion.requirement_id == req.id)
            .order_by(RequirementVersion.version_number.desc())
            .first()
        )
        next_version_num = (latest_version.version_number + 1) if latest_version else 1

        # 2. Extract proposed fields and merge onto current version
        proposed = cr.proposed_fields_json or {}
        new_title = proposed.get("title", latest_version.title if latest_version else req.display_id)
        new_desc = proposed.get("description", latest_version.description if latest_version else "")
        new_ac = proposed.get("acceptance_criteria", latest_version.acceptance_criteria_json if latest_version else [])
        new_rationale = proposed.get("rationale", cr.reason)

        # 3. Create new immutable approved version
        new_version = RequirementVersion(
            requirement_id=req.id,
            version_number=next_version_num,
            title=new_title,
            description=new_desc,
            rationale=new_rationale,
            acceptance_criteria_json=new_ac,
            status="APPROVED",
            created_by=user_id,
            approved_by=user_id,
            approved_at=now,
        )
        db.add(new_version)
        db.flush()

        # Update requirement current version pointer
        req.current_version_id = new_version.id

        # If priority or criticality were in proposed fields, update requirement metadata
        if "priority" in proposed:
            req.priority = proposed["priority"]
        if "criticality" in proposed:
            req.criticality = proposed["criticality"]

        # 4. Automatically generate remediation actions for impacted results
        results = (
            db.query(ImpactResult)
            .filter(ImpactResult.impact_analysis_id == analysis.id)
            .all()
        )
        for r in results:
            if r.disposition in ("UPDATE_REQUIRED", "RETEST_REQUIRED"):
                action_type = "RETEST" if r.disposition == "RETEST_REQUIRED" else "UPDATE"
                action_title = f"{action_type.title()} {r.artifact.display_id if r.artifact else 'Artifact'}"
                action = RemediationAction(
                    impact_result_id=r.id,
                    title=action_title,
                    action_type=action_type,
                    description=f"Action generated from approved change request '{cr.title}'.",
                    assigned_to=r.artifact.owner_user_id if r.artifact else None,
                    status="OPEN",
                )
                db.add(action)

        # 5. Transition Change Request to APPROVED -> IMPLEMENTING
        cr.status = "IMPLEMENTING"
        cr.decided_at = now
        cr.decided_by = user_id
        cr.decision_rationale = rationale or "Approved based on impact analysis review."

        db.commit()
        db.refresh(cr)
        return cr

    @staticmethod
    def reject_change_request(
        db: Session,
        change_request_id: str,
        user_id: str,
        rationale: str,
    ) -> ChangeRequest:
        if not rationale or not rationale.strip():
            raise ValidationError("A written rationale is mandatory for rejecting a change request.")

        cr = db.query(ChangeRequest).filter(ChangeRequest.id == change_request_id).first()
        if not cr:
            raise EntityNotFoundError("ChangeRequest", change_request_id)

        ChangeStateMachine.validate_transition(cr.status, "REJECTED")

        cr.status = "REJECTED"
        cr.decided_at = datetime.now(timezone.utc)
        cr.decided_by = user_id
        cr.decision_rationale = rationale.strip()

        db.commit()
        db.refresh(cr)
        return cr

    @staticmethod
    def defer_change_request(
        db: Session,
        change_request_id: str,
        user_id: str,
        rationale: str,
    ) -> ChangeRequest:
        if not rationale or not rationale.strip():
            raise ValidationError("A written rationale is mandatory for deferring a change request.")

        cr = db.query(ChangeRequest).filter(ChangeRequest.id == change_request_id).first()
        if not cr:
            raise EntityNotFoundError("ChangeRequest", change_request_id)

        ChangeStateMachine.validate_transition(cr.status, "DEFERRED")

        cr.status = "DEFERRED"
        cr.decided_at = datetime.now(timezone.utc)
        cr.decided_by = user_id
        cr.decision_rationale = rationale.strip()

        db.commit()
        db.refresh(cr)
        return cr

    @staticmethod
    def update_disposition(
        db: Session,
        impact_result_id: str,
        disposition: str,
        rationale: str,
        user_id: str,
    ) -> ImpactResult:
        if disposition in ("NOT_APPLICABLE", "RISK_ACCEPTED") and (not rationale or not rationale.strip()):
            raise ValidationError(
                f"A justification rationale is mandatory when marking disposition as '{disposition}'."
            )

        res = db.query(ImpactResult).filter(ImpactResult.id == impact_result_id).first()
        if not res:
            raise EntityNotFoundError("ImpactResult", impact_result_id)

        res.disposition = disposition
        res.review_rationale = rationale
        res.reviewed_by = user_id
        res.reviewed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(res)
        return res
