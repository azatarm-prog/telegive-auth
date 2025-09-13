"""
Account management routes for service integration
Provides endpoints for other services to validate and retrieve account information
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import logging

from src.models import db, Account, AuthSession
from utils.validation import InputValidator
from utils.errors import (
    AuthError, ValidationError, AccountError, 
    handle_error, create_success_response
)

accounts_bp = Blueprint('accounts', __name__)
logger = logging.getLogger(__name__)

@accounts_bp.route('/<int:account_id>', methods=['GET'])
def get_account_by_id(account_id):
    """
    Get account information by account ID
    
    GET /api/accounts/{account_id}
    """
    try:
        logger.info(f"Account lookup request for ID: {account_id}")
        
        # Find account by bot_id (which is used as account_id in other services)
        account = Account.query.filter_by(bot_id=account_id).first()
        
        if not account:
            logger.warning(f"Account not found for ID: {account_id}")
            return jsonify({
                'success': False,
                'code': 'ACCOUNT_NOT_FOUND',
                'error': 'Account not found or invalid'
            }), 404
        
        if not account.is_active:
            logger.warning(f"Account inactive for ID: {account_id}")
            return jsonify({
                'success': False,
                'code': 'ACCOUNT_INACTIVE',
                'error': 'Account is inactive'
            }), 403
        
        logger.info(f"Account found for ID: {account_id}, username: {account.bot_username}")
        
        return jsonify({
            'success': True,
            'account': {
                'id': account.bot_id,
                'bot_id': account.bot_id,
                'username': account.bot_username,
                'name': account.bot_name,
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'updated_at': account.updated_at.isoformat() if account.updated_at else None,
                'last_login': account.last_login.isoformat() if account.last_login else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving account {account_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@accounts_bp.route('/<int:account_id>/validate', methods=['GET'])
def validate_account(account_id):
    """
    Validate account exists and is active
    
    GET /api/accounts/{account_id}/validate
    """
    try:
        logger.info(f"Account validation request for ID: {account_id}")
        
        # Find account by bot_id
        account = Account.query.filter_by(bot_id=account_id).first()
        
        if not account:
            logger.warning(f"Account validation failed - not found: {account_id}")
            return jsonify({
                'success': False,
                'valid': False,
                'code': 'ACCOUNT_NOT_FOUND',
                'error': 'Account not found in database'
            }), 404
        
        if not account.is_active:
            logger.warning(f"Account validation failed - inactive: {account_id}")
            return jsonify({
                'success': False,
                'valid': False,
                'code': 'ACCOUNT_INACTIVE',
                'error': 'Account is inactive'
            }), 403
        
        logger.info(f"Account validation successful for ID: {account_id}")
        
        return jsonify({
            'success': True,
            'valid': True,
            'account': {
                'id': account.bot_id,
                'username': account.bot_username,
                'name': account.bot_name,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'updated_at': account.updated_at.isoformat() if account.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating account {account_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'valid': False,
            'error': 'Database error'
        }), 500

@accounts_bp.route('/<int:account_id>/info', methods=['GET'])
def get_account_info(account_id):
    """
    Get detailed account information for service integration
    
    GET /api/accounts/{account_id}/info
    """
    try:
        logger.info(f"Account info request for ID: {account_id}")
        
        # Find account by bot_id
        account = Account.query.filter_by(bot_id=account_id).first()
        
        if not account:
            logger.warning(f"Account info failed - not found: {account_id}")
            return jsonify({
                'success': False,
                'code': 'ACCOUNT_NOT_FOUND',
                'error': 'Account not found'
            }), 404
        
        # Get active sessions count
        active_sessions = AuthSession.query.filter_by(
            account_id=account.id,
            is_active=True
        ).count()
        
        logger.info(f"Account info retrieved for ID: {account_id}")
        
        return jsonify({
            'success': True,
            'account': {
                'id': account.bot_id,
                'bot_id': account.bot_id,
                'username': account.bot_username,
                'name': account.bot_name,
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'updated_at': account.updated_at.isoformat() if account.updated_at else None,
                'last_login': account.last_login.isoformat() if account.last_login else None,
                'last_bot_check': account.last_bot_check.isoformat() if account.last_bot_check else None,
                'active_sessions': active_sessions
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting account info {account_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@accounts_bp.route('/list', methods=['GET'])
def list_accounts():
    """
    List all accounts (for debugging/admin purposes)
    
    GET /api/accounts/list
    """
    try:
        logger.info("Account list request")
        
        # Get all accounts
        accounts = Account.query.order_by(Account.created_at.desc()).limit(50).all()
        
        account_list = []
        for account in accounts:
            account_list.append({
                'id': account.bot_id,
                'username': account.bot_username,
                'name': account.bot_name,
                'is_active': account.is_active,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'last_login': account.last_login.isoformat() if account.last_login else None
            })
        
        logger.info(f"Account list retrieved: {len(account_list)} accounts")
        
        return jsonify({
            'success': True,
            'accounts': account_list,
            'total': len(account_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing accounts: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Error handlers for the blueprint
@accounts_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

@accounts_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found'
    }), 404

@accounts_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

