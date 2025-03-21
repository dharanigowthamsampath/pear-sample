from fastapi import HTTPException, status


class APIException(HTTPException):
    """Base exception for API-related errors with status code and detail message."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class NotFoundError(DatabaseError):
    """Exception raised when a requested resource is not found."""
    pass


class UserExistsError(DatabaseError):
    """Exception raised when attempting to create a user that already exists."""
    pass


# HTTP Exceptions
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

permission_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not enough permissions",
)

user_exists_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Username or email already registered",
)

not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found",
)