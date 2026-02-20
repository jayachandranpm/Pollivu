"""
Pollivu - Main Routes
Public-facing pages: landing, privacy policy, how-it-works.
"""

from flask import render_template
from datetime import datetime, timezone
from . import main_bp

@main_bp.route('/')
def landing():
    return render_template('landing.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html', now=datetime.now(timezone.utc))


@main_bp.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')
