"""
Database information routes for service coordination
Provides database connection and schema information for other services
"""
from flask import Blueprint, jsonify
import logging
import os
from sqlalchemy import text, inspect
from src.models import db, Account

database_info_bp = Blueprint('database_info', __name__)
logger = logging.getLogger(__name__)

@database_info_bp.route('/database/info', methods=['GET'])
def get_database_info():
    """
    Get database connection information for service coordination
    
    GET /api/database/info
    """
    try:
        logger.info("Database info request")
        
        # Get database connection info
        engine = db.engine
        url = str(engine.url)
        
        # Parse database URL safely (mask sensitive info)
        if url.startswith('postgresql://'):
            # Extract components safely
            parts = url.replace('postgresql://', '').split('/')
            host_port = parts[0].split('@')[-1] if '@' in parts[0] else parts[0]
            database_name = parts[1].split('?')[0] if len(parts) > 1 else 'unknown'
            
            if ':' in host_port:
                host, port = host_port.split(':')
            else:
                host, port = host_port, '5432'
        else:
            host, port, database_name = 'unknown', 'unknown', 'unknown'
        
        # Get database version and current user
        try:
            with db.engine.connect() as conn:
                version_result = conn.execute(text("SELECT version()")).fetchone()
                user_result = conn.execute(text("SELECT current_user")).fetchone()
                db_result = conn.execute(text("SELECT current_database()")).fetchone()
                
                postgres_version = version_result[0] if version_result else 'unknown'
                current_user = user_result[0] if user_result else 'unknown'
                current_db = db_result[0] if db_result else 'unknown'
        except Exception as query_error:
            logger.warning(f"Could not get database details: {str(query_error)}")
            postgres_version = 'unknown'
            current_user = 'unknown'
            current_db = database_name
        
        response = {
            'success': True,
            'database': {
                'host': host,
                'port': port,
                'database_name': current_db,
                'user': current_user,
                'version': postgres_version,
                'connection_type': 'postgresql',
                'service': 'auth-service',
                'service_url': 'https://web-production-ddd7e.up.railway.app'
            },
            'environment': {
                'service_name': os.environ.get('SERVICE_NAME', 'auth-service'),
                'environment': 'production',
                'platform': 'railway'
            }
        }
        
        logger.info("Database info retrieved successfully")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting database info: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Could not retrieve database information',
            'details': str(e)
        }), 500

@database_info_bp.route('/database/schema', methods=['GET'])
def get_database_schema():
    """
    Get accounts table schema information
    
    GET /api/database/schema
    """
    try:
        logger.info("Database schema request")
        
        # Get table schema using SQLAlchemy inspector
        inspector = inspect(db.engine)
        
        # Get accounts table columns
        accounts_columns = inspector.get_columns('accounts')
        
        # Format column information
        schema_info = []
        for column in accounts_columns:
            schema_info.append({
                'column_name': column['name'],
                'data_type': str(column['type']),
                'nullable': column['nullable'],
                'default': str(column['default']) if column['default'] is not None else None,
                'primary_key': column.get('primary_key', False)
            })
        
        # Get indexes
        try:
            indexes = inspector.get_indexes('accounts')
            index_info = []
            for index in indexes:
                index_info.append({
                    'name': index['name'],
                    'columns': index['column_names'],
                    'unique': index['unique']
                })
        except Exception as index_error:
            logger.warning(f"Could not get index info: {str(index_error)}")
            index_info = []
        
        response = {
            'success': True,
            'table': 'accounts',
            'columns': schema_info,
            'indexes': index_info,
            'service': 'auth-service'
        }
        
        logger.info("Database schema retrieved successfully")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting database schema: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Could not retrieve database schema',
            'details': str(e)
        }), 500

@database_info_bp.route('/database/sample-account', methods=['GET'])
def get_sample_account():
    """
    Get sample account data format
    
    GET /api/database/sample-account
    """
    try:
        logger.info("Sample account data request")
        
        # Get the first account as a sample
        account = Account.query.first()
        
        if not account:
            return jsonify({
                'success': False,
                'error': 'No accounts found in database'
            }), 404
        
        # Return account data in the format other services should expect
        sample_data = {
            'id': account.id,
            'bot_id': account.bot_id,
            'bot_username': account.bot_username,
            'bot_name': account.bot_name,
            'channel_id': account.channel_id,
            'channel_username': account.channel_username,
            'channel_title': account.channel_title,
            'is_active': account.is_active,
            'bot_verified': account.bot_verified,
            'channel_verified': account.channel_verified,
            'created_at': account.created_at.isoformat() if account.created_at else None,
            'last_login_at': account.last_login_at.isoformat() if account.last_login_at else None,
            'last_bot_check_at': account.last_bot_check_at.isoformat() if account.last_bot_check_at else None
        }
        
        response = {
            'success': True,
            'sample_account': sample_data,
            'note': 'This is the data format other services should expect',
            'service': 'auth-service'
        }
        
        logger.info("Sample account data retrieved successfully")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting sample account: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Could not retrieve sample account data',
            'details': str(e)
        }), 500

@database_info_bp.route('/database/sync-info', methods=['GET'])
def get_sync_info():
    """
    Get information needed for database synchronization
    
    GET /api/database/sync-info
    """
    try:
        logger.info("Database sync info request")
        
        # Get account count and recent accounts
        total_accounts = Account.query.count()
        recent_accounts = Account.query.order_by(Account.created_at.desc()).limit(5).all()
        
        recent_data = []
        for account in recent_accounts:
            recent_data.append({
                'id': account.id,
                'bot_id': account.bot_id,
                'bot_username': account.bot_username,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'is_active': account.is_active
            })
        
        response = {
            'success': True,
            'sync_info': {
                'total_accounts': total_accounts,
                'recent_accounts': recent_data,
                'last_updated': recent_accounts[0].created_at.isoformat() if recent_accounts else None
            },
            'endpoints': {
                'account_lookup': 'GET /api/accounts/{account_id}',
                'account_validation': 'GET /api/accounts/{account_id}/validate',
                'bot_validation': 'GET /api/v1/bots/validate/{bot_id}',
                'accounts_list': 'GET /api/accounts/list'
            },
            'service': 'auth-service',
            'service_url': 'https://web-production-ddd7e.up.railway.app'
        }
        
        logger.info("Database sync info retrieved successfully")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting sync info: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Could not retrieve sync information',
            'details': str(e)
        }), 500

