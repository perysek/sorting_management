import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Flask application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'scrap_data.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
