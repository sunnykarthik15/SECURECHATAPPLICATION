import pytest
from app import create_app
from config import TestConfig
from extensions import db
from models.database import User

SAMPLE_SPKI_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzX1YgQ5Q8+hG7M0YhZ..."
    "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
)

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed users
        alice = User(username='alice', public_key=SAMPLE_SPKI_KEY)
        alice.set_password('Password123!')
        bob = User(username='bob', public_key="") # Bob has no key yet
        bob.set_password('Password123!')
        charlie = User(username='charlie', public_key=SAMPLE_SPKI_KEY)
        charlie.set_password('Password123!')

        db.session.add_all([alice, bob, charlie])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_peer_public_key_success(client, app):
    """Test retrieving peer's public key when authenticated."""
    with app.app_context():
        charlie = User.query.filter_by(username='charlie').first()
        charlie_id = charlie.id

    # Login as alice
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})

    # Fetch charlie's public key
    response = client.get(f'/api/users/{charlie_id}/public_key')
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'charlie'
    assert data['public_key'] == SAMPLE_SPKI_KEY

def test_get_peer_public_key_unauthenticated(client, app):
    """Test that unauthenticated requests to public_key endpoint return 401."""
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        alice_id = alice.id

    response = client.get(f'/api/users/{alice_id}/public_key')
    assert response.status_code == 401
    assert 'Authentication required' in response.get_json()['error']

def test_get_peer_public_key_not_found(client):
    """Test requesting public key for nonexistent user returns 404."""
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    response = client.get('/api/users/99999/public_key')
    assert response.status_code == 404
    assert 'User not found' in response.get_json()['error']

def test_get_peer_public_key_missing(client, app):
    """Test requesting public key for user who has not registered one returns 404."""
    with app.app_context():
        bob = User.query.filter_by(username='bob').first()
        bob_id = bob.id

    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    response = client.get(f'/api/users/{bob_id}/public_key')
    assert response.status_code == 404
    assert 'not registered a public key' in response.get_json()['error']

def test_update_public_key_success(client, app):
    """Test authenticated user can upload or update their public RSA key."""
    # Login as bob (who had no key)
    client.post('/api/login', json={'username': 'bob', 'password': 'Password123!'})

    new_key = SAMPLE_SPKI_KEY + "_BOB_NEW"
    response = client.put('/api/users/public_key', json={'public_key': new_key})
    assert response.status_code == 200
    assert 'updated successfully' in response.get_json()['message']

    # Verify key is now persisted in DB
    with app.app_context():
        bob = User.query.filter_by(username='bob').first()
        assert bob.public_key == new_key

def test_update_public_key_validation(client):
    """Test validation constraints on public key upload."""
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})

    # Empty body
    assert client.put('/api/users/public_key', data="").status_code == 400

    # Missing public_key field
    res = client.put('/api/users/public_key', json={'other': 'data'})
    assert res.status_code == 400
    assert 'cannot be empty' in res.get_json()['error']

    # Key too short (< 100 chars)
    short_res = client.put('/api/users/public_key', json={'public_key': 'too_short'})
    assert short_res.status_code == 400
    assert 'Invalid public key format or length' in short_res.get_json()['error']

    # Key too long (> 4096 chars)
    long_key = 'A' * 5000
    long_res = client.put('/api/users/public_key', json={'public_key': long_key})
    assert long_res.status_code == 400
    assert 'Invalid public key format or length' in long_res.get_json()['error']
