# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users

router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, tags=["authentication"])
router.include_router(users.router, prefix="/users", tags=["users"])

# Add more routers as your API grows