from typing import Set, Dict
from app.core.errors import ValidationError

ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "DRAFT": {"SUBMITTED", "CANCELLED"},
    "SUBMITTED": {"ANALYSIS_READY", "CANCELLED"},
    "ANALYSIS_READY": {"IN_REVIEW", "APPROVED", "REJECTED", "DEFERRED", "SUBMITTED"},
    "IN_REVIEW": {"APPROVED", "REJECTED", "DEFERRED"},
    "DEFERRED": {"SUBMITTED", "CANCELLED"},
    "APPROVED": {"IMPLEMENTING"},
    "IMPLEMENTING": {"VERIFICATION_PENDING", "CLOSED"},
    "VERIFICATION_PENDING": {"IMPLEMENTING", "CLOSED"},
    "REJECTED": set(),
    "CLOSED": set(),
    "CANCELLED": set(),
}


class ChangeStateMachine:
    @staticmethod
    def validate_transition(current_status: str, target_status: str) -> None:
        current_status = current_status.upper()
        target_status = target_status.upper()

        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ValidationError(
                f"Invalid workflow transition from status '{current_status}' to '{target_status}'. "
                f"Allowed target statuses: {sorted(list(allowed)) if allowed else 'None (terminal state)'}."
            )
