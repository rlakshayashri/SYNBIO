from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthCheckResponse(BaseModel):
    """Schema for API health status check."""

    status: str
    service: str
    version: str = "0.1.0"


@router.get("/health", response_model=HealthCheckResponse, summary="System Health Check")
def health_check() -> HealthCheckResponse:
    """Returns basic health status of the SynDataX backend application."""
    return HealthCheckResponse(
        status="ok",
        service="SynDataX backend",
        version="0.1.0",
    )
