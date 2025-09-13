"""
Token debug routes for verifying token storage and decryption
"""
from flask import Blueprint, jsonify
import logging
from src.models import db, Account
from utils.encryption import decrypt_token, encrypt_token

token_debug_bp = Blueprint('token_debug', __name__)
logger = logging.getLogger(__name__)

@token_debug_bp.route('/token-debug/verify/<int:bot_id>', methods=['GET'])
def verify_token_storage(bot_id):
    """
    Verify token storage and decryption for a specific bot_id
    
    GET /api/token-debug/verify/{bot_id}
    """
    try:
        logger.info(f"Token verification request for bot_id: {bot_id}")
        
        # Get account
        account = Account.query.filter_by(bot_id=bot_id).first()
        
        if not account:
            return jsonify({
                'success': False,
                'error': f'Account not found for bot_id {bot_id}'
            }), 404
        
        # Check encrypted token
        encrypted_token = account.bot_token_encrypted
        
        if not encrypted_token:
            return jsonify({
                'success': False,
                'error': 'No encrypted token found',
                'bot_id': bot_id,
                'database_id': account.id
            }), 404
        
        # Try to decrypt the token
        try:
            decrypted_token = decrypt_token(encrypted_token)
            decryption_success = True
            decryption_error = None
        except Exception as e:
            decrypted_token = None
            decryption_success = False
            decryption_error = str(e)
        
        # Check token format
        token_format_valid = False
        if decrypted_token:
            # Bot tokens should be in format: bot_id:token_string
            expected_prefix = f"{bot_id}:"
            token_format_valid = decrypted_token.startswith(expected_prefix)
        
        # Test the property
        try:
            property_token = account.bot_token
            property_success = True
            property_error = None
        except Exception as e:
            property_token = None
            property_success = False
            property_error = str(e)
        
        response = {
            'success': True,
            'bot_id': bot_id,
            'database_id': account.id,
            'token_analysis': {
                'encrypted_token_exists': encrypted_token is not None,
                'encrypted_token_length': len(encrypted_token) if encrypted_token else 0,
                'encrypted_token_preview': encrypted_token[:50] + '...' if encrypted_token else None,
                'decryption_success': decryption_success,
                'decryption_error': decryption_error,
                'decrypted_token_preview': decrypted_token[:20] + '...' if decrypted_token else None,
                'token_format_valid': token_format_valid,
                'expected_format': f'{bot_id}:XXXXXXXXXX',
                'property_access_success': property_success,
                'property_error': property_error,
                'property_token_preview': property_token[:20] + '...' if property_token else None
            },
            'recommendations': []
        }
        
        # Add recommendations based on findings
        if not decryption_success:
            response['recommendations'].append('Fix token decryption - encrypted token cannot be decrypted')
        
        if decryption_success and not token_format_valid:
            response['recommendations'].append(f'Fix token format - should start with {bot_id}:')
        
        if not property_success:
            response['recommendations'].append('Fix bot_token property - property access failing')
        
        if decryption_success and token_format_valid and property_success:
            response['recommendations'].append('Token storage appears correct - check Telegram API validation')
        
        logger.info(f"Token verification completed for bot_id: {bot_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error verifying token for {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Token verification failed',
            'details': str(e),
            'bot_id': bot_id
        }), 500

@token_debug_bp.route('/token-debug/update/<int:bot_id>', methods=['POST'])
def update_token_for_bot(bot_id):
    """
    Update the bot token for a specific bot_id with the correct token
    
    POST /api/token-debug/update/{bot_id}
    Body: {"token": "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"}
    """
    try:
        from flask import request
        
        logger.info(f"Token update request for bot_id: {bot_id}")
        
        # Get the new token from request
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing token in request body',
                'expected_format': '{"token": "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"}'
            }), 400
        
        new_token = data['token']
        
        # Validate token format
        expected_prefix = f"{bot_id}:"
        if not new_token.startswith(expected_prefix):
            return jsonify({
                'success': False,
                'error': f'Invalid token format. Must start with {expected_prefix}',
                'provided_token': new_token[:20] + '...'
            }), 400
        
        # Get account
        account = Account.query.filter_by(bot_id=bot_id).first()
        
        if not account:
            return jsonify({
                'success': False,
                'error': f'Account not found for bot_id {bot_id}'
            }), 404
        
        # Store old token for comparison
        old_encrypted = account.bot_token_encrypted
        
        # Encrypt and store the new token
        try:
            encrypted_new_token = encrypt_token(new_token)
            account.bot_token_encrypted = encrypted_new_token
            db.session.commit()
            
            # Verify the update worked
            updated_account = Account.query.filter_by(bot_id=bot_id).first()
            verification_token = updated_account.bot_token
            
            response = {
                'success': True,
                'bot_id': bot_id,
                'database_id': account.id,
                'update_details': {
                    'old_encrypted_preview': old_encrypted[:50] + '...' if old_encrypted else None,
                    'new_encrypted_preview': encrypted_new_token[:50] + '...',
                    'new_token_preview': new_token[:20] + '...',
                    'verification_token_preview': verification_token[:20] + '...' if verification_token else None,
                    'update_successful': verification_token == new_token
                },
                'next_steps': [
                    'Test Channel Service with updated token',
                    'Verify Telegram API calls work',
                    'Check channel verification functionality'
                ]
            }
            
            logger.info(f"Token updated successfully for bot_id: {bot_id}")
            return jsonify(response), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating token for {bot_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to update token',
                'details': str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Error in token update for {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Token update failed',
            'details': str(e),
            'bot_id': bot_id
        }), 500

@token_debug_bp.route('/token-debug/test-encryption', methods=['POST'])
def test_encryption():
    """
    Test encryption/decryption with a sample token
    
    POST /api/token-debug/test-encryption
    Body: {"token": "262662172:AAGyAYVzuFFe23GagWY-FnP2NlAQRy_JsRk"}
    """
    try:
        from flask import request
        
        logger.info("Encryption test request")
        
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing token in request body'
            }), 400
        
        test_token = data['token']
        
        # Test encryption
        try:
            encrypted = encrypt_token(test_token)
            encryption_success = True
            encryption_error = None
        except Exception as e:
            encrypted = None
            encryption_success = False
            encryption_error = str(e)
        
        # Test decryption
        decryption_success = False
        decryption_error = None
        decrypted = None
        
        if encryption_success:
            try:
                decrypted = decrypt_token(encrypted)
                decryption_success = True
                round_trip_success = decrypted == test_token
            except Exception as e:
                decryption_success = False
                decryption_error = str(e)
                round_trip_success = False
        else:
            round_trip_success = False
        
        response = {
            'success': True,
            'test_results': {
                'original_token': test_token[:20] + '...',
                'encryption_success': encryption_success,
                'encryption_error': encryption_error,
                'encrypted_preview': encrypted[:50] + '...' if encrypted else None,
                'decryption_success': decryption_success,
                'decryption_error': decryption_error,
                'decrypted_preview': decrypted[:20] + '...' if decrypted else None,
                'round_trip_success': round_trip_success
            }
        }
        
        logger.info("Encryption test completed")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in encryption test: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Encryption test failed',
            'details': str(e)
        }), 500

