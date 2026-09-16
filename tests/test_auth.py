import pytest
from app import create_app
from config import TestConfig
from extensions import db
from models.database import User
from routes.auth import login_required
from flask import jsonify

@pytest.fixture
def app():
    """Create and configure a clean application instance for testing."""
    app = create_app(TestConfig)
    
    # Add a dummy protected test route to verify @login_required decorator
    @app.route('/api/protected-test')
    @login_required
    def protected_test():
        return jsonify({'message': 'Access granted to protected resource.'}), 200

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client preserving session state."""
    return app.test_client()

def test_register_success(client):
    """Test successful user registration with valid credentials."""
    response = client.post('/api/register', json={
        'username': 'alice',
        'password': 'Password123!',
        'public_key': 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'user' in data
    assert data['user']['username'] == 'alice'
    assert 'password_hash' not in data['user']
    assert data['user']['public_key'] == 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...'

def test_register_duplicate_username(client):
    """Test that duplicate usernames are rejected with 409 Conflict."""
    payload = {'username': 'bob', 'password': 'SecurePassword123'}
    res1 = client.post('/api/register', json=payload)
    assert res1.status_code == 201

    res2 = client.post('/api/register', json=payload)
    assert res2.status_code == 409
    assert 'already taken' in res2.get_json()['error']

def test_register_validation_errors(client):
    """Test input validations: empty fields, short usernames, invalid characters, short passwords."""
    # Empty body
    assert client.post('/api/register', data="").status_code == 400

    # Short username
    res = client.post('/api/register', json={'username': 'ab', 'password': 'ValidPassword123'})
    assert res.status_code == 400
    assert 'between 3 and 32' in res.get_json()['error']

    # Invalid characters in username
    res = client.post('/api/register', json={'username': 'user@bad!', 'password': 'ValidPassword123'})
    assert res.status_code == 400
    assert 'alphanumeric' in res.get_json()['error']

    # Short password (<8 characters)
    res = client.post('/api/register', json={'username': 'charlie', 'password': '123'})
    assert res.status_code == 400
    assert 'at least 8 characters' in res.get_json()['error']

def test_password_hashing_security(app):
    """Test that passwords are cryptographically hashed and never stored in plaintext."""
    with app.app_context():
        user = User(username='dave')
        raw_pw = 'SuperSecretKey999!'
        user.set_password(raw_pw)

        # Ensure password is not plaintext
        assert user.password_hash != raw_pw
        # Ensure standard secure prefix (scrypt or pbkdf2)
        assert any(user.password_hash.startswith(prefix) for prefix in ['scrypt:', 'pbkdf2:'])
        # Ensure password checks work accurately
        assert user.check_password(raw_pw) is True
        assert user.check_password('WrongPassword') is False
        assert user.check_password('') is False

def test_login_success(client):
    """Test login with valid credentials establishes session."""
    # Register first
    client.post('/api/register', json={'username': 'eve', 'password': 'PasswordEve123'})

    # Login
    response = client.post('/api/login', json={'username': 'eve', 'password': 'PasswordEve123'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['username'] == 'eve'

    # Verify session cookie was set by requesting /api/auth/me
    me_resp = client.get('/api/auth/me')
    assert me_resp.status_code == 200
    assert me_resp.get_json()['user']['username'] == 'eve'

def test_login_invalid_credentials(client):
    """Test login fails with non-existent user and wrong password."""
    # Non-existent user
    res1 = client.post('/api/login', json={'username': 'nonexistent', 'password': 'Password123'})
    assert res1.status_code == 401
    assert 'Invalid username or password' in res1.get_json()['error']

    # Wrong password
    client.post('/api/register', json={'username': 'frank', 'password': 'PasswordFrank123'})
    res2 = client.post('/api/login', json={'username': 'frank', 'password': 'IncorrectPassword'})
    assert res2.status_code == 401
    assert 'Invalid username or password' in res2.get_json()['error']

def test_logout_and_session_invalidation(client):
    """Test logout clears session and invalidates access."""
    # Register and login
    client.post('/api/register', json={'username': 'grace', 'password': 'PasswordGrace123'})
    client.post('/api/login', json={'username': 'grace', 'password': 'PasswordGrace123'})

    # Verify currently authenticated
    assert client.get('/api/auth/me').status_code == 200

    # Logout
    logout_res = client.post('/api/logout')
    assert logout_res.status_code == 200
    assert 'Logged out successfully' in logout_res.get_json()['message']

    # Verify unauthenticated after logout
    assert client.get('/api/auth/me').status_code == 401

def test_login_required_protection(client):
    """Test that endpoints with @login_required block unauthenticated callers."""
    # Direct access without session -> 401
    unauth_resp = client.get('/api/protected-test')
    assert unauth_resp.status_code == 401
    assert 'Authentication required' in unauth_resp.get_json()['error']

    # Login and try again -> 200
    client.post('/api/register', json={'username': 'heidi', 'password': 'PasswordHeidi123'})
    client.post('/api/login', json={'username': 'heidi', 'password': 'PasswordHeidi123'})
    auth_resp = client.get('/api/protected-test')
    assert auth_resp.status_code == 200
    assert 'Access granted' in auth_resp.get_json()['message']
