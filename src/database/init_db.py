"""
Database initialization script for the Authentication Service
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Flask
from src.models import db, Account, AuthSession
from config.settings import config

def create_app(config_name='development'):
    """Create Flask application with specified configuration"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize database
    db.init_app(app)
    
    return app

def init_database(config_name='development'):
    """Initialize the database with tables and indexes"""
    app = create_app(config_name)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create indexes as specified in the schema
        try:
            # Index for bot_token_encrypted
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_accounts_bot_token ON accounts(bot_token_encrypted)'
            )
            
            # Index for bot_id
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_accounts_bot_id ON accounts(bot_id)'
            )
            
            # Index for channel_id
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_accounts_channel_id ON accounts(channel_id)'
            )
            
            # Index for session_id
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_auth_sessions_session_id ON auth_sessions(session_id)'
            )
            
            # Index for account_id in sessions
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_auth_sessions_account_id ON auth_sessions(account_id)'
            )
            
            print("Database initialized successfully with all tables and indexes")
            
        except Exception as e:
            print(f"Note: Some indexes may already exist: {e}")
            print("Database tables created successfully")

def drop_database(config_name='development'):
    """Drop all database tables (use with caution!)"""
    app = create_app(config_name)
    
    with app.app_context():
        db.drop_all()
        print("All database tables dropped")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database management for Auth Service')
    parser.add_argument('--config', default='development', 
                       choices=['development', 'production', 'testing'],
                       help='Configuration to use')
    parser.add_argument('--drop', action='store_true', 
                       help='Drop all tables (use with caution!)')
    
    args = parser.parse_args()
    
    if args.drop:
        confirm = input("Are you sure you want to drop all tables? (yes/no): ")
        if confirm.lower() == 'yes':
            drop_database(args.config)
        else:
            print("Operation cancelled")
    else:
        init_database(args.config)

