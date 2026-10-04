from fastapi import APIRouter

from app.api.v1 import datasets, experiments, health, projects

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
