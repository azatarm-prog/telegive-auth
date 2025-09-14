"""
Bot Service Notifier
Pushes bot token updates to Bot Service instead of waiting for polling
"""
import requests
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BotServiceNotifier:
    """Handles pushing bot token updates to Bot Service"""
    
    def __init__(self):
        self.bot_service_url = os.environ.get('BOT_SERVICE_URL', 'https://telegive-bot-service-production.up.railway.app')
        self.service_token = os.environ.get('SERVICE_TO_SERVICE_SECRET')
        self.timeout = 10
    
    def notify_token_update(self, bot_token: str, bot_username: str, bot_id: int) -> bool:
        """
        Notify Bot Service of a new/updated bot token
        
        Args:
            bot_token (str): The new bot token
            bot_username (str): Bot username
            bot_id (int): Bot ID
            
        Returns:
            bool: True if notification was successful, False otherwise
        """
        try:
            logger.info(f"Notifying Bot Service of token update for bot {bot_id}")
            
            # Prepare notification payload
            payload = {
                'bot_token': bot_token,
                'bot_username': bot_username,
                'bot_id': bot_id,
                'status': 'active',
                'updated_at': None  # Will be set by Bot Service
            }
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Service-Token': self.service_token,
                'X-Service-Name': 'auth-service'
            }
            
            # Send notification to Bot Service
            response = requests.post(
                f"{self.bot_service_url}/bot/token/update",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Bot Service notified successfully for bot {bot_id}")
                return True
            else:
                logger.warning(f"Bot Service notification failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning(f"Bot Service notification timeout for bot {bot_id}")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning(f"Bot Service connection error for bot {bot_id}")
            return False
        except Exception as e:
            logger.error(f"Bot Service notification error for bot {bot_id}: {str(e)}")
            return False
    
    def notify_token_removed(self, bot_id: int) -> bool:
        """
        Notify Bot Service that a bot token has been removed/deactivated
        
        Args:
            bot_id (int): Bot ID that was deactivated
            
        Returns:
            bool: True if notification was successful, False otherwise
        """
        try:
            logger.info(f"Notifying Bot Service of token removal for bot {bot_id}")
            
            # Prepare notification payload
            payload = {
                'bot_token': None,
                'bot_id': bot_id,
                'status': 'removed',
                'updated_at': None
            }
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-Service-Token': self.service_token,
                'X-Service-Name': 'auth-service'
            }
            
            # Send notification to Bot Service
            response = requests.post(
                f"{self.bot_service_url}/bot/token/update",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Bot Service notified of token removal for bot {bot_id}")
                return True
            else:
                logger.warning(f"Bot Service removal notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Bot Service removal notification error for bot {bot_id}: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to Bot Service
        
        Returns:
            bool: True if Bot Service is reachable, False otherwise
        """
        try:
            logger.info("Testing Bot Service connection")
            
            headers = {
                'X-Service-Token': self.service_token,
                'X-Service-Name': 'auth-service'
            }
            
            response = requests.get(
                f"{self.bot_service_url}/bot/status",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("Bot Service connection test successful")
                return True
            else:
                logger.warning(f"Bot Service connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Bot Service connection test error: {str(e)}")
            return False

# Global notifier instance
bot_service_notifier = BotServiceNotifier()

