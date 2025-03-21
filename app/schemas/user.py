# app/schemas/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.core.roles import UserRole

# Base user schema with common fields
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    
    class Config:
        from_attributes = True

# For user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

# For updating user information
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    disabled: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

# Password change schema
class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

# Response model (returned to clients)
class User(UserBase):
    id: str
    role: UserRole
    disabled: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    last_login: Optional[datetime] = None

# Full user details (for admin use)
class UserAdminView(User):
    pass  # Add any admin-only fields here