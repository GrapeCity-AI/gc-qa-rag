"""
PgVector HTTP Adapter
A lightweight HTTP service that exposes pgvector functionality
with Qdrant-compatible API endpoints.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="PgVector HTTP Adapter",
    description="Qdrant-compatible API for PostgreSQL + pgvector",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PgVector HTTP Adapter",
        "version": "1.0.0",
        "status": "running",
        "compatible_with": "Qdrant API"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,  # Use Qdrant's default port for compatibility
        reload=False,
        log_level="info"
    )