from fastapi import status


def test_auth_flow(client):
    # 1. Register new user
    reg_payload = {
        "email": "newuser@reqripple.local",
        "name": "New User",
        "password": "strongpassword123",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@reqripple.local"
    token = data["access_token"]

    # 2. Get current user profile
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["email"] == "newuser@reqripple.local"

    # 3. Login with credentials
    login_payload = {
        "email": "newuser@reqripple.local",
        "password": "strongpassword123",
    }
    res = client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == status.HTTP_200_OK
    assert "access_token" in res.json()

    # 4. Bad password fails
    bad_login = {
        "email": "newuser@reqripple.local",
        "password": "wrongpassword",
    }
    res = client.post("/api/v1/auth/login", json=bad_login)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_project_crud_and_access_control(client, auth_headers, second_auth_headers):
    # 1. Create Project
    create_payload = {
        "name": "Integration Test System",
        "description": "Testing permissions and CRUD",
        "domain": "Fintech",
    }
    res = client.post("/api/v1/projects", json=create_payload, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED
    project = res.json()
    project_id = project["id"]
    assert project["name"] == "Integration Test System"

    # 2. Project Detail
    res = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["requirements_count"] == 0

    # 3. Second user (not a member yet) cannot access
    res = client.get(f"/api/v1/projects/{project_id}", headers=second_auth_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 4. Add second user as member
    member_payload = {
        "user_email": "second@reqripple.local",
        "role": "ANALYST",
    }
    res = client.post(
        f"/api/v1/projects/{project_id}/members",
        json=member_payload,
        headers=auth_headers,
    )
    assert res.status_code == status.HTTP_201_CREATED

    # 5. Now second user can access
    res = client.get(f"/api/v1/projects/{project_id}", headers=second_auth_headers)
    assert res.status_code == status.HTTP_200_OK


def test_requirements_and_artifacts_workflow(client, auth_headers, test_project):
    pid = test_project.id

    # 1. Create Requirement
    req_payload = {
        "display_id": "REQ-01",
        "title": "Payment Processing",
        "description": "Process credit card payments securely.",
        "requirement_type": "FUNCTIONAL",
        "priority": "HIGH",
        "criticality": 5,
        "acceptance_criteria": ["PCI-DSS compliant", "Tokenized card storage"],
    }
    res = client.post(f"/api/v1/projects/{pid}/requirements", json=req_payload, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED
    req = res.json()
    req_id = req["id"]
    req_node_id = req["graph_node_id"]
    assert req["display_id"] == "REQ-01"

    # 2. Create Artifact
    art_payload = {
        "display_id": "API-01",
        "artifact_type": "API_ENDPOINT",
        "title": "Process Charge API",
        "description": "POST /api/v1/charges",
        "criticality": 5,
        "estimated_effort_hours": 16.0,
    }
    res = client.post(f"/api/v1/projects/{pid}/artifacts", json=art_payload, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED
    art = res.json()
    art_id = art["id"]
    art_node_id = art["graph_node_id"]
    assert art["display_id"] == "API-01"

    # 3. Create Traceability Edge
    edge_payload = {
        "source_node_id": req_node_id,
        "target_node_id": art_node_id,
        "relation_type": "IMPLEMENTED_BY",
        "notes": "Direct API endpoint implementing payment processing",
    }
    res = client.post(f"/api/v1/projects/{pid}/edges", json=edge_payload, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED
    edge = res.json()
    edge_id = edge["id"]
    assert edge["relation_type"] == "IMPLEMENTED_BY"

    # 4. Get Project Graph
    res = client.get(f"/api/v1/projects/{pid}/graph", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK
    graph = res.json()
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
    assert graph["edges"][0]["source_display_id"] == "REQ-01"
    assert graph["edges"][0]["target_display_id"] == "API-01"

    # 5. Check Traceability Health
    res = client.get(f"/api/v1/projects/{pid}/traceability-health", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK
    health = res.json()
    assert health["total_requirements"] == 1
    assert health["requirements_with_implementation"] == 1
    assert health["critical_untested_count"] == 1  # API-01 has criticality 5 and no test linked!

    # 6. Update Edge attributes
    patch_edge_res = client.patch(
        f"/api/v1/edges/{edge_id}",
        json={"confirmation_status": "NEEDS_REVIEW", "notes": "Updated review note"},
        headers=auth_headers,
    )
    assert patch_edge_res.status_code == status.HTTP_200_OK
    assert patch_edge_res.json()["confirmation_status"] == "NEEDS_REVIEW"

    # 7. Deactivate Edge
    res = client.delete(f"/api/v1/edges/{edge_id}", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["is_active"] is False

    # 8. Graph now reflects 0 active edges
    res = client.get(f"/api/v1/projects/{pid}/graph", headers=auth_headers)
    assert len(res.json()["edges"]) == 0


def test_requirements_and_artifacts_filters_and_search(client, auth_headers, test_project):
    pid = test_project.id

    # Create two requirements
    client.post(
        f"/api/v1/projects/{pid}/requirements",
        json={
            "display_id": "REQ-A",
            "title": "Alpha Notification",
            "description": "Send SMS notifications to users.",
            "priority": "LOW",
            "criticality": 2,
        },
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/projects/{pid}/requirements",
        json={
            "display_id": "REQ-B",
            "title": "Beta Encryption",
            "description": "Encrypt data at rest with AES-256.",
            "priority": "CRITICAL",
            "criticality": 5,
        },
        headers=auth_headers,
    )

    # Filter by priority
    res = client.get(f"/api/v1/projects/{pid}/requirements?priority=CRITICAL", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["display_id"] == "REQ-B"

    # Search by title keyword
    res = client.get(f"/api/v1/projects/{pid}/requirements?search=Notification", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["display_id"] == "REQ-A"
