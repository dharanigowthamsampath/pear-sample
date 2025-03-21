# PROJECT STRUCTURE

    project_root/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                # Entry point with FastAPI instance
    │   ├── config.py              # Configuration settings
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── base.py            # Base DB setup
    │   │   ├── session.py         # Session management
    │   │   └── migrations/        # For Alembic migrations
    │   │       └── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── user.py            # User model
    │   │   ├── permission.py      # Permission model (future)
    │   │   └── organization.py    # Organization model (future)
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── dependencies/
    │   │   │   ├── __init__.py
    │   │   │   ├── auth.py        # Auth dependencies
    │   │   │   └── pagination.py  # Pagination dependencies
    │   │   └── v1/                # API version 1
    │   │       ├── __init__.py
    │   │       ├── router.py      # Main router for v1
    │   │       └── endpoints/
    │   │           ├── __init__.py
    │   │           ├── auth.py
    │   │           └── users.py
    │   ├── schemas/
    │   │   ├── __init__.py
    │   │   ├── base.py            # Base schemas with common fields
    │   │   ├── token.py           # Token schemas
    │   │   └── user.py            # User schemas
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── security.py        # JWT/security functions
    │   │   ├── roles.py           # Role definitions
    │   │   └── exceptions.py      # Custom exceptions
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── user_service.py    # User-related business logic
    │   │   └── auth_service.py    # Auth-related business logic
    │   └── utils/
    │       ├── __init__.py
    │       ├── db_utils.py        # DB utilities
    │       └── logging.py         # Logging configuration
    ├── alembic.ini                # Alembic configuration
    ├── .env                       # Environment variables
    ├── .env.example               # Example environment variables
    ├── docker-compose.yml         # Docker setup
    ├── Dockerfile                 # Docker image definition
    ├── requirements.txt           # Dependencies
    └── README.md                  # Documentation

# User Management API

A FastAPI application for user management with role-based access control.

## Features

- User authentication with JWT
- Role-based access control
- PostgreSQL database with async support
- Docker and Docker Compose setup

## Getting Started with Docker

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

2. Start the application with Docker Compose:

```bash
docker-compose up -d
```

This will start both the FastAPI application and PostgreSQL database.

3. Access the application:

- API: http://localhost:8000
- Swagger UI Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc

### Development Mode

The default Docker Compose setup includes volume mapping and reload support, allowing for real-time code changes.

### Environment Variables

You can customize the application by setting environment variables in the `docker-compose.yml` file:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT token generation
- `DEBUG`: Enable/disable debug mode

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Schema

The application uses PostgreSQL with SQLAlchemy ORM. The database schema includes:

- Users table with role-based access control

## Default Super Admin

A default super admin user is created on first startup:

- Username: admin
- Password: adminpassword

**Important:** Change the default admin password in production!

## License

[Your License]
