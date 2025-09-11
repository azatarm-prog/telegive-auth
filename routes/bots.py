"""
Bot management routes for the Telegive Auth Service
Provides v1 API endpoints for bot registration and management
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import logging
import os

from src.models import db, Account, AuthSession
from utils.encryption import TokenEncryption
from utils.telegram_api import TelegramAPI
from utils.validation import InputValidator
from utils.errors import (
    AuthError, ValidationError, TokenError, SessionError, 
    AccountError, handle_error, create_success_response
)

bots_bp = Blueprint('bots', __name__)
logger = logging.getLogger(__name__)

@bots_bp.route('/register', methods=['POST', 'OPTIONS'])
def register_bot():
    """
    Register/authenticate bot (unified endpoint for both new and existing bots)
    
    POST /api/v1/bots/register
    {
        "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
    }
    
    Returns:
    - For new bots: Creates account and returns success
    - For existing bots: Validates token and returns success
    """
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info("Bot registration request received")
        
        # Validate request data
        data = request.get_json()
        if not data:
            logger.warning("Request body is not JSON")
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        bot_token = data.get('bot_token')
        if not bot_token:
            logger.warning("Bot token missing from request")
            return jsonify({'error': 'Bot token is required'}), 400
        
        # Basic token format validation
        if not isinstance(bot_token, str) or ':' not in bot_token:
            logger.warning(f"Invalid bot token format: {bot_token[:10]}...")
            return jsonify({'error': 'Invalid bot token format'}), 400
        
        try:
            bot_id_str = bot_token.split(':')[0]
            if not bot_id_str.isdigit():
                logger.warning("Bot ID is not numeric")
                return jsonify({'error': 'Invalid bot token format'}), 400
            bot_id = int(bot_id_str)
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to extract bot ID: {str(e)}")
            return jsonify({'error': 'Invalid bot token format'}), 400
        
        logger.info(f"Processing bot registration for bot_id: {bot_id}")
        
        # Check if account already exists first (before Telegram API call)
        try:
            existing_account = Account.query.filter_by(bot_id=bot_id).first()
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        
        if existing_account:
            logger.info(f"Found existing account for bot_id: {bot_id}")
            # Existing bot - validate token and return success
            try:
                stored_token = TokenEncryption.decrypt_token(existing_account.bot_token_encrypted)
                if stored_token != bot_token:
                    logger.warning(f"Token mismatch for bot_id: {bot_id}")
                    return jsonify({'error': 'Invalid bot token'}), 400
            except Exception as e:
                logger.error(f"Token decryption failed for bot_id {bot_id}: {str(e)}")
                return jsonify({'error': 'Invalid bot token'}), 400
            
            if not existing_account.is_active:
                logger.warning(f"Account deactivated for bot_id: {bot_id}")
                return jsonify({'error': 'Account is deactivated'}), 403
            
            # Update last login
            try:
                existing_account.update_last_login()
                db.session.commit()
                logger.info(f"Updated last login for bot_id: {bot_id}")
            except Exception as e:
                logger.error(f"Failed to update last login: {str(e)}")
                # Don't fail the request for this
            
            return jsonify({
                'message': 'Bot registered successfully',
                'bot_id': str(bot_id),
                'access_token': f"auth_{existing_account.id}_{bot_id}"
            }), 200
        
        else:
            logger.info(f"New bot registration for bot_id: {bot_id}")
            # New bot - validate with Telegram API
            try:
                telegram_api = TelegramAPI()
                validation_result = telegram_api.validate_bot_token(bot_token)
                
                if not validation_result['success']:
                    logger.warning(f"Telegram API validation failed: {validation_result.get('error')}")
                    return jsonify({'error': validation_result.get('error', 'Bot token validation failed')}), 400
                
                bot_info = validation_result['bot_info']
                logger.info(f"Telegram API validation successful for bot: {bot_info.get('username', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Telegram API validation error: {str(e)}")
                return jsonify({'error': 'Failed to validate bot token with Telegram'}), 500
            
            # Create new account
            try:
                encrypted_token = TokenEncryption.encrypt_token(bot_token)
                
                account = Account(
                    bot_token_encrypted=encrypted_token,
                    bot_id=bot_id,
                    bot_username=bot_info.get('username', ''),
                    bot_name=bot_info.get('first_name', 'Unknown Bot')
                )
                
                db.session.add(account)
                db.session.commit()
                
                logger.info(f"New account created for bot_id: {bot_id}, username: {account.bot_username}")
                
                return jsonify({
                    'message': 'Bot registered successfully',
                    'bot_id': str(bot_id),
                    'access_token': f"auth_{account.id}_{bot_id}"
                }), 200
                
            except Exception as e:
                logger.error(f"Failed to create account: {str(e)}")
                try:
                    db.session.rollback()
                except:
                    pass
                return jsonify({'error': 'Failed to create account'}), 500
        
    except Exception as e:
        logger.error(f"Unexpected error during bot registration: {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': 'Internal server error'}), 500

@bots_bp.route('/validate/<int:bot_id>', methods=['GET'])
def validate_bot(bot_id):
    """
    Validate bot exists and is active
    
    GET /api/v1/bots/validate/{bot_id}
    """
    try:
        account = Account.query.filter_by(bot_id=bot_id).first()
        if not account:
            return jsonify({'error': 'Bot not found'}), 404
        
        if not account.is_active:
            return jsonify({'error': 'Bot is inactive'}), 403
        
        return jsonify({
            'valid': True,
            'bot_id': str(bot_id),
            'bot_username': account.bot_username,
            'bot_name': account.bot_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating bot {bot_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@bots_bp.route('/token/<int:bot_id>', methods=['GET'])
def get_bot_token(bot_id):
    """
    Get decrypted bot token for API calls
    
    GET /api/v1/bots/token/{bot_id}
    Headers:
        X-Service-Token: service_secret (for service-to-service calls)
    """
    try:
        # Check service token for authorization
        service_token = request.headers.get('X-Service-Token')
        expected_token = os.environ.get('SERVICE_TO_SERVICE_SECRET')
        
        if not service_token or service_token != expected_token:
            return jsonify({'error': 'Unauthorized'}), 401
        
        account = Account.query.filter_by(bot_id=bot_id).first()
        if not account:
            return jsonify({'error': 'Bot not found'}), 404
        
        if not account.is_active:
            return jsonify({'error': 'Bot is inactive'}), 403
        
        # Decrypt token
        decrypted_token = TokenEncryption.decrypt_token(account.bot_token_encrypted)
        
        # Update last bot check
        account.update_bot_check()
        db.session.commit()
        
        return jsonify({
            'bot_token': decrypted_token,
            'bot_id': str(bot_id)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting token for bot {bot_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# Error handlers for the blueprint
@bots_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@bots_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@bots_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@bots_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

