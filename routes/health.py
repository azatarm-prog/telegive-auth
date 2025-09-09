"""
Health check routes for the Telegive Auth Service
"""
from flask import Blueprint, jsonify
from datetime import datetime
import logging

from src.models import db

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    GET /health
    """
    try:
        # Check database connectivity with proper SQLAlchemy syntax
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        database_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        database_status = "disconnected"
    
    # Determine overall status
    status = "healthy" if database_status == "connected" else "unhealthy"
    
    response = {
        "status": status,
        "service": "auth-service",
        "version": "1.0.0",
        "database": database_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    status_code = 200 if status == "healthy" else 503
    
    return jsonify(response), status_code

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check endpoint with more information
    
    GET /health/detailed
    """
    try:
        # Check database connectivity and get some stats with proper SQLAlchemy syntax
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        database_status = "connected"
        
        # Get account count
        from src.models import Account, AuthSession
        account_count = Account.query.count()
        active_sessions = AuthSession.query.filter_by(is_active=True).count()
        
        database_info = {
            "status": "connected",
            "account_count": account_count,
            "active_sessions": active_sessions
        }
        
    except Exception as e:
        logger.error(f"Detailed database health check failed: {str(e)}")
        database_info = {
            "status": "disconnected",
            "error": str(e)
        }
    
    # Check external dependencies
    external_services = {
        "telegram_api": "available"  # Could add actual check here
    }
    
    # Determine overall status
    status = "healthy" if database_info["status"] == "connected" else "unhealthy"
    
    response = {
        "status": status,
        "service": "auth-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database": database_info,
        "external_services": external_services,
        "uptime": "N/A"  # Could implement actual uptime tracking
    }
    
    status_code = 200 if status == "healthy" else 503
    
    return jsonify(response), status_code

