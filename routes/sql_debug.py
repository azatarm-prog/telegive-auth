"""
SQL Debug routes for Channel Service coordination
Provides SQL query results and database structure information
"""
from flask import Blueprint, jsonify, request
import logging
from sqlalchemy import text
from src.models import db

sql_debug_bp = Blueprint('sql_debug', __name__)
logger = logging.getLogger(__name__)

@sql_debug_bp.route('/sql-debug/account-structure/<int:bot_id>', methods=['GET'])
def debug_account_structure(bot_id):
    """
    Show the actual database structure for the account
    
    GET /api/sql-debug/account-structure/{bot_id}
    """
    try:
        logger.info(f"SQL debug request for bot_id: {bot_id}")
        
        with db.engine.connect() as conn:
            # Show what fields actually exist
            result = conn.execute(text("""
                SELECT 
                    bot_id,
                    bot_token_encrypted,  -- This is the actual field name
                    LENGTH(bot_token_encrypted) as encrypted_token_length,
                    bot_username,
                    bot_name,
                    is_active,
                    created_at
                FROM accounts 
                WHERE bot_id = :bot_id
            """), {'bot_id': bot_id})
            
            row = result.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': f'No account found for bot_id {bot_id}',
                    'sql_attempted': 'SELECT * FROM accounts WHERE bot_id = :bot_id'
                }), 404
            
            # Convert to dict
            columns = result.keys()
            account_data = dict(zip(columns, row))
            
            # Show the field mapping
            field_mapping = {
                'WRONG_FIELD_NAME': 'bot_token',
                'CORRECT_FIELD_NAME': 'bot_token_encrypted',
                'EXPLANATION': 'Channel Service is looking for bot_token but should use bot_token_encrypted'
            }
            
            response = {
                'success': True,
                'bot_id': bot_id,
                'actual_database_fields': account_data,
                'field_mapping': field_mapping,
                'channel_service_fix': {
                    'wrong_query': 'SELECT bot_token FROM accounts WHERE bot_id = 262662172',
                    'correct_query': 'SELECT bot_token_encrypted FROM accounts WHERE bot_id = 262662172',
                    'python_fix': 'Use account.bot_token (property) or account.bot_token_encrypted (field)'
                }
            }
            
            logger.info(f"SQL debug completed for bot_id: {bot_id}")
            return jsonify(response), 200
            
    except Exception as e:
        logger.error(f"Error in SQL debug for {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SQL debug failed',
            'details': str(e),
            'bot_id': bot_id
        }), 500

@sql_debug_bp.route('/sql-debug/table-schema', methods=['GET'])
def debug_table_schema():
    """
    Show the complete accounts table schema
    
    GET /api/sql-debug/table-schema
    """
    try:
        logger.info("Table schema debug request")
        
        with db.engine.connect() as conn:
            # Get complete table schema
            result = conn.execute(text("""
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
            for row in result:
                schema_data.append({
                    'column_name': row[0],
                    'data_type': row[1],
                    'is_nullable': row[2],
                    'column_default': row[3],
                    'max_length': row[4]
                })
            
            # Highlight the token field
            token_field_info = None
            for field in schema_data:
                if field['column_name'] == 'bot_token_encrypted':
                    token_field_info = field
                    break
            
            response = {
                'success': True,
                'table_name': 'accounts',
                'all_columns': schema_data,
                'token_field_details': token_field_info,
                'important_note': {
                    'message': 'There is NO bot_token field. Use bot_token_encrypted instead.',
                    'channel_service_error': 'Looking for non-existent bot_token field',
                    'solution': 'Use bot_token_encrypted field or account.bot_token property'
                }
            }
            
            logger.info("Table schema debug completed")
            return jsonify(response), 200
            
    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Schema debug failed',
            'details': str(e)
        }), 500

@sql_debug_bp.route('/sql-debug/correct-query/<int:bot_id>', methods=['GET'])
def show_correct_query(bot_id):
    """
    Show the correct SQL query and results
    
    GET /api/sql-debug/correct-query/{bot_id}
    """
    try:
        logger.info(f"Correct query demo for bot_id: {bot_id}")
        
        with db.engine.connect() as conn:
            # Show the WRONG query that Channel Service is trying
            wrong_query = f"SELECT bot_id, bot_token, LENGTH(bot_token) FROM accounts WHERE bot_id = {bot_id}"
            
            # Show the CORRECT query
            correct_query = "SELECT bot_id, bot_token_encrypted, LENGTH(bot_token_encrypted) FROM accounts WHERE bot_id = :bot_id"
            
            # Execute the correct query
            result = conn.execute(text(correct_query), {'bot_id': bot_id})
            row = result.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': f'No account found for bot_id {bot_id}',
                    'wrong_query': wrong_query,
                    'correct_query': correct_query
                }), 404
            
            # Show results
            query_results = {
                'bot_id': row[0],
                'bot_token_encrypted': f"{str(row[1])[:20]}..." if row[1] else None,
                'encrypted_token_length': row[2]
            }
            
            response = {
                'success': True,
                'bot_id': bot_id,
                'wrong_query_attempted': wrong_query,
                'error_from_wrong_query': 'column "bot_token" does not exist',
                'correct_query': correct_query,
                'correct_query_results': query_results,
                'channel_service_solution': {
                    'option_1': 'Use account.bot_token property (recommended)',
                    'option_2': 'Use account.bot_token_encrypted field and decrypt manually',
                    'python_code': 'token = account.bot_token  # This now works with the property'
                }
            }
            
            logger.info(f"Correct query demo completed for bot_id: {bot_id}")
            return jsonify(response), 200
            
    except Exception as e:
        logger.error(f"Error in correct query demo for {bot_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Query demo failed',
            'details': str(e),
            'bot_id': bot_id
        }), 500

