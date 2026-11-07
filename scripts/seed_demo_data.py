#!/usr/bin/env python3
"""
Seed script for ReqRipple: Demonstrates the 'Campus Event Management Platform' dataset.
Populates:
- 4 Users (Admin, Analyst, Developer, QA)
- 1 Demo Project
- 10 Requirements (REQ-001 to REQ-010) with initial approved baseline Version 1
- 24 Engineering Artifacts (MOD, API, DB, UI, TEST, DOC)
- Realistic directed Traceability Edges
"""

import os
import sys

# Ensure backend app is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.graph import GraphNode, TraceabilityEdge
from app.models.requirement import Requirement, RequirementVersion
from app.models.artifact import Artifact
from app.core.security import hash_password
from datetime import datetime, timezone


def seed():
    db = SessionLocal()
    try:
        print("🌱 Seeding Demo Dataset for ReqRipple...")

        # 1. Users
        users_data = [
            {"email": "admin@reqripple.local", "name": "Alex ProjectManager", "role": "ADMIN"},
            {"email": "analyst@reqripple.local", "name": "Alice Analyst", "role": "ANALYST"},
            {"email": "dev@reqripple.local", "name": "Bob Developer", "role": "DEVELOPER"},
            {"email": "qa@reqripple.local", "name": "Carol Tester", "role": "TESTER"},
        ]
        user_records = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                existing = User(
                    email=u["email"],
                    name=u["name"],
                    password_hash=hash_password("password123"),
                )
                db.add(existing)
                db.flush()
            user_records[u["role"]] = existing
        db.commit()
        print("✓ Users verified/created.")

        admin_user = user_records["ADMIN"]
        analyst_user = user_records["ANALYST"]
        dev_user = user_records["DEVELOPER"]
        qa_user = user_records["TESTER"]

        # 2. Project
        project_name = "Campus Event Management Platform"
        project = db.query(Project).filter(Project.name == project_name).first()
        if project:
            print(f"ℹ️ Project '{project_name}' already exists. Skipping duplicate seeding.")
            return

        project = Project(
            name=project_name,
            description="Integrated student event discovery, registration, QR check-in, and attendance audit platform.",
            domain="Education / Campus Life",
            owner_user_id=admin_user.id,
            status="ACTIVE",
        )
        db.add(project)
        db.flush()

        # Add project members
        for u in users_data:
            db.add(
                ProjectMember(
                    project_id=project.id,
                    user_id=user_records[u["role"]].id,
                    role=u["role"],
                )
            )
        db.flush()
        print("✓ Project and members created.")

        now = datetime.now(timezone.utc)

        # 3. Requirements (REQ-001 to REQ-010)
        reqs_def = [
            {
                "id": "REQ-001",
                "title": "Account Creation",
                "desc": "Students shall be able to create an account using their university email address.",
                "type": "FUNCTIONAL",
                "priority": "HIGH",
                "crit": 4,
                "ac": ["Must accept @university.edu addresses", "Must send email activation link"],
            },
            {
                "id": "REQ-002",
                "title": "Secure Login",
                "desc": "Students shall be able to log in securely with multi-factor authentication.",
                "type": "SECURITY",
                "priority": "HIGH",
                "crit": 5,
                "ac": ["Passwords must be hashed with Argon2id/Bcrypt", "MFA code prompt upon login"],
            },
            {
                "id": "REQ-003",
                "title": "Event Registration",
                "desc": "Students shall be able to register for an event.",
                "type": "FUNCTIONAL",
                "priority": "CRITICAL",
                "crit": 5,
                "ac": ["Student can click 'Register' on any active event", "Capacity check before confirming"],
            },
            {
                "id": "REQ-004",
                "title": "Registration Confirmation",
                "desc": "Students shall receive a registration confirmation email with an entry QR code.",
                "type": "FUNCTIONAL",
                "priority": "MEDIUM",
                "crit": 3,
                "ac": ["Email sent within 30 seconds of registration", "Attached QR code contains unique ticket token"],
            },
            {
                "id": "REQ-005",
                "title": "Participant Roster",
                "desc": "Organisers shall be able to view and search registered participants for their events.",
                "type": "FUNCTIONAL",
                "priority": "MEDIUM",
                "crit": 3,
                "ac": ["Filter by name, department, status", "Export roster to CSV"],
            },
            {
                "id": "REQ-006",
                "title": "Registration Cancellation",
                "desc": "Students shall be able to cancel a registration up to 2 hours before event start.",
                "type": "FUNCTIONAL",
                "priority": "MEDIUM",
                "crit": 3,
                "ac": ["Cancellation frees up seat for waitlist", "Confirmation email sent upon cancellation"],
            },
            {
                "id": "REQ-007",
                "title": "QR Entry Check-in",
                "desc": "Organisers shall be able to scan a student's QR code at event entry to record attendance.",
                "type": "FUNCTIONAL",
                "priority": "HIGH",
                "crit": 4,
                "ac": ["Scan responds under 1 second", "Prevents duplicate check-in with same code"],
            },
            {
                "id": "REQ-008",
                "title": "Prevent Duplicate Registrations",
                "desc": "The system shall prevent duplicate registrations for the same student on the same event.",
                "type": "FUNCTIONAL",
                "priority": "HIGH",
                "crit": 4,
                "ac": ["Unique database constraint on (student_id, event_id)", "UI displays error if already registered"],
            },
            {
                "id": "REQ-009",
                "title": "Attendance Audit Record",
                "desc": "The system shall retain an immutable, auditable event attendance record for safety and compliance.",
                "type": "REGULATORY",
                "priority": "HIGH",
                "crit": 4,
                "ac": ["Log entry timestamp, operator ID, and location", "Audit logs retained for 3 years"],
            },
            {
                "id": "REQ-010",
                "title": "Participant Data Access Restriction",
                "desc": "The system shall restrict participant PII data access strictly to authorised organiser roles.",
                "type": "SECURITY",
                "priority": "CRITICAL",
                "crit": 5,
                "ac": ["Role-based access check on participant APIs", "Redact student phone number from general view"],
            },
        ]

        req_node_map = {}
        for r in reqs_def:
            g_node = GraphNode(project_id=project.id, node_type="REQUIREMENT", display_id=r["id"])
            db.add(g_node)
            db.flush()
            req_node_map[r["id"]] = g_node.id

            req = Requirement(
                project_id=project.id,
                graph_node_id=g_node.id,
                display_id=r["id"],
                requirement_type=r["type"],
                priority=r["priority"],
                criticality=r["crit"],
                owner_user_id=analyst_user.id,
                lifecycle_status="APPROVED",
            )
            db.add(req)
            db.flush()

            ver = RequirementVersion(
                requirement_id=req.id,
                version_number=1,
                title=r["title"],
                description=r["desc"],
                rationale="Initial approved baseline version.",
                acceptance_criteria_json=r["ac"],
                status="APPROVED",
                created_by=analyst_user.id,
                approved_by=admin_user.id,
                approved_at=now,
            )
            db.add(ver)
            db.flush()

            req.current_version_id = ver.id
        print(f"✓ 10 Requirements created with Version 1 baseline.")

        # 4. Artifacts (24 artifacts)
        artifacts_def = [
            # Modules
            ("MOD-001", "MODULE_SERVICE", "Authentication Service", "Handles token issuance, password verification, and session control.", 5, dev_user.id, 24.0),
            ("MOD-002", "MODULE_SERVICE", "Registration Service", "Orchestrates event registration, quota checking, and seat allocation.", 5, dev_user.id, 32.0),
            ("MOD-003", "MODULE_SERVICE", "Event Management Service", "Manages event creation, capacity limits, schedules, and rosters.", 4, dev_user.id, 20.0),
            # APIs
            ("API-001", "API_ENDPOINT", "Login API", "POST /api/v1/auth/login", 5, dev_user.id, 8.0),
            ("API-002", "API_ENDPOINT", "Register Event API", "POST /api/v1/events/{id}/register", 5, dev_user.id, 12.0),
            ("API-003", "API_ENDPOINT", "Cancel Registration API", "POST /api/v1/registrations/{id}/cancel", 3, dev_user.id, 6.0),
            ("API-004", "API_ENDPOINT", "Participant List API", "GET /api/v1/events/{id}/participants", 4, dev_user.id, 8.0),
            ("API-005", "API_ENDPOINT", "QR Check-in API", "POST /api/v1/checkin/qr", 4, dev_user.id, 10.0),
            # DB Entities
            ("DB-001", "DATABASE_ENTITY", "Student Entity", "Table students (id, email, name, dept)", 4, dev_user.id, 6.0),
            ("DB-002", "DATABASE_ENTITY", "Event Entity", "Table events (id, title, capacity, start_time)", 4, dev_user.id, 6.0),
            ("DB-003", "DATABASE_ENTITY", "Registration Entity", "Table registrations (id, student_id, event_id, status, ticket_code)", 5, dev_user.id, 8.0),
            ("DB-004", "DATABASE_ENTITY", "Attendance Entity", "Table attendance_logs (id, event_id, student_id, scanned_at, operator_id)", 4, dev_user.id, 6.0),
            # UI Screens
            ("UI-001", "UI_SCREEN", "Login Screen", "Student and organiser login interface with MFA prompt.", 4, dev_user.id, 16.0),
            ("UI-002", "UI_SCREEN", "Event Listing Screen", "Browse upcoming events and check remaining capacity.", 3, dev_user.id, 16.0),
            ("UI-003", "UI_SCREEN", "Event Registration Screen", "Event details with registration trigger and confirmation modal.", 5, dev_user.id, 20.0),
            ("UI-004", "UI_SCREEN", "Registration Confirmation Screen", "Summary ticket screen displaying generated entry QR code.", 4, dev_user.id, 12.0),
            ("UI-005", "UI_SCREEN", "Organiser Dashboard", "Overview of active events, registrations, and check-in rate.", 3, dev_user.id, 18.0),
            ("UI-006", "UI_SCREEN", "QR Check-in Screen", "Mobile scanner view for event check-in staff.", 4, dev_user.id, 14.0),
            # Test Cases
            ("TEST-001", "TEST_CASE", "Login Test Suite", "Unit and integration tests for authentication and bad login lockout.", 5, qa_user.id, 12.0),
            ("TEST-002", "TEST_CASE", "Registration API Test", "Integration test verifying quota check and happy path registration.", 5, qa_user.id, 14.0),
            ("TEST-003", "TEST_CASE", "Duplicate Registration Test", "Verifies concurrent duplicate registration rejection.", 4, qa_user.id, 8.0),
            ("TEST-004", "TEST_CASE", "Cancellation Test", "Verifies waitlist advance and quota restore upon cancellation.", 3, qa_user.id, 8.0),
            ("TEST-005", "TEST_CASE", "QR Check-in Test", "Tests QR scanning, fast response, and second-scan prevention.", 4, qa_user.id, 10.0),
            ("TEST-006", "TEST_CASE", "Access Control Test", "Validates that non-organisers cannot access participant PII.", 5, qa_user.id, 10.0),
            # Documentation
            ("DOC-001", "DOCUMENTATION", "Student Registration Guide", "User guide explaining how to register and present QR tickets.", 2, analyst_user.id, 6.0),
            ("DOC-002", "DOCUMENTATION", "Organiser Guide", "Operations manual for managing events and operating scanners.", 3, analyst_user.id, 8.0),
        ]

        art_node_map = {}
        for a in artifacts_def:
            disp_id, art_type, title, desc, crit, owner_id, effort = a
            g_node = GraphNode(project_id=project.id, node_type="ARTIFACT", display_id=disp_id)
            db.add(g_node)
            db.flush()
            art_node_map[disp_id] = g_node.id

            art = Artifact(
                project_id=project.id,
                graph_node_id=g_node.id,
                display_id=disp_id,
                artifact_type=art_type,
                title=title,
                description=desc,
                criticality=crit,
                owner_user_id=owner_id,
                status="ACTIVE",
                estimated_effort_hours=effort,
                last_reviewed_at=now,
            )
            db.add(art)
        print(f"✓ 26 Engineering Artifacts created.")

        # 5. Directed Traceability Edges
        # Edges follow the convention: "if source changes, target may need review" (Source -> Target)
        edges_data = [
            # REQ-001 Account Creation
            ("REQ-001", "MOD-001", "IMPLEMENTED_BY", 1.0, "CONFIRMED"),
            ("MOD-001", "DB-001", "USES", 0.85, "CONFIRMED"),

            # REQ-002 Secure Login
            ("REQ-002", "MOD-001", "IMPLEMENTED_BY", 1.0, "CONFIRMED"),
            ("MOD-001", "API-001", "EXPOSES", 0.90, "CONFIRMED"),
            ("API-001", "UI-001", "CONSUMED_BY", 0.85, "CONFIRMED"),
            ("API-001", "TEST-001", "VERIFIED_BY", 0.95, "CONFIRMED"),

            # REQ-003 Event Registration (Central Demo Path!)
            ("REQ-003", "MOD-002", "IMPLEMENTED_BY", 1.0, "CONFIRMED"),
            ("MOD-002", "API-002", "EXPOSES", 0.90, "CONFIRMED"),
            ("MOD-002", "DB-003", "USES", 0.85, "CONFIRMED"),
            ("API-002", "UI-003", "CONSUMED_BY", 0.85, "CONFIRMED"),
            ("API-002", "TEST-002", "VERIFIED_BY", 0.95, "CONFIRMED"),
            ("UI-003", "UI-004", "DEPENDS_ON", 0.80, "CONFIRMED"),
            ("UI-003", "DOC-001", "DOCUMENTED_BY", 0.60, "CONFIRMED"),

            # REQ-004 Registration Confirmation
            ("REQ-004", "UI-004", "REALISED_AS", 0.95, "CONFIRMED"),
            ("REQ-004", "DOC-001", "DOCUMENTED_BY", 0.60, "CONFIRMED"),

            # REQ-005 Participant Roster
            ("REQ-005", "MOD-003", "IMPLEMENTED_BY", 1.0, "CONFIRMED"),
            ("MOD-003", "API-004", "EXPOSES", 0.90, "CONFIRMED"),
            ("API-004", "UI-005", "CONSUMED_BY", 0.85, "CONFIRMED"),

            # REQ-006 Cancellation
            ("REQ-006", "MOD-002", "IMPLEMENTED_BY", 1.0, "CONFIRMED"),
            ("MOD-002", "API-003", "EXPOSES", 0.90, "CONFIRMED"),
            ("API-003", "TEST-004", "VERIFIED_BY", 0.95, "CONFIRMED"),

            # REQ-007 QR Entry Check-in
            ("REQ-007", "API-005", "EXPOSES", 0.90, "CONFIRMED"),
            ("API-005", "UI-006", "CONSUMED_BY", 0.85, "CONFIRMED"),
            ("API-005", "DB-004", "USES", 0.85, "CONFIRMED"),
            ("API-005", "TEST-005", "VERIFIED_BY", 0.95, "CONFIRMED"),
            ("UI-006", "DOC-002", "DOCUMENTED_BY", 0.60, "CONFIRMED"),

            # REQ-008 Duplicate Registration Prevention
            ("REQ-008", "DB-003", "CONSTRAINED_BY", 0.90, "CONFIRMED"),
            ("DB-003", "TEST-003", "VERIFIED_BY", 0.95, "CONFIRMED"),

            # REQ-009 Attendance Audit Record
            ("REQ-009", "DB-004", "REALISED_AS", 0.95, "CONFIRMED"),
            # Notice: DB-004 has no linked TEST case deliberately (creates a traceability health warning!)

            # REQ-010 Participant Data Restriction
            ("REQ-010", "API-004", "CONSTRAINED_BY", 0.90, "CONFIRMED"),
            ("API-004", "TEST-006", "VERIFIED_BY", 0.95, "CONFIRMED"),
        ]

        node_lookup = {**req_node_map, **art_node_map}
        edges_count = 0
        for src, tgt, rel, strength, status in edges_data:
            if src in node_lookup and tgt in node_lookup:
                edge = TraceabilityEdge(
                    project_id=project.id,
                    source_node_id=node_lookup[src],
                    target_node_id=node_lookup[tgt],
                    relation_type=rel,
                    relationship_strength=strength,
                    confirmation_status=status,
                    propagation_enabled=True,
                    is_active=True,
                    created_by=analyst_user.id,
                )
                db.add(edge)
                edges_count += 1

        db.commit()
        print(f"✓ {edges_count} directed traceability edges established.")
        print("\n🎉 Demo dataset seeded successfully!")
        print(f"Project ID: {project.id}")
        print("Default users:")
        print("  - Alex ProjectManager (ADMIN)    : admin@reqripple.local / password123")
        print("  - Alice Analyst       (ANALYST)  : analyst@reqripple.local / password123")
        print("  - Bob Developer       (DEVELOPER): dev@reqripple.local / password123")
        print("  - Carol Tester        (TESTER)   : qa@reqripple.local / password123")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
