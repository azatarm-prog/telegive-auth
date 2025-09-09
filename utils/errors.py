"""
Custom error classes and error handling utilities
"""

class AuthError(Exception):
    """Base exception class for authentication errors"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 400):
        self.message = message
        self.error_code = error_code or 'AUTH_ERROR'
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert error to dictionary for API responses"""
        return {
            'success': False,
            'error': self.message,
            'error_code': self.error_code
        }

class ValidationError(AuthError):
    """Exception raised for input validation errors"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'VALIDATION_ERROR', 400)

class TelegramAPIError(AuthError):
    """Exception raised for Telegram API related errors"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'TELEGRAM_API_ERROR', 502)

class TokenError(AuthError):
    """Exception raised for token related errors"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'TOKEN_ERROR', 401)

class SessionError(AuthError):
    """Exception raised for session related errors"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'SESSION_ERROR', 401)

class AccountError(AuthError):
    """Exception raised for account related errors"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'ACCOUNT_ERROR', 404)

class RateLimitError(AuthError):
    """Exception raised when rate limits are exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", error_code: str = None):
        super().__init__(message, error_code or 'RATE_LIMIT_EXCEEDED', 429)

class DatabaseError(AuthError):
    """Exception raised for database related errors"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or 'DATABASE_ERROR', 500)

def handle_error(error):
    """
    Convert various error types to standardized error responses
    
    Args:
        error: The error to handle
        
    Returns:
        tuple: (response_dict, status_code)
    """
    if isinstance(error, AuthError):
        return error.to_dict(), error.status_code
    
    elif isinstance(error, ValueError):
        return {
            'success': False,
            'error': str(error),
            'error_code': 'INVALID_INPUT'
        }, 400
    
    elif isinstance(error, KeyError):
        return {
            'success': False,
            'error': f'Missing required field: {str(error)}',
            'error_code': 'MISSING_FIELD'
        }, 400
    
    elif isinstance(error, TypeError):
        return {
            'success': False,
            'error': 'Invalid data type in request',
            'error_code': 'INVALID_TYPE'
        }, 400
    
    else:
        # Log unexpected errors but don't expose details to client
        import logging
        logging.error(f"Unexpected error: {str(error)}", exc_info=True)
        
        return {
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }, 500

def create_error_response(message: str, error_code: str = None, status_code: int = 400):
    """
    Create a standardized error response
    
    Args:
        message: Error message
        error_code: Machine-readable error code
        status_code: HTTP status code
        
    Returns:
        tuple: (response_dict, status_code)
    """
    return {
        'success': False,
        'error': message,
        'error_code': error_code or 'ERROR'
    }, status_code

def create_success_response(data: dict = None, message: str = None):
    """
    Create a standardized success response
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        dict: Success response
    """
    response = {'success': True}
    
    if data:
        response.update(data)
    
    if message:
        response['message'] = message
    
    return response

