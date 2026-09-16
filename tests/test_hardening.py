import pytest
from app import create_app
from config import TestConfig
from extensions import db

@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    # Register an intentional error route to test 500 handler sanitization
    @app.route('/test/trigger-error')
    def trigger_error():
        raise RuntimeError("CRITICAL_INTERNAL_DB_PASSWORD_LEAK_12345")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_security_headers_present(client):
    """Test that all HTTP responses include hardened security headers."""
    response = client.get('/health')
    assert response.status_code == 200

    headers = response.headers
    # CSP
    assert 'Content-Security-Policy' in headers
    csp = headers['Content-Security-Policy']
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp

    # Anti-sniffing & framing
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('X-Frame-Options') == 'DENY'
    assert headers.get('X-XSS-Protection') == '1; mode=block'
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    assert 'Permissions-Policy' in headers

def test_404_error_sanitization(client):
    """Test 404 returns sanitized JSON error without server stack leak."""
    response = client.get('/api/invalid-route-does-not-exist')
    assert response.status_code == 404
    data = response.get_json()
    assert data is not None
    assert 'error' in data
    assert data['error'] == 'Resource not found.'

def test_500_error_sanitization(app):
    """Test 500 handler catches exceptions and masks internal details."""
    app.config['PROPAGATE_EXCEPTIONS'] = False
    app.config['TESTING'] = False
    client = app.test_client()

    response = client.get('/test/trigger-error')
    assert response.status_code == 500
    data = response.get_json()
    assert data is not None
    assert 'CRITICAL_INTERNAL_DB_PASSWORD_LEAK' not in response.data.decode('utf-8')
    assert 'An internal server error occurred' in data['error']

def test_cookie_security_attributes(client):
    """Test that session cookies carry HttpOnly and SameSite flags."""
    client.post('/api/register', json={'username': 'test_hardening_user', 'password': 'Password123!'})
    login_resp = client.post('/api/login', json={'username': 'test_hardening_user', 'password': 'Password123!'})
    assert login_resp.status_code == 200

    set_cookie_headers = login_resp.headers.getlist('Set-Cookie')
    assert len(set_cookie_headers) > 0
    cookie_str = set_cookie_headers[0].lower()
    assert 'httponly' in cookie_str
    assert 'samesite=lax' in cookie_str
