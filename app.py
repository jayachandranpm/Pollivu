"""
Pollivu - Application Entry Point
Initializes the Flask app, extensions, blueprints, security middleware,
and error handlers. Loads configuration from environment variables.
"""

# Load environment variables before anything else
from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, session, request, render_template, jsonify
import logging

from config import config
from services.config_validation import validate_config
from extensions import db, migrate, csrf, login_manager, limiter, socketio, cache
from models import User
from utils import generate_session_id, format_time_remaining

# Validate required env vars before anything else
validate_config()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'production')])

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
limiter.init_app(app)

# SocketIO — restrict CORS in production
if os.getenv('FLASK_ENV') == 'development':
    _cors_origins = '*'
else:
    _origins_raw = os.getenv('ALLOWED_ORIGINS', '')
    _cors_origins = [o.strip() for o in _origins_raw.split(',') if o.strip()] or []
socketio.init_app(app, cors_allowed_origins=_cors_origins)
cache.init_app(app)

# Create tables on startup if they don't exist
with app.app_context():
    try:
        db.create_all()
        app.logger.info("Database tables verified.")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {e}")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Register Blueprints
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.polls import polls_bp
from blueprints.api import api_bp
from blueprints.main import main_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(polls_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(main_bp)

# Production Logging
if os.getenv('FLASK_ENV') != 'development':
    # Configure logging to stdout for container/PaaS environments
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplication
    app.logger.handlers = []
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('Pollivu starting up in production mode...')


# Session setup
@app.before_request
def setup_session():
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
        session.permanent = True


# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add comprehensive security headers to all responses."""
    # Prevent clickjacking attacks
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS filter in browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Control referrer information
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions policy (restrict sensitive APIs)
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Content Security Policy - prevent XSS and data injection
    # Allow Ollama localhost in dev only
    connect_src = "'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net"
    if os.getenv('FLASK_ENV') == 'development':
        connect_src += " http://localhost:11434"
    
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        f"connect-src {connect_src}; "
        "frame-ancestors 'self'; "
        "form-action 'self'; "
        "base-uri 'self'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # Only add HSTS in production (HTTPS only)
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Prevent caching of sensitive pages
    if request.path in ['/login', '/register', '/settings', '/dashboard']:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response


# Register template filters
@app.template_filter('format_time')
def format_time_filter(timedelta_obj):
    return format_time_remaining(timedelta_obj)


# Error Handlers — return JSON for API routes, HTML otherwise
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404


@app.errorhandler(403)
def forbidden_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('errors/403.html'), 403


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Too many requests'}), 429
    return render_template('429.html'), 429

if __name__ == '__main__':
    is_dev = os.getenv('FLASK_ENV') == 'development'
    socketio.run(app, debug=is_dev)
