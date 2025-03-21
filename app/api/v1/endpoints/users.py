# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated, Optional

from app.db.session import get_db
from app.api.dependencies.auth import get_current_user, get_current_active_superuser
from app.schemas.user import User, UserCreate, UserUpdate, UserPasswordChange
from app.services.user_service import (
    create_new_user, get_user_by_id, get_all_users, 
    update_existing_user, delete_user, change_user_password
)
from app.core.roles import UserRole

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new user (requires appropriate role)"""
    return await create_new_user(db, user_data, current_user)

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update own user information (limited fields)"""
    # Prevent users from changing their own role
    if user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )
    
    return await update_existing_user(db, current_user.id, user_data)

@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change own password"""
    await change_user_password(
        db, current_user.id, 
        password_data.current_password, 
        password_data.new_password
    )
    return {"status": "password changed"}

@router.get("/", response_model=List[User])
async def read_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[UserRole] = None
):
    """Get all users (admin/manager only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view all users"
        )
    
    return await get_all_users(db, skip, limit, role)

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get user by ID (admin/manager or self)"""
    # Allow users to view their own data or admins/managers to view any user
    if current_user.id != user_id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update user by ID (admin/manager or self with limitations)"""
    # Check if user exists
    existing_user = await get_user_by_id(db, user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Self-update (with limitations) or admin update
    if current_user.id == user_id:
        # Prevent users from changing their own role
        if user_data.role is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role"
            )
    elif current_user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await update_existing_user(db, user_id, user_data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete user (super admin only)"""
    # Prevent deletion of own account
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot delete your own account"
        )
    
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"status": "user deleted"}