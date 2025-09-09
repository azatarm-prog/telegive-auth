"""
Telegram API integration utilities for bot token validation
"""
import requests
import os
from typing import Dict, Any, Optional
from .errors import TelegramAPIError

class TelegramAPI:
    """Handles communication with Telegram Bot API"""
    
    BASE_URL = "https://api.telegram.org"
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize TelegramAPI client
        
        Args:
            base_url (str, optional): Custom base URL for Telegram API
        """
        self.base_url = base_url or os.environ.get('TELEGRAM_API_BASE', self.BASE_URL)
    
    def validate_bot_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a bot token with Telegram API and get bot information
        
        Args:
            token (str): The bot token to validate
            
        Returns:
            dict: Response containing success status and bot info or error
            
        Example success response:
            {
                'success': True,
                'bot_info': {
                    'id': 1234567890,
                    'username': 'test_bot',
                    'first_name': 'Test Bot',
                    'is_bot': True,
                    'can_join_groups': True,
                    'can_read_all_group_messages': False,
                    'supports_inline_queries': False
                }
            }
            
        Example error response:
            {
                'success': False,
                'error': 'Invalid bot token',
                'error_code': 'INVALID_TOKEN'
            }
        """
        if not token:
            return {
                'success': False,
                'error': 'Bot token is required',
                'error_code': 'MISSING_TOKEN'
            }
        
        try:
            # Make request to Telegram API
            url = f"{self.base_url}/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    
                    # Validate that this is actually a bot
                    if not bot_info.get('is_bot', False):
                        return {
                            'success': False,
                            'error': 'Token does not belong to a bot',
                            'error_code': 'NOT_A_BOT'
                        }
                    
                    return {
                        'success': True,
                        'bot_info': bot_info
                    }
                else:
                    error_description = data.get('description', 'Unknown error')
                    return {
                        'success': False,
                        'error': error_description,
                        'error_code': 'TELEGRAM_API_ERROR'
                    }
            
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Invalid bot token',
                    'error_code': 'INVALID_TOKEN'
                }
            
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': 'Bot not found',
                    'error_code': 'BOT_NOT_FOUND'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Telegram API returned status {response.status_code}',
                    'error_code': 'API_ERROR'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request to Telegram API timed out',
                'error_code': 'TIMEOUT'
            }
        
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Failed to connect to Telegram API',
                'error_code': 'CONNECTION_ERROR'
            }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request error: {str(e)}',
                'error_code': 'REQUEST_ERROR'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_code': 'UNKNOWN_ERROR'
            }
    
    def get_bot_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get bot information if token is valid
        
        Args:
            token (str): The bot token
            
        Returns:
            dict or None: Bot information if valid, None if invalid
        """
        result = self.validate_bot_token(token)
        if result['success']:
            return result['bot_info']
        return None
    
    def check_bot_permissions(self, token: str, chat_id: int) -> Dict[str, Any]:
        """
        Check bot permissions in a specific chat
        
        Args:
            token (str): The bot token
            chat_id (int): The chat ID to check permissions for
            
        Returns:
            dict: Response containing permission information
        """
        try:
            url = f"{self.base_url}/bot{token}/getChatMember"
            params = {
                'chat_id': chat_id,
                'user_id': self.extract_bot_id_from_token(token)
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok'):
                    member_info = data.get('result', {})
                    status = member_info.get('status', 'unknown')
                    
                    permissions = {
                        'can_post_messages': False,
                        'can_edit_messages': False,
                        'can_send_media': False
                    }
                    
                    if status in ['administrator', 'creator']:
                        # Extract permissions for administrators
                        permissions.update({
                            'can_post_messages': member_info.get('can_post_messages', False),
                            'can_edit_messages': member_info.get('can_edit_messages', False),
                            'can_send_media': member_info.get('can_send_media_messages', False)
                        })
                    
                    return {
                        'success': True,
                        'status': status,
                        'permissions': permissions
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('description', 'Failed to get chat member info'),
                        'error_code': 'CHAT_MEMBER_ERROR'
                    }
            else:
                return {
                    'success': False,
                    'error': f'API returned status {response.status_code}',
                    'error_code': 'API_ERROR'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking permissions: {str(e)}',
                'error_code': 'PERMISSION_CHECK_ERROR'
            }
    
    @staticmethod
    def extract_bot_id_from_token(token: str) -> int:
        """
        Extract bot ID from token
        
        Args:
            token (str): The bot token
            
        Returns:
            int: The bot ID
            
        Raises:
            ValueError: If token format is invalid
        """
        if not token or ':' not in token:
            raise ValueError("Invalid token format")
        
        bot_id_str = token.split(':')[0]
        if not bot_id_str.isdigit():
            raise ValueError("Invalid bot ID in token")
        
        return int(bot_id_str)

