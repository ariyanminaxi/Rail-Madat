"""
RailMadat — Application Configuration

Loads all configuration from environment variables.
Use .env for local development; set real env vars in production.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:[PASSWORD]@db.xxxxxxxx.supabase.co:5432/postgres",
)

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

JWT_SECRET = os.environ.get("JWT_SECRET", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = int(os.environ.get("TOKEN_EXPIRY_MINUTES", "480"))

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if not CORS_ORIGINS and FRONTEND_URL:
    CORS_ORIGINS = [FRONTEND_URL]

# Fallback for development
if not CORS_ORIGINS:
    CORS_ORIGINS = [
        "http://localhost:3000",  # railmadat-frontend
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Alternative frontend
    ]

# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@railmaintain.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ADMIN_DISPLAY_NAME = os.environ.get("ADMIN_DISPLAY_NAME", "System Administrator")

# ---------------------------------------------------------------------------
# Data Mode
# ---------------------------------------------------------------------------
# Options: supabase, csv, memory
#   supabase — read/write from Supabase (production)
#   csv      — read from CSV files in backend/data/ (offline testing)
#   memory   — in-memory store only (unit tests)
DATA_MODE = os.environ.get("DATA_MODE", "csv")
CSV_DATA_PATH = os.environ.get("CSV_DATA_PATH", "data")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

APP_TITLE = "RailMadat API"
APP_VERSION = "1.0.0"
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
