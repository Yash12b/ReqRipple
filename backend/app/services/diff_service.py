from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.change_request import ChangeRequest, ChangeRequestDiff
from app.models.requirement import Requirement, RequirementVersion
from app.domain.impact.change_classifier import ChangeClassifier, DiffResult
from app.core.errors import EntityNotFoundError


class DiffService:
    @staticmethod
    def compute_and_store_diffs(db: Session, change_request: ChangeRequest) -> List[ChangeRequestDiff]:
        req = db.query(Requirement).filter(Requirement.id == change_request.requirement_id).first()
        if not req:
            raise EntityNotFoundError("Requirement", change_request.requirement_id)

        current_version = None
        if req.current_version_id:
            current_version = (
                db.query(RequirementVersion)
                .filter(RequirementVersion.id == req.current_version_id)
                .first()
            )

        current_data: Dict[str, Any] = {}
        if current_version:
            current_data = {
                "title": current_version.title,
                "description": current_version.description,
                "acceptance_criteria": current_version.acceptance_criteria_json,
                "rationale": current_version.rationale,
                "priority": req.priority,
                "criticality": req.criticality,
            }

        proposed_data = change_request.proposed_fields_json or {}

        # Use pure domain classifier
        diff_results: List[DiffResult] = ChangeClassifier.compare_requirement_versions(
            current_data, proposed_data
        )

        # Clear existing diffs for this change request
        db.query(ChangeRequestDiff).filter(
            ChangeRequestDiff.change_request_id == change_request.id
        ).delete()

        stored_diffs: List[ChangeRequestDiff] = []
        for d in diff_results:
            diff_record = ChangeRequestDiff(
                change_request_id=change_request.id,
                field_name=d.field_name,
                old_value=d.old_value,
                new_value=d.new_value,
                diff_type=d.diff_type,
                change_category=d.change_category,
            )
            db.add(diff_record)
            stored_diffs.append(diff_record)

        db.commit()
        return stored_diffs

    @staticmethod
    def get_diffs(db: Session, change_request_id: str) -> List[ChangeRequestDiff]:
        return (
            db.query(ChangeRequestDiff)
            .filter(ChangeRequestDiff.change_request_id == change_request_id)
            .all()
        )
