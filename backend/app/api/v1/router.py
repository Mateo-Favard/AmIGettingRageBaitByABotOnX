from fastapi import APIRouter

from app.api.v1.endpoints import account, analyze, health

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(analyze.router, tags=["analyze"])
api_v1_router.include_router(account.router, tags=["account"])
