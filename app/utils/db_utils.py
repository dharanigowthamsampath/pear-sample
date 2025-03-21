from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.core.roles import UserRole
from app.core.security import get_password_hash
import logging
import uuid
from app.db.session import async_session_maker

logger = logging.getLogger(__name__)

async def verify_and_update_schema() -> None:
    """
    Verify and update database schema if needed.
    This function is called on application startup.
    """
    logger.info("Verifying database schema...")
    
    async with async_session_maker() as session:
        try:
            # You can add schema verification logic here if needed
            # For example, checking if all required tables exist
            
            # Simple test query to verify database connection
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            logger.info("Database schema verification completed")
        except SQLAlchemyError as e:
            logger.error(f"Database schema verification error: {str(e)}")
            raise

async def ensure_super_admin() -> None:
    """
    Ensure a super admin user exists in the database.
    If no super admin exists, create one with default credentials.
    """
    logger.info("Checking for super admin user...")
    
    async with async_session_maker() as session:
        try:
            # Check if super admin exists
            result = await session.execute(
                text("SELECT * FROM users WHERE role = :role"),
                {"role": UserRole.SUPER_ADMIN.value}
            )
            super_admin = result.fetchone()
            
            if not super_admin:
                logger.info("No super admin found. Creating default super admin user...")
                
                # Create default super admin
                user_id = str(uuid.uuid4())
                hashed_password = get_password_hash("adminpassword")  # Change this in production
                
                await session.execute(
                    text("""
                        INSERT INTO users (id, username, email, password, role, disabled)
                        VALUES (:id, :username, :email, :password, :role, :disabled)
                    """),
                    {
                        "id": user_id,
                        "username": "admin",
                        "email": "admin@example.com",
                        "password": hashed_password,
                        "role": UserRole.SUPER_ADMIN.value,
                        "disabled": False
                    }
                )
                
                await session.commit()
                logger.info("Default super admin created successfully")
            else:
                logger.info("Super admin user already exists")
        except SQLAlchemyError as e:
            logger.error(f"Error ensuring super admin: {str(e)}")
            await session.rollback()
            raise