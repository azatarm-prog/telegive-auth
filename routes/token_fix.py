"""
Simple token fix endpoint
"""
from flask import Blueprint, jsonify, request
import logging
from src.models import db, Account
from utils.encryption import TokenEncryption

token_fix_bp = Blueprint('token_fix', __name__)
logger = logging.getLogger(__name__)

@token_fix_bp.route('/fix-token/<int:bot_id>', methods=['POST'])
def fix_token(bot_id):
    """
    Fix the token for a specific bot_id
    
    POST /api/fix-token/{bot_id}
    Body: {"token": "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"}
    """
    try:
        logger.info(f"Token fix request for bot_id: {bot_id}")
        
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing token in request body'
            }), 400
        
        new_token = data['token']
        
        # Validate token format
        if not TokenEncryption.verify_token_format(new_token):
            return jsonify({
                'success': False,
                'error': 'Invalid token format'
            }), 400
        
        # Check if bot_id matches token
        token_bot_id = TokenEncryption.extract_bot_id(new_token)
        if token_bot_id != bot_id:
            return jsonify({
                'success': False,
                'error': f'Token bot_id {token_bot_id} does not match requested bot_id {bot_id}'
            }), 400
        
        # Get account
        account = Account.query.filter_by(bot_id=bot_id).first()
        if not account:
            return jsonify({
                'success': False,
                'error': f'Account not found for bot_id {bot_id}'
            }), 404
        
        # Encrypt and store the new token
        encrypted_token = TokenEncryption.encrypt_token(new_token)
        account.bot_token_encrypted = encrypted_token
        db.session.commit()
        
        # Verify the fix worked
        test_decrypted = account.bot_token
        
        response = {
            'success': True,
            'bot_id': bot_id,
            'message': 'Token updated successfully',
            'verification': {
                'decryption_works': test_decrypted == new_token,
                'token_preview': new_token[:20] + '...'
            }
        }
        
        logger.info(f"Token fixed successfully for bot_id: {bot_id}")
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing token for {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Token fix failed',
            'details': str(e)
        }), 500

