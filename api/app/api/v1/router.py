"""API v1 router - aggregates all API endpoints"""

from fastapi import APIRouter
from app.api.v1 import settings, diet, meal, recipe, admin

# Create the main API router
api_router = APIRouter()

# Include all feature routers
api_router.include_router(settings.router)
api_router.include_router(diet.router)
api_router.include_router(meal.router)
api_router.include_router(recipe.router)
api_router.include_router(admin.router)