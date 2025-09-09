"""
Load tests for Telegive Authentication Service
"""
import pytest
import asyncio
import aiohttp
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from src.models import db, Account, AuthSession
from utils.encryption import TokenEncryption

class TestLoadPerformance:
    """Test class for load and performance testing"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    def generate_test_token(self, bot_id):
        """Generate a test bot token for given bot ID"""
        return f"{bot_id}:ABCdefGHIjklMNOpqrSTUvwxYZ{bot_id:010d}"
    
    def mock_telegram_response(self, bot_id):
        """Create mock Telegram API response"""
        return {
            'ok': True,
            'result': {
                'id': bot_id,
                'username': f'test_bot_{bot_id}',
                'first_name': f'Test Bot {bot_id}',
                'is_bot': True,
                'can_join_groups': True,
                'can_read_all_group_messages': False,
                'supports_inline_queries': False
            }
        }
    
    @patch('utils.telegram_api.requests.get')
    def test_concurrent_registrations(self, mock_get, client):
        """Test handling multiple concurrent registrations"""
        
        def register_user(bot_id):
            """Register a single user"""
            # Mock Telegram API response for this bot
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_telegram_response(bot_id)
            mock_get.return_value = mock_response
            
            token = self.generate_test_token(bot_id)
            response = client.post('/api/auth/register',
                                 json={'bot_token': token},
                                 content_type='application/json')
            return response.status_code, bot_id
        
        # Test with 50 concurrent registrations
        num_users = 50
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_user, i) for i in range(1000000000, 1000000000 + num_users)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle 50 concurrent requests in under 10 seconds
        assert duration < 10.0, f"Registration took {duration:.2f} seconds, expected < 10"
        
        # Count successful registrations
        successful = sum(1 for status_code, _ in results if status_code == 201)
        assert successful >= num_users * 0.9, f"Only {successful}/{num_users} registrations succeeded"
        
        print(f"Concurrent registrations: {successful}/{num_users} successful in {duration:.2f}s")
    
    @patch('utils.telegram_api.requests.get')
    def test_concurrent_logins(self, mock_get, client):
        """Test handling multiple concurrent logins"""
        
        # First, register some users
        num_users = 30
        tokens = []
        
        for i in range(2000000000, 2000000000 + num_users):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_telegram_response(i)
            mock_get.return_value = mock_response
            
            token = self.generate_test_token(i)
            tokens.append(token)
            
            response = client.post('/api/auth/register',
                                 json={'bot_token': token},
                                 content_type='application/json')
            assert response.status_code == 201
        
        def login_user(token):
            """Login a single user"""
            response = client.post('/api/auth/login',
                                 json={'bot_token': token},
                                 content_type='application/json')
            return response.status_code
        
        # Test concurrent logins
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login_user, token) for token in tokens]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle logins quickly
        assert duration < 5.0, f"Logins took {duration:.2f} seconds, expected < 5"
        
        # Count successful logins
        successful = sum(1 for status_code in results if status_code == 200)
        assert successful >= num_users * 0.9, f"Only {successful}/{num_users} logins succeeded"
        
        print(f"Concurrent logins: {successful}/{num_users} successful in {duration:.2f}s")
    
    def test_session_verification_performance(self, client):
        """Test session verification performance"""
        
        # Create a session first
        with patch('utils.telegram_api.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_telegram_response(3000000000)
            mock_get.return_value = mock_response
            
            token = self.generate_test_token(3000000000)
            
            # Register and login
            client.post('/api/auth/register',
                       json={'bot_token': token},
                       content_type='application/json')
            
            client.post('/api/auth/login',
                       json={'bot_token': token},
                       content_type='application/json')
        
        def verify_session():
            """Verify session"""
            response = client.get('/api/auth/verify-session')
            return response.status_code
        
        # Test multiple session verifications
        num_verifications = 100
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(verify_session) for _ in range(num_verifications)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle verifications quickly
        assert duration < 3.0, f"Session verifications took {duration:.2f} seconds, expected < 3"
        
        # All should succeed
        successful = sum(1 for status_code in results if status_code == 200)
        assert successful == num_verifications, f"Only {successful}/{num_verifications} verifications succeeded"
        
        print(f"Session verifications: {successful}/{num_verifications} successful in {duration:.2f}s")
    
    def test_encryption_performance(self):
        """Test encryption/decryption performance"""
        tokens = [self.generate_test_token(i) for i in range(4000000000, 4000000000 + 100)]
        
        # Test encryption performance
        start_time = time.time()
        encrypted_tokens = [TokenEncryption.encrypt_token(token) for token in tokens]
        encryption_time = time.time() - start_time
        
        # Test decryption performance
        start_time = time.time()
        decrypted_tokens = [TokenEncryption.decrypt_token(encrypted) for encrypted in encrypted_tokens]
        decryption_time = time.time() - start_time
        
        # Verify correctness
        assert decrypted_tokens == tokens
        
        # Performance assertions
        assert encryption_time < 2.0, f"Encryption took {encryption_time:.2f} seconds, expected < 2"
        assert decryption_time < 2.0, f"Decryption took {decryption_time:.2f} seconds, expected < 2"
        
        print(f"Encryption: 100 tokens in {encryption_time:.2f}s")
        print(f"Decryption: 100 tokens in {decryption_time:.2f}s")
    
    def test_database_performance(self, app):
        """Test database operations performance"""
        with app.app_context():
            db.create_all()
            
            # Test account creation performance
            accounts = []
            start_time = time.time()
            
            for i in range(5000000000, 5000000000 + 50):
                encrypted_token = TokenEncryption.encrypt_token(self.generate_test_token(i))
                account = Account(
                    bot_token_encrypted=encrypted_token,
                    bot_id=i,
                    bot_username=f'test_bot_{i}',
                    bot_name=f'Test Bot {i}'
                )
                accounts.append(account)
                db.session.add(account)
            
            db.session.commit()
            creation_time = time.time() - start_time
            
            # Test account retrieval performance
            start_time = time.time()
            retrieved_accounts = []
            for i in range(5000000000, 5000000000 + 50):
                account = Account.query.filter_by(bot_id=i).first()
                retrieved_accounts.append(account)
            
            retrieval_time = time.time() - start_time
            
            # Verify correctness
            assert len(retrieved_accounts) == 50
            assert all(account is not None for account in retrieved_accounts)
            
            # Performance assertions
            assert creation_time < 5.0, f"Account creation took {creation_time:.2f} seconds, expected < 5"
            assert retrieval_time < 2.0, f"Account retrieval took {retrieval_time:.2f} seconds, expected < 2"
            
            print(f"Database creation: 50 accounts in {creation_time:.2f}s")
            print(f"Database retrieval: 50 accounts in {retrieval_time:.2f}s")
    
    def test_health_check_performance(self, client):
        """Test health check endpoint performance"""
        
        def health_check():
            """Perform health check"""
            response = client.get('/health')
            return response.status_code
        
        # Test multiple health checks
        num_checks = 200
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(health_check) for _ in range(num_checks)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle health checks very quickly
        assert duration < 2.0, f"Health checks took {duration:.2f} seconds, expected < 2"
        
        # All should succeed
        successful = sum(1 for status_code in results if status_code == 200)
        assert successful == num_checks, f"Only {successful}/{num_checks} health checks succeeded"
        
        print(f"Health checks: {successful}/{num_checks} successful in {duration:.2f}s")
    
    def test_memory_usage_stability(self, app):
        """Test that memory usage remains stable under load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with app.app_context():
            db.create_all()
            
            # Perform many operations
            for batch in range(10):
                # Create accounts
                for i in range(batch * 10, (batch + 1) * 10):
                    bot_id = 6000000000 + i
                    encrypted_token = TokenEncryption.encrypt_token(self.generate_test_token(bot_id))
                    account = Account(
                        bot_token_encrypted=encrypted_token,
                        bot_id=bot_id,
                        bot_username=f'test_bot_{bot_id}',
                        bot_name=f'Test Bot {bot_id}'
                    )
                    db.session.add(account)
                
                db.session.commit()
                
                # Create sessions
                for i in range(batch * 10, (batch + 1) * 10):
                    session_id = TokenEncryption.generate_session_id()
                    auth_session = AuthSession(session_id=session_id, account_id=i + 1)
                    db.session.add(auth_session)
                
                db.session.commit()
                
                # Force garbage collection
                gc.collect()
                
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory should not increase dramatically
                assert memory_increase < 100, f"Memory increased by {memory_increase:.2f} MB after batch {batch}"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.2f} MB -> {final_memory:.2f} MB (+{total_increase:.2f} MB)")
        
        # Total memory increase should be reasonable
        assert total_increase < 200, f"Total memory increase of {total_increase:.2f} MB is too high"

