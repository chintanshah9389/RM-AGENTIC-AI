from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.response import fail
from app.db.base import Base
from app.db.session import engine

# Ensure models are registered
import app.models  # noqa: F401

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "POC Environment - Synthetic Data. Agentic AI Banking CRM for Relationship Managers. "
        "Demonstration only. Scores and offers are not real lending decisions."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # Ensure DB file directory exists for SQLite
    if settings.database_url.startswith("sqlite:///./"):
        db_name = settings.database_url.replace("sqlite:///./", "")
        Path(db_name).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # noqa: ARG001
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(
            code="HTTP_ERROR",
            message=str(exc.detail),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  # noqa: ARG001
    return JSONResponse(
        status_code=422,
        content=fail(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details=exc.errors(),
        ),
    )


app.include_router(api_router)


@app.get("/")
def root():
    return {
        "success": True,
        "data": {
            "app": settings.app_name,
            "docs": "/docs",
            "health": "/api/v1/health",
            "notice": "POC Environment - Synthetic Data",
        },
        "error": None,
    }
