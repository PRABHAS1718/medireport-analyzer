"""MediReport Analyzer FastAPI Application Entrypoint.

Configures middleware, lifecycle handlers, routes, and OpenAPI metadata.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.
    
    Handles startup and shutdown logic such as initializing database
    connections, validating storage directories, and cleaning up resources.
    """
    # Startup: Ensure storage directory exists
    storage_path = settings.resolved_storage_path
    
    # Initialize MongoDB connection
    from app.database.mongodb import mongo_manager
    await mongo_manager.connect()
    
    yield
    
    # Shutdown: Clean up connections
    await mongo_manager.close()


def create_application() -> FastAPI:
    """Factory function to build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        description=(
            "MediReport Analyzer API: Evidence-grounded medical report understanding, "
            "longitudinal comparison, and persistent medical memory system."
        ),
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount v1 API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    async def root():
        """Root API welcome message with links to documentation."""
        return {
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "documentation": "/docs",
            "api_v1": f"{settings.API_V1_STR}/health",
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
