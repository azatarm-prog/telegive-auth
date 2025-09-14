"""
Emergency token fix route - simple and direct
"""
from flask import Blueprint, jsonify
import logging
from src.models import db, Account
from utils.encryption import TokenEncryption

emergency_fix_bp = Blueprint('emergency_fix', __name__)
logger = logging.getLogger(__name__)

@emergency_fix_bp.route('/emergency-fix-token-262662172', methods=['GET'])
def emergency_fix_token():
    """
    Emergency fix for bot_id 262662172 token
    
    GET /api/emergency-fix-token-262662172
    """
    try:
        logger.info("Emergency token fix request for bot_id 262662172")
        
        # The correct working token
        correct_token = "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"
        bot_id = 262662172
        
        # Get account
        account = Account.query.filter_by(bot_id=bot_id).first()
        
        if not account:
            return jsonify({
                'success': False,
                'error': f'Account not found for bot_id {bot_id}'
            }), 404
        
        # Store old token info
        old_encrypted = account.bot_token_encrypted
        old_encrypted_preview = old_encrypted[:50] + '...' if old_encrypted else None
        
        # Try to decrypt old token
        try:
            old_decrypted = TokenEncryption.decrypt_token(old_encrypted)
            old_decryption_worked = True
        except:
            old_decrypted = None
            old_decryption_worked = False
        
        # Encrypt the correct token
        new_encrypted = TokenEncryption.encrypt_token(correct_token)
        
        # Update the database
        account.bot_token_encrypted = new_encrypted
        db.session.commit()
        
        # Verify the fix worked
        updated_account = Account.query.filter_by(bot_id=bot_id).first()
        
        # Test the property
        try:
            property_token = updated_account.bot_token
            property_works = property_token == correct_token
        except Exception as e:
            property_token = None
            property_works = False
        
        response = {
            'success': True,
            'bot_id': bot_id,
            'message': 'Emergency token fix completed',
            'before_fix': {
                'encrypted_preview': old_encrypted_preview,
                'decryption_worked': old_decryption_worked,
                'decrypted_token': old_decrypted[:20] + '...' if old_decrypted else None
            },
            'after_fix': {
                'new_encrypted_preview': new_encrypted[:50] + '...',
                'property_token_preview': property_token[:20] + '...' if property_token else None,
                'property_works': property_works,
                'fix_successful': property_works
            },
            'next_steps': [
                'Test Channel Service with account_id 262662172',
                'Should no longer get INVALID_BOT_TOKEN error',
                'Channel verification should work now'
            ]
        }
        
        logger.info(f"Emergency token fix completed for bot_id: {bot_id}, success: {property_works}")
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Emergency token fix failed: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Emergency token fix failed',
            'details': str(e)
        }), 500

