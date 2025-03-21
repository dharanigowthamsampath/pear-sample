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
