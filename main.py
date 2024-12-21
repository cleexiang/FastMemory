from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import litellm
import os
from config import settings
from app.routers import memory
from app.logger import setup_logging

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""    
    # Configure logging
    setup_logging()
    
    # Configure LiteLLM
    os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
    
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]

    app = FastAPI(
        title="AI Memory Service",
        description="Long-term memory service for AI chatbots",
        version="1.0.0"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(memory.router, prefix="/api/v1", tags=["memory"])

    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app

app = create_app()