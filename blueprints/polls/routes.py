"""
Pollivu - Poll Routes
Core poll CRUD operations: create, view, vote, edit, close/reopen,
delete, export CSV, QR code generation, AI suggestions, and embedding.
"""

import logging
from flask import (render_template, redirect, url_for, flash, request, session, 
                   jsonify, abort, make_response, current_app)
from flask_login import login_required, current_user
import io
import csv
try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

from extensions import db, limiter, cache, csrf
from models import User, Poll, PollOption, Vote
from forms import PollCreationForm, EditPollForm, AIGenerateForm
from utils import (is_valid_poll_id, generate_voter_token, hash_voter_token,
                   sanitize_text, is_poll_creator, generate_creator_token, hash_creator_token)
from services.poll_service import PollService
from ai_service import AIService
from . import polls_bp

logger = logging.getLogger(__name__)


@polls_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_poll():
    form = PollCreationForm()
    
    if form.validate_on_submit():
        # Prepare data for service
        form_data = {
            'question': form.question.data,
            'expiration': form.expiration.data,
            'allow_vote_change': form.allow_vote_change.data,
            'show_results_before_voting': form.show_results_before_voting.data,
            'is_public': form.is_public.data,
            'options': form.get_options()
        }
        
        poll, creator_token = PollService.create_poll(
            form_data, 
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        # Store creator token in session
        if 'creator_tokens' not in session:
            session['creator_tokens'] = {}
        session['creator_tokens'][poll.id] = creator_token
        session.modified = True
        
        flash('Poll created successfully!', 'success')
        return redirect(url_for('polls.poll_results', poll_id=poll.id))
    
    return render_template('create_poll.html', form=form)


@polls_bp.route('/create/ai', methods=['GET', 'POST'])
@login_required
def create_poll_ai():
    form = AIGenerateForm()
    
    # Get available providers for user
    ai_service = AIService(current_user, current_app.config['SECRET_KEY'])
    providers = ai_service.get_available_providers()
    
    return render_template('create_poll_ai.html', form=form, providers=providers)


@polls_bp.route('/poll/<poll_id>')
@limiter.exempt
def view_poll(poll_id):
    """View a poll for voting (GET request)."""
    if not is_valid_poll_id(poll_id):
        abort(404)
    
    poll = Poll.query.get_or_404(poll_id)
    
    # Access Control:
    # "Private" polls are treated as "Unlisted".
    # Anyone with the link (ID) can view the poll.
    # We rely on the secrecy of the 32-char ID.
    
    # Check if user already voted
    voter_token = generate_voter_token(session.get('session_id', ''), poll_id)
    voter_hash = hash_voter_token(voter_token)
    existing_vote = Vote.query.filter_by(
        poll_id=poll_id,
        voter_token_hash=voter_hash
    ).first()

    is_creator = is_poll_creator(poll) or (current_user.is_authenticated and poll.user_id == current_user.id)

    return render_template('poll.html',
                          poll=poll,
                          is_creator=is_creator,
                          has_voted=existing_vote is not None,
                          voted_option_id=existing_vote.option_id if existing_vote else None)


@polls_bp.route('/poll/<poll_id>/vote', methods=['POST'])
@csrf.exempt
@limiter.limit("30 per minute")
def vote(poll_id):
    if not is_valid_poll_id(poll_id):
        return jsonify({'error': 'Invalid poll ID'}), 400
    
    poll = PollService.get_poll(poll_id)
    if not poll:
        abort(404)
    
    data = request.get_json()
    option_id = data.get('option_id') if data else None
    
    if not option_id:
        return jsonify({'error': 'No option selected'}), 400

    try:
        option_id = int(option_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid option ID'}), 400

    session_id = session.get('session_id', '')
    success, message, result_data = PollService.vote(poll, option_id, session_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': message,
            **result_data
        })
    else:
        # Determine error code based on message (simplified)
        status_code = 403 if "already voted" in message or "active" in message else 400
        return jsonify({'error': message}), status_code


@polls_bp.route('/poll/<poll_id>/results')
@limiter.exempt
def poll_results(poll_id):
    if not is_valid_poll_id(poll_id):
        abort(404)
    
    poll = Poll.query.get_or_404(poll_id)
    
    is_creator = is_poll_creator(poll)
    is_owner = current_user.is_authenticated and poll.user_id == current_user.id
    
    # Access Control:
    # "Private" polls are treated as "Unlisted".
    # Anyone with the link (ID) can view the results.
    
    voter_token = generate_voter_token(session.get('session_id', ''), poll_id)
    voter_hash = hash_voter_token(voter_token)
    existing_vote = Vote.query.filter_by(
        poll_id=poll_id,
        voter_token_hash=voter_hash
    ).first()
    
    return render_template('results.html',
                          poll=poll,
                          is_creator=is_creator or is_owner,
                          has_voted=existing_vote is not None,
                          voted_option_id=existing_vote.option_id if existing_vote else None)


@polls_bp.route('/poll/<poll_id>/close', methods=['POST'])
def close_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    if not is_poll_creator(poll) and not (current_user.is_authenticated and poll.user_id == current_user.id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    PollService.close_poll(poll)
    
    return jsonify({'success': True, 'message': 'Poll closed'})


@polls_bp.route('/poll/<poll_id>/reopen', methods=['POST'])
def reopen_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    if not is_poll_creator(poll) and not (current_user.is_authenticated and poll.user_id == current_user.id):
        return jsonify({'error': 'Unauthorized'}), 403

    # If the poll has expired, clear expiration so it actually becomes active
    if poll.is_expired:
        poll.expires_at = None

    PollService.reopen_poll(poll)
    
    return jsonify({'success': True, 'message': 'Poll reopened'})


@polls_bp.route('/poll/<poll_id>/delete', methods=['POST'])
def delete_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    if not is_poll_creator(poll) and not (current_user.is_authenticated and poll.user_id == current_user.id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    PollService.delete_poll(poll)
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': 'Poll deleted', 'redirect': url_for('dashboard.dashboard')})
    
    flash('Poll deleted successfully.', 'success')
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('main.landing'))


@polls_bp.route('/poll/<poll_id>/toggle-public', methods=['POST'])
@login_required
def toggle_public(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    if poll.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    is_public = PollService.toggle_public(poll)
    
    status = 'public' if is_public else 'private'
    return jsonify({'success': True, 'is_public': is_public, 'message': f'Poll is now {status}'})


@polls_bp.route('/poll/<poll_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    # Check authorization (only creator can edit)
    if poll.user_id != current_user.id:
        abort(403)
        
    form = EditPollForm()
    
    # Dynamically inject current expiration if exists
    if poll.expires_at:
        try:
             expiration_label = poll.expires_at.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError):
             expiration_label = str(poll.expires_at)
        
        # Insert as first choice
        form.expiration.choices.insert(0, ('current', f'Current: {expiration_label}'))
    
    if form.validate_on_submit():
        form_data = {
            'question': form.question.data,
            'allow_vote_change': form.allow_vote_change.data,
            'show_results_before_voting': form.show_results_before_voting.data,
            'is_public': form.is_public.data,
            'share_results_chart': form.share_results_chart.data,
            'share_results_list': form.share_results_list.data,
            'share_insights': form.share_insights.data,
            'expiration': form.expiration.data
        }
        
        PollService.edit_poll(poll, form_data)
        
        flash('Poll settings updated successfully.', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    elif request.method == 'GET':
        # Pre-fill form
        form.question.data = poll.question
        form.allow_vote_change.data = poll.allow_vote_change
        form.show_results_before_voting.data = poll.show_results_before_voting
        form.is_public.data = poll.is_public
        form.share_results_chart.data = poll.share_results_chart if poll.share_results_chart is not None else True
        form.share_results_list.data = poll.share_results_list if poll.share_results_list is not None else True
        form.share_insights.data = poll.share_insights if poll.share_insights is not None else True
        
        if poll.expires_at:
            form.expiration.data = 'current'
        else:
            form.expiration.data = 'never'
            
    else:
        # POST request but validation failed
        flash('Please check the form for errors.', 'error')
            
    return render_template('edit_poll.html', form=form, poll=poll)


@polls_bp.route('/poll/<poll_id>/option/add', methods=['POST'])
@login_required
def add_poll_option(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    if poll.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    option_text = sanitize_text(data.get('option_text', ''))
    
    if not option_text:
        return jsonify({'error': 'Option text required'}), 400

    success, result = PollService.add_option(poll, option_text)
    
    if not success:
        return jsonify({'error': result}), 400
    
    # result is the newly created PollOption object
    new_option = result
    
    return jsonify({
        'success': True,
        'message': 'Option added',
        'option': {
            'id': new_option.id,
            'option_text': new_option.option_text,
            'vote_count': 0
        }
    })


@polls_bp.route('/poll/<poll_id>/option/<option_id>/delete', methods=['POST'])
@login_required
def delete_poll_option(poll_id, option_id):
    poll = Poll.query.get_or_404(poll_id)
    option = db.session.get(PollOption, option_id)
    
    if poll.user_id != current_user.id or not option or option.poll_id != poll.id:
        return jsonify({'error': 'Unauthorized or Not Found'}), 403
        
    # Prevent deleting if it's one of the last 2 options?
    if poll.options.count() <= 2:
        return jsonify({'error': 'Poll must have at least 2 options'}), 400
    
    # Delete votes for this option first to avoid foreign key constraint violation
    # Also deduct those votes from the poll total
    poll.total_votes = max(0, poll.total_votes - option.vote_count)
    Vote.query.filter_by(option_id=option_id).delete()
    
    db.session.delete(option)
    db.session.commit()
    
    return jsonify({'success': True})


@polls_bp.route('/poll/<poll_id>/options/suggest', methods=['POST'])
@login_required
def suggest_poll_options(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    if poll.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Prepare AI service
        ai = AIService(current_user, current_app.config['SECRET_KEY'])
        providers = ai.get_available_providers()
        
        if not providers:
            return jsonify({'error': 'No AI provider configured. Go to Settings to add an API key.'}), 400
            
        # Use first available provider
        provider_name = providers[0]['id']
        
        # Get existing options to exclude from suggestions
        existing_options = [opt.option_text for opt in poll.options]
        
        # Use dedicated suggest_new_options which tells the AI what already exists
        result = ai.suggest_new_options(provider_name, poll.question, existing_options, num_options=4)
        suggestions = result.get('options', [])
        
        # Double-check filter (AI might still repeat some)
        existing_lower = {t.lower() for t in existing_options}
        filtered = [s for s in suggestions if s.lower() not in existing_lower]
        
        if not filtered:
            return jsonify({'success': True, 'suggestions': [], 'message': 'AI could not generate new unique options. Try rephrasing your question.'})
        
        return jsonify({'success': True, 'suggestions': filtered[:4]})
        
    except Exception as e:
        current_app.logger.error(f"AI Suggestion Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@polls_bp.route('/poll/<poll_id>/export/csv')
def export_csv(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Pollivu Export'])
    writer.writerow(['Question', poll.question])
    writer.writerow(['Total Votes', poll.total_votes])
    writer.writerow([])
    writer.writerow(['Option', 'Votes', 'Percentage'])
    
    for option in poll.options:
        writer.writerow([option.option_text, option.vote_count, f'{option.percentage}%'])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=poll_{poll_id}_results.csv'
    
    return response


@polls_bp.route('/poll/<poll_id>/qr')
def generate_qr(poll_id):
    if not QR_AVAILABLE:
        return jsonify({'error': 'QR code generation not available'}), 501
    
    poll = Poll.query.get_or_404(poll_id)
    
    poll_url = request.host_url.rstrip('/') + url_for('polls.view_poll', poll_id=poll_id)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(poll_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color='#059669', back_color='white')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'inline; filename=poll_{poll_id}_qr.png'
    
    return response


@polls_bp.route('/poll/<poll_id>/embed')
@limiter.exempt
def embed_poll(poll_id):
    """Render a lightweight embeddable version of the poll for iframes."""
    if not is_valid_poll_id(poll_id):
        abort(404)
    
    poll = Poll.query.get_or_404(poll_id)
    
    voter_token = generate_voter_token(session.get('session_id', ''), poll_id)
    voter_hash = hash_voter_token(voter_token)
    existing_vote = Vote.query.filter_by(
        poll_id=poll_id,
        voter_token_hash=voter_hash
    ).first()
    
    response = make_response(render_template('embed_poll.html',
                          poll=poll,
                          has_voted=existing_vote is not None,
                          voted_option_id=existing_vote.option_id if existing_vote else None))
    
    # Allow this route to be iframed from any origin
    response.headers.pop('X-Frame-Options', None)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-ancestors *; "
        "form-action 'self'; "
        "base-uri 'self'"
    )
    return response
