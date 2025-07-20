#!/usr/bin/env python3
"""FastAPI backend for SOTD pipeline analyzer web UI."""

import logging
import os
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from webui.api.analysis import router as analysis_router
from webui.api.brush_splits import router as brush_splits_router
from webui.api.catalogs import router as catalogs_router
from webui.api.files import router as files_router
from webui.api.filtered import router as filtered_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SOTD Pipeline Analyzer API",
    description="API for analyzing SOTD pipeline data",
    version="1.0.0",
)

# Include routers
app.include_router(files_router)
app.include_router(catalogs_router)
app.include_router(analysis_router)
app.include_router(filtered_router)
app.include_router(brush_splits_router)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        # Allow all origins for test environment
        "*" if os.getenv("ENVIRONMENT") == "test" else None,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "SOTD Pipeline Analyzer API"}


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0", "service": "SOTD Pipeline Analyzer API"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
