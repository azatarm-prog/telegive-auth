"""
Bot token endpoint for Bot Service integration
Provides current Telegram bot token to Bot Service for dynamic token management
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import logging
import os

# Import models directly
from src.models import db, Account

bot_token_bp = Blueprint('bot_token', __name__)
logger = logging.getLogger(__name__)

@bot_token_bp.route('/token', methods=['GET'])
def get_bot_token():
    """
    Get current bot token for Bot Service
    
    GET /api/bot/token
    Headers:
        X-Service-Token: service_secret (required for authentication)
    
    Returns:
        200: Bot token data or not_configured status
        401: Unauthorized (invalid service token)
        500: Internal server error
    """
    try:
        logger.info("Bot Service token request received")
        
        # Check service token for authorization
        service_token = request.headers.get('X-Service-Token')
        expected_service_token = os.environ.get('SERVICE_TO_SERVICE_SECRET')
        
        if not service_token or service_token != expected_service_token:
            logger.warning("Bot Service token request - unauthorized")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid or missing service token'
            }), 401
        
        logger.info("Bot Service token request - authenticated")
        
        # Get the most recently active account (assuming this is the current bot)
        # You may need to adjust this query based on your specific requirements
        account = Account.query.filter_by(is_active=True).order_by(Account.last_login_at.desc()).first()
        
        if not account:
            logger.info("No active bot account found")
            return jsonify({
                'bot_token': None,
                'status': 'not_configured',
                'message': 'No bot token configured by admin'
            }), 200
        
        # Get decrypted bot token
        bot_token = account.bot_token
        
        if not bot_token:
            logger.warning(f"Bot token decryption failed for account {account.bot_id}")
            return jsonify({
                'bot_token': None,
                'status': 'not_configured',
                'message': 'Bot token not available or decryption failed'
            }), 200
        
        logger.info(f"Bot token provided for account {account.bot_id}")
        
        # Update last bot check timestamp
        account.update_bot_check()
        db.session.commit()
        
        return jsonify({
            'bot_token': bot_token,
            'status': 'active',
            'updated_at': account.last_bot_check_at.isoformat() if account.last_bot_check_at else datetime.utcnow().isoformat(),
            'bot_username': account.bot_username,
            'bot_id': account.bot_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving bot token: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve bot token',
            'details': str(e)
        }), 500

# Error handlers for the blueprint
@bot_token_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad request',
        'message': 'Invalid request format'
    }), 400

@bot_token_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Invalid or missing service token'
    }), 401

@bot_token_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'Failed to retrieve bot token'
    }), 500

