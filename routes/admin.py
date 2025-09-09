"""
Admin routes for database management
"""
from flask import Blueprint, jsonify
import logging

from src.models import db, Account, AuthSession

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.route('/init-db', methods=['POST'])
def init_database():
    """
    Initialize database tables
    
    POST /admin/init-db
    """
    try:
        # Create all database tables
        db.create_all()
        
        # Verify tables were created
        tables_created = []
        
        # Check if Account table exists
        try:
            Account.query.count()
            tables_created.append('accounts')
        except Exception:
            pass
            
        # Check if AuthSession table exists  
        try:
            AuthSession.query.count()
            tables_created.append('auth_sessions')
        except Exception:
            pass
        
        logger.info(f"Database tables created: {tables_created}")
        
        return jsonify({
            'success': True,
            'message': 'Database tables created successfully',
            'tables_created': tables_created
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create database tables',
            'error_details': str(e)
        }), 500

@admin_bp.route('/db-status', methods=['GET'])
def database_status():
    """
    Check database table status
    
    GET /admin/db-status
    """
    try:
        status = {
            'accounts_table': False,
            'auth_sessions_table': False,
            'account_count': 0,
            'session_count': 0
        }
        
        # Check Account table
        try:
            status['account_count'] = Account.query.count()
            status['accounts_table'] = True
        except Exception as e:
            logger.debug(f"Account table check failed: {e}")
        
        # Check AuthSession table
        try:
            status['session_count'] = AuthSession.query.count()
            status['auth_sessions_table'] = True
        except Exception as e:
            logger.debug(f"AuthSession table check failed: {e}")
        
        return jsonify({
            'success': True,
            'database_status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Database status check failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Database status check failed',
            'error_details': str(e)
        }), 500

