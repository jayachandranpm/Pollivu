"""
Pollivu - Application Configuration
Defines base, development, and production configurations.
All sensitive values are loaded from environment variables.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask — no fallback; validate_config() ensures this is set
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Database
    _db_user = os.getenv('DB_USER')
    _db_password = os.getenv('DB_PASSWORD')
    _db_host = os.getenv('DB_HOST')
    _db_port = os.getenv('DB_PORT', '3306')
    _db_name = os.getenv('DB_NAME')
    
    if _db_host and _db_user and _db_name:
        SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///polls.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Cookie Security
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    
    # Poll Settings
    POLL_EXPIRATION_OPTIONS = {
        '1h': timedelta(hours=1),
        '6h': timedelta(hours=6),
        '24h': timedelta(days=1),
        '7d': timedelta(days=7),
        '30d': timedelta(days=30),
        'never': None
    }
    
    MAX_POLL_OPTIONS = 10
    MIN_POLL_OPTIONS = 2
    MAX_QUESTION_LENGTH = 500
    MAX_OPTION_LENGTH = 200
    
    # Caching
    CACHE_TYPE = 'SimpleCache'  # Default to memory
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    
    if CACHE_REDIS_URL:
        CACHE_TYPE = 'RedisCache'



class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
