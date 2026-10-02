from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    DatasetNotFoundError,
    DatasetParseError,
    DatasetTooLargeError,
    ProjectNotFoundError,
    SynDataXError,
    UnsupportedFileTypeError,
)
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown events."""
    logger.info("SynDataX backend application startup complete.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="SynDataX - Scientific Data Intelligence Platform Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(ProjectNotFoundError)
def project_not_found_handler(request: Request, exc: ProjectNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "ProjectNotFoundError", "detail": exc.message},
    )


@app.exception_handler(DatasetNotFoundError)
def dataset_not_found_handler(request: Request, exc: DatasetNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "DatasetNotFoundError", "detail": exc.message},
    )


@app.exception_handler(UnsupportedFileTypeError)
def unsupported_file_type_handler(request: Request, exc: UnsupportedFileTypeError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "UnsupportedFileTypeError", "detail": exc.message},
    )


@app.exception_handler(DatasetTooLargeError)
def dataset_too_large_handler(request: Request, exc: DatasetTooLargeError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"error": "DatasetTooLargeError", "detail": exc.message},
    )


@app.exception_handler(DatasetParseError)
def dataset_parse_handler(request: Request, exc: DatasetParseError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "DatasetParseError", "detail": exc.message},
    )


@app.exception_handler(SynDataXError)
def syndatax_error_handler(request: Request, exc: SynDataXError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.__class__.__name__, "detail": exc.message},
    )


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", summary="Root Index")
def root() -> dict[str, str]:
    """Root status endpoint."""
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
