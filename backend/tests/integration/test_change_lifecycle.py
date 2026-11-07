from fastapi import status


def test_complete_change_lifecycle(client, auth_headers, test_project):
    pid = test_project.id

    # 1. Create requirement REQ-001
    req_res = client.post(
        f"/api/v1/projects/{pid}/requirements",
        json={
            "display_id": "REQ-001",
            "title": "Event Registration",
            "description": "Students shall be able to register for events.",
            "priority": "HIGH",
            "criticality": 5,
            "acceptance_criteria": ["Students receive confirmation"],
        },
        headers=auth_headers,
    )
    assert req_res.status_code == status.HTTP_201_CREATED
    req = req_res.json()
    req_id = req["id"]
    req_node_id = req["graph_node_id"]

    # 2. Create downstream artifacts: MOD-01, API-01, TEST-01
    mod_res = client.post(
        f"/api/v1/projects/{pid}/artifacts",
        json={
            "display_id": "MOD-01",
            "artifact_type": "MODULE_SERVICE",
            "title": "Registration Service",
            "criticality": 5,
        },
        headers=auth_headers,
    )
    mod = mod_res.json()

    api_res = client.post(
        f"/api/v1/projects/{pid}/artifacts",
        json={
            "display_id": "API-01",
            "artifact_type": "API_ENDPOINT",
            "title": "Register Event API",
            "criticality": 5,
        },
        headers=auth_headers,
    )
    api = api_res.json()

    test_res = client.post(
        f"/api/v1/projects/{pid}/artifacts",
        json={
            "display_id": "TEST-01",
            "artifact_type": "TEST_CASE",
            "title": "Registration Integration Test",
            "criticality": 4,
        },
        headers=auth_headers,
    )
    test_art = test_res.json()

    # 3. Create edges: REQ -> MOD -> API -> TEST
    client.post(
        f"/api/v1/projects/{pid}/edges",
        json={
            "source_node_id": req_node_id,
            "target_node_id": mod["graph_node_id"],
            "relation_type": "IMPLEMENTED_BY",
        },
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/projects/{pid}/edges",
        json={
            "source_node_id": mod["graph_node_id"],
            "target_node_id": api["graph_node_id"],
            "relation_type": "EXPOSES",
        },
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/projects/{pid}/edges",
        json={
            "source_node_id": api["graph_node_id"],
            "target_node_id": test_art["graph_node_id"],
            "relation_type": "VERIFIED_BY",
        },
        headers=auth_headers,
    )

    # 4. Propose Change Request: Require OTP Verification
    cr_res = client.post(
        f"/api/v1/projects/{pid}/change-requests",
        json={
            "requirement_id": req_id,
            "title": "Add OTP Verification to Event Registration",
            "reason": "Prevent unauthorized bot registrations.",
            "urgency": "HIGH",
            "proposed_fields": {
                "title": "Event Registration with OTP",
                "description": "Students shall be able to register for events after verifying a one-time password.",
                "acceptance_criteria": [
                    "Students receive confirmation",
                    "OTP prompt appears before checkout",
                ],
            },
        },
        headers=auth_headers,
    )
    assert cr_res.status_code == status.HTTP_201_CREATED
    cr = cr_res.json()
    cr_id = cr["id"]
    assert cr["status"] == "SUBMITTED"

    # 5. Check computed field-level diff
    diff_res = client.get(f"/api/v1/change-requests/{cr_id}/diff", headers=auth_headers)
    assert diff_res.status_code == status.HTTP_200_OK
    diffs = diff_res.json()
    assert len(diffs) >= 2

    # 6. Run What-if Simulation (must NOT change baseline or cr status)
    sim_res = client.post(f"/api/v1/change-requests/{cr_id}/simulate", headers=auth_headers)
    assert sim_res.status_code == status.HTTP_200_OK
    sim = sim_res.json()
    assert sim["is_preview"] is True
    assert sim["summary"]["total_impacted_artifacts"] == 3

    # Verify original requirement version was unchanged
    req_check = client.get(f"/api/v1/requirements/{req_id}", headers=auth_headers).json()
    assert len(req_check["versions"]) == 1
    assert req_check["current_version"]["title"] == "Event Registration"

    # 7. Run real Impact Analysis
    analysis_res = client.post(f"/api/v1/change-requests/{cr_id}/analyse", headers=auth_headers)
    assert analysis_res.status_code == status.HTTP_200_OK
    analysis = analysis_res.json()
    analysis_id = analysis["id"]
    assert len(analysis["results"]) == 3
    # Check that explanation paths are present
    assert len(analysis["results"][0]["explanation_paths_json"]) > 0

    # 8. Approve the change request
    approve_res = client.post(
        f"/api/v1/change-requests/{cr_id}/approve",
        json={"decision": "APPROVE", "rationale": "Security requirement approved."},
        headers=auth_headers,
    )
    assert approve_res.status_code == status.HTTP_200_OK
    assert approve_res.json()["status"] == "IMPLEMENTING"

    # Verify new Version 2 was created!
    req_after = client.get(f"/api/v1/requirements/{req_id}", headers=auth_headers).json()
    assert len(req_after["versions"]) == 2
    assert req_after["current_version"]["version_number"] == 2
    assert req_after["current_version"]["title"] == "Event Registration with OTP"

    # Verify remediation actions were automatically created
    updated_analysis = client.get(f"/api/v1/impact-analyses/{analysis_id}", headers=auth_headers).json()
    first_res = updated_analysis["results"][0]
    action_id = first_res["actions"][0]["id"]
    assert first_res["actions"][0]["status"] == "OPEN"

    # 9. Closure check fails because actions are OPEN
    closure_check = client.get(f"/api/v1/change-requests/{cr_id}/closure-check", headers=auth_headers).json()
    assert closure_check["can_close"] is False

    # 10. Complete remediation actions and record passing test
    client.patch(
        f"/api/v1/remediation-actions/{action_id}",
        json={"status": "DONE", "completion_notes": "Module updated with OTP check."},
        headers=auth_headers,
    )
    for res_item in updated_analysis["results"][1:]:
        if res_item["actions"]:
            client.patch(
                f"/api/v1/remediation-actions/{res_item['actions'][0]['id']}",
                json={"status": "DONE", "completion_notes": "Updated and verified."},
                headers=auth_headers,
            )

    # Record passing test execution
    client.post(
        f"/api/v1/artifacts/{test_art['id']}/test-executions",
        json={"change_request_id": cr_id, "result": "PASSED", "notes": "All tests green"},
        headers=auth_headers,
    )

    # 11. Closure check now passes!
    closure_check_2 = client.get(f"/api/v1/change-requests/{cr_id}/closure-check", headers=auth_headers).json()
    assert closure_check_2["can_close"] is True

    # 12. Close Change Request
    close_res = client.post(f"/api/v1/change-requests/{cr_id}/close", headers=auth_headers)
    assert close_res.status_code == status.HTTP_200_OK
    assert close_res.json()["status"] == "CLOSED"

    # 13. CSV Export
    csv_res = client.get(f"/api/v1/impact-analyses/{analysis_id}/export.csv", headers=auth_headers)
    assert csv_res.status_code == status.HTTP_200_OK
    assert "Artifact ID" in csv_res.text
    assert "Registration Service" in csv_res.text

    # 14. Check Volatility report
    vol_res = client.get(f"/api/v1/projects/{pid}/volatility", headers=auth_headers)
    assert vol_res.status_code == status.HTTP_200_OK
    assert vol_res.json()[0]["version_count"] == 2
