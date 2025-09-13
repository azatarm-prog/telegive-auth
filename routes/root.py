"""
Root routes for the Telegive Auth Service
Updated to trigger redeploy with SQLAlchemy fix
"""
from flask import Blueprint, jsonify

root_bp = Blueprint('root', __name__)

@root_bp.route('/', methods=['GET'])
def index():
    """Root endpoint with service information"""
    return jsonify({
        'service': 'Telegive Authentication Service',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'auth': '/api/auth/*',
            'bots_v1': '/api/v1/bots/*',
            'accounts': '/api/accounts/*'
        }
    })

@root_bp.route('/api', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        'service': 'Telegive Authentication Service API',
        'version': '1.0.0',
        'endpoints': {
            'bot_register': 'POST /api/v1/bots/register',
            'bot_validate': 'GET /api/v1/bots/validate/{bot_id}',
            'bot_token': 'GET /api/v1/bots/token/{bot_id}',
            'account_get': 'GET /api/accounts/{account_id}',
            'account_validate': 'GET /api/accounts/{account_id}/validate',
            'account_info': 'GET /api/accounts/{account_id}/info',
            'account_list': 'GET /api/accounts/list',
            'register': 'POST /api/auth/register',
            'login': 'POST /api/auth/login',
            'verify_session': 'GET /api/auth/verify-session',
            'get_account': 'GET /api/auth/account/{account_id}',
            'decrypt_token': 'GET /api/auth/decrypt-token/{account_id}',
            'logout': 'POST /api/auth/logout'
        }
    })

