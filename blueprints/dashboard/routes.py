"""
Pollivu - Dashboard Routes
User dashboard, account settings, and API key management.
All routes require authentication via @login_required.
"""

import logging
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Poll
from forms import APIKeyForm, UpdateAccountForm
from ai_service import AIService
from . import dashboard_bp

logger = logging.getLogger(__name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    polls = current_user.polls.order_by(Poll.created_at.desc()).all()
    return render_template('dashboard.html', polls=polls)


@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    api_form = APIKeyForm()
    account_form = UpdateAccountForm()
    
    # Load existing keys
    keys = current_user.get_api_keys(current_app.config['SECRET_KEY'])
    
    # Handle Account Update
    if account_form.validate_on_submit() and 'submit_account' in request.form:
        if not current_user.check_password(account_form.current_password.data):
            flash('Incorrect current password.', 'error')
        else:
            # Update profile
            current_user.display_name = account_form.display_name.data
            
            # Update email if changed (and check uniqueness)
            if account_form.email.data.lower() != current_user.email:
                if User.query.filter_by(email=account_form.email.data.lower()).first():
                    flash('Email already in use.', 'error')
                    return redirect(url_for('dashboard.settings'))
                current_user.email = account_form.email.data.lower()
            
            # Update password if provided
            if account_form.new_password.data:
                current_user.set_password(account_form.new_password.data)
                flash('Password updated successfully.', 'success')
            
            db.session.commit()
            logger.info(f"Account settings updated for user {current_user.id}")
            flash('Account settings updated.', 'success')
            return redirect(url_for('dashboard.settings'))

    # Handle API Key Update
    if api_form.validate_on_submit() and 'submit_api' in request.form:
        # Update API keys - only update if new value provided
        if api_form.gemini_key.data and api_form.gemini_key.data.strip():
            current_user.set_api_key('gemini', api_form.gemini_key.data.strip(), current_app.config['SECRET_KEY'])
        if api_form.openai_key.data and api_form.openai_key.data.strip():
            current_user.set_api_key('openai', api_form.openai_key.data.strip(), current_app.config['SECRET_KEY'])
        if api_form.claude_key.data and api_form.claude_key.data.strip():
            current_user.set_api_key('claude', api_form.claude_key.data.strip(), current_app.config['SECRET_KEY'])
        
        # Save model selections for each provider
        if api_form.gemini_model.data and api_form.gemini_model.data.strip():
            current_user.set_api_key('gemini_model', api_form.gemini_model.data.strip(), current_app.config['SECRET_KEY'])
        if api_form.openai_model.data and api_form.openai_model.data.strip():
            current_user.set_api_key('openai_model', api_form.openai_model.data.strip(), current_app.config['SECRET_KEY'])
        if api_form.claude_model.data and api_form.claude_model.data.strip():
            current_user.set_api_key('claude_model', api_form.claude_model.data.strip(), current_app.config['SECRET_KEY'])
        
        # Always save Ollama settings (even if updating to different values)
        ollama_url = api_form.ollama_url.data.strip() if api_form.ollama_url.data else 'http://localhost:11434'
        ollama_model = api_form.ollama_model.data.strip() if api_form.ollama_model.data else 'qwen3:8b'
        current_user.set_api_key('ollama_url', ollama_url, current_app.config['SECRET_KEY'])
        current_user.set_api_key('ollama_model', ollama_model, current_app.config['SECRET_KEY'])
        
        db.session.add(current_user)
        db.session.commit()
        logger.info(f"API keys updated for user {current_user.id}")
        flash('API settings saved successfully.', 'success')
        return redirect(url_for('dashboard.settings'))
    
    # Pre-populate form with existing values (on GET request)
    if request.method == 'GET':
        # Account defaults
        account_form.display_name.data = current_user.display_name
        account_form.email.data = current_user.email
        
        # API defaults
        api_form.gemini_model.data = keys.get('gemini_model', 'gemini-2.5-flash')
        api_form.openai_model.data = keys.get('openai_model', 'gpt-4.1')
        api_form.claude_model.data = keys.get('claude_model', 'claude-sonnet-4-5')
        api_form.ollama_url.data = keys.get('ollama_url', 'http://localhost:11434')
        api_form.ollama_model.data = keys.get('ollama_model', '')
    
    # Mask existing keys for display (first 8 + last 4 chars only)
    masked_keys = {}
    for key_name in ['gemini', 'openai', 'claude']:
        if keys.get(key_name):
            key = keys[key_name]
            if len(key) >= 12:
                masked_keys[key_name] = key[:8] + '...' + key[-4:]
            else:
                masked_keys[key_name] = '*' * len(key)
    
    # Build a safe subset — never send raw API key values to templates
    safe_keys = {
        'gemini': bool(keys.get('gemini')),
        'openai': bool(keys.get('openai')),
        'claude': bool(keys.get('claude')),
        'gemini_model': keys.get('gemini_model', 'gemini-2.5-flash'),
        'openai_model': keys.get('openai_model', 'gpt-4.1'),
        'claude_model': keys.get('claude_model', 'claude-sonnet-4-5'),
        'ollama_url': keys.get('ollama_url', ''),
        'ollama_model': keys.get('ollama_model', ''),
    }
    
    return render_template('settings.html', api_form=api_form, account_form=account_form, keys=safe_keys, masked_keys=masked_keys)


@dashboard_bp.route('/settings/api-keys/delete/<provider>', methods=['POST'])
@login_required
def delete_api_key(provider):
    # Whitelist valid provider names
    valid_providers = ['gemini', 'openai', 'claude', 'ollama_url', 'ollama_model',
                       'gemini_model', 'openai_model', 'claude_model']
    if provider not in valid_providers:
        flash('Invalid provider.', 'error')
        return redirect(url_for('dashboard.settings'))
    
    current_user.remove_api_key(provider, current_app.config['SECRET_KEY'])
    # Also remove the associated model selection when deleting a provider key
    model_key = f'{provider}_model'
    if provider in ('gemini', 'openai', 'claude') and model_key not in valid_providers:
        pass  # model_key is already in valid_providers
    if provider in ('gemini', 'openai', 'claude'):
        current_user.remove_api_key(model_key, current_app.config['SECRET_KEY'])
    db.session.add(current_user)
    db.session.commit()
    logger.info(f"{provider.capitalize()} API key removed for user {current_user.id}")
    flash(f'{provider.capitalize()} API key removed.', 'success')
    return redirect(url_for('dashboard.settings'))


@dashboard_bp.route('/settings/ollama/models', methods=['POST'])
@login_required
def fetch_ollama_models():
    data = request.get_json()
    url = data.get('url', 'http://localhost:11434')
    
    ai_service = AIService()
    models = ai_service.get_ollama_models(url)
    
    if models:
        return jsonify({'success': True, 'models': models})
    else:
        return jsonify({'success': False, 'error': 'Could not fetch models. Check URL and ensure Ollama is running.'}), 400
