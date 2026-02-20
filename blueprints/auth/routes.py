"""
Pollivu - Authentication Routes
Handles user registration, login, logout with rate limiting
and session security (regeneration, open redirect prevention).
"""

import logging
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timezone
from extensions import db, limiter
from models import User
from forms import RegistrationForm, LoginForm
from utils import generate_session_id
from . import auth_bp

logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute", error_message="Too many registration attempts. Please try again later.")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if email already exists
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html', form=form)
        
        user = User(
            email=form.email.data.lower(),
            display_name=form.display_name.data or None
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        logger.info(f"New user registered: {user.email}")
        flash('Welcome to Pollivu! Your account has been created.', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", error_message="Too many login attempts. Please try again in a minute.")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            # Session regeneration to prevent session fixation attacks
            session.clear()
            session['session_id'] = generate_session_id()
            session.permanent = True
            
            login_user(user, remember=form.remember_me.data)
            logger.info(f"User logged in: {user.email}")
            flash('Welcome back!', 'success')
            
            # Validate next URL to prevent open redirect attacks
            next_page = request.args.get('next')
            if next_page and (not next_page.startswith('/') or next_page.startswith('//') or ':' in next_page):
                next_page = None
            return redirect(next_page or url_for('dashboard.dashboard'))
        
        # Generic error — don't reveal whether the email exists
        logger.warning(f"Failed login attempt for: {form.email.data.lower()[:5]}***")
        flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logger.info(f"User logged out: {current_user.email}")
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.landing'))
