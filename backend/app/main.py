"""
RailMaintain — FastAPI Application Entry Point

Initializes the application, includes all API routers,
configures CORS, middleware, and startup/shutdown hooks.

Frontend integration: PENDING
Frontend will connect to API endpoints at /api/*
CORS configuration will be updated when frontend is ready.
Frontend environment variables will be added later.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    APP_TITLE,
    APP_VERSION,
    DEBUG,
    CORS_ORIGINS,
)
from app.api import ALL_ROUTERS


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan: runs on startup and shutdown."""
    # Startup
    # Uncomment the following line when the database is configured:
    # from app.database.database import init_db
    # init_db()
    yield
    # Shutdown


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

API_PREFIX = "/api"

for router in ALL_ROUTERS:
    app.include_router(router, prefix=API_PREFIX)

# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    """Root endpoint — confirms the API is running."""
    return {
        "application": APP_TITLE,
        "version": APP_VERSION,
        "docs": "/docs",
        "health": f"{API_PREFIX}/health",
        # Frontend integration: PENDING
        # Frontend will connect to API endpoints at /api/*
    }


# ---------------------------------------------------------------------------
# Entry point for development
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
    )
