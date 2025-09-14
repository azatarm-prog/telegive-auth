"""
Main Flask application for Telegive Authentication Service
"""
import os
import sys
import logging
import logging.handlers
from datetime import timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import configurations
from config.settings import config

# Import models and database
from src.models import db, Account, AuthSession

# Import routes
from routes.auth import auth_bp
from routes.health import health_bp

def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app
    
    Args:
        config_name (str): Configuration name to use
        
    Returns:
        Flask: Configured Flask application
    """
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    # Handle case where config_name might not exist in config dict
    if config_name not in config:
        config_name = 'production'
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Set up logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def init_extensions(app):
    """Initialize Flask extensions"""
    
    # Initialize database
    db.init_app(app)
    
    # Initialize CORS for cross-origin requests
    CORS(app, 
         origins=app.config.get('CORS_ORIGINS', ['*']),
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Service-Name', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         expose_headers=['Content-Type', 'Authorization'])
    
    # TODO: Add rate limiting back later - temporarily disabled to fix deployment
    # Initialize rate limiter with proper syntax
    # limiter = Limiter(
    #     app=app,
    #     key_func=get_remote_address,
    #     storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://'),
    #     default_limits=["1000 per hour"]
    # )
    
    # Apply rate limits to specific endpoints - temporarily disabled
    # limiter.limit("5 per minute")(auth_bp, methods=['POST'], endpoint='register')
    # limiter.limit("10 per minute")(auth_bp, methods=['POST'], endpoint='login')
    # limiter.limit("100 per minute")(auth_bp, methods=['GET'], endpoint='verify_session')
    # limiter.limit("50 per minute")(auth_bp, methods=['GET'], endpoint='decrypt_token')
    
    # Store limiter in app for access in routes if needed - temporarily disabled
    # app.limiter = limiter

def register_blueprints(app):
    """Register Flask blueprints"""
    
    # Register root routes
    from routes.root import root_bp
    app.register_blueprint(root_bp)
    
    # Register authentication routes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Register v1 bots routes
    from routes.bots import bots_bp
    app.register_blueprint(bots_bp, url_prefix='/api/v1/bots')
    
    # Register accounts routes for service integration
    from routes.accounts import accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
    
    # Register database info routes for service coordination
    from routes.database_info import database_info_bp
    app.register_blueprint(database_info_bp, url_prefix='/api')
    
    # Register debug routes for troubleshooting
    from routes.debug_account import debug_account_bp
    app.register_blueprint(debug_account_bp, url_prefix='/api')
    
    # Register SQL debug routes for Channel Service coordination
    from routes.sql_debug import sql_debug_bp
    app.register_blueprint(sql_debug_bp, url_prefix='/api')
    
    # Register token fix route
    from routes.token_fix import token_fix_bp
    app.register_blueprint(token_fix_bp, url_prefix='/api')
    
    # Register emergency token fix route
    from routes.emergency_token_fix import emergency_fix_bp
    app.register_blueprint(emergency_fix_bp, url_prefix='/api')
    
    # Register health check routes (no prefix for /health)
    app.register_blueprint(health_bp)
    
    # Register admin routes
    from routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

def setup_logging(app):
    """Set up application logging"""
    
    if not app.debug and not app.testing:
        # Production logging setup
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/auth_service.log', maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Telegive Auth Service startup')

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'error_code': 'BAD_REQUEST'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'error_code': 'UNAUTHORIZED'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'error_code': 'FORBIDDEN'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not found',
            'error_code': 'NOT_FOUND'
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded',
            'error_code': 'RATE_LIMIT_EXCEEDED'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', app.config.get('SERVICE_PORT', 8001)))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )

