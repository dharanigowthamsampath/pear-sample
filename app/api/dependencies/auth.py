# app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import jwt
from pydantic import ValidationError
from jwt.exceptions import PyJWTError

from app.core.security import ALGORITHM
from app.config import settings
from app.db.session import get_db
from app.schemas.token import TokenPayload
from app.services.user_service import get_user_by_id
from app.schemas.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Validate token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        
        # Check token expiration
        if token_data.exp is None:
            raise credentials_exception
    except (PyJWTError, ValidationError):
        raise credentials_exception
    
    user = await get_user_by_id(db, token_data.sub)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Check if current user is active"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Check if current user is a superadmin"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions"
        )
    return current_user