"""
Gym Tracker Pro - Configuration Settings
"""
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "gym-tracker-pro-super-secret-key-2026-production")
    DATABASE_NAME = "gym_tracker.db"
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1")
