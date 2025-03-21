from sqlalchemy.ext.declarative import declarative_base

# Create the base class
Base = declarative_base()

# Import models at the end to avoid circular imports
from app.models.user import UserModel  # noqa
# Import other models as needed