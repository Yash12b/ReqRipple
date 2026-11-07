import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from app.models.change_request import (
    ChangeRequest,
    ImpactAnalysis,
    ImpactResult,
    TestExecution,
)
from app.models.requirement import Requirement, RequirementVersion
from app.models.artifact import Artifact
from app.models.graph import GraphNode, TraceabilityEdge
from app.models.project import Project
from app.domain.graph.traversal import GraphEngine, GraphEdgeView
from app.domain.impact.scoring import ScoringEngine
from app.services.diff_service import DiffService
from app.core.errors import EntityNotFoundError


class ImpactAnalysisService:
    @staticmethod
    def run_analysis(
        db: Session,
        change_request_id: str,
        user_id: str,
        is_preview: bool = False,
    ) -> Dict[str, Any]:
        cr = db.query(ChangeRequest).filter(ChangeRequest.id == change_request_id).first()
        if not cr:
            raise EntityNotFoundError("ChangeRequest", change_request_id)

        project = db.query(Project).filter(Project.id == cr.project_id).first()
        req = db.query(Requirement).filter(Requirement.id == cr.requirement_id).first()
        if not req:
            raise EntityNotFoundError("Requirement", cr.requirement_id)

        # 1. Ensure diff is computed
        diffs = DiffService.compute_and_store_diffs(db, cr)

        # 2. Collect active graph edges and nodes
        active_edges = (
            db.query(TraceabilityEdge)
            .filter(
                TraceabilityEdge.project_id == cr.project_id,
                TraceabilityEdge.is_active.is_(True),
            )
            .all()
        )
        nodes = db.query(GraphNode).filter(GraphNode.project_id == cr.project_id).all()
        node_display_map = {n.id: n.display_id for n in nodes}
        node_type_map = {n.id: n.node_type for n in nodes}

        edge_views = [
            GraphEdgeView(
                id=e.id,
                source_id=e.source_node_id,
                target_id=e.target_node_id,
                relation_type=e.relation_type,
                relationship_strength=e.relationship_strength,
                propagation_enabled=e.propagation_enabled,
                confirmation_status=e.confirmation_status,
            )
            for e in active_edges
        ]

        # 3. Graph hash for snapshot tracking
        graph_repr = "".join(sorted([f"{e.source_node_id}->{e.target_node_id}" for e in active_edges]))
        graph_snapshot_hash = hashlib.sha256(graph_repr.encode("utf-8")).hexdigest()[:16]

        # 4. Execute deterministic BFS traversal
        traversal_results, traversal_warnings = GraphEngine.traverse_impact(
            start_node_id=req.graph_node_id,
            edges=edge_views,
            node_display_map=node_display_map,
        )

        # 5. Lookup all artifacts in project
        artifacts = db.query(Artifact).filter(Artifact.project_id == cr.project_id).all()
        art_by_node_id = {a.graph_node_id: a for a in artifacts}

        # Verification lookup: find test cases connected to artifacts
        test_executions = (
            db.query(TestExecution)
            .filter(TestExecution.change_request_id == cr.id)
            .all()
        )
        latest_test_results = {t.artifact_id: t.result for t in test_executions}

        # Project scoring weights
        weights = project.settings_json.get("weights", ScoringEngine.DEFAULT_WEIGHTS)

        # 6. Assemble impact items
        impact_items = []
        band_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        total_estimated_effort = 0.0

        for node_id, t_res in traversal_results.items():
            # Check if reached node is an artifact
            art = art_by_node_id.get(node_id)
            if not art:
                # Could be another requirement or sub-node
                continue

            total_estimated_effort += art.estimated_effort_hours or 0.0

            # Determine test status
            test_status = "NONE"
            if art.artifact_type == "TEST_CASE":
                res = latest_test_results.get(art.id, "NOT_RUN")
                test_status = "PASSING" if res == "PASSED" else ("FAILING" if res in ("FAILED", "BLOCKED") else "STALE")
            else:
                # Check if there is an outgoing VERIFIED_BY or incoming edge to a test
                linked_tests = [
                    e for e in active_edges
                    if (e.source_node_id == art.graph_node_id and e.relation_type == "VERIFIED_BY")
                    or (e.target_node_id == art.graph_node_id and e.relation_type == "VERIFIED_BY")
                ]
                if linked_tests:
                    test_status = "STALE"

            score_data = ScoringEngine.compute_score(
                path_strength=t_res.path_strength,
                shortest_distance=t_res.shortest_distance,
                criticality=art.criticality,
                test_status=test_status,
                custom_weights=weights,
            )

            band = score_data["priority_band"]
            band_counts[band] = band_counts.get(band, 0) + 1

            warnings = list(traversal_warnings)
            if t_res.has_unconfirmed_edges:
                warnings.append("One or more dependency edges on the shortest path are unconfirmed.")
            if not art.owner_user_id:
                warnings.append("Artifact has no assigned owner.")
            if art.criticality >= 4 and test_status == "NONE":
                warnings.append("High criticality artifact has no linked verification/test coverage.")

            impact_items.append(
                {
                    "artifact_id": art.id,
                    "artifact_display_id": art.display_id,
                    "artifact_title": art.title,
                    "artifact_type": art.artifact_type,
                    "shortest_distance": t_res.shortest_distance,
                    "path_strength": t_res.path_strength,
                    "criticality_factor": score_data["criticality_factor"],
                    "proximity_factor": score_data["proximity_factor"],
                    "verification_gap_factor": score_data["verification_gap_factor"],
                    "impact_score": score_data["final_score"],
                    "priority_band": band,
                    "explanation_paths_json": t_res.explanation_paths,
                    "warning_flags_json": warnings,
                    "disposition": "UPDATE_REQUIRED",
                }
            )

        # Sort impact items by impact_score descending
        impact_items.sort(key=lambda x: x["impact_score"], reverse=True)

        summary = {
            "total_impacted_artifacts": len(impact_items),
            "priority_counts": band_counts,
            "total_estimated_effort_hours": round(total_estimated_effort, 1),
            "critical_items_count": band_counts["CRITICAL"],
            "high_items_count": band_counts["HIGH"],
            "graph_snapshot_hash": graph_snapshot_hash,
        }

        # 7. Persistence (only if NOT in preview mode)
        if not is_preview:
            # Delete any previous non-preview analysis for this change request
            db.query(ImpactAnalysis).filter(
                ImpactAnalysis.change_request_id == cr.id,
                ImpactAnalysis.is_preview.is_(False),
            ).delete()

            analysis = ImpactAnalysis(
                change_request_id=cr.id,
                source_requirement_version_id=req.current_version_id,
                graph_snapshot_hash=graph_snapshot_hash,
                algorithm_version="1.0.0",
                scoring_weights_json=weights,
                summary_json=summary,
                is_preview=False,
                created_by=user_id,
            )
            db.add(analysis)
            db.flush()

            for item in impact_items:
                res = ImpactResult(
                    impact_analysis_id=analysis.id,
                    artifact_id=item["artifact_id"],
                    shortest_distance=item["shortest_distance"],
                    path_strength=item["path_strength"],
                    criticality_factor=item["criticality_factor"],
                    proximity_factor=item["proximity_factor"],
                    verification_gap_factor=item["verification_gap_factor"],
                    impact_score=item["impact_score"],
                    priority_band=item["priority_band"],
                    explanation_paths_json=item["explanation_paths_json"],
                    warning_flags_json=item["warning_flags_json"],
                    disposition=item["disposition"],
                )
                db.add(res)

            # Move status to ANALYSIS_READY if currently SUBMITTED or DRAFT
            if cr.status in ("DRAFT", "SUBMITTED"):
                cr.status = "ANALYSIS_READY"

            db.commit()
            db.refresh(analysis)
            return ImpactAnalysisService.get_analysis_detail(db, analysis.id)

        # For preview / simulation
        return {
            "change_request_id": cr.id,
            "is_preview": True,
            "summary": summary,
            "diffs": [d.to_dict() if hasattr(d, "to_dict") else {
                "field_name": d.field_name,
                "old_value": d.old_value,
                "new_value": d.new_value,
                "diff_type": d.diff_type,
                "change_category": d.change_category,
            } for d in diffs],
            "results": impact_items,
            "warnings": traversal_warnings,
        }

    @staticmethod
    def get_analysis_detail(db: Session, analysis_id: str) -> dict:
        analysis = db.query(ImpactAnalysis).filter(ImpactAnalysis.id == analysis_id).first()
        if not analysis:
            raise EntityNotFoundError("ImpactAnalysis", analysis_id)

        results = (
            db.query(ImpactResult)
            .filter(ImpactResult.impact_analysis_id == analysis_id)
            .order_by(ImpactResult.impact_score.desc())
            .all()
        )

        result_items = []
        for r in results:
            result_items.append(
                {
                    "id": r.id,
                    "impact_analysis_id": r.impact_analysis_id,
                    "artifact_id": r.artifact_id,
                    "artifact_display_id": r.artifact.display_id if r.artifact else None,
                    "artifact_title": r.artifact.title if r.artifact else None,
                    "artifact_type": r.artifact.artifact_type if r.artifact else None,
                    "shortest_distance": r.shortest_distance,
                    "path_strength": r.path_strength,
                    "criticality_factor": r.criticality_factor,
                    "proximity_factor": r.proximity_factor,
                    "verification_gap_factor": r.verification_gap_factor,
                    "impact_score": r.impact_score,
                    "priority_band": r.priority_band,
                    "explanation_paths_json": r.explanation_paths_json,
                    "warning_flags_json": r.warning_flags_json,
                    "disposition": r.disposition,
                    "reviewed_by": r.reviewed_by,
                    "reviewed_at": r.reviewed_at,
                    "review_rationale": r.review_rationale,
                    "reviewer": r.reviewer,
                    "actions": r.actions,
                }
            )

        return {
            "id": analysis.id,
            "change_request_id": analysis.change_request_id,
            "source_requirement_version_id": analysis.source_requirement_version_id,
            "algorithm_version": analysis.algorithm_version,
            "scoring_weights_json": analysis.scoring_weights_json,
            "summary_json": analysis.summary_json,
            "is_preview": analysis.is_preview,
            "created_by": analysis.created_by,
            "created_at": analysis.created_at,
            "results": result_items,
        }
