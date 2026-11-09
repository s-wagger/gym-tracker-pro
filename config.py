"""
Gym Tracker Pro - Configuration Settings
"""
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "gym-tracker-pro-super-secret-key-2026-production")
    DATABASE_NAME = "gym_tracker.db"
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1")

    # Supabase / PostgreSQL & Database Migration Support
    raw_db_url = os.environ.get("DATABASE_URL")
    if raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    DATABASE_URL = raw_db_url
    SQLALCHEMY_DATABASE_URI = raw_db_url or f"sqlite:///{os.path.join(os.path.dirname(__file__), 'gym_tracker.db')}"
