"""
Pollivu - Poll Service
Core business logic for creating, retrieving, voting, editing,
and deleting polls. All mutations are logged for audit trails.
"""

import logging
from datetime import datetime, timedelta, timezone
from models import db, Poll, PollOption, Vote, User
from utils import (generate_poll_id, generate_creator_token, hash_creator_token, 
                   generate_voter_token, hash_voter_token, sanitize_text)

logger = logging.getLogger(__name__)


class PollService:
    @staticmethod
    def create_poll(form_data, user_id=None):
        """
        Create a new poll from form data.
        Returns: (poll, creator_token)
        """
        poll_id = generate_poll_id()
        creator_token = generate_creator_token()
        
        # Calculate expiration
        expires_at = None
        expiration = form_data.get('expiration')
        
        if expiration == '1h':
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        elif expiration == '24h':
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        elif expiration == '7d':
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        elif expiration == '30d':
            expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            
        # Create poll
        poll = Poll(
            id=poll_id,
            question=sanitize_text(form_data.get('question')),
            expires_at=expires_at,
            allow_vote_change=form_data.get('allow_vote_change', False),
            show_results_before_voting=form_data.get('show_results_before_voting', False),
            is_public=form_data.get('is_public', True),
            creator_token_hash=hash_creator_token(creator_token),
            user_id=user_id
        )
        
        # Add options
        options = form_data.get('options', [])
        for i, option_text in enumerate(options):
            if option_text and option_text.strip():
                option = PollOption(
                    poll_id=poll_id,
                    option_text=sanitize_text(option_text),
                    display_order=i
                )
                db.session.add(option)
        
        db.session.add(poll)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.error(f"Failed to create poll {poll_id}", exc_info=True)
            raise
        
        logger.info(f"Poll created: {poll_id} by user {user_id or 'anonymous'}")
        return poll, creator_token

    @staticmethod
    def get_poll(poll_id):
        """Get poll by ID."""
        return Poll.query.get(poll_id)

    @staticmethod
    def vote(poll, option_id, session_id):
        """
        Cast a vote on a poll.
        Returns: (success, message, updated_data)
        """
        if not poll.is_active:
            return False, "Poll is no longer active", None
            
        option = PollOption.query.filter_by(id=option_id, poll_id=poll.id).first()
        if not option:
            return False, "Invalid option", None
            
        voter_token = generate_voter_token(session_id, poll.id)
        voter_hash = hash_voter_token(voter_token)
        
        existing_vote = Vote.query.filter_by(
            poll_id=poll.id,
            voter_token_hash=voter_hash
        ).first()
        
        if existing_vote:
            if poll.allow_vote_change:
                # Change vote
                old_option = PollOption.query.get(existing_vote.option_id)
                if old_option:
                    old_option.vote_count = max(0, old_option.vote_count - 1)
                
                existing_vote.option_id = option_id
                option.vote_count += 1
                db.session.commit()
                
                logger.info(f"Vote changed on poll {poll.id}: option {existing_vote.option_id} -> {option_id}")
                return True, "Vote changed successfully", {
                    'voted_option_id': option_id,
                    'total_votes': poll.total_votes,
                    'results': [opt.to_dict() for opt in poll.options]
                }
            else:
                return False, "You have already voted", None
        
        # New vote
        vote = Vote(
            poll_id=poll.id,
            voter_token_hash=voter_hash,
            option_id=option_id
        )
        
        option.vote_count += 1
        poll.total_votes += 1
        
        db.session.add(vote)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.error(f"Failed to record vote on poll {poll.id}", exc_info=True)
            raise
        
        logger.info(f"New vote on poll {poll.id}: option {option_id} (total: {poll.total_votes})")
        return True, "Vote recorded", {
            'voted_option_id': option_id,
            'total_votes': poll.total_votes,
            'results': [opt.to_dict() for opt in poll.options]
        }

    @staticmethod
    def edit_poll(poll, form_data):
        """Update poll settings and expiration."""
        poll.updated_at = datetime.now(timezone.utc)
        poll.question = sanitize_text(form_data.get('question'))
        poll.allow_vote_change = form_data.get('allow_vote_change')
        poll.show_results_before_voting = form_data.get('show_results_before_voting')
        poll.is_public = form_data.get('is_public')
        poll.share_results_chart = form_data.get('share_results_chart', True)
        poll.share_results_list = form_data.get('share_results_list', True)
        poll.share_insights = form_data.get('share_insights', True)
        
        # Handle expiration update
        expiration = form_data.get('expiration')
        if expiration != 'current':
            if expiration == 'never':
                poll.expires_at = None
            elif expiration == '1h':
                poll.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            elif expiration == '24h':
                poll.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            elif expiration == '7d':
                poll.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            elif expiration == '30d':
                poll.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.error(f"Failed to edit poll {poll.id}", exc_info=True)
            raise
        
        logger.info(f"Poll edited: {poll.id}")
        return True, "Poll settings updated successfully."

    @staticmethod
    def add_option(poll, option_text):
        """Add a new option to an existing poll."""
        option_text = sanitize_text(option_text)
        
        if not option_text or len(option_text) > 200:
            return False, "Invalid option text"
            
        if poll.options.count() >= 10:
            return False, "Maximum 10 options allowed"

        # Check dupes
        existing_options = poll.options.all() 
        if any(opt.option_text.lower() == option_text.lower() for opt in existing_options):
            return False, "Option already exists"
            
        max_order = 0
        if existing_options:
            max_order = max(opt.display_order for opt in existing_options)
            
        new_option = PollOption(
            poll_id=poll.id, 
            option_text=option_text,
            display_order=max_order + 1
        )
        db.session.add(new_option)
        db.session.commit()
        
        return True, new_option  # Return the actual option object

    @staticmethod
    def toggle_public(poll):
        """Toggle public/private status."""
        poll.is_public = not poll.is_public
        poll.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return poll.is_public

    @staticmethod
    def close_poll(poll):
        """Close a poll."""
        poll.is_closed = True
        poll.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Poll closed: {poll.id}")
    
    @staticmethod
    def reopen_poll(poll):
        """Reopen a poll."""
        poll.is_closed = False
        poll.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Poll reopened: {poll.id}")
        
    @staticmethod
    def delete_poll(poll):
        """Delete a poll and all associated data."""
        poll_id = poll.id
        try:
            db.session.delete(poll)
            db.session.commit()
            logger.info(f"Poll deleted: {poll_id}")
        except Exception:
            db.session.rollback()
            logger.error(f"Failed to delete poll {poll_id}", exc_info=True)
            raise

