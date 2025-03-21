# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.user import UserModel
from app.schemas.user import UserCreate, UserUpdate, User
from app.core.security import get_password_hash, verify_password
from app.core.roles import UserRole, check_role_permissions

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get a user by ID"""
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalars().first()
    if user:
        return User.model_validate(user)
    return None

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserModel]:
    """Get a user by username"""
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    """Get a user by email"""
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalars().first()

async def get_all_users(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    role: Optional[UserRole] = None
) -> List[User]:
    """Get all users with pagination and optional role filter"""
    query = select(UserModel).offset(skip).limit(limit)
    
    if role:
        query = query.where(UserModel.role == role)
    
    result = await db.execute(query)
    users = result.scalars().all()
    return [User.model_validate(user) for user in users]

async def create_new_user(
    db: AsyncSession, 
    user_data: UserCreate, 
    current_user: User
) -> User:
    """Create a new user"""
    # Check if current user can create a user with given role
    if not check_role_permissions(current_user.role, user_data.role):
        raise ValueError(f"User with role {current_user.role} cannot create user with role {user_data.role}")
    
    # Check if username or email already exists
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise ValueError("Username already registered")
    
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise ValueError("Email already registered")
    
    # Create user model
    hashed_password = get_password_hash(user_data.password)
    db_user = UserModel(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return User.model_validate(db_user)

async def update_existing_user(
    db: AsyncSession, 
    user_id: str, 
    user_data: UserUpdate
) -> Optional[User]:
    """Update an existing user"""
    db_user = await db.get(UserModel, user_id)
    if not db_user:
        return None
    
    # Update user fields if provided
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Check if username or email is being changed and if it already exists
    if "username" in update_data and update_data["username"] != db_user.username:
        existing_user = await get_user_by_username(db, update_data["username"])
        if existing_user:
            raise ValueError("Username already registered")
    
    if "email" in update_data and update_data["email"] != db_user.email:
        existing_email = await get_user_by_email(db, update_data["email"])
        if existing_email:
            raise ValueError("Email already registered")
    
    # Update user
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    await db.commit()
    await db.refresh(db_user)
    
    return User.model_validate(db_user)

async def delete_user(db: AsyncSession, user_id: str) -> bool:
    """Delete a user"""
    db_user = await db.get(UserModel, user_id)
    if not db_user:
        return False
    
    await db.delete(db_user)
    await db.commit()
    
    return True

async def change_user_password(
    db: AsyncSession, 
    user_id: str, 
    current_password: str, 
    new_password: str
) -> bool:
    """Change a user's password"""
    db_user = await db.get(UserModel, user_id)
    if not db_user:
        return False
    
    # Verify current password
    if not verify_password(current_password, db_user.password):
        raise ValueError("Current password is incorrect")
    
    # Update password
    db_user.password = get_password_hash(new_password)
    await db.commit()
    
    return True

async def update_user_last_login(
    db: AsyncSession, 
    user_id: str, 
    login_time: datetime
) -> bool:
    """Update the last login time for a user"""
    db_user = await db.get(UserModel, user_id)
    if not db_user:
        return False
    
    db_user.last_login = login_time
    await db.commit()
    
    return True