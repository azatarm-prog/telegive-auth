"""
Authentication routes for the Telegive Auth Service
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
import logging

from src.models import db, Account, AuthSession
from utils.encryption import TokenEncryption
from utils.telegram_api import TelegramAPI
from utils.validation import InputValidator
from utils.errors import (
    AuthError, ValidationError, TokenError, SessionError, 
    AccountError, handle_error, create_success_response
)

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new bot account
    
    POST /api/auth/register
    {
        "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
    }
    """
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
            raise AccountError("Account with this bot already exists", "ACCOUNT_EXISTS")
        
        # Encrypt the bot token
        encrypted_token = TokenEncryption.encrypt_token(bot_token)
        
        # Create new account
        account = Account(
            bot_token_encrypted=encrypted_token,
            bot_id=bot_id,
            bot_username=bot_info.get('username', ''),
            bot_name=bot_info.get('first_name', 'Unknown Bot')
        )
        
        db.session.add(account)
        db.session.commit()
        
        logger.info(f"New account registered: bot_id={bot_id}, username={account.bot_username}")
        
        return jsonify(create_success_response({
            'account_id': account.id,
            'bot_info': {
                'id': bot_info['id'],
                'username': bot_info.get('username', ''),
                'first_name': bot_info.get('first_name', '')
            },
            'requires_channel_setup': not account.channel_verified
        })), 201
        
    except AuthError as e:
        logger.warning(f"Registration failed: {e.message}")
        response, status_code = handle_error(e)
        return jsonify(response), status_code
    
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        response, status_code = handle_error(e)
        return jsonify(response), status_code

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and create session
    
    POST /api/auth/login
    {
        "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            raise ValidationError("Request body must be JSON")
        
        validated_data = InputValidator.validate_login_data(data)
        bot_token = validated_data['bot_token']
        
        # Extract bot ID from token to find account
        try:
            bot_id = int(bot_token.split(':')[0])
        except (ValueError, IndexError):
            raise TokenError("Invalid bot token format", "INVALID_CREDENTIALS")
        
        # Find account by bot_id
        account = Account.query.filter_by(bot_id=bot_id).first()
        if not account:
            raise TokenError("Invalid bot token", "INVALID_CREDENTIALS")
        
        # Verify the token by decrypting stored token and comparing
        try:
            stored_token = TokenEncryption.decrypt_token(account.bot_token_encrypted)
            if stored_token != bot_token:
                raise TokenError("Invalid bot token", "INVALID_CREDENTIALS")
        except Exception:
            raise TokenError("Invalid bot token", "INVALID_CREDENTIALS")
        
        if not account.is_active:
            raise AccountError("Account is deactivated", "ACCOUNT_DEACTIVATED")
        
        # Create new session
        session_id = TokenEncryption.generate_session_id()
        auth_session = AuthSession(session_id=session_id, account_id=account.id)
        
        db.session.add(auth_session)
        
        # Update last login timestamp
        account.update_last_login()
        
        db.session.commit()
        
        # Set session cookie
        session['session_id'] = session_id
        session['account_id'] = account.id
        session.permanent = True
        
        logger.info(f"User logged in: account_id={account.id}, session_id={session_id}")
        
        return jsonify(create_success_response({
            'session_id': session_id,
            'account_info': account.to_public_dict()
        })), 200
        
    except AuthError as e:
        logger.warning(f"Login failed: {e.message}")
        response, status_code = handle_error(e)
        return jsonify(response), status_code
    
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        response, status_code = handle_error(e)
        return jsonify(response), status_code

@auth_bp.route('/verify-session', methods=['GET'])
def verify_session():
    """
    Verify session validity
    
    GET /api/auth/verify-session
    Headers: 
        Cookie: session=sess_abc123 OR
        Authorization: Bearer sess_abc123
    """
    try:
        # Get session ID from cookie or Authorization header
        session_id = session.get('session_id')
        
        # If not in cookie, check Authorization header
        if not session_id:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                session_id = auth_header[7:]  # Remove 'Bearer ' prefix
        
        if not session_id:
            raise SessionError("No session found", "NO_SESSION")
        
        # Validate session ID format
        InputValidator.validate_session_id(session_id)
        
        # Get valid session
        auth_session = AuthSession.get_valid_session(session_id)
        if not auth_session:
            # Clear invalid session
            session.clear()
            raise SessionError("Invalid or expired session", "INVALID_SESSION")
        
        # Get account information
        account = Account.query.get(auth_session.account_id)
        if not account or not account.is_active:
            # Clear session for inactive account
            session.clear()
            auth_session.invalidate()
            raise AccountError("Account not found or inactive", "ACCOUNT_INACTIVE")
        
        return jsonify({
            'valid': True,
            'account_id': account.id,
            'account_info': account.to_public_dict()
        }), 200
        
    except AuthError as e:
        logger.warning(f"Session verification failed: {e.message}")
        return jsonify({
            'valid': False,
            'error': e.message,
            'error_code': e.error_code
        }), e.status_code
    
    except Exception as e:
        logger.error(f"Unexpected error during session verification: {str(e)}", exc_info=True)
        return jsonify({
            'valid': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/account/<int:account_id>', methods=['GET'])
def get_account(account_id):
    """
    Get account information
    
    GET /api/auth/account/{account_id}
    """
    try:
        # Validate account ID
        account_id = InputValidator.validate_account_id(account_id)
        
        # Get account
        account = Account.query.get(account_id)
        if not account:
            raise AccountError("Account not found", "ACCOUNT_NOT_FOUND")
        
        return jsonify(create_success_response({
            'account': account.to_dict()
        })), 200
        
    except AuthError as e:
        logger.warning(f"Get account failed: {e.message}")
        response, status_code = handle_error(e)
        return jsonify(response), status_code
    
    except Exception as e:
        logger.error(f"Unexpected error getting account: {str(e)}", exc_info=True)
        response, status_code = handle_error(e)
        return jsonify(response), status_code

@auth_bp.route('/decrypt-token/<int:account_id>', methods=['GET'])
def decrypt_token(account_id):
    """
    Get decrypted bot token for API calls
    
    GET /api/auth/decrypt-token/{account_id}
    """
    try:
        # Validate account ID
        account_id = InputValidator.validate_account_id(account_id)
        
        # Get account
        account = Account.query.get(account_id)
        if not account:
            raise AccountError("Account not found", "ACCOUNT_NOT_FOUND")
        
        if not account.is_active:
            raise AccountError("Account is inactive", "ACCOUNT_INACTIVE")
        
        # Decrypt token
        decrypted_token = TokenEncryption.decrypt_token(account.bot_token_encrypted)
        
        # Update last bot check timestamp
        account.update_bot_check()
        
        logger.info(f"Token decrypted for account_id={account_id}")
        
        return jsonify(create_success_response({
            'bot_token': decrypted_token
        })), 200
        
    except AuthError as e:
        logger.warning(f"Token decryption failed: {e.message}")
        response, status_code = handle_error(e)
        return jsonify(response), status_code
    
    except Exception as e:
        logger.error(f"Unexpected error decrypting token: {str(e)}", exc_info=True)
        response, status_code = handle_error(e)
        return jsonify(response), status_code

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Invalidate session
    
    POST /api/auth/logout
    """
    try:
        # Get session ID from cookie
        session_id = session.get('session_id')
        if session_id:
            # Invalidate session in database
            auth_session = AuthSession.query.filter_by(session_id=session_id).first()
            if auth_session:
                auth_session.invalidate()
                db.session.commit()
        
        # Clear session cookie
        session.clear()
        
        logger.info(f"User logged out: session_id={session_id}")
        
        return jsonify(create_success_response(
            message="Logged out successfully"
        )), 200
        
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}", exc_info=True)
        response, status_code = handle_error(e)
        return jsonify(response), status_code

# Error handlers for the blueprint
@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'error_code': 'BAD_REQUEST'
    }), 400

@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'error_code': 'UNAUTHORIZED'
    }), 401

@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'error_code': 'NOT_FOUND'
    }), 404

@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500

