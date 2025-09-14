"""
Bot push notification testing route
Provides endpoints to test push notifications to Bot Service
"""
from flask import Blueprint, request, jsonify
import logging
import os

from utils.bot_service_notifier import bot_service_notifier
from src.models import Account

bot_push_bp = Blueprint('bot_push', __name__)
logger = logging.getLogger(__name__)

@bot_push_bp.route('/test-notification', methods=['POST'])
def test_push_notification():
    """
    Test push notification to Bot Service
    
    POST /api/bot/test-notification
    Headers:
        X-Service-Token: service_secret (required for authentication)
    
    Body (optional):
        {
            "bot_id": 262662172
        }
    """
    try:
        logger.info("Bot Service push notification test requested")
        
        # Check service token for authorization
        service_token = request.headers.get('X-Service-Token')
        expected_service_token = os.environ.get('SERVICE_TO_SERVICE_SECRET')
        
        if not service_token or service_token != expected_service_token:
            logger.warning("Push notification test - unauthorized")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid or missing service token'
            }), 401
        
        # Get bot_id from request or use default
        data = request.get_json() or {}
        bot_id = data.get('bot_id', 262662172)
        
        # Get account for testing
        account = Account.query.filter_by(bot_id=bot_id, is_active=True).first()
        
        if not account:
            return jsonify({
                'success': False,
                'message': f'No active account found for bot_id {bot_id}'
            }), 404
        
        # Get bot token
        bot_token = account.bot_token
        
        if not bot_token:
            return jsonify({
                'success': False,
                'message': f'No bot token available for bot_id {bot_id}'
            }), 400
        
        # Test Bot Service connection first
        logger.info("Testing Bot Service connection...")
        connection_ok = bot_service_notifier.test_connection()
        
        if not connection_ok:
            return jsonify({
                'success': False,
                'message': 'Bot Service is not reachable',
                'connection_test': False
            }), 503
        
        # Send push notification
        logger.info(f"Sending push notification for bot_id {bot_id}")
        notification_sent = bot_service_notifier.notify_token_update(
            bot_token=bot_token,
            bot_username=account.bot_username,
            bot_id=bot_id
        )
        
        if notification_sent:
            return jsonify({
                'success': True,
                'message': f'Push notification sent successfully for bot_id {bot_id}',
                'bot_id': bot_id,
                'bot_username': account.bot_username,
                'connection_test': True,
                'notification_sent': True
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Push notification failed for bot_id {bot_id}',
                'bot_id': bot_id,
                'connection_test': True,
                'notification_sent': False
            }), 500
        
    except Exception as e:
        logger.error(f"Push notification test error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bot_push_bp.route('/connection-test', methods=['GET'])
def test_bot_service_connection():
    """
    Test connection to Bot Service
    
    GET /api/bot/connection-test
    Headers:
        X-Service-Token: service_secret (required for authentication)
    """
    try:
        logger.info("Bot Service connection test requested")
        
        # Check service token for authorization
        service_token = request.headers.get('X-Service-Token')
        expected_service_token = os.environ.get('SERVICE_TO_SERVICE_SECRET')
        
        if not service_token or service_token != expected_service_token:
            logger.warning("Connection test - unauthorized")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid or missing service token'
            }), 401
        
        # Test connection
        connection_ok = bot_service_notifier.test_connection()
        
        return jsonify({
            'success': connection_ok,
            'message': 'Bot Service is reachable' if connection_ok else 'Bot Service is not reachable',
            'bot_service_url': bot_service_notifier.bot_service_url,
            'connection_ok': connection_ok
        }), 200 if connection_ok else 503
        
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

