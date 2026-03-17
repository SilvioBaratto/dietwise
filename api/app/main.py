"""Modern FastAPI application factory for API Diet"""

import os
import secrets
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text

from app.config import settings
from app.database import database_manager, init_db, close_db
from app.auth.supabase_auth import initialize_supabase, close_supabase
from app.exceptions import setup_exception_handlers
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limiting import RateLimitingMiddleware
from app.api.v1.router import api_router

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.log_format == 'text' 
           else '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# FastAPI Basic Auth for documentation
security = HTTPBasic()


def get_current_username(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Validate Swagger UI credentials"""
    if not settings.swagger_user or not settings.swagger_pass:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Swagger authentication not configured",
        )
    
    if not (
        secrets.compare_digest(credentials.username, settings.swagger_user)
        and secrets.compare_digest(credentials.password, settings.swagger_pass)
    ):
        logger.warning(f"Failed Swagger authentication attempt: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    Optimized for VS Code debugger compatibility.
    """
    # Startup
    logger.info(f"Starting {settings.project_name} API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    try:
        # In development/debug mode, use non-blocking startup for VS Code compatibility
        if settings.is_development:
            logger.info("Development mode: Using non-blocking startup sequence")
            
            # Initialize database (non-blocking)
            try:
                init_db()
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.warning(f"Database initialization skipped in development: {e}")
            
            # Initialize Supabase (non-blocking)
            try:
                import asyncio
                await asyncio.wait_for(initialize_supabase(), timeout=5.0)
                logger.info("Supabase authentication initialized successfully")
            except Exception as e:
                logger.warning(f"Supabase initialization skipped in development: {e}")
            
            # Skip health check in development to prevent debugger hanging
            logger.info("Skipping database health check in development mode")
        
        else:
            # Production startup with full checks
            logger.info("Production mode: Using full startup sequence")
            
            # Initialize database with timeout
            import asyncio
            init_db()
            logger.info("Database initialized successfully")
            
            # Initialize Supabase authentication
            await asyncio.wait_for(initialize_supabase(), timeout=60.0)
            logger.info("Supabase authentication initialized successfully")
            
            # Test database connection
            try:
                health_check_passed = database_manager.health_check()
                if health_check_passed:
                    logger.info("Database health check passed")
                else:
                    logger.warning("Database health check failed but continuing startup")
            except Exception as e:
                logger.warning(f"Database health check failed but continuing startup: {e}")
        
        logger.info(f"{settings.project_name} API startup complete")
        yield
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        if settings.is_development:
            logger.warning("Continuing startup in development mode despite errors")
            yield
        else:
            raise
    
    # Shutdown
    logger.info(f"Shutting down {settings.project_name} API...")
    
    try:
        await close_supabase()
        close_db()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI application with correct OpenAPI configuration
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        description="Modern API",
        docs_url=None,  # Disable default docs - we'll set up custom ones
        redoc_url=None,  # Disable default redoc - we'll set up custom ones
        openapi_url="/openapi.json" if settings.is_development else None,  # Keep OpenAPI JSON accessible in dev
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Add middleware stack (order matters - reverse order of execution)
    
    # 1. CORS middleware (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "X-Requested-With",
            "X-Client-Info",
            "X-Dev-User"
        ],
        expose_headers=["X-Total-Count", "X-Rate-Limit-Remaining"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    # 2. Rate limiting middleware (enabled in production)
    if settings.is_production_like:
        app.add_middleware(
            RateLimitingMiddleware,
            requests=settings.rate_limit_requests,
            window=settings.rate_limit_window
        )
    
    # 3. Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 4. Request logging middleware (innermost)
    if settings.debug or settings.log_level.upper() in ["DEBUG", "INFO"]:
        app.add_middleware(LoggingMiddleware)
    
    # Add API routes
    app.include_router(api_router, prefix=settings.api_v1_str)
    
    # Add health check and monitoring endpoints
    setup_health_endpoints(app)
    setup_monitoring_endpoints(app)
    
    # Setup documentation endpoints based on environment
    setup_documentation_endpoints(app)
    
    return app


def setup_health_endpoints(app: FastAPI) -> None:
    """Setup health check and monitoring endpoints"""
    
    @app.get("/")
    async def read_root() -> Dict[str, Any]:
        """Root endpoint with API information"""
        return {
            "message": f"Welcome to the {settings.project_name}!",
            "version": settings.version,
            "status": "operational",
            "environment": settings.environment,
            "api_version": "v1",
            "docs_url": "/docs" if settings.debug else None,
            "redoc_url": "/redoc" if settings.debug else None
        }
    
    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        """Simple health check endpoint - just return OK"""
        return {"status": "ok"}
    
    @app.get("/health/deep")
    async def deep_health_check() -> Dict[str, Any]:
        """Comprehensive health check for production monitoring"""
        try:
            import psutil
            
            checks = {}
            all_healthy = True
            
            # Database check with timeout protection
            try:
                db_healthy = database_manager.health_check()
                checks["database"] = {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "connection_mode": "sync_psycopg2",
                    "timeout_protected": False
                }
                if not db_healthy:
                    all_healthy = False
            except Exception as e:
                checks["database"] = {"status": "unhealthy", "error": str(e)}
                all_healthy = False
            
            # Memory check
            try:
                memory = psutil.virtual_memory()
                memory_status = "healthy"
                if memory.percent > 90:
                    memory_status = "critical"
                    all_healthy = False
                elif memory.percent > 80:
                    memory_status = "warning"
                
                checks["memory"] = {
                    "status": memory_status,
                    "usage_percent": memory.percent,
                    "available_mb": round(memory.available / 1024 / 1024, 2)
                }
            except Exception as e:
                checks["memory"] = {"status": "unhealthy", "error": str(e)}
                all_healthy = False
            
            # Disk check
            try:
                disk = psutil.disk_usage('/')
                disk_status = "healthy"
                if disk.percent > 90:
                    disk_status = "critical"
                    all_healthy = False
                elif disk.percent > 80:
                    disk_status = "warning"
                
                checks["disk"] = {
                    "status": disk_status,
                    "usage_percent": disk.percent,
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
                }
            except Exception as e:
                checks["disk"] = {"status": "unhealthy", "error": str(e)}
                all_healthy = False
            
            # Fly.io specific system information
            fly_info = {
                "region": os.getenv("FLY_REGION", "unknown"),
                "app_name": os.getenv("FLY_APP_NAME", "api-diet"),
                "instance_id": os.getenv("FLY_ALLOC_ID", "unknown"),
                "machine_id": os.getenv("FLY_MACHINE_ID", "unknown"),
                "public_ip": os.getenv("FLY_PUBLIC_IP", "unknown"),
                "private_ip": os.getenv("FLY_PRIVATE_IP", "unknown")
            }
            
            response_data = {
                "status": "healthy" if all_healthy else "unhealthy",
                "timestamp": time.time(),
                "version": settings.version,
                "environment": settings.environment,
                "checks": checks,
                "system": fly_info,
                "performance": {
                    "process_count": len(psutil.pids()),
                    "boot_time": psutil.boot_time()
                }
            }
            
            status_code = 200 if all_healthy else 503
            return JSONResponse(content=response_data, status_code=status_code)
            
        except Exception as e:
            logger.error(f"Deep health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "timestamp": time.time(),
                    "error": str(e)
                }
            )
    


def setup_documentation_endpoints(app: FastAPI) -> None:
    """Setup documentation endpoints based on environment and configuration"""
    
    if settings.is_development:
        # Development mode: unprotected docs for easy access during testing
        logger.info("Setting up unprotected documentation endpoints for development")
        
        @app.get("/docs", include_in_schema=False)
        def swagger_ui_dev():
            """Development Swagger UI - unprotected for debugging"""
            logger.info(f"🔍 Swagger UI requested - OpenAPI URL: {app.openapi_url}")
            return get_swagger_ui_html(
                openapi_url="/openapi.json",  # Force explicit URL for debugging
                title=f"{app.title} – Development Docs",
                swagger_js_url="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js",
                swagger_css_url="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css"
            )
        
        @app.get("/redoc", include_in_schema=False)
        def redoc_ui_dev():
            """Development ReDoc UI - unprotected for debugging"""
            logger.info(f"🔍 ReDoc UI requested - OpenAPI URL: {app.openapi_url}")
            return get_redoc_html(
                openapi_url="/openapi.json", 
                title=f"{app.title} – Development ReDoc",
                redoc_js_url="https://unpkg.com/redoc@2.1.0/bundles/redoc.standalone.js"
            )
        
        @app.get("/docs-debug", include_in_schema=False)
        def docs_debug():
            """Debug endpoint to check documentation configuration"""
            return {
                "message": "Docs debug endpoint working",
                "app_title": app.title,
                "openapi_url": app.openapi_url,
                "debug": settings.debug,
                "is_development": settings.is_development,
                "environment": settings.environment
            }
    
    elif settings.swagger_user and settings.swagger_pass:
        # Production mode with authentication
        logger.info("Setting up protected documentation endpoints for production")
        
        @app.get("/docs", include_in_schema=False)
        def swagger_ui_protected(username: str = Depends(get_current_username)):
            """Protected Swagger UI for production"""
            return get_swagger_ui_html(
                openapi_url="/openapi.json", 
                title=f"{app.title} – Swagger UI",
                swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
                swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
            )
        
        @app.get("/redoc", include_in_schema=False)
        def redoc_ui_protected(username: str = Depends(get_current_username)):
            """Protected ReDoc UI for production"""
            return get_redoc_html(
                openapi_url="/openapi.json", 
                title=f"{app.title} – ReDoc",
                redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"
            )
    
    else:
        logger.info("Documentation endpoints disabled - no authentication configured")
    
    # Always provide OpenAPI JSON if development or authenticated production
    if settings.is_development or (settings.swagger_user and settings.swagger_pass):
        @app.get("/openapi.json", include_in_schema=False)
        def get_openapi_json():
            """OpenAPI JSON schema"""
            return get_openapi(title=app.title, version=app.version, routes=app.routes)


def setup_monitoring_endpoints(app: FastAPI) -> None:
    """Setup monitoring and metrics endpoints for Fly.io"""
    
    @app.get("/metrics")
    async def prometheus_metrics():
        """Prometheus metrics endpoint for Fly.io monitoring"""
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        except ImportError:
            # Fallback if prometheus_client is not available
            return JSONResponse(
                content={
                    "error": "Prometheus client not installed",
                    "message": "Install prometheus-client package for metrics"
                },
                status_code=503
            )
    
    @app.get("/fly/system")
    async def fly_system_info() -> Dict[str, Any]:
        """Fly.io specific system information endpoint"""
        import psutil
        
        try:
            # Get system information
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                "timestamp": time.time(),
                "fly": {
                    "region": os.getenv("FLY_REGION", "unknown"),
                    "app_name": os.getenv("FLY_APP_NAME", "api-diet"),
                    "instance_id": os.getenv("FLY_ALLOC_ID", "unknown"),
                    "machine_id": os.getenv("FLY_MACHINE_ID", "unknown"),
                    "public_ip": os.getenv("FLY_PUBLIC_IP", "unknown"),
                    "private_ip": os.getenv("FLY_PRIVATE_IP", "unknown")
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total_mb": round(memory.total / 1024 / 1024, 2),
                        "available_mb": round(memory.available / 1024 / 1024, 2),
                        "percent": memory.percent
                    },
                    "disk": {
                        "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                        "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                        "percent": round((disk.used / disk.total) * 100, 2)
                    },
                    "processes": len(psutil.pids())
                },
                "database": {"status": "simplified_version"}
            }
        except Exception as e:
            logger.error(f"System info error: {e}")
            return JSONResponse(
                content={"error": "Failed to gather system information", "details": str(e)},
                status_code=500
            )

# Create the application instance
app = create_application()

# For development server compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )