from fastapi import APIRouter

from app.api.v1 import auth, campaigns, dashboard, system

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(campaigns.router)
api_router.include_router(system.router)
