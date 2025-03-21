from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.core.roles import UserRole
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)

def verify_and_update_schema(db: Session) -> None:
    """
    Verify and update database schema if needed.
    This function is called on application startup.
    
    Args:
        db: Database session
    """
    try:
        # Log schema verification
        logger.info("Verifying database schema...")
        
        # You can add schema verification logic here if needed
        # For example, checking if all required tables exist
        
        logger.info("Database schema verification completed")
    except SQLAlchemyError as e:
        logger.error(f"Database schema verification error: {str(e)}")
        raise

def ensure_super_admin(db: Session) -> None:
    """
    Ensure a super admin user exists in the database.
    If no super admin exists, create one with default credentials.
    
    Args:
        db: Database session
    """
    try:
        # Check if super admin exists
        super_admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        
        if not super_admin:
            logger.info("No super admin found. Creating default super admin user...")
            
            # Create default super admin
            default_admin = User(
                email="admin@example.com",
                username="admin",
                password_hash=get_password_hash("adminpassword"),  # Change this in production
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            
            db.add(default_admin)
            db.commit()
            
            logger.info("Default super admin created successfully")
        else:
            logger.info("Super admin user already exists")
    except SQLAlchemyError as e:
        logger.error(f"Error ensuring super admin: {str(e)}")
        db.rollback()
        raise