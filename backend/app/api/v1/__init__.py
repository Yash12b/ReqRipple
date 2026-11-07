from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.requirements import router as requirements_router
from app.api.v1.artifacts import router as artifacts_router
from app.api.v1.traceability import router as traceability_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(requirements_router)
api_router.include_router(artifacts_router)
api_router.include_router(traceability_router)
