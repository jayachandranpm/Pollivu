"""
Pollivu - Flask Extension Instances
Centralized initialization of all Flask extensions.
Imported by app.py and other modules to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_caching import Cache

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # Overridden by RATELIMIT_STORAGE_URL from config
)
socketio = SocketIO()
cache = Cache()
