"""
Pytest configuration and shared fixtures for Telegive Auth Service tests
"""
import pytest
import os
import sys
import tempfile
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from src.models import db

@pytest.fixture(scope='session')
def app():
    """Create application for testing session"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ENCRYPTION_KEY': 'test-encryption-key'
    })
    
    with app.app_context():
        yield app

@pytest.fixture(scope='function')
def client(app):
    """Create test client for each test function"""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def sample_tokens():
    """Provide sample bot tokens for testing"""
    return {
        'valid': '1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890',
        'invalid_format': 'invalid_token',
        'invalid_bot_id': 'abc:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890',
        'short_auth': '1234567890:short',
        'long_auth': '1234567890:' + 'A' * 60
    }

@pytest.fixture
def sample_bot_info():
    """Provide sample bot information for testing"""
    return {
        'id': 1234567890,
        'username': 'test_bot',
        'first_name': 'Test Bot',
        'is_bot': True,
        'can_join_groups': True,
        'can_read_all_group_messages': False,
        'supports_inline_queries': False
    }

@pytest.fixture
def mock_telegram_success(sample_bot_info):
    """Mock successful Telegram API response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'ok': True,
        'result': sample_bot_info
    }
    return mock_response

@pytest.fixture
def mock_telegram_invalid():
    """Mock invalid Telegram API response"""
    mock_response = Mock()
    mock_response.status_code = 401
    return mock_response

@pytest.fixture
def mock_telegram_not_bot():
    """Mock Telegram API response for non-bot user"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'ok': True,
        'result': {
            'id': 1234567890,
            'username': 'test_user',
            'first_name': 'Test User',
            'is_bot': False
        }
    }
    return mock_response

# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "load: mark test as a load test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# Skip slow tests by default
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers"""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runload", action="store_true", default=False, help="run load tests"
    )

