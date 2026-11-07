from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.change_request import (
    ChangeRequest,
    ImpactAnalysis,
    ImpactResult,
    RemediationAction,
    TestExecution,
)
from app.models.requirement import Requirement, RequirementVersion
from app.models.artifact import Artifact
from app.models.graph import TraceabilityEdge
from app.services.traceability_service import TraceabilityService


class DashboardService:
    @staticmethod
    def get_project_dashboard(db: Session, project_id: str) -> Dict[str, Any]:
        # Basic counts
        total_reqs = db.query(func.count(Requirement.id)).filter(Requirement.project_id == project_id).scalar() or 0
        total_arts = db.query(func.count(Artifact.id)).filter(Artifact.project_id == project_id).scalar() or 0
        total_edges = (
            db.query(func.count(TraceabilityEdge.id))
            .filter(TraceabilityEdge.project_id == project_id, TraceabilityEdge.is_active.is_(True))
            .scalar()
            or 0
        )

        # Change request statuses
        open_crs = (
            db.query(ChangeRequest)
            .filter(
                ChangeRequest.project_id == project_id,
                ChangeRequest.status.in_(["SUBMITTED", "ANALYSIS_READY", "IN_REVIEW", "IMPLEMENTING", "VERIFICATION_PENDING"]),
            )
            .count()
        )

        # Traceability health
        health = TraceabilityService.get_traceability_health(db, project_id)

        # Change debt indicators
        debt = DashboardService.get_change_debt(db, project_id)

        # Recent change requests
        recent_crs = (
            db.query(ChangeRequest)
            .filter(ChangeRequest.project_id == project_id)
            .order_by(ChangeRequest.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "project_id": project_id,
            "total_requirements": total_reqs,
            "total_artifacts": total_arts,
            "total_active_edges": total_edges,
            "open_change_requests_count": open_crs,
            "traceability_health": health,
            "change_debt": debt,
            "recent_change_requests": [
                {
                    "id": cr.id,
                    "title": cr.title,
                    "status": cr.status,
                    "urgency": cr.urgency,
                    "created_at": cr.created_at,
                }
                for cr in recent_crs
            ],
        }

    @staticmethod
    def get_change_debt(db: Session, project_id: str) -> Dict[str, Any]:
        # Get all non-preview analyses for this project's change requests
        cr_ids = [
            r[0] for r in db.query(ChangeRequest.id).filter(ChangeRequest.project_id == project_id).all()
        ]

        # 1. Unreviewed high/critical impacts
        unreviewed_high_critical = (
            db.query(ImpactResult)
            .join(ImpactAnalysis, ImpactResult.impact_analysis_id == ImpactAnalysis.id)
            .filter(
                ImpactAnalysis.change_request_id.in_(cr_ids),
                ImpactAnalysis.is_preview.is_(False),
                ImpactResult.priority_band.in_(["CRITICAL", "HIGH"]),
                ImpactResult.reviewed_by.is_(None),
            )
            .count()
        )

        # 2. Overdue remediation actions
        now = datetime.now(timezone.utc)
        overdue_actions = (
            db.query(RemediationAction)
            .join(ImpactResult, RemediationAction.impact_result_id == ImpactResult.id)
            .join(ImpactAnalysis, ImpactResult.impact_analysis_id == ImpactAnalysis.id)
            .filter(
                ImpactAnalysis.change_request_id.in_(cr_ids),
                RemediationAction.status.in_(["OPEN", "IN_PROGRESS", "BLOCKED"]),
                RemediationAction.due_date.isnot(None),
                RemediationAction.due_date < now,
            )
            .count()
        )

        # 3. Pending retests
        pending_retests = (
            db.query(ImpactResult)
            .join(ImpactAnalysis, ImpactResult.impact_analysis_id == ImpactAnalysis.id)
            .filter(
                ImpactAnalysis.change_request_id.in_(cr_ids),
                ImpactAnalysis.is_preview.is_(False),
                ImpactResult.disposition == "RETEST_REQUIRED",
            )
            .count()
        )

        # 4. Failed/blocked tests
        failed_tests = (
            db.query(TestExecution)
            .filter(
                TestExecution.change_request_id.in_(cr_ids),
                TestExecution.result.in_(["FAILED", "BLOCKED"]),
            )
            .count()
        )

        # 5. Accepted risks
        accepted_risks = (
            db.query(ImpactResult)
            .join(ImpactAnalysis, ImpactResult.impact_analysis_id == ImpactAnalysis.id)
            .filter(
                ImpactAnalysis.change_request_id.in_(cr_ids),
                ImpactAnalysis.is_preview.is_(False),
                ImpactResult.disposition == "RISK_ACCEPTED",
            )
            .count()
        )

        # 6. Active implementing changes
        implementing_changes = (
            db.query(ChangeRequest)
            .filter(
                ChangeRequest.project_id == project_id,
                ChangeRequest.status.in_(["APPROVED", "IMPLEMENTING", "VERIFICATION_PENDING"]),
            )
            .count()
        )

        return {
            "unreviewed_high_critical_count": unreviewed_high_critical,
            "overdue_actions_count": overdue_actions,
            "pending_retests_count": pending_retests,
            "failed_tests_count": failed_tests,
            "accepted_risks_count": accepted_risks,
            "open_approved_changes_count": implementing_changes,
        }

    @staticmethod
    def get_volatility(db: Session, project_id: str) -> List[Dict[str, Any]]:
        # Count approved changes / versions per requirement
        reqs = db.query(Requirement).filter(Requirement.project_id == project_id).all()
        results = []
        for r in reqs:
            v_count = (
                db.query(func.count(RequirementVersion.id))
                .filter(RequirementVersion.requirement_id == r.id)
                .scalar()
                or 0
            )
            approved_crs = (
                db.query(func.count(ChangeRequest.id))
                .filter(
                    ChangeRequest.requirement_id == r.id,
                    ChangeRequest.status.in_(["APPROVED", "IMPLEMENTING", "VERIFICATION_PENDING", "CLOSED"]),
                )
                .scalar()
                or 0
            )
            results.append(
                {
                    "requirement_id": r.id,
                    "display_id": r.display_id,
                    "title": r.versions[0].title if r.versions else r.display_id,
                    "version_count": v_count,
                    "approved_changes_count": approved_crs,
                    "volatility_signal": "HIGH" if approved_crs >= 3 else ("MEDIUM" if approved_crs >= 1 else "STABLE"),
                }
            )

        results.sort(key=lambda x: x["approved_changes_count"], reverse=True)
        return results
