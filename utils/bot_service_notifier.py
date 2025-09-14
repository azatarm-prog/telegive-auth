"""
Bot Service Notifier
Pushes bot token updates to Bot Service according to their specifications
Aligned with Bot Service Push Notification Integration Guide
"""
import requests
import logging
import os
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BotServiceNotifier:
    """Handles pushing bot token updates to Bot Service according to their specifications"""
    
    def __init__(self):
        self.bot_service_url = os.environ.get('BOT_SERVICE_URL', 'https://telegive-bot-service-production.up.railway.app')
        self.service_token = os.environ.get('SERVICE_TO_SERVICE_SECRET', 'ch4nn3l_s3rv1c3_t0k3n_2025_s3cur3_r4nd0m_str1ng')
        self.timeout = 10
        self.max_retries = 3
    
    def notify_token_update(self, bot_token: str, bot_username: str, bot_id: int, status: str = 'active') -> Dict[str, Any]:
        """
        Notify Bot Service of a bot token update with retry logic
        
        Args:
            bot_token (str): The bot token (or None for removal)
            bot_username (str): Bot username
            bot_id (int): Bot ID
            status (str): 'active' or 'removed'
            
        Returns:
            dict: Result with success status and details
        """
        return self._notify_with_retry(bot_token, bot_username, bot_id, status)
    
    def _notify_with_retry(self, bot_token: str, bot_username: str, bot_id: int, status: str) -> Dict[str, Any]:
        """
        Send notification with exponential backoff retry logic
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔔 Push notification attempt {attempt}/{self.max_retries} for bot_id: {bot_id}")
                
                result = self._send_notification(bot_token, bot_username, bot_id, status)
                
                if result['success']:
                    logger.info(f"✅ Push notification successful on attempt {attempt}")
                    self._log_push_notification(bot_id, status, True, None)
                    return result
                
                last_error = result.get('error', 'Unknown error')
                
                if attempt < self.max_retries:
                    delay = (2 ** attempt) * 1000 / 1000  # Exponential backoff in seconds
                    logger.info(f"⏳ Retrying in {delay}s...")
                    time.sleep(delay)
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Push notification attempt {attempt} failed: {str(e)}")
                
                if attempt < self.max_retries:
                    delay = (2 ** attempt) * 1000 / 1000
                    time.sleep(delay)
        
        logger.error(f"❌ All push notification attempts failed for bot_id: {bot_id} - {last_error}")
        self._log_push_notification(bot_id, status, False, last_error)
        
        return {
            'success': False,
            'error': last_error,
            'attempts': self.max_retries
        }
    
    def _send_notification(self, bot_token: str, bot_username: str, bot_id: int, status: str) -> Dict[str, Any]:
        """
        Send single notification attempt to Bot Service
        """
        try:
            logger.info(f"🔔 Sending push notification to Bot Service for bot_id: {bot_id}")
            
            # Prepare notification payload according to Bot Service specifications
            payload = {
                'bot_token': bot_token if status == 'active' else None,
                'bot_username': bot_username,
                'bot_id': bot_id,
                'status': status,
                'updated_at': None  # Bot Service will set this
            }
            
            # Prepare headers according to Bot Service specifications
            headers = {
                'Content-Type': 'application/json',
                'X-Service-Token': self.service_token,
                'X-Service-Name': 'auth-service',
                'User-Agent': 'Telegive-Auth-Service/1.0'
            }
            
            # Send notification to Bot Service
            response = requests.post(
                f"{self.bot_service_url}/bot/token/update",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Bot Service notified successfully for bot_id: {bot_id}")
                logger.info(f"   Response: {result}")
                return {
                    'success': True,
                    'data': result,
                    'bot_initialized': result.get('bot_initialized', False)
                }
            else:
                error_text = response.text
                logger.warning(f"❌ Bot Service notification failed: {response.status_code} - {error_text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {error_text}",
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"Bot Service notification timeout for bot_id: {bot_id}"
            logger.warning(error_msg)
            return {'success': False, 'error': 'Timeout'}
        except requests.exceptions.ConnectionError:
            error_msg = f"Bot Service connection error for bot_id: {bot_id}"
            logger.warning(error_msg)
            return {'success': False, 'error': 'Connection error'}
        except Exception as e:
            error_msg = f"Bot Service notification error for bot_id: {bot_id}: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': str(e)}
    
    def notify_token_removed(self, bot_id: int, bot_username: str = None) -> Dict[str, Any]:
        """
        Notify Bot Service that a bot token has been removed/deactivated
        
        Args:
            bot_id (int): Bot ID that was deactivated
            bot_username (str): Bot username (optional)
            
        Returns:
            dict: Result with success status and details
        """
        return self.notify_token_update(None, bot_username or '', bot_id, 'removed')
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Bot Service
        
        Returns:
            dict: Connection test result
        """
        try:
            logger.info("🧪 Testing Bot Service connection")
            
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
                status_data = response.json()
                logger.info("✅ Bot Service connection test successful")
                return {
                    'success': True,
                    'message': 'Bot Service is reachable',
                    'bot_service_url': self.bot_service_url,
                    'status': status_data
                }
            else:
                logger.warning(f"⚠️ Bot Service connection test failed: {response.status_code}")
                return {
                    'success': False,
                    'message': f'Bot Service returned {response.status_code}',
                    'bot_service_url': self.bot_service_url,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"❌ Bot Service connection test error: {str(e)}")
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}',
                'bot_service_url': self.bot_service_url,
                'error': str(e)
            }
    
    def _log_push_notification(self, bot_id: int, status: str, success: bool, error: str = None):
        """
        Log push notification attempt according to Bot Service specifications
        """
        log_entry = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'event': 'bot_service_push_notification',
            'bot_id': bot_id,
            'status': status,  # 'active' or 'removed'
            'success': success,
            'error': error,
            'target_service': 'bot-service',
            'bot_service_url': self.bot_service_url
        }
        
        logger.info(f"🔔 Push Notification Log: {log_entry}")
        
        # Could store in database or external logging system here
        # await store_log(log_entry)

# Global notifier instance
bot_service_notifier = BotServiceNotifier()

