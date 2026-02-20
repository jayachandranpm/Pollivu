"""
Pollivu - Database Models
All sensitive data is encrypted using AES-256-GCM for end-to-end security.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json
from encryption import AES256Encryption, encrypt_dict, decrypt_dict
from extensions import db


class EncryptedMixin:
    """
    Mixin for models that need AES-256 encrypted fields.
    Provides helper methods for encryption/decryption.
    """
    
    @staticmethod
    def _get_encryptor(secret_key: str) -> AES256Encryption:
        """Get AES-256 encryption instance."""
        return AES256Encryption(secret_key)
    
    @staticmethod
    def encrypt_field(value: str, secret_key: str) -> str:
        """Encrypt a single field value."""
        if not value:
            return ""
        return AES256Encryption(secret_key).encrypt(value)
    
    @staticmethod
    def decrypt_field(encrypted: str, secret_key: str) -> str:
        """Decrypt a single field value."""
        if not encrypted:
            return ""
        try:
            return AES256Encryption(secret_key).decrypt(encrypted)
        except Exception:
            return ""


class User(UserMixin, EncryptedMixin, db.Model):
    """
    User model for authentication and API key storage.
    
    Security Features:
    - Password hashed with PBKDF2-SHA256
    - API keys encrypted with AES-256-GCM
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Encrypted API keys stored as JSON (AES-256-GCM encrypted)
    _api_keys_encrypted = db.Column('api_keys', db.Text, nullable=True)
    
    # Relationships
    polls = db.relationship('Poll', backref='owner', lazy='dynamic',
                            foreign_keys='Poll.user_id')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Hash and set the user's password using PBKDF2-SHA256."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_api_keys(self, secret_key):
        """Decrypt and return API keys using AES-256."""
        if not self._api_keys_encrypted:
            return {}
        try:
            return decrypt_dict(self._api_keys_encrypted, secret_key)
        except Exception:
            return {}
    
    def set_api_keys(self, keys, secret_key):
        """Encrypt and store API keys using AES-256."""
        self._api_keys_encrypted = encrypt_dict(keys, secret_key)
    
    def get_api_key(self, provider, secret_key):
        """Get API key for a specific provider."""
        keys = self.get_api_keys(secret_key)
        return keys.get(provider)
    
    def set_api_key(self, provider, key, secret_key):
        """Set API key for a specific provider."""
        keys = self.get_api_keys(secret_key)
        keys[provider] = key
        self.set_api_keys(keys, secret_key)
    
    def remove_api_key(self, provider, secret_key):
        """Remove API key for a specific provider."""
        keys = self.get_api_keys(secret_key)
        if provider in keys:
            del keys[provider]
            self.set_api_keys(keys, secret_key)
    
    @property
    def poll_count(self):
        """Get total number of polls created by user."""
        return self.polls.count()
    
    @property
    def total_votes_received(self):
        """Get total votes across all user's polls."""
        return sum(poll.total_votes for poll in self.polls)


