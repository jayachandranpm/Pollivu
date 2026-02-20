"""
Pollivu - Utility Functions
Cryptographic helpers, input sanitization, poll ID validation,
and session-based creator/voter token management.
"""

import hashlib
import secrets
import re
import bleach
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash


def generate_poll_id(length=16):
    """Generate a URL-safe random poll ID."""
    return secrets.token_urlsafe(length)[:length]


def generate_session_id():
    """Generate a secure session ID."""
    return secrets.token_urlsafe(32)


def generate_creator_token():
    """Generate a token for poll creator rights."""
    return secrets.token_urlsafe(32)


def hash_creator_token(token):
    """Hash a creator token before storing in database."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_voter_token(session_id, poll_id):
    """
    Generate unique voter token.
    Combines session_id and poll_id so token is unique per poll per user.
    """
    message = f"{session_id}:{poll_id}".encode()
    return hashlib.sha256(message).hexdigest()


def hash_voter_token(token):
    """Hash a voter token for storage/comparison."""
    return hashlib.sha256(token.encode()).hexdigest()


def get_browser_fingerprint(request):
    """
    Create a lightweight fingerprint from browser headers.
    This is privacy-respecting as it doesn't use IP addresses.
    """
    user_agent = request.headers.get('User-Agent', '')
    accept_language = request.headers.get('Accept-Language', '')
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]


def sanitize_text(text):
    """
    Remove any HTML tags and sanitize user input.
    Prevents XSS attacks.
    """
    if text is None:
        return ""
    return bleach.clean(text, tags=[], strip=True).strip()


def is_valid_poll_id(poll_id):
    """Check if poll ID matches expected format."""
    if not poll_id:
        return False
    return bool(re.match(r'^[A-Za-z0-9_-]{8,32}$', poll_id))


def validate_poll_id(poll_id):
    """
    Ensure poll_id matches expected format.
    Prevents SQL injection and path traversal.
    """
    if not poll_id:
        raise ValueError("Poll ID is required")
    if not re.match(r'^[A-Za-z0-9_-]{8,32}$', poll_id):
        raise ValueError("Invalid poll ID format")
    return poll_id


def format_time_remaining(timedelta_obj):
    """Format a timedelta into a human-readable string."""
    if timedelta_obj is None:
        return "Never expires"
    
    total_seconds = int(timedelta_obj.total_seconds())
    
    if total_seconds < 0:
        return "Expired"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 and days == 0:
        parts.append(f"{minutes}m")
    if seconds > 0 and days == 0 and hours == 0:
        parts.append(f"{seconds}s")
    
    return " ".join(parts) if parts else "Less than a second"


def is_poll_creator(poll):
    """Check if current session is the poll creator."""
    creator_tokens = session.get('creator_tokens', {})
    stored_token = creator_tokens.get(poll.id)
    
    if stored_token:
        # hash_creator_token is defined in this file, so we can use it directly
        return hash_creator_token(stored_token) == poll.creator_token_hash
    
    return False
