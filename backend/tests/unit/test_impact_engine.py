import pytest
from app.domain.graph.traversal import GraphEngine, GraphEdgeView
from app.domain.impact.scoring import ScoringEngine
from app.domain.impact.change_classifier import ChangeClassifier
from app.domain.workflows.change_state_machine import ChangeStateMachine
from app.domain.workflows.closure_rules import ClosureRules
from app.core.errors import ValidationError


def test_linear_path_traversal():
    edges = [
        GraphEdgeView("e1", "N_REQ", "N_MOD", "IMPLEMENTED_BY", 1.0, True, "CONFIRMED"),
        GraphEdgeView("e2", "N_MOD", "N_API", "EXPOSES", 0.9, True, "CONFIRMED"),
        GraphEdgeView("e3", "N_API", "N_UI", "CONSUMED_BY", 0.85, True, "CONFIRMED"),
    ]
    results, warnings = GraphEngine.traverse_impact("N_REQ", edges)

    assert len(results) == 3
    assert results["N_MOD"].shortest_distance == 1
    assert results["N_MOD"].path_strength == 1.0

    assert results["N_API"].shortest_distance == 2
    assert results["N_API"].path_strength == 0.9

    assert results["N_UI"].shortest_distance == 3
    assert results["N_UI"].path_strength == round(1.0 * 0.9 * 0.85, 4)
    assert len(results["N_UI"].explanation_paths) == 1


def test_branching_and_multiple_paths():
    edges = [
        GraphEdgeView("e1", "N_REQ", "N_B", "DEPENDS_ON", 0.9, True, "CONFIRMED"),
        GraphEdgeView("e2", "N_REQ", "N_C", "DEPENDS_ON", 0.8, True, "CONFIRMED"),
        GraphEdgeView("e3", "N_B", "N_D", "DEPENDS_ON", 0.9, True, "CONFIRMED"),
        GraphEdgeView("e4", "N_C", "N_D", "DEPENDS_ON", 0.7, True, "CONFIRMED"),
    ]
    results, warnings = GraphEngine.traverse_impact("N_REQ", edges)

    assert "N_D" in results
    assert results["N_D"].shortest_distance == 2
    # Two paths reach N_D: via B (0.9*0.9 = 0.81) and via C (0.8*0.7 = 0.56)
    assert len(results["N_D"].explanation_paths) == 2
    assert results["N_D"].path_strength == 0.81


def test_cycle_safe_traversal():
    # Graph containing a cycle: N_REQ -> N_A -> N_B -> N_A
    edges = [
        GraphEdgeView("e1", "N_REQ", "N_A", "IMPLEMENTED_BY", 1.0, True, "CONFIRMED"),
        GraphEdgeView("e2", "N_A", "N_B", "DEPENDS_ON", 0.9, True, "CONFIRMED"),
        GraphEdgeView("e3", "N_B", "N_A", "DEPENDS_ON", 0.9, True, "CONFIRMED"),
    ]
    results, warnings = GraphEngine.traverse_impact("N_REQ", edges)

    assert "N_A" in results
    assert "N_B" in results
    assert results["N_A"].shortest_distance == 1
    assert results["N_B"].shortest_distance == 2
    assert any("cycles" in w for w in warnings)


def test_inactive_and_non_propagating_edges_ignored():
    edges = [
        GraphEdgeView("e1", "N_REQ", "N_A", "IMPLEMENTED_BY", 1.0, False, "CONFIRMED"), # disabled
    ]
    results, warnings = GraphEngine.traverse_impact("N_REQ", edges)
    assert len(results) == 0
    assert any("no outgoing active propagation links" in w for w in warnings)


def test_scoring_engine_computation():
    # Database artifact with path strength 0.90, distance 2, criticality 5, no linked test
    score_data = ScoringEngine.compute_score(
        path_strength=0.90,
        shortest_distance=2,
        criticality=5,
        test_status="NONE",
    )
    # D = 0.90, P = 0.50, C = 1.00, V = 1.00
    # Score = round(100 * (0.30*0.90 + 0.20*0.50 + 0.25*1.00 + 0.25*1.00)) = round(87.0) = 87
    assert score_data["final_score"] == 87
    assert score_data["priority_band"] == "CRITICAL"


def test_change_classifier_diff():
    current = {
        "title": "Register Event",
        "description": "Students can register for events.",
        "acceptance_criteria": ["Receive confirmation email"],
    }
    proposed = {
        "title": "Register Event",
        "description": "Students can register for events after completing OTP verification.",
        "acceptance_criteria": ["Receive confirmation email", "Must verify valid OTP"],
    }
    diffs = ChangeClassifier.compare_requirement_versions(current, proposed)
    assert len(diffs) == 2
    diff_fields = {d.field_name: d for d in diffs}

    assert "description" in diff_fields
    assert diff_fields["description"].diff_type == "MODIFIED"

    assert "acceptance_criteria" in diff_fields
    assert diff_fields["acceptance_criteria"].diff_type == "MODIFIED"


def test_state_machine_and_closure_rules():
    # Valid transition
    ChangeStateMachine.validate_transition("DRAFT", "SUBMITTED")
    ChangeStateMachine.validate_transition("SUBMITTED", "ANALYSIS_READY")
    ChangeStateMachine.validate_transition("ANALYSIS_READY", "IN_REVIEW")

    # Invalid transition raises ValidationError
    with pytest.raises(ValidationError):
        ChangeStateMachine.validate_transition("DRAFT", "CLOSED")

    # Closure rules test: pending actions block closure
    impact_results = [{"id": "r1", "artifact_id": "a1", "disposition": "UPDATE_REQUIRED"}]
    incomplete_actions = [{"id": "act1", "status": "OPEN"}]
    test_execs = []
    can_close, reasons = ClosureRules.evaluate_closure_conditions(
        impact_results, incomplete_actions, test_execs
    )
    assert can_close is False
    assert len(reasons) > 0

    # Once action is DONE, closure is allowed
    completed_actions = [{"id": "act1", "status": "DONE"}]
    can_close, reasons = ClosureRules.evaluate_closure_conditions(
        impact_results, completed_actions, test_execs
    )
    assert can_close is True
    assert len(reasons) == 0
