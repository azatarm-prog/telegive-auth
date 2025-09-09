"""
Root routes for the Telegive Auth Service
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
            'auth': '/api/auth/*'
        }
    })

@root_bp.route('/api', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        'service': 'Telegive Authentication Service API',
        'version': '1.0.0',
        'endpoints': {
            'register': 'POST /api/auth/register',
            'login': 'POST /api/auth/login',
            'verify_session': 'GET /api/auth/verify-session',
            'get_account': 'GET /api/auth/account/{account_id}',
            'decrypt_token': 'GET /api/auth/decrypt-token/{account_id}',
            'logout': 'POST /api/auth/logout'
        }
    })

