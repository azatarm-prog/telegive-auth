"""
Unit tests for Telegive Authentication Service
"""
import pytest
import json
import os
import sys
from unittest.mock import patch, Mock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from src.models import db, Account, AuthSession
from utils.encryption import TokenEncryption
from utils.telegram_api import TelegramAPI
from utils.validation import InputValidator
from utils.errors import ValidationError, TokenError

class TestAuthService:
    """Test class for authentication service functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def sample_bot_token(self):
        """Sample bot token for testing"""
        return '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890'
    
    @pytest.fixture
    def sample_bot_info(self):
        """Sample bot info for testing"""
        return {
            'id': 1234567890,
            'username': 'test_bot',
            'first_name': 'Test Bot',
            'is_bot': True,
            'can_join_groups': True,
            'can_read_all_group_messages': False,
            'supports_inline_queries': False
        }
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] in ['healthy', 'unhealthy']
        assert data['service'] == 'auth-service'
        assert data['version'] == '1.0.0'
        assert 'database' in data
    
    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get('/api')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['service'] == 'Telegive Authentication Service API'
        assert 'endpoints' in data
    
    @patch('utils.telegram_api.requests.get')
    def test_register_valid_token(self, mock_get, client, sample_bot_token, sample_bot_info):
        """Test registration with valid bot token"""
        # Mock Telegram API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        response = client.post('/api/auth/register', 
                             json={'bot_token': sample_bot_token},
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'account_id' in data
        assert data['bot_info']['id'] == sample_bot_info['id']
        assert data['requires_channel_setup'] == True
    
    @patch('utils.telegram_api.requests.get')
    def test_register_invalid_token(self, mock_get, client):
        """Test registration with invalid bot token"""
        # Mock Telegram API response for invalid token
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        response = client.post('/api/auth/register',
                             json={'bot_token': 'invalid_token'},
                             content_type='application/json')
        
        assert response.status_code == 400  # Validation error for invalid format
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_register_missing_token(self, client):
        """Test registration without bot token"""
        response = client.post('/api/auth/register',
                             json={},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'bot_token' in data['error'].lower()
    
    @patch('utils.telegram_api.requests.get')
    def test_register_duplicate_account(self, mock_get, client, sample_bot_token, sample_bot_info):
        """Test registration with already existing bot"""
        # Mock Telegram API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        # First registration
        response1 = client.post('/api/auth/register',
                              json={'bot_token': sample_bot_token},
                              content_type='application/json')
        assert response1.status_code == 201
        
        # Second registration with same token
        response2 = client.post('/api/auth/register',
                              json={'bot_token': sample_bot_token},
                              content_type='application/json')
        assert response2.status_code == 400
        data = json.loads(response2.data)
        assert data['success'] == False
        assert 'already exists' in data['error'].lower()
    
    @patch('utils.telegram_api.requests.get')
    def test_login_valid_credentials(self, mock_get, client, sample_bot_token, sample_bot_info):
        """Test login with valid credentials"""
        # Mock Telegram API response for registration
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        # First register
        client.post('/api/auth/register',
                   json={'bot_token': sample_bot_token},
                   content_type='application/json')
        
        # Then login
        response = client.post('/api/auth/login',
                             json={'bot_token': sample_bot_token},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'session_id' in data
        assert 'account_info' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login',
                             json={'bot_token': '1234567890:InvalidTokenForTesting123456789'},
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'invalid' in data['error'].lower()
    
    @patch('utils.telegram_api.requests.get')
    def test_verify_session_valid(self, mock_get, client, sample_bot_token, sample_bot_info):
        """Test session verification with valid session"""
        # Mock Telegram API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        # Register and login first
        client.post('/api/auth/register',
                   json={'bot_token': sample_bot_token},
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   json={'bot_token': sample_bot_token},
                                   content_type='application/json')
        
        # Verify session
        response = client.get('/api/auth/verify-session')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == True
        assert 'account_info' in data
    
    def test_verify_session_invalid(self, client):
        """Test session verification with invalid session"""
        response = client.get('/api/auth/verify-session')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['valid'] == False
    
    @patch('utils.telegram_api.requests.get')
    def test_get_account_valid(self, mock_get, client, sample_bot_token, sample_bot_info):
        """Test getting account information with valid account ID"""
        # Mock Telegram API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        # Register account
        register_response = client.post('/api/auth/register',
                                      json={'bot_token': sample_bot_token},
                                      content_type='application/json')
        
        register_data = json.loads(register_response.data)
        account_id = register_data['account_id']
        
        # Get account info
        response = client.get(f'/api/auth/account/{account_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'account' in data
        assert data['account']['id'] == account_id
    
    def test_get_account_invalid(self, client):
        """Test getting account information with invalid account ID"""
        response = client.get('/api/auth/account/99999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
    
    @patch('utils.telegram_api.requests.get')
    def test_decrypt_token_valid(self, mock_get, client, sample_bot_token, sample_bot_info):
        """Test token decryption with valid account ID"""
        # Mock Telegram API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        # Register account
        register_response = client.post('/api/auth/register',
                                      json={'bot_token': sample_bot_token},
                                      content_type='application/json')
        
        register_data = json.loads(register_response.data)
        account_id = register_data['account_id']
        
        # Decrypt token
        response = client.get(f'/api/auth/decrypt-token/{account_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['bot_token'] == sample_bot_token
    
    def test_decrypt_token_invalid(self, client):
        """Test token decryption with invalid account ID"""
        response = client.get('/api/auth/decrypt-token/99999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
    
    @patch('utils.telegram_api.requests.get')
    def test_logout(self, mock_get, client, sample_bot_token, sample_bot_info):
        """Test logout functionality"""
        # Mock Telegram API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'result': sample_bot_info
        }
        mock_get.return_value = mock_response
        
        # Register and login
        client.post('/api/auth/register',
                   json={'bot_token': sample_bot_token},
                   content_type='application/json')
        
        client.post('/api/auth/login',
                   json={'bot_token': sample_bot_token},
                   content_type='application/json')
        
        # Logout
        response = client.post('/api/auth/logout')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Verify session is invalid after logout
        verify_response = client.get('/api/auth/verify-session')
        assert verify_response.status_code == 401
    
    def test_token_encryption_decryption(self):
        """Test token encryption and decryption"""
        original_token = '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890'
        encrypted = TokenEncryption.encrypt_token(original_token)
        decrypted = TokenEncryption.decrypt_token(encrypted)
        
        assert decrypted == original_token
        assert encrypted != original_token
        assert len(encrypted) > len(original_token)
    
    def test_token_validation(self):
        """Test token format validation"""
        # Valid token
        valid_token = '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890'
        assert TokenEncryption.verify_token_format(valid_token) == True
        
        # Invalid tokens
        assert TokenEncryption.verify_token_format('invalid') == False
        assert TokenEncryption.verify_token_format('123:short') == False
        assert TokenEncryption.verify_token_format('abc:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890') == False
        assert TokenEncryption.verify_token_format('') == False
        assert TokenEncryption.verify_token_format(None) == False
    
    def test_input_validation(self):
        """Test input validation utilities"""
        # Valid bot token
        valid_token = '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890'
        validated = InputValidator.validate_bot_token(valid_token)
        assert validated == valid_token
        
        # Invalid bot token
        with pytest.raises(ValidationError):
            InputValidator.validate_bot_token('invalid_token')
        
        with pytest.raises(ValidationError):
            InputValidator.validate_bot_token('')
        
        with pytest.raises(ValidationError):
            InputValidator.validate_bot_token(None)
    
    def test_session_id_generation(self):
        """Test session ID generation"""
        session_id = TokenEncryption.generate_session_id()
        assert session_id.startswith('sess_')
        assert len(session_id) == 37  # 'sess_' + 32 characters
        
        # Generate multiple and ensure they're unique
        session_ids = [TokenEncryption.generate_session_id() for _ in range(10)]
        assert len(set(session_ids)) == 10  # All unique
    
    def test_account_model(self, app):
        """Test Account model functionality"""
        with app.app_context():
            db.create_all()
            
            # Create account
            encrypted_token = TokenEncryption.encrypt_token('1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890')
            account = Account(
                bot_token_encrypted=encrypted_token,
                bot_id=1234567890,
                bot_username='test_bot',
                bot_name='Test Bot'
            )
            
            db.session.add(account)
            db.session.commit()
            
            # Test methods
            account_dict = account.to_dict()
            assert account_dict['bot_username'] == 'test_bot'
            assert account_dict['bot_id'] == 1234567890
            
            public_dict = account.to_public_dict()
            assert 'bot_token_encrypted' not in public_dict
            assert public_dict['bot_username'] == 'test_bot'
    
    def test_session_model(self, app):
        """Test AuthSession model functionality"""
        with app.app_context():
            db.create_all()
            
            # Create account first
            encrypted_token = TokenEncryption.encrypt_token('1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890')
            account = Account(
                bot_token_encrypted=encrypted_token,
                bot_id=1234567890,
                bot_username='test_bot',
                bot_name='Test Bot'
            )
            db.session.add(account)
            db.session.commit()
            
            # Create session
            session_id = TokenEncryption.generate_session_id()
            auth_session = AuthSession(session_id=session_id, account_id=account.id)
            
            db.session.add(auth_session)
            db.session.commit()
            
            # Test methods
            assert auth_session.is_valid() == True
            assert auth_session.is_expired() == False
            
            # Test session retrieval
            retrieved_session = AuthSession.get_valid_session(session_id)
            assert retrieved_session is not None
            assert retrieved_session.session_id == session_id

