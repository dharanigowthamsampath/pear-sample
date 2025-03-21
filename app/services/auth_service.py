# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.security import verify_password
from app.config import settings
from app.schemas.user import User
from app.services.user_service import get_user_by_username

async def authenticate_user(
    db: AsyncSession, 
    username: str, 
    password: str
) -> Optional[User]:
    """Authenticate a user by username and password"""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    
    return User.model_validate(user)

def create_user_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT token for a user"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt