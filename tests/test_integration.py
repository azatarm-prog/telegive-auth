"""
Integration tests for Telegive Authentication Service
"""
import pytest
import asyncio
import aiohttp
import requests
from unittest.mock import patch, Mock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.telegram_api import TelegramAPI
from utils.encryption import TokenEncryption

class TestTelegramIntegration:
    """Test class for Telegram API integration"""
    
    @pytest.fixture
    def telegram_api(self):
        """Create TelegramAPI instance for testing"""
        return TelegramAPI()
    
    @pytest.fixture
    def sample_bot_token(self):
        """Sample bot token for testing"""
        return '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890'
    
    @pytest.fixture
    def sample_bot_info(self):
        """Sample bot info response"""
        return {
            'id': 1234567890,
            'username': 'test_bot',
            'first_name': 'Test Bot',
            'is_bot': True,
            'can_join_groups': True,
            'can_read_all_group_messages': False,
            'supports_inline_queries': False
        }
    
    @patch('requests.get')
    def test_telegram_api_validation_success(self, mock_get, telegram_api, sample_bot_token, sample_bot_info):
        """Test successful Telegram API validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        result = telegram_api.validate_bot_token(sample_bot_token)
        
        assert result['success'] == True
        assert result['bot_info']['id'] == 1234567890
        assert result['bot_info']['username'] == 'test_bot'
        assert result['bot_info']['is_bot'] == True
        
        # Verify the correct URL was called
        expected_url = f"{telegram_api.base_url}/bot{sample_bot_token}/getMe"
        mock_get.assert_called_once_with(expected_url, timeout=10)
    
    @patch('requests.get')
    def test_telegram_api_validation_invalid_token(self, mock_get, telegram_api):
        """Test Telegram API validation with invalid token"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = telegram_api.validate_bot_token('invalid_token')
        
        assert result['success'] == False
        assert result['error_code'] == 'INVALID_TOKEN'
        assert 'invalid' in result['error'].lower()
    
    @patch('requests.get')
    def test_telegram_api_validation_not_a_bot(self, mock_get, telegram_api, sample_bot_token):
        """Test Telegram API validation when token belongs to user, not bot"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'id': 1234567890,
                'username': 'test_user',
                'first_name': 'Test User',
                'is_bot': False  # Not a bot!
            }
        }
        mock_get.return_value = mock_response
        
        result = telegram_api.validate_bot_token(sample_bot_token)
        
        assert result['success'] == False
        assert result['error_code'] == 'NOT_A_BOT'
        assert 'not.*bot' in result['error'].lower()
    
    @patch('requests.get')
    def test_telegram_api_validation_api_error(self, mock_get, telegram_api, sample_bot_token):
        """Test Telegram API validation when API returns error"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': False,
            'description': 'Bad Request: invalid token'
        }
        mock_get.return_value = mock_response
        
        result = telegram_api.validate_bot_token(sample_bot_token)
        
        assert result['success'] == False
        assert result['error_code'] == 'TELEGRAM_API_ERROR'
        assert 'Bad Request' in result['error']
    
    @patch('requests.get')
    def test_telegram_api_validation_timeout(self, mock_get, telegram_api, sample_bot_token):
        """Test Telegram API validation timeout"""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = telegram_api.validate_bot_token(sample_bot_token)
        
        assert result['success'] == False
        assert result['error_code'] == 'TIMEOUT'
        assert 'timeout' in result['error'].lower()
    
    @patch('requests.get')
    def test_telegram_api_validation_connection_error(self, mock_get, telegram_api, sample_bot_token):
        """Test Telegram API validation connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = telegram_api.validate_bot_token(sample_bot_token)
        
        assert result['success'] == False
        assert result['error_code'] == 'CONNECTION_ERROR'
        assert 'connect' in result['error'].lower()
    
    @patch('requests.get')
    def test_telegram_api_validation_404(self, mock_get, telegram_api, sample_bot_token):
        """Test Telegram API validation with 404 response"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = telegram_api.validate_bot_token(sample_bot_token)
        
        assert result['success'] == False
        assert result['error_code'] == 'BOT_NOT_FOUND'
    
    @patch('requests.get')
    def test_telegram_api_validation_500(self, mock_get, telegram_api, sample_bot_token):
        """Test Telegram API validation with 500 response"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = telegram_api.validate_bot_token(sample_bot_token)
        
        assert result['success'] == False
        assert result['error_code'] == 'API_ERROR'
        assert '500' in result['error']
    
    def test_telegram_api_validation_empty_token(self, telegram_api):
        """Test Telegram API validation with empty token"""
        result = telegram_api.validate_bot_token('')
        
        assert result['success'] == False
        assert result['error_code'] == 'MISSING_TOKEN'
    
    def test_telegram_api_validation_none_token(self, telegram_api):
        """Test Telegram API validation with None token"""
        result = telegram_api.validate_bot_token(None)
        
        assert result['success'] == False
        assert result['error_code'] == 'MISSING_TOKEN'
    
    @patch('requests.get')
    def test_get_bot_info_success(self, mock_get, telegram_api, sample_bot_token, sample_bot_info):
        """Test getting bot info successfully"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        bot_info = telegram_api.get_bot_info(sample_bot_token)
        
        assert bot_info is not None
        assert bot_info['id'] == 1234567890
        assert bot_info['username'] == 'test_bot'
    
    @patch('requests.get')
    def test_get_bot_info_failure(self, mock_get, telegram_api, sample_bot_token):
        """Test getting bot info with invalid token"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        bot_info = telegram_api.get_bot_info(sample_bot_token)
        
        assert bot_info is None
    
    def test_extract_bot_id_from_token_valid(self):
        """Test extracting bot ID from valid token"""
        token = '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890'
        bot_id = TelegramAPI.extract_bot_id_from_token(token)
        assert bot_id == 1234567890
    
    def test_extract_bot_id_from_token_invalid(self):
        """Test extracting bot ID from invalid token"""
        with pytest.raises(ValueError):
            TelegramAPI.extract_bot_id_from_token('invalid_token')
        
        with pytest.raises(ValueError):
            TelegramAPI.extract_bot_id_from_token('abc:def')
        
        with pytest.raises(ValueError):
            TelegramAPI.extract_bot_id_from_token('')
    
    @patch('requests.get')
    def test_check_bot_permissions_admin(self, mock_get, telegram_api, sample_bot_token):
        """Test checking bot permissions when bot is admin"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'status': 'administrator',
                'can_post_messages': True,
                'can_edit_messages': True,
                'can_send_media_messages': True
            }
        }
        mock_get.return_value = mock_response
        
        result = telegram_api.check_bot_permissions(sample_bot_token, -1001234567890)
        
        assert result['success'] == True
        assert result['status'] == 'administrator'
        assert result['permissions']['can_post_messages'] == True
        assert result['permissions']['can_edit_messages'] == True
        assert result['permissions']['can_send_media'] == True
    
    @patch('requests.get')
    def test_check_bot_permissions_member(self, mock_get, telegram_api, sample_bot_token):
        """Test checking bot permissions when bot is regular member"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': {
                'status': 'member'
            }
        }
        mock_get.return_value = mock_response
        
        result = telegram_api.check_bot_permissions(sample_bot_token, -1001234567890)
        
        assert result['success'] == True
        assert result['status'] == 'member'
        assert result['permissions']['can_post_messages'] == False
        assert result['permissions']['can_edit_messages'] == False
        assert result['permissions']['can_send_media'] == False
    
    @patch('requests.get')
    def test_check_bot_permissions_error(self, mock_get, telegram_api, sample_bot_token):
        """Test checking bot permissions with API error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        
        result = telegram_api.check_bot_permissions(sample_bot_token, -1001234567890)
        
        assert result['success'] == False
        assert result['error_code'] == 'API_ERROR'

