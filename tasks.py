"""
Pollivu - Background Tasks
Scheduled maintenance tasks for poll cleanup and statistics.
Must be called within a Flask application context.
"""

import logging
from datetime import datetime, timezone
from models import db, Poll

logger = logging.getLogger(__name__)


def cleanup_expired_polls():
    """
    Delete polls that have passed their expiration date.
    Must be called within a Flask app context.
    """
    now = datetime.now(timezone.utc)
    expired_polls = Poll.query.filter(
        Poll.expires_at.isnot(None),
        Poll.expires_at < now
    ).all()
    
    count = len(expired_polls)
    
    for poll in expired_polls:
        db.session.delete(poll)
    
    db.session.commit()
    
    logger.info(f"Cleaned up {count} expired polls")
    return count


def get_poll_stats():
    """Get statistics about all polls."""
    total_polls = Poll.query.count()
    active_polls = Poll.query.filter(
        Poll.is_closed == False,
        db.or_(
            Poll.expires_at.is_(None),
            Poll.expires_at > datetime.now(timezone.utc)
        )
    ).count()
    
    return {
        'total_polls': total_polls,
        'active_polls': active_polls
    }
