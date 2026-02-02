"""
Endpoint tests - Test HTTP endpoints for proper responses and status codes.
These tests verify that endpoints return expected status codes and handle
authentication/authorization correctly.
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    import app
    app.app.config['TESTING'] = True
    app.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.app.test_client() as client:
        yield client


@pytest.fixture
def mock_session():
    """Create a mock session with authenticated user"""
    return {
        'authenticated': True,
        'user': {
            'name': 'Test User',
            'email': 'test@example.com'
        },
        'token_cache': {'mock': 'token'}
    }


class TestPublicEndpoints:
    """Test publicly accessible endpoints"""
    
    def test_login_page_accessible(self, client):
        """Test that login page redirects to Microsoft"""
        response = client.get('/login', follow_redirects=False)
        # Should redirect to Microsoft auth
        assert response.status_code in [302, 307]
    
    def test_session_ended_page_exists(self, client):
        """Test that session ended page is accessible"""
        response = client.get('/session/ended')
        assert response.status_code == 200


class TestProtectedEndpoints:
    """Test endpoints that require authentication"""
    
    def test_index_requires_auth(self, client):
        """Test that index redirects to login when not authenticated"""
        response = client.get('/', follow_redirects=False)
        assert response.status_code in [302, 401]
    
    def test_api_properties_requires_auth(self, client):
        """Test that properties API requires authentication"""
        response = client.get('/api/properties', follow_redirects=False)
        assert response.status_code in [302, 401]
    
    def test_api_analyze_requires_auth(self, client):
        """Test that analyze endpoint requires authentication"""
        response = client.post('/api/analyze', follow_redirects=False)
        assert response.status_code in [302, 400, 401]


class TestSessionEndpoints:
    """Test session management endpoints"""
    
    def test_session_end_endpoint_exists(self, client):
        """Test that session end endpoint is accessible"""
        response = client.get('/logout', follow_redirects=False)
        # Will fail auth but endpoint should exist
        assert response.status_code in [200, 302, 401]
    
    def test_session_start_endpoint_exists(self, client):
        """Test that session start endpoint is accessible"""
        response = client.post('/session/start', follow_redirects=False)
        # Will fail without valid tokens but endpoint should exist
        assert response.status_code in [200, 401]
    
    def test_session_check_endpoint_exists(self, client):
        """Test that session check endpoint is accessible"""
        response = client.get('/session/check')
        assert response.status_code == 200
        # Should return JSON
        assert response.content_type == 'application/json'


class TestAPIEndpoints:
    """Test API endpoint responses"""
    
    def test_api_analyze_without_files(self, client):
        """Test analyze endpoint rejects requests without files"""
        with client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['user'] = {'name': 'Test', 'email': 'test@test.com'}
        
        response = client.post('/api/analyze')
        # Should return error (400 or 401 depending on auth handling)
        assert response.status_code in [400, 401, 302]


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_404_handling(self, client):
        """Test that 404 errors are handled"""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test invalid HTTP methods are rejected"""
        # Session start only accepts POST
        response = client.get('/session/start')
        assert response.status_code in [405, 302, 401]


class TestHealthChecks:
    """Basic health check tests"""
    
    def test_app_has_secret_key(self, client):
        """Test that app has a secret key configured"""
        import app
        assert app.app.secret_key is not None
        assert len(app.app.secret_key) > 0
    
    def test_app_in_correct_mode(self, client):
        """Test that app is in testing mode when testing"""
        import app
        assert app.app.config['TESTING'] == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
