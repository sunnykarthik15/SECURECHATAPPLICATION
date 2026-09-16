import pytest
from app import create_app
from config import TestConfig
from extensions import db, socketio
from models.database import User

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed users
        alice = User(username='alice', public_key='PUB_KEY_ALICE')
        alice.set_password('Password123!')
        bob = User(username='bob', public_key='PUB_KEY_BOB')
        bob.set_password('Password123!')
        charlie = User(username='charlie', public_key='PUB_KEY_CHARLIE')
        charlie.set_password('Password123!')

        db.session.add_all([alice, bob, charlie])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

def test_socket_unauthenticated_connection_rejected(app):
    """Test that an unauthenticated socket connection is rejected."""
    client = app.test_client()
    socket_client = socketio.test_client(app, flask_test_client=client)
    assert not socket_client.is_connected()

def test_socket_authenticated_connection(app):
    """Test that an authenticated user connects and joins private room."""
    client = app.test_client()
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})

    socket_client = socketio.test_client(app, flask_test_client=client)
    assert socket_client.is_connected()

    received = socket_client.get_received()
    assert len(received) > 0
    ack = received[0]
    assert ack['name'] == 'connected_ack'
    assert ack['args'][0]['username'] == 'alice'
    assert ack['args'][0]['room'].startswith('user_')

    socket_client.disconnect()

def test_send_encrypted_message_routing(app):
    """Test that Alice can send an encrypted message to Bob, and Bob receives it."""
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        bob = User.query.filter_by(username='bob').first()
        alice_id = alice.id
        bob_id = bob.id

    # Client A: Alice
    client_alice = app.test_client()
    client_alice.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    socket_alice = socketio.test_client(app, flask_test_client=client_alice)
    assert socket_alice.is_connected()
    socket_alice.get_received()  # Clear ack

    # Client B: Bob
    client_bob = app.test_client()
    client_bob.post('/api/login', json={'username': 'bob', 'password': 'Password123!'})
    socket_bob = socketio.test_client(app, flask_test_client=client_bob)
    assert socket_bob.is_connected()
    socket_bob.get_received()  # Clear ack

    # Alice sends encrypted payload for Bob
    payload = {
        'recipient_id': bob_id,
        'ciphertext': 'CIPHERTEXT_BASE64_SAMPLE',
        'iv': 'IV_BASE64_SAMPLE_12B',
        'sender_encrypted_key': 'KEY_WRAPPED_FOR_ALICE',
        'recipient_encrypted_key': 'KEY_WRAPPED_FOR_BOB'
    }
    socket_alice.emit('send_encrypted_message', payload)

    # Verify Alice receives message_sent_ack
    alice_received = socket_alice.get_received()
    assert len(alice_received) == 1
    assert alice_received[0]['name'] == 'message_sent_ack'
    assert alice_received[0]['args'][0]['recipient_id'] == bob_id

    # Verify Bob receives receive_encrypted_message
    bob_received = socket_bob.get_received()
    assert len(bob_received) == 1
    msg_event = bob_received[0]
    assert msg_event['name'] == 'receive_encrypted_message'
    msg_data = msg_event['args'][0]
    assert msg_data['sender_id'] == alice_id
    assert msg_data['sender_username'] == 'alice'
    assert msg_data['recipient_id'] == bob_id
    assert msg_data['ciphertext'] == 'CIPHERTEXT_BASE64_SAMPLE'
    assert msg_data['iv'] == 'IV_BASE64_SAMPLE_12B'
    assert msg_data['encrypted_key'] == 'KEY_WRAPPED_FOR_BOB'

    socket_alice.disconnect()
    socket_bob.disconnect()

def test_private_message_isolation(app):
    """Test that User C does NOT receive messages exchanged between Alice and Bob."""
    with app.app_context():
        bob = User.query.filter_by(username='bob').first()
        bob_id = bob.id

    client_alice = app.test_client()
    client_alice.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    socket_alice = socketio.test_client(app, flask_test_client=client_alice)

    client_charlie = app.test_client()
    client_charlie.post('/api/login', json={'username': 'charlie', 'password': 'Password123!'})
    socket_charlie = socketio.test_client(app, flask_test_client=client_charlie)
    socket_charlie.get_received()  # Clear ack

    # Alice sends to Bob
    socket_alice.emit('send_encrypted_message', {
        'recipient_id': bob_id,
        'ciphertext': 'SECRET_TEXT',
        'iv': 'SECRET_IV',
        'sender_encrypted_key': 'KEY_ALICE',
        'recipient_encrypted_key': 'KEY_BOB'
    })

    # Assert Charlie received nothing
    charlie_received = socket_charlie.get_received()
    assert len(charlie_received) == 0

    socket_alice.disconnect()
    socket_charlie.disconnect()

def test_send_message_validation_errors(app):
    """Test payload validations on send_encrypted_message."""
    client = app.test_client()
    client.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    socket_client = socketio.test_client(app, flask_test_client=client)
    socket_client.get_received()

    # Missing fields
    socket_client.emit('send_encrypted_message', {'recipient_id': 9999})
    received = socket_client.get_received()
    assert len(received) == 1
    assert received[0]['name'] == 'error'
    assert 'Recipient not found' in received[0]['args'][0]['error']

    socket_client.disconnect()
