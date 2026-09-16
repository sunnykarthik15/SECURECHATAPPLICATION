import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from config import TestConfig
from extensions import db
from models.database import User, Message

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        alice = User(username='alice', public_key='PUB_KEY_ALICE')
        alice.set_password('Password123!')
        bob = User(username='bob', public_key='PUB_KEY_BOB')
        bob.set_password('Password123!')
        charlie = User(username='charlie', public_key='PUB_KEY_CHARLIE')
        charlie.set_password('Password123!')

        db.session.add_all([alice, bob, charlie])
        db.session.commit()

        # Seed messages between Alice and Bob
        t0 = datetime.now(timezone.utc)
        m1 = Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            ciphertext='CIPHER_1_ALICE_TO_BOB',
            iv='IV_1',
            sender_encrypted_key='KEY_1_FOR_ALICE',
            recipient_encrypted_key='KEY_1_FOR_BOB',
            created_at=t0
        )
        m2 = Message(
            sender_id=bob.id,
            recipient_id=alice.id,
            ciphertext='CIPHER_2_BOB_TO_ALICE',
            iv='IV_2',
            sender_encrypted_key='KEY_2_FOR_BOB',
            recipient_encrypted_key='KEY_2_FOR_ALICE',
            created_at=t0 + timedelta(seconds=10)
        )
        m3 = Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            ciphertext='CIPHER_3_ALICE_TO_BOB',
            iv='IV_3',
            sender_encrypted_key='KEY_3_FOR_ALICE',
            recipient_encrypted_key='KEY_3_FOR_BOB',
            created_at=t0 + timedelta(seconds=20)
        )
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_chat_history_alice_perspective(client, app):
    """Test history retrieval from Alice's perspective with correct contextual keys."""
    with app.app_context():
        bob = User.query.filter_by(username='bob').first()
        bob_id = bob.id

    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    response = client.get(f'/api/chat/history/{bob_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 3
    messages = data['messages']

    # Msg 1 (Alice sent) -> encrypted_key is KEY_1_FOR_ALICE
    assert messages[0]['ciphertext'] == 'CIPHER_1_ALICE_TO_BOB'
    assert messages[0]['encrypted_key'] == 'KEY_1_FOR_ALICE'

    # Msg 2 (Bob sent) -> encrypted_key is KEY_2_FOR_ALICE
    assert messages[1]['ciphertext'] == 'CIPHER_2_BOB_TO_ALICE'
    assert messages[1]['encrypted_key'] == 'KEY_2_FOR_ALICE'

    # Msg 3 (Alice sent) -> encrypted_key is KEY_3_FOR_ALICE
    assert messages[2]['ciphertext'] == 'CIPHER_3_ALICE_TO_BOB'
    assert messages[2]['encrypted_key'] == 'KEY_3_FOR_ALICE'

def test_get_chat_history_bob_perspective(client, app):
    """Test history retrieval from Bob's perspective with correct contextual keys."""
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        alice_id = alice.id

    client.post('/api/login', json={'username': 'bob', 'password': 'Password123!'})
    response = client.get(f'/api/chat/history/{alice_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 3
    messages = data['messages']

    # Msg 1 (Alice sent to Bob) -> encrypted_key is KEY_1_FOR_BOB
    assert messages[0]['ciphertext'] == 'CIPHER_1_ALICE_TO_BOB'
    assert messages[0]['encrypted_key'] == 'KEY_1_FOR_BOB'

    # Msg 2 (Bob sent to Alice) -> encrypted_key is KEY_2_FOR_BOB
    assert messages[1]['ciphertext'] == 'CIPHER_2_BOB_TO_ALICE'
    assert messages[1]['encrypted_key'] == 'KEY_2_FOR_BOB'

    # Msg 3 (Alice sent to Bob) -> encrypted_key is KEY_3_FOR_BOB
    assert messages[2]['ciphertext'] == 'CIPHER_3_ALICE_TO_BOB'
    assert messages[2]['encrypted_key'] == 'KEY_3_FOR_BOB'

def test_chat_history_isolation_charlie(client, app):
    """Test that Charlie cannot see Alice and Bob's chat history."""
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        alice_id = alice.id

    client.post('/api/login', json={'username': 'charlie', 'password': 'Password123!'})
    response = client.get(f'/api/chat/history/{alice_id}')
    assert response.status_code == 200
    data = response.get_json()
    # Zero messages between Charlie and Alice
    assert data['count'] == 0
    assert len(data['messages']) == 0

def test_chat_history_unauthenticated(client, app):
    """Test that unauthenticated requests to history endpoint return 401."""
    with app.app_context():
        bob = User.query.filter_by(username='bob').first()
        bob_id = bob.id

    response = client.get(f'/api/chat/history/{bob_id}')
    assert response.status_code == 401
    assert 'Authentication required' in response.get_json()['error']

def test_chat_history_nonexistent_contact(client):
    """Test that requesting history for a nonexistent contact returns 404."""
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    response = client.get('/api/chat/history/99999')
    assert response.status_code == 404
    assert 'Contact user not found' in response.get_json()['error']

def test_chat_history_pagination(client, app):
    """Test pagination bounds (limit & offset)."""
    with app.app_context():
        bob = User.query.filter_by(username='bob').first()
        bob_id = bob.id

    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    response = client.get(f'/api/chat/history/{bob_id}?limit=1&offset=1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 1
    assert data['messages'][0]['ciphertext'] == 'CIPHER_2_BOB_TO_ALICE'
