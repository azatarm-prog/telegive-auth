"""
Token encryption utilities using AES-256 encryption
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class TokenEncryption:
    """Handles encryption and decryption of bot tokens using AES-256"""
    
    _fernet = None
    
    @classmethod
    def _get_fernet(cls):
        """Get or create Fernet instance for encryption/decryption"""
        if cls._fernet is None:
            # Get encryption key from environment or use default for development
            encryption_key = os.environ.get('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production')
            
            # Derive a proper key from the encryption key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'telegive_auth_salt',  # Fixed salt for consistency
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            cls._fernet = Fernet(key)
        
        return cls._fernet
    
    @classmethod
    def encrypt_token(cls, token):
        """
        Encrypt a bot token using AES-256
        
        Args:
            token (str): The bot token to encrypt
            
        Returns:
            str: Base64 encoded encrypted token
            
        Raises:
            ValueError: If token is empty or None
        """
        if not token:
            raise ValueError("Token cannot be empty or None")
        
        try:
            fernet = cls._get_fernet()
            encrypted_bytes = fernet.encrypt(token.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encrypt token: {str(e)}")
    
    @classmethod
    def decrypt_token(cls, encrypted_token):
        """
        Decrypt an encrypted bot token
        
        Args:
            encrypted_token (str): Base64 encoded encrypted token
            
        Returns:
            str: The decrypted bot token
            
        Raises:
            ValueError: If decryption fails or token is invalid
        """
        if not encrypted_token:
            raise ValueError("Encrypted token cannot be empty or None")
        
        try:
            fernet = cls._get_fernet()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode('utf-8'))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {str(e)}")
    
    @classmethod
    def verify_token_format(cls, token):
        """
        Verify that a token has the correct Telegram bot token format
        
        Args:
            token (str): The token to verify
            
        Returns:
            bool: True if token format is valid, False otherwise
        """
        if not token or not isinstance(token, str):
            return False
        
        # Telegram bot tokens have the format: bot_id:auth_token
        # bot_id is a number, auth_token is alphanumeric with some special chars
        parts = token.split(':')
        if len(parts) != 2:
            return False
        
        bot_id, auth_token = parts
        
        # Check if bot_id is numeric
        if not bot_id.isdigit():
            return False
        
        # Check if auth_token has reasonable length and characters
        if len(auth_token) < 30 or len(auth_token) > 50:
            return False
        
        # Auth token should contain only alphanumeric characters, hyphens, and underscores
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(c in allowed_chars for c in auth_token):
            return False
        
        return True
    
    @classmethod
    def extract_bot_id(cls, token):
        """
        Extract bot ID from a Telegram bot token
        
        Args:
            token (str): The bot token
            
        Returns:
            int: The bot ID
            
        Raises:
            ValueError: If token format is invalid
        """
        if not cls.verify_token_format(token):
            raise ValueError("Invalid token format")
        
        bot_id = token.split(':')[0]
        return int(bot_id)
    
    @classmethod
    def generate_session_id(cls):
        """
        Generate a secure session ID
        
        Returns:
            str: A secure session ID
        """
        import secrets
        import string
        
        # Generate a 32-character random string
        alphabet = string.ascii_letters + string.digits
        session_id = ''.join(secrets.choice(alphabet) for _ in range(32))
        return f"sess_{session_id}"

