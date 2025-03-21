# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.db.session import engine
from app.utils.db_utils import verify_and_update_schema, ensure_super_admin
from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.core.exceptions import APIException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Database setup and verification
    logger.info("Starting application")
    await verify_and_update_schema()
    await ensure_super_admin()
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Shutting down application")
    await engine.dispose()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="User management API with role-based access control",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production if needed
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for custom API exceptions
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Include API router with version prefix
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
async def health_check():
    return {"status": "ok", "version": settings.VERSION}