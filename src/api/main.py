"""FastAPI Application Entry Point"""

from contextlib import asynccontextmanager
from datetime import datetime
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.core.models import HealthResponse
from .routes import chat, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    print("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="RAG Chatbot API - Internal Document Search",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.frontend_url,
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    app.include_router(websocket.router, tags=["websocket"])

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            timestamp=datetime.now(),
        )

    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint"""
        return {
            "message": "RAG Chatbot API",
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()