# Async load tests using aiohttp
class TestAsyncLoadPerformance:
    """Test class for async load testing"""
    
    @pytest.mark.asyncio
    async def test_async_health_checks(self):
        """Test async health check performance"""
        
        async def health_check(session):
            """Perform async health check"""
            try:
                async with session.get('http://localhost:8001/health') as response:
                    return response.status
            except:
                return 0  # Connection failed
        
        # This test would require the server to be running
        # For now, we'll just test the structure
        
        async with aiohttp.ClientSession() as session:
            # In a real scenario, we'd test against a running server
            # tasks = [health_check(session) for _ in range(100)]
            # results = await asyncio.gather(*tasks, return_exceptions=True)
            pass
    
    def test_stress_test_simulation(self):
        """Simulate stress test conditions"""
        
        # Simulate high load conditions
        start_time = time.time()
        
        # Simulate CPU-intensive operations
        operations = 0
        while time.time() - start_time < 1.0:  # Run for 1 second
            # Simulate token operations
            token = self.generate_test_token(operations % 1000000 + 7000000000)
            encrypted = TokenEncryption.encrypt_token(token)
            decrypted = TokenEncryption.decrypt_token(encrypted)
            assert decrypted == token
            operations += 1
        
        # Should handle reasonable number of operations per second
        ops_per_second = operations / 1.0
        assert ops_per_second > 100, f"Only {ops_per_second:.0f} ops/sec, expected > 100"
        
        print(f"Stress test: {operations} operations in 1 second ({ops_per_second:.0f} ops/sec)")
    
    def generate_test_token(self, bot_id):
        """Generate a test bot token for given bot ID"""
        return f"{bot_id}:ABCdefGHIjklMNOpqrSTUvwxYZ{bot_id:010d}"

