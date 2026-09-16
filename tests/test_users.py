import pytest
from app import create_app
from config import TestConfig
from extensions import db
from models.database import User

@pytest.fixture
def app():
    """Create test application context with populated users."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed test users
        for name in ['alice', 'bob', 'charlie', 'david']:
            u = User(username=name, public_key=f"PUB_KEY_{name.upper()}")
            u.set_password('Password123!')
            db.session.add(u)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_users_unauthenticated_access(client):
    """Test that unauthenticated requests to /api/users return 401."""
    response = client.get('/api/users')
    assert response.status_code == 401
    assert 'Authentication required' in response.get_json()['error']

def test_users_list_excludes_self(client):
    """Test that the user directory lists registered users excluding the caller."""
    # Login as alice
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})

    response = client.get('/api/users')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 3
    usernames = [u['username'] for u in data['users']]
    assert 'alice' not in usernames
    assert set(usernames) == {'bob', 'charlie', 'david'}
    assert all(u['has_public_key'] is True for u in data['users'])

def test_users_search_filter(client):
    """Test filtering users by search term."""
    # Login as alice
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})

    # Search for 'char'
    response = client.get('/api/users?search=char')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 1
    assert data['users'][0]['username'] == 'charlie'

    # Search for non-matching term
    empty_resp = client.get('/api/users?search=nonexistent')
    assert empty_resp.status_code == 200
    assert empty_resp.get_json()['count'] == 0

def test_get_user_by_id(client, app):
    """Test retrieving a specific user by ID."""
    # Login as alice
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})

    with app.app_context():
        bob = User.query.filter_by(username='bob').first()
        bob_id = bob.id

    # Fetch bob
    response = client.get(f'/api/users/{bob_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['username'] == 'bob'
    assert data['user']['public_key'] == 'PUB_KEY_BOB'

    # Non-existent user
    not_found = client.get('/api/users/99999')
    assert not_found.status_code == 404
    assert 'User not found' in not_found.get_json()['error']