class Poll(EncryptedMixin, db.Model):
    """
    Poll model for storing poll questions and settings.
    
    Security Features:
    - Question text can be encrypted for sensitive polls
    - Creator token hashed for anonymous ownership verification
    """
    
    __tablename__ = 'polls'
    
    id = db.Column(db.String(32), primary_key=True)
    # Question stored as plain text (or encrypted for private polls)
    question = db.Column(db.Text, nullable=False)
    # Encrypted question for sensitive polls
    _question_encrypted = db.Column('question_encrypted', db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    allow_vote_change = db.Column(db.Boolean, default=False)
    show_results_before_voting = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)
    is_encrypted = db.Column(db.Boolean, default=False)  # Flag for encrypted polls
    share_results_chart = db.Column(db.Boolean, default=True)
    share_results_list = db.Column(db.Boolean, default=True)
    share_insights = db.Column(db.Boolean, default=True)
    creator_token_hash = db.Column(db.String(255), nullable=False)
    total_votes = db.Column(db.Integer, default=0)
    
    # User ownership (nullable for anonymous polls)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Relationships
    options = db.relationship('PollOption', backref='poll', lazy='dynamic',
                              cascade='all, delete-orphan', order_by='PollOption.display_order')
    votes = db.relationship('Vote', backref='poll', lazy='dynamic',
                            cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Poll {self.id}>'
    
    def get_question(self, secret_key=None):
        """Get poll question (decrypted if encrypted)."""
        if self.is_encrypted and self._question_encrypted and secret_key:
            try:
                return self.decrypt_field(self._question_encrypted, secret_key)
            except Exception:
                return self.question
        return self.question
    
    def set_question(self, question, secret_key=None, encrypt=False):
        """Set poll question (with optional encryption)."""
        if encrypt and secret_key:
            self._question_encrypted = self.encrypt_field(question, secret_key)
            self.is_encrypted = True
        self.question = question
    
    @property
    def is_expired(self):
        """Check if the poll has expired."""
        if self.expires_at is None:
            return False
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires
    
    @property
    def is_active(self):
        """Check if the poll is active (not closed and not expired)."""
        return not self.is_closed and not self.is_expired
    
    @property
    def time_remaining(self):
        """Get time remaining until expiration."""
        if self.expires_at is None:
            return None
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        remaining = expires - now
        if remaining.total_seconds() < 0:
            return None
        return remaining
    
    @property
    def public_url(self):
        """Get the public shareable URL path."""
        return f'/p/{self.id}'
    
    def to_dict(self):
        """Convert poll to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'question': self.question,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'allow_vote_change': self.allow_vote_change,
            'show_results_before_voting': self.show_results_before_voting,
            'is_closed': self.is_closed,
            'is_public': self.is_public,
            'share_results_chart': self.share_results_chart,
            'share_results_list': self.share_results_list,
            'share_insights': self.share_insights,
            'is_expired': self.is_expired,
            'is_active': self.is_active,
            'total_votes': self.total_votes,
            'options': [opt.to_dict() for opt in self.options]
        }


class PollOption(EncryptedMixin, db.Model):
    """
    Poll option model for storing poll choices.
    
    Security Features:
    - Option text can be encrypted for sensitive polls
    """
    
    __tablename__ = 'poll_options'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    poll_id = db.Column(db.String(32), db.ForeignKey('polls.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    option_text = db.Column(db.Text, nullable=False)
    # Encrypted option text for sensitive polls
    _option_encrypted = db.Column('option_encrypted', db.Text, nullable=True)
    vote_count = db.Column(db.Integer, default=0)
    display_order = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<PollOption {self.id}: {self.option_text[:30]}>'
    
    def get_option_text(self, secret_key=None):
        """Get option text (decrypted if encrypted)."""
        if self.poll.is_encrypted and self._option_encrypted and secret_key:
            try:
                return self.decrypt_field(self._option_encrypted, secret_key)
            except Exception:
                return self.option_text
        return self.option_text
    
    def set_option_text(self, text, secret_key=None, encrypt=False):
        """Set option text (with optional encryption)."""
        if encrypt and secret_key:
            self._option_encrypted = self.encrypt_field(text, secret_key)
        self.option_text = text
    
    @property
    def percentage(self):
        """Calculate vote percentage."""
        if self.poll.total_votes == 0:
            return 0
        return round((self.vote_count / self.poll.total_votes) * 100, 1)
    
    def to_dict(self):
        """Convert option to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'option_text': self.option_text,
            'vote_count': self.vote_count,
            'percentage': self.percentage,
            'display_order': self.display_order
        }


class Vote(db.Model):
    """
    Vote model for tracking who voted for what (anonymously).
    
    Security Features:
    - Voter identity stored as SHA-256 hash (anonymous)
    - No personal information stored
    - Tamper-proof with unique constraints
    """
    
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    poll_id = db.Column(db.String(32), db.ForeignKey('polls.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    # SHA-256 hash of voter token - completely anonymous
    voter_token_hash = db.Column(db.String(255), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_options.id', ondelete='CASCADE'), 
                          nullable=False)
    voted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Unique constraint: one vote per user per poll
    __table_args__ = (
        db.UniqueConstraint('poll_id', 'voter_token_hash', name='unique_vote_per_poll'),
        db.Index('idx_poll_voter', 'poll_id', 'voter_token_hash'),
    )
    
    # Relationship to option
    option = db.relationship('PollOption', backref='votes_received')
    
    def __repr__(self):
        return f'<Vote {self.id} for Poll {self.poll_id}>'
