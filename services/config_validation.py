"""
Pollivu - Configuration Validator
Ensures all required environment variables are set before startup.
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

REQUIRED_VARS = [
    'SECRET_KEY',
    'POLLIVU_SALT',
    # 'DATABASE_URL' is optional as we fallback to sqlite locally, 
    # but strictly required for production if we were enforcing that here.
]

def validate_config():
    """
    Validate that all required environment variables are present.
    Exits the application if any are missing.
    """
    missing = []
    for var in REQUIRED_VARS:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        error_msg = f"CRITICAL: Missing required environment variables: {', '.join(missing)}"
        logger.critical(error_msg)
        sys.exit(1)
        
    # Warn if using default SQLite in production (heuristic)
    if os.getenv('FLASK_ENV') == 'production' and not os.getenv('DATABASE_URL'):
        logger.warning("WARNING: Running in production mode but using default SQLite database.")

if __name__ == "__main__":
    validate_config()
