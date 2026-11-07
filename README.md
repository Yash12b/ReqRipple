# ReqRipple: Software Requirement Change Impact Analyser

> Understand the consequences of every software requirement change.

ReqRipple is a centralized, traceability-driven change-impact analysis and requirements engineering management platform. It maintains structured, versioned requirements, connects them across downstream engineering artifacts (stories, APIs, database entities, UI views, test cases, and documentation), visualises the directed traceability graph, simulates change ripple effects, and guides remediation to prevent project debt.

## Architecture & Technology Stack

- **Backend**: Python 3.11+ / FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, SQLite (Local MVP)
- **Frontend**: React 18+, TypeScript, Vite, Tailwind CSS, TanStack Query, React Flow
- **Style**: Modular Monolith with clean boundary between pure graph traversal, application services, and web APIs.

## Project Structure

```
ReqRipple/
├── docs/                # Architecture, SRS, API contracts, data models
├── backend/             # FastAPI modular monolith application
│   ├── app/
│   │   ├── api/v1/      # REST API route handlers
│   │   ├── core/        # Security, config, permissions
│   │   ├── db/          # Database connection and session management
│   │   ├── domain/      # Pure graph traversal, scoring, workflows
│   │   ├── models/      # SQLAlchemy ORM models
│   │   ├── schemas/     # Pydantic request/response schemas
│   │   └── services/    # Business logic orchestration
│   ├── alembic/         # Database migrations
│   └── tests/           # Unit and integration tests
├── frontend/            # React + TypeScript + Vite UI
└── scripts/             # Demo seeding and utility scripts
```

## Quick Start (Backend)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python ../scripts/seed_demo_data.py
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at `http://127.0.0.1:8000/docs`.

## License
MIT
