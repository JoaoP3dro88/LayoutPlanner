from fastapi import APIRouter

from . import layouts

api_router = APIRouter()
api_router.include_router(layouts.router, prefix="/layouts", tags=["layouts"])
