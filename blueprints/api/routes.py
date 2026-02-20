"""
Pollivu - API Routes
JSON API endpoints for AI generation, AI suggestions, live poll stats,
poll status, and poll analytics (vote timeline + word cloud).
"""

import logging
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import limiter, cache
from models import Poll
from ai_service import AIService
from utils import is_poll_creator
from . import api_bp

logger = logging.getLogger(__name__)

@api_bp.route('/ai/generate', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def api_ai_generate():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    topic = data.get('topic', '').strip()
    provider = data.get('provider', 'gemini')
    try:
        num_options = max(2, min(10, int(data.get('num_options', 4))))
    except (ValueError, TypeError):
        num_options = 4
    style = data.get('style', 'neutral')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    try:
        ai_service = AIService(current_user, current_app.config['SECRET_KEY'])
        result = ai_service.generate_poll(provider, topic, num_options, style)
        return jsonify({'success': True, 'poll': result})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"AI generation failed for provider '{provider}': {e}", exc_info=True)
        return jsonify({'error': f'AI generation failed: {str(e)}'}), 500


@api_bp.route('/ai/suggest', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def api_ai_suggest():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    question = data.get('question', '').strip()
    options = data.get('options', [])
    provider = data.get('provider', 'gemini')
    
    if not question or not options:
        return jsonify({'error': 'Question and options are required'}), 400
    
    try:
        ai_service = AIService(current_user, current_app.config['SECRET_KEY'])
        result = ai_service.suggest_improvements(provider, question, options)
        return jsonify({'success': True, 'suggestions': result})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"AI suggestion failed for provider '{provider}': {e}", exc_info=True)
        return jsonify({'error': f'AI suggestion failed: {str(e)}'}), 500


@api_bp.route('/poll/<poll_id>/live_stats')
@limiter.limit("60 per minute")
@cache.cached(timeout=10)
def api_poll_stats(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    # Access: anyone with the poll ID can read live stats (same as the HTML results page)
    return jsonify({
        'success': True,
        'poll_id': poll_id,
        'total_votes': poll.total_votes,
        'is_active': poll.is_active,
        'results': [opt.to_dict() for opt in poll.options]
    })


@api_bp.route('/poll/<poll_id>/status')
@limiter.limit("60 per minute")
@cache.cached(timeout=10)
def api_poll_status(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    # Access: anyone with the poll ID can read status
    return jsonify({
        'success': True,
        'is_active': poll.is_active,
        'is_closed': poll.is_closed,
        'is_expired': poll.is_expired,
        'total_votes': poll.total_votes
    })


@api_bp.route('/poll/<poll_id>/analytics')
@limiter.limit("30 per minute")
def api_poll_analytics(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    # Check access permission
    is_creator = is_poll_creator(poll)
    is_owner = current_user.is_authenticated and poll.user_id == current_user.id
    # share_insights=None means legacy poll (pre-migration), default to allowed
    insights_shared = poll.share_insights is None or poll.share_insights is True

    if not is_creator and not is_owner and not insights_shared:
        return jsonify({'error': 'Unauthorized access'}), 403

    # Votes over time (Group by Hour)
    # Using simple date truncation for broader compatibility/simplicity
    # For MySQL: func.date_format(Vote.voted_at, '%Y-%m-%d %H:00:00')
    from models import Vote
    from extensions import db
    from sqlalchemy import func

    timeline_data = []
    if poll.total_votes > 0:
        try:
            # Detect database dialect for compatible date truncation
            dialect = db.engine.dialect.name
            if dialect == 'mysql':
                time_bucket = func.date_format(Vote.voted_at, '%Y-%m-%d %H:00')
            else:
                # SQLite fallback
                time_bucket = func.strftime('%Y-%m-%d %H:00', Vote.voted_at)

            results = db.session.query(
                time_bucket.label('time_bucket'),
                func.count(Vote.id)
            ).filter(
                Vote.poll_id == poll_id
            ).group_by(
                'time_bucket'
            ).order_by(
                'time_bucket'
            ).all()
            
            timeline_data = [{'time': r[0], 'count': r[1]} for r in results]
        except Exception as e:
            current_app.logger.error(f"Analytics Error: {str(e)}")
            timeline_data = []

    # Word Cloud Data (Option Text + Vote Count)
    word_cloud_data = [
        {'text': opt.option_text, 'weight': opt.vote_count} 
        for opt in poll.options if opt.vote_count > 0
    ]

    return jsonify({
        'success': True,
        'timeline': timeline_data,
        'word_cloud': word_cloud_data
    })
