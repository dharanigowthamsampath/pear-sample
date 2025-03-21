import uuid
from sqlalchemy import Column, String, Boolean, Enum as SQLAlchemyEnum, DateTime
from sqlalchemy.sql import func

# Import Base directly from session instead of base.py
from app.db.session import Base
from app.core.roles import UserRole

class User(Base):  # Changed class name to match what's expected in db_utils.py
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)  # Changed from password to password_hash to match db_utils
    role = Column(SQLAlchemyEnum(UserRole, name="userrole"))
    is_active = Column(Boolean, default=True)  # Changed from disabled to is_active
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional fields for future expansion
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

# Create an alias for backward compatibility if needed
UserModel = User