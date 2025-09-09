"""
Input validation utilities for API requests and data validation
"""
import re
from typing import Dict, Any, List, Optional
from .errors import ValidationError

class InputValidator:
    """Handles validation of input data for API requests"""
    
    # Regular expressions for validation
    BOT_TOKEN_PATTERN = re.compile(r'^\d+:[A-Za-z0-9_-]{35}$')
    SESSION_ID_PATTERN = re.compile(r'^sess_[A-Za-z0-9]{32}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{5,32}$')
    
    @classmethod
    def validate_bot_token(cls, token: Any) -> str:
        """
        Validate bot token format
        
        Args:
            token: The token to validate
            
        Returns:
            str: The validated token
            
        Raises:
            ValidationError: If token is invalid
        """
        if not token:
            raise ValidationError("Bot token is required", "MISSING_TOKEN")
        
        if not isinstance(token, str):
            raise ValidationError("Bot token must be a string", "INVALID_TOKEN_TYPE")
        
        token = token.strip()
        
        if not token:
            raise ValidationError("Bot token cannot be empty", "EMPTY_TOKEN")
        
        # Check basic format: number:alphanumeric_string
        if ':' not in token:
            raise ValidationError("Invalid bot token format", "INVALID_TOKEN_FORMAT")
        
        parts = token.split(':')
        if len(parts) != 2:
            raise ValidationError("Invalid bot token format", "INVALID_TOKEN_FORMAT")
        
        bot_id_str, auth_token = parts
        
        # Validate bot ID part
        if not bot_id_str.isdigit():
            raise ValidationError("Invalid bot ID in token", "INVALID_BOT_ID")
        
        bot_id = int(bot_id_str)
        if bot_id <= 0:
            raise ValidationError("Bot ID must be positive", "INVALID_BOT_ID")
        
        # Validate auth token part
        if len(auth_token) < 30 or len(auth_token) > 50:
            raise ValidationError("Invalid auth token length", "INVALID_AUTH_TOKEN")
        
        # Check allowed characters in auth token
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(c in allowed_chars for c in auth_token):
            raise ValidationError("Invalid characters in auth token", "INVALID_AUTH_TOKEN")
        
        return token
    
    @classmethod
    def validate_session_id(cls, session_id: Any) -> str:
        """
        Validate session ID format
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            str: The validated session ID
            
        Raises:
            ValidationError: If session ID is invalid
        """
        if not session_id:
            raise ValidationError("Session ID is required", "MISSING_SESSION_ID")
        
        if not isinstance(session_id, str):
            raise ValidationError("Session ID must be a string", "INVALID_SESSION_ID_TYPE")
        
        session_id = session_id.strip()
        
        if not cls.SESSION_ID_PATTERN.match(session_id):
            raise ValidationError("Invalid session ID format", "INVALID_SESSION_ID_FORMAT")
        
        return session_id
    
    @classmethod
    def validate_account_id(cls, account_id: Any) -> int:
        """
        Validate account ID
        
        Args:
            account_id: The account ID to validate
            
        Returns:
            int: The validated account ID
            
        Raises:
            ValidationError: If account ID is invalid
        """
        if account_id is None:
            raise ValidationError("Account ID is required", "MISSING_ACCOUNT_ID")
        
        try:
            account_id = int(account_id)
        except (ValueError, TypeError):
            raise ValidationError("Account ID must be a number", "INVALID_ACCOUNT_ID_TYPE")
        
        if account_id <= 0:
            raise ValidationError("Account ID must be positive", "INVALID_ACCOUNT_ID")
        
        return account_id
    
    @classmethod
    def validate_registration_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate registration request data
        
        Args:
            data: The registration data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError("Request data must be a JSON object", "INVALID_DATA_TYPE")
        
        # Validate required fields
        if 'bot_token' not in data:
            raise ValidationError("bot_token is required", "MISSING_BOT_TOKEN")
        
        validated_data = {
            'bot_token': cls.validate_bot_token(data['bot_token'])
        }
        
        return validated_data
    
    @classmethod
    def validate_login_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate login request data
        
        Args:
            data: The login data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError("Request data must be a JSON object", "INVALID_DATA_TYPE")
        
        # Validate required fields
        if 'bot_token' not in data:
            raise ValidationError("bot_token is required", "MISSING_BOT_TOKEN")
        
        validated_data = {
            'bot_token': cls.validate_bot_token(data['bot_token'])
        }
        
        return validated_data
    
    @classmethod
    def validate_username(cls, username: Any) -> str:
        """
        Validate username format
        
        Args:
            username: The username to validate
            
        Returns:
            str: The validated username
            
        Raises:
            ValidationError: If username is invalid
        """
        if not username:
            raise ValidationError("Username is required", "MISSING_USERNAME")
        
        if not isinstance(username, str):
            raise ValidationError("Username must be a string", "INVALID_USERNAME_TYPE")
        
        username = username.strip()
        
        if not username:
            raise ValidationError("Username cannot be empty", "EMPTY_USERNAME")
        
        if not cls.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username must be 5-32 characters long and contain only letters, numbers, and underscores",
                "INVALID_USERNAME_FORMAT"
            )
        
        return username
    
    @classmethod
    def validate_pagination_params(cls, page: Any = None, per_page: Any = None) -> Dict[str, int]:
        """
        Validate pagination parameters
        
        Args:
            page: Page number
            per_page: Items per page
            
        Returns:
            dict: Validated pagination parameters
            
        Raises:
            ValidationError: If parameters are invalid
        """
        validated = {}
        
        # Validate page
        if page is not None:
            try:
                page = int(page)
            except (ValueError, TypeError):
                raise ValidationError("Page must be a number", "INVALID_PAGE_TYPE")
            
            if page < 1:
                raise ValidationError("Page must be at least 1", "INVALID_PAGE_VALUE")
            
            validated['page'] = page
        else:
            validated['page'] = 1
        
        # Validate per_page
        if per_page is not None:
            try:
                per_page = int(per_page)
            except (ValueError, TypeError):
                raise ValidationError("Per page must be a number", "INVALID_PER_PAGE_TYPE")
            
            if per_page < 1:
                raise ValidationError("Per page must be at least 1", "INVALID_PER_PAGE_VALUE")
            
            if per_page > 100:
                raise ValidationError("Per page cannot exceed 100", "PER_PAGE_TOO_LARGE")
            
            validated['per_page'] = per_page
        else:
            validated['per_page'] = 20
        
        return validated
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = None) -> str:
        """
        Sanitize string input
        
        Args:
            value: The string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: The sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Strip whitespace
        value = value.strip()
        
        # Truncate if necessary
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value

