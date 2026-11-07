import pytest
from app.services.requirement_service import RequirementService
from app.services.artifact_service import ArtifactService
from app.services.traceability_service import TraceabilityService
from app.schemas.requirement import RequirementCreate, RequirementUpdate
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate
from app.schemas.graph import TraceabilityEdgeCreate, TraceabilityEdgeUpdate
from app.models.project import Project
from app.core.errors import EntityConflictError, EntityNotFoundError, ValidationError


def test_requirement_creation_and_version_immutability(db, test_project, test_user):
    # 1. Create requirement
    req_data = RequirementCreate(
        display_id="REQ-001",
        title="Initial Baseline Requirement",
        description="First description of the requirement.",
        requirement_type="FUNCTIONAL",
        priority="HIGH",
        criticality=4,
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        rationale="Initial approved baseline",
    )
    req = RequirementService.create_requirement(db, test_project.id, req_data, test_user.id)
    assert req.display_id == "REQ-001"
    assert req.current_version_id is not None

    # Verify version 1 snapshot
    versions = RequirementService.get_versions(db, req.id)
    assert len(versions) == 1
    v1 = versions[0]
    assert v1.version_number == 1
    assert v1.title == "Initial Baseline Requirement"
    assert v1.description == "First description of the requirement."
    assert v1.acceptance_criteria_json == ["Criterion 1", "Criterion 2"]

    # 2. Update requirement metadata
    RequirementService.update_metadata(
        db, req.id, RequirementUpdate(priority="CRITICAL", criticality=5)
    )

    # 3. Verify Version 1 was not mutated by the requirement update
    versions_after = RequirementService.get_versions(db, req.id)
    v1_after = versions_after[0]
    assert v1_after.title == "Initial Baseline Requirement"
    assert v1_after.description == "First description of the requirement."
    assert v1_after.version_number == 1


def test_graph_node_display_id_uniqueness_within_project(db, test_project, test_user):
    # Create requirement with REQ-001
    RequirementService.create_requirement(
        db,
        test_project.id,
        RequirementCreate(
            display_id="DUP-001",
            title="First Requirement",
            description="Testing duplicate detection.",
        ),
        test_user.id,
    )

    # Attempting to create an artifact with the same display_id in the same project must fail
    with pytest.raises(EntityConflictError):
        ArtifactService.create_artifact(
            db,
            test_project.id,
            ArtifactCreate(
                display_id="DUP-001",
                artifact_type="API_ENDPOINT",
                title="Duplicate API",
            ),
            test_user.id,
        )


def test_graph_node_display_id_allowed_across_different_projects(db, test_project, test_user):
    # Create a second project
    p2 = Project(
        name="Project Beta",
        description="Second project",
        owner_user_id=test_user.id,
    )
    db.add(p2)
    db.commit()

    # Same display_id in project 1
    req1 = RequirementService.create_requirement(
        db,
        test_project.id,
        RequirementCreate(display_id="COMMON-01", title="Req 1", description="Desc 1 long enough"),
        test_user.id,
    )
    # Same display_id in project 2 is allowed
    req2 = RequirementService.create_requirement(
        db,
        p2.id,
        RequirementCreate(display_id="COMMON-01", title="Req 2", description="Desc 2 long enough"),
        test_user.id,
    )

    assert req1.display_id == req2.display_id
    assert req1.project_id != req2.project_id


def test_traceability_edge_rules(db, test_project, test_user):
    # Create requirement and artifact
    req = RequirementService.create_requirement(
        db,
        test_project.id,
        RequirementCreate(display_id="REQ-100", title="Test Req", description="Detailed test description."),
        test_user.id,
    )
    art = ArtifactService.create_artifact(
        db,
        test_project.id,
        ArtifactCreate(
            display_id="API-100",
            artifact_type="API_ENDPOINT",
            title="Test API",
        ),
        test_user.id,
    )

    # 1. Self-referencing edge is rejected
    with pytest.raises(ValidationError):
        TraceabilityService.create_edge(
            db,
            test_project.id,
            TraceabilityEdgeCreate(
                source_node_id=req.graph_node_id,
                target_node_id=req.graph_node_id,
                relation_type="DEPENDS_ON",
            ),
            test_user.id,
        )

    # 2. Valid edge creation
    edge = TraceabilityService.create_edge(
        db,
        test_project.id,
        TraceabilityEdgeCreate(
            source_node_id=req.graph_node_id,
            target_node_id=art.graph_node_id,
            relation_type="IMPLEMENTED_BY",
        ),
        test_user.id,
    )
    assert edge.id is not None
    assert edge.is_active is True
    assert edge.relationship_strength == 1.00  # Default for IMPLEMENTED_BY

    # 3. Duplicate active edge is rejected
    with pytest.raises(EntityConflictError):
        TraceabilityService.create_edge(
            db,
            test_project.id,
            TraceabilityEdgeCreate(
                source_node_id=req.graph_node_id,
                target_node_id=art.graph_node_id,
                relation_type="IMPLEMENTED_BY",
            ),
            test_user.id,
        )

    # 4. Soft deactivation works
    deactivated = TraceabilityService.deactivate_edge(db, edge.id)
    assert deactivated.is_active is False

    # 5. After deactivation, a new edge between same pair can be created
    new_edge = TraceabilityService.create_edge(
        db,
        test_project.id,
        TraceabilityEdgeCreate(
            source_node_id=req.graph_node_id,
            target_node_id=art.graph_node_id,
            relation_type="REALISED_AS",
        ),
        test_user.id,
    )
    assert new_edge.id != edge.id
    assert new_edge.is_active is True


def test_cross_project_edge_rejection(db, test_project, test_user):
    p2 = Project(
        name="External Project",
        description="Isolated project",
        owner_user_id=test_user.id,
    )
    db.add(p2)
    db.commit()

    req_p1 = RequirementService.create_requirement(
        db,
        test_project.id,
        RequirementCreate(display_id="REQ-P1", title="Req P1", description="Valid long description"),
        test_user.id,
    )
    art_p2 = ArtifactService.create_artifact(
        db,
        p2.id,
        ArtifactCreate(display_id="API-P2", artifact_type="API_ENDPOINT", title="API P2"),
        test_user.id,
    )

    # Attempting to link cross-project must fail
    with pytest.raises(EntityNotFoundError):
        TraceabilityService.create_edge(
            db,
            test_project.id,
            TraceabilityEdgeCreate(
                source_node_id=req_p1.graph_node_id,
                target_node_id=art_p2.graph_node_id,
                relation_type="DEPENDS_ON",
            ),
            test_user.id,
        )
