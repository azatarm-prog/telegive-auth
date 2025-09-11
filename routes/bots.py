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
        # Validate request data
        data = request.get_json()
        if not data:
            raise ValidationError("Request body must be JSON")
        
        validated_data = InputValidator.validate_registration_data(data)
        bot_token = validated_data['bot_token']
        
        # Validate token with Telegram API
        telegram_api = TelegramAPI()
        validation_result = telegram_api.validate_bot_token(bot_token)
        
        if not validation_result['success']:
            raise TokenError(
                validation_result['error'], 
                validation_result['error_code']
            )
        
        bot_info = validation_result['bot_info']
        bot_id = bot_info['id']
        
        # Check if account already exists
        existing_account = Account.query.filter_by(bot_id=bot_id).first()
        
        if existing_account:
            # Existing bot - validate token and return success
            try:
                stored_token = TokenEncryption.decrypt_token(existing_account.bot_token_encrypted)
                if stored_token != bot_token:
                    raise TokenError("Invalid bot token", "INVALID_TOKEN")
            except Exception:
                raise TokenError("Invalid bot token", "INVALID_TOKEN")
            
            if not existing_account.is_active:
                raise AccountError("Account is deactivated", "ACCOUNT_DEACTIVATED")
            
            # Update last login
            existing_account.update_last_login()
            db.session.commit()
            
            logger.info(f"Existing bot authenticated: bot_id={bot_id}, username={existing_account.bot_username}")
            
            return jsonify({
                'message': 'Bot registered successfully',
                'bot_id': str(bot_id),
                'access_token': f"auth_{existing_account.id}_{bot_id}"
            }), 200
        
        else:
            # New bot - create account
            encrypted_token = TokenEncryption.encrypt_token(bot_token)
            
            account = Account(
                bot_token_encrypted=encrypted_token,
                bot_id=bot_id,
                bot_username=bot_info.get('username', ''),
                bot_name=bot_info.get('first_name', 'Unknown Bot')
            )
            
            db.session.add(account)
            db.session.commit()
            
            logger.info(f"New bot registered: bot_id={bot_id}, username={account.bot_username}")
            
            return jsonify({
                'message': 'Bot registered successfully',
                'bot_id': str(bot_id),
                'access_token': f"auth_{account.id}_{bot_id}"
            }), 200
        
    except AuthError as e:
        logger.warning(f"Bot registration failed: {e.message}")
        return jsonify({'error': e.message}), e.status_code
    
    except Exception as e:
        logger.error(f"Unexpected error during bot registration: {str(e)}", exc_info=True)
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

