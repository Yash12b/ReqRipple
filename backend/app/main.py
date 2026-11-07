from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1 import api_router
from app.core.errors import (
    EntityNotFoundError,
    EntityConflictError,
    PermissionDeniedError,
    AuthenticationError,
    ValidationError,
)

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    version="1.0.0",
    description="Software Requirement Change Impact Analyser - Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "environment": settings.APP_ENV}


# Global Exception Handlers
@app.exception_handler(EntityNotFoundError)
def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Not Found", "detail": exc.detail},
    )


@app.exception_handler(EntityConflictError)
def entity_conflict_handler(request: Request, exc: EntityConflictError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Conflict", "detail": exc.detail},
    )


@app.exception_handler(PermissionDeniedError)
def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Forbidden", "detail": exc.detail},
    )


@app.exception_handler(AuthenticationError)
def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Unauthorized", "detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Unprocessable Entity", "detail": exc.detail},
    )
