from fastapi import APIRouter

from app.api.v1 import auth, clients, documents, engagements, filings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(clients.router)
api_router.include_router(engagements.router)
api_router.include_router(documents.router)
api_router.include_router(filings.router)

__all__ = ["api_router"]