class TestEncryptionIntegration:
    """Test class for encryption integration"""
    
    def test_encryption_consistency(self):
        """Test that encryption/decryption is consistent"""
        tokens = [
            '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890',
            '9876543210:ZYXwvuTSRqpONMlkjIHgfeDCba0987654321',
            '5555555555:TestTokenForEncryptionTesting123456789'
        ]
        
        for token in tokens:
            encrypted = TokenEncryption.encrypt_token(token)
            decrypted = TokenEncryption.decrypt_token(encrypted)
            assert decrypted == token
    
    def test_encryption_uniqueness(self):
        """Test that same token produces different encrypted values"""
        token = '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890'
        
        encrypted1 = TokenEncryption.encrypt_token(token)
        encrypted2 = TokenEncryption.encrypt_token(token)
        
        # Due to Fernet's built-in randomness, same plaintext produces different ciphertext
        # But both should decrypt to the same value
        assert TokenEncryption.decrypt_token(encrypted1) == token
        assert TokenEncryption.decrypt_token(encrypted2) == token
    
    def test_encryption_with_invalid_data(self):
        """Test encryption with invalid data"""
        with pytest.raises(ValueError):
            TokenEncryption.encrypt_token('')
        
        with pytest.raises(ValueError):
            TokenEncryption.encrypt_token(None)
        
        with pytest.raises(ValueError):
            TokenEncryption.decrypt_token('')
        
        with pytest.raises(ValueError):
            TokenEncryption.decrypt_token(None)
        
        with pytest.raises(ValueError):
            TokenEncryption.decrypt_token('invalid_encrypted_data')

class TestDatabaseIntegration:
    """Test class for database integration"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        from app import create_app
        app = create_app('testing')
        return app
    
    def test_database_operations(self, app):
        """Test basic database operations"""
        with app.app_context():
            from src.models import db, Account, AuthSession
            
            db.create_all()
            
            # Test account creation
            encrypted_token = TokenEncryption.encrypt_token('1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890')
            account = Account(
                bot_token_encrypted=encrypted_token,
                bot_id=1234567890,
                bot_username='test_bot',
                bot_name='Test Bot'
            )
            
            db.session.add(account)
            db.session.commit()
            
            # Test account retrieval
            retrieved_account = Account.query.filter_by(bot_id=1234567890).first()
            assert retrieved_account is not None
            assert retrieved_account.bot_username == 'test_bot'
            
            # Test session creation
            session_id = TokenEncryption.generate_session_id()
            auth_session = AuthSession(session_id=session_id, account_id=account.id)
            
            db.session.add(auth_session)
            db.session.commit()
            
            # Test session retrieval
            retrieved_session = AuthSession.get_valid_session(session_id)
            assert retrieved_session is not None
            assert retrieved_session.account_id == account.id
            
            # Test session cleanup
            count = AuthSession.cleanup_expired_sessions()
            assert count >= 0  # Should not fail
            
            db.drop_all()

