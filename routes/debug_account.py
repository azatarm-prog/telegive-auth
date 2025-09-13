"""
Debug routes for account token investigation
Provides detailed account information for troubleshooting
"""
from flask import Blueprint, jsonify
import logging
from sqlalchemy import text
from src.models import db, Account

debug_account_bp = Blueprint('debug_account', __name__)
logger = logging.getLogger(__name__)

@debug_account_bp.route('/debug/account/<int:bot_id>', methods=['GET'])
def debug_account_by_bot_id(bot_id):
    """
    Debug account information by bot_id
    
    GET /api/debug/account/{bot_id}
    """
    try:
        logger.info(f"Debug account request for bot_id: {bot_id}")
        
        # Get account using SQLAlchemy
        account = Account.query.filter_by(bot_id=bot_id).first()
        
        if not account:
            return jsonify({
                'success': False,
                'error': 'Account not found',
                'bot_id': bot_id
            }), 404
        
        # Get all account attributes
        account_data = {}
        for column in Account.__table__.columns:
            value = getattr(account, column.name)
            if column.name == 'bot_token_encrypted' and value:
                # Show token info without exposing the actual token
                account_data[column.name] = {
                    'has_value': True,
                    'length': len(value),
                    'starts_with': value[:10] + '...' if len(value) > 10 else value
                }
            else:
                account_data[column.name] = value
        
        # Check for any token-related fields
        token_fields = {}
        for attr_name in dir(account):
            if 'token' in attr_name.lower() and not attr_name.startswith('_'):
                value = getattr(account, attr_name)
                if callable(value):
                    continue
                token_fields[attr_name] = {
                    'has_value': value is not None and value != '',
                    'type': type(value).__name__,
                    'length': len(str(value)) if value else 0
                }
        
        response = {
            'success': True,
            'bot_id': bot_id,
            'database_id': account.id,
            'account_data': account_data,
            'token_fields': token_fields,
            'debug_info': {
                'table_name': Account.__tablename__,
                'primary_key': account.id,
                'found_via': 'bot_id lookup'
            }
        }
        
        logger.info(f"Debug account data retrieved for bot_id: {bot_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error debugging account {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Debug query failed',
            'details': str(e),
            'bot_id': bot_id
        }), 500

@debug_account_bp.route('/debug/account/raw/<int:bot_id>', methods=['GET'])
def debug_account_raw_query(bot_id):
    """
    Debug account using raw SQL query
    
    GET /api/debug/account/raw/{bot_id}
    """
    try:
        logger.info(f"Raw debug account request for bot_id: {bot_id}")
        
        # Execute raw SQL query
        with db.engine.connect() as conn:
            # Get all columns from accounts table
            result = conn.execute(text("""
                SELECT * FROM accounts WHERE bot_id = :bot_id
            """), {'bot_id': bot_id})
            
            row = result.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': 'Account not found in raw query',
                    'bot_id': bot_id
                }), 404
            
            # Convert row to dictionary
            columns = result.keys()
            account_data = {}
            
            for i, column in enumerate(columns):
                value = row[i]
                if 'token' in column.lower() and value:
                    # Show token info without exposing the actual token
                    account_data[column] = {
                        'has_value': True,
                        'length': len(str(value)),
                        'type': type(value).__name__,
                        'starts_with': str(value)[:10] + '...' if len(str(value)) > 10 else str(value)
                    }
                else:
                    account_data[column] = value
        
        response = {
            'success': True,
            'bot_id': bot_id,
            'raw_query_result': account_data,
            'debug_info': {
                'query': 'SELECT * FROM accounts WHERE bot_id = :bot_id',
                'method': 'raw_sql'
            }
        }
        
        logger.info(f"Raw debug account data retrieved for bot_id: {bot_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in raw debug query for {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Raw debug query failed',
            'details': str(e),
            'bot_id': bot_id
        }), 500

@debug_account_bp.route('/debug/account/token-check/<int:bot_id>', methods=['GET'])
def debug_token_check(bot_id):
    """
    Specific token field check for account
    
    GET /api/debug/account/token-check/{bot_id}
    """
    try:
        logger.info(f"Token check request for bot_id: {bot_id}")
        
        with db.engine.connect() as conn:
            # Check all possible token fields
            result = conn.execute(text("""
                SELECT 
                    id,
                    bot_id,
                    bot_token_encrypted,
                    CASE 
                        WHEN bot_token_encrypted IS NULL THEN 'NULL'
                        WHEN bot_token_encrypted = '' THEN 'EMPTY'
                        ELSE 'HAS_VALUE'
                    END as token_status,
                    LENGTH(bot_token_encrypted) as token_length,
                    created_at,
                    last_login_at
                FROM accounts 
                WHERE bot_id = :bot_id
            """), {'bot_id': bot_id})
            
            row = result.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': 'Account not found',
                    'bot_id': bot_id
                }), 404
            
            # Convert to dict
            columns = result.keys()
            token_data = dict(zip(columns, row))
        
        response = {
            'success': True,
            'bot_id': bot_id,
            'token_analysis': token_data,
            'recommendations': {
                'token_field_name': 'bot_token_encrypted',
                'channel_service_should_use': 'bot_token_encrypted field',
                'token_available': token_data['token_status'] == 'HAS_VALUE'
            }
        }
        
        logger.info(f"Token check completed for bot_id: {bot_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in token check for {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Token check failed',
            'details': str(e),
            'bot_id': bot_id
        }), 500

@debug_account_bp.route('/debug/database/schema-info', methods=['GET'])
def debug_database_schema():
    """
    Get detailed database schema information
    
    GET /api/debug/database/schema-info
    """
    try:
        logger.info("Database schema debug request")
        
        with db.engine.connect() as conn:
            # Get table schema
            schema_result = conn.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'accounts' 
                ORDER BY ordinal_position
            """))
            
            schema_data = []
            for row in schema_result:
                schema_data.append({
                    'column_name': row[0],
                    'data_type': row[1],
                    'is_nullable': row[2],
                    'column_default': row[3],
                    'max_length': row[4]
                })
            
            # Get indexes
            indexes_result = conn.execute(text("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename = 'accounts'
            """))
            
            indexes_data = []
            for row in indexes_result:
                indexes_data.append({
                    'index_name': row[0],
                    'definition': row[1]
                })
        
        response = {
            'success': True,
            'table_name': 'accounts',
            'columns': schema_data,
            'indexes': indexes_data,
            'debug_info': {
                'database_type': 'postgresql',
                'service': 'auth-service'
            }
        }
        
        logger.info("Database schema debug completed")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting database schema: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Schema debug failed',
            'details': str(e)
        }), 500

