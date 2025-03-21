# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime

from app.db.session import get_db
from app.services.auth_service import authenticate_user, create_user_token
from app.schemas.token import Token, TokenPayload
from app.services.user_service import update_user_last_login

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await update_user_last_login(db, user.id, datetime.utcnow())
    
    # Create access token
    access_token = create_user_token(data={"sub": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}