import pytest
from datetime import datetime, timezone
from app import create_app
from config import TestConfig
from extensions import db, socketio
from models.database import User, Message

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed test users
        alice = User(username='alice', public_key='PUB_KEY_ALICE')
        alice.set_password('Password123!')
        bob = User(username='bob', public_key='PUB_KEY_BOB')
        bob.set_password('Password123!')

        db.session.add_all([alice, bob])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_message_persistence(app):
    """Test creating and retrieving Message models from the database."""
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        bob = User.query.filter_by(username='bob').first()

        msg = Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            ciphertext='ENCRYPTED_PAYLOAD_BASE64',
            iv='IV_BASE64_96BIT',
            sender_encrypted_key='KEY_WRAPPED_FOR_ALICE',
            recipient_encrypted_key='KEY_WRAPPED_FOR_BOB',
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(msg)
        db.session.commit()

        saved = Message.query.filter_by(id=msg.id).first()
        assert saved is not None
        assert saved.sender_id == alice.id
        assert saved.recipient_id == bob.id
        assert saved.ciphertext == 'ENCRYPTED_PAYLOAD_BASE64'
        assert saved.iv == 'IV_BASE64_96BIT'
        assert saved.sender_encrypted_key == 'KEY_WRAPPED_FOR_ALICE'
        assert saved.recipient_encrypted_key == 'KEY_WRAPPED_FOR_BOB'

        # Test to_dict helper with user context
        alice_view = saved.to_dict(for_user_id=alice.id)
        assert alice_view['encrypted_key'] == 'KEY_WRAPPED_FOR_ALICE'

        bob_view = saved.to_dict(for_user_id=bob.id)
        assert bob_view['encrypted_key'] == 'KEY_WRAPPED_FOR_BOB'

def test_zero_plaintext_in_database(app):
    """Verify that the database stores only encrypted strings and zero plaintext."""
    plaintext = "Sensitive personal intelligence message 12345"
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        bob = User.query.filter_by(username='bob').first()

        msg = Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            ciphertext='4A6f9L/23kZ...',
            iv='xY7812901234',
            sender_encrypted_key='RSA_OAEP_WRAPPED_KEY_A',
            recipient_encrypted_key='RSA_OAEP_WRAPPED_KEY_B'
        )
        db.session.add(msg)
        db.session.commit()

        # Direct SQL inspection
        row = db.session.execute(
            db.text("SELECT ciphertext, sender_encrypted_key, recipient_encrypted_key FROM messages WHERE id = :id"),
            {'id': msg.id}
        ).fetchone()

        assert plaintext not in row[0]
        assert plaintext not in row[1]
        assert plaintext not in row[2]

def test_socket_message_persisted_to_db(app):
    """Test that emitting a Socket.IO message automatically persists it to SQLite."""
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        bob = User.query.filter_by(username='bob').first()
        alice_id = alice.id
        bob_id = bob.id

    client_alice = app.test_client()
    client_alice.post('/api/login', json={'username': 'alice', 'password': 'Password123!'})
    socket_alice = socketio.test_client(app, flask_test_client=client_alice)

    client_bob = app.test_client()
    client_bob.post('/api/login', json={'username': 'bob', 'password': 'Password123!'})
    socket_bob = socketio.test_client(app, flask_test_client=client_bob)

    # Alice sends message
    payload = {
        'recipient_id': bob_id,
        'ciphertext': 'SOCKET_CIPHERTEXT_123',
        'iv': 'SOCKET_IV_456',
        'sender_encrypted_key': 'KEY_FOR_ALICE_DB',
        'recipient_encrypted_key': 'KEY_FOR_BOB_DB'
    }
    socket_alice.emit('send_encrypted_message', payload)

    # Check ack
    alice_received = socket_alice.get_received()
    assert len(alice_received) > 0
    ack = [e for e in alice_received if e['name'] == 'message_sent_ack'][0]
    msg_id = ack['args'][0]['message_id']
    assert isinstance(msg_id, int)

    # Query DB to verify persistence
    with app.app_context():
        db_msg = db.session.get(Message, msg_id)
        assert db_msg is not None
        assert db_msg.sender_id == alice_id
        assert db_msg.recipient_id == bob_id
        assert db_msg.ciphertext == 'SOCKET_CIPHERTEXT_123'
        assert db_msg.iv == 'SOCKET_IV_456'
        assert db_msg.sender_encrypted_key == 'KEY_FOR_ALICE_DB'
        assert db_msg.recipient_encrypted_key == 'KEY_FOR_BOB_DB'

    socket_alice.disconnect()
    socket_bob.disconnect()

def test_cascade_deletion(app):
    """Test that deleting a user removes their messages via CASCADE."""
    with app.app_context():
        alice = User.query.filter_by(username='alice').first()
        bob = User.query.filter_by(username='bob').first()

        msg = Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            ciphertext='CIPHER',
            iv='IV',
            sender_encrypted_key='KEY_A',
            recipient_encrypted_key='KEY_B'
        )
        db.session.add(msg)
        db.session.commit()
        msg_id = msg.id

        # Delete alice
        db.session.delete(alice)
        db.session.commit()

        # Message should be removed
        assert db.session.get(Message, msg_id) is None
