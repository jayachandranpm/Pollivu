import pytest
from services.poll_service import PollService
from models import Poll, PollOption, Vote

def test_create_poll(test_app, db_session):
    """Test creating a basic poll."""
    form_data = {
        'question': 'Test Poll?',
        'options': ['Option A', 'Option B'],
        'expiration': '24' 
    }
    
    # We mock the form object structure since PollService expects a form_data dict-like or object
    # The actual implementation calls form.question.data etc. if it's a form object, 
    # OR form_data['question'] if it's a dict? 
    # Let's check PollService implementation.
    # It assumes form_data is a dict or object with .data access?
    # Actually PollService.create_poll(form_data) uses:
    # question = form_data.get('question')
    # So it expects a dictionary for form_data.
    
    poll, token = PollService.create_poll(form_data)
    
    assert poll is not None
    assert poll.question == 'Test Poll?'
    assert poll.options.count() == 2
    assert token is not None
    
    # Verify DB persistence
    saved_poll = Poll.query.get(poll.id)
    assert saved_poll is not None
    assert saved_poll.question == 'Test Poll?'

def test_vote_poll(test_app, db_session):
    """Test voting on a poll."""
    # Create poll first
    form_data = {
        'question': 'Voting Test',
        'options': ['Yes', 'No'],
        'expiration': '24'
    }
    poll, _ = PollService.create_poll(form_data)
    
    option_id = poll.options.first().id
    session_id = 'test_session_id'
    
    success, message, result = PollService.vote(poll, option_id, session_id)
    
    assert success is True
    assert result['total_votes'] == 1
    
    # Verify vote persistence
    vote = Vote.query.filter_by(poll_id=poll.id).first()
    assert vote is not None
    assert vote.option_id == option_id

def test_close_poll(test_app, db_session):
    """Test closing a poll."""
    form_data = {'question': 'Close Me', 'options': ['A', 'B']}
    poll, token = PollService.create_poll(form_data)
    
    PollService.close_poll(poll)
    
    assert poll.is_closed is True

def test_reopen_poll(test_app, db_session):
    """Test reopening a poll."""
    form_data = {'question': 'Reopen Me', 'options': ['A', 'B']}
    poll, token = PollService.create_poll(form_data)
    
    PollService.close_poll(poll)
    assert poll.is_closed is True
    
    PollService.reopen_poll(poll)
    assert poll.is_closed is False
