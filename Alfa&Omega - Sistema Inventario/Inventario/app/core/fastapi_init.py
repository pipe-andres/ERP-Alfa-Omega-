"""FastAPI application factory."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.v1 import purchases, sales, transfers


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        debug=settings.debug,
        description="API for Alfa & Omega Inventory Management System"
    )
    
    # ==================== Middleware ====================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ==================== Event Handlers ====================
    @app.on_event("startup")
    async def startup_event():
        """Run on application startup."""
        logger.info("Starting Alfa & Omega Inventory API...")
        logger.info(f"Database engine: {settings.db_engine}")
        logger.info(f"Cost policy: {settings.inventory_cost_policy}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Run on application shutdown."""
        logger.info("Shutting down Alfa & Omega Inventory API...")
    
    # ==================== Global Exception Handler ====================
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions globally."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred",
                "status_code": 500
            }
        )
    
    # ==================== Health Check ====================
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "Alfa & Omega Inventory API",
            "version": settings.app_version
        }
    
    # ==================== API Routes ====================
    api_v1 = FastAPI(title="API v1")
    
    # Include routers
    api_v1.include_router(purchases.router)
    api_v1.include_router(sales.router)
    api_v1.include_router(transfers.router)
    
    # Mount v1 API
    app.include_router(api_v1.router, prefix="/api/v1")
    
    # ==================== Root ====================
    @app.get("/", tags=["root"])
    async def root() -> dict:
        """API documentation root."""
        return {
            "name": settings.app_title,
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        }
    
    return app
