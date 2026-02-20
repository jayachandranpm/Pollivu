"""
Pollivu - SocketIO Event Handlers
Real-time WebSocket events for poll rooms (join/leave).
Vote updates are emitted from poll routes, not here.
"""

from flask_socketio import join_room, leave_room
from flask_login import current_user
from extensions import socketio

@socketio.on('join')
def on_join(data):
    """User joins a poll room to receive real-time vote updates."""
    poll_id = data.get('poll_id')
    if poll_id:
        room = f"poll_{poll_id}"
        join_room(room)

@socketio.on('leave')
def on_leave(data):
    """User leaves a poll room."""
    poll_id = data.get('poll_id')
    if poll_id:
        room = f"poll_{poll_id}"
        leave_room(room)
