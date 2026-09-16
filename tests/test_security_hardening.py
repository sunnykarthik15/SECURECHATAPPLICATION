import uuid
import base64
import pytest
from app import create_app
from config import TestConfig
from extensions import db, socketio
from models.database import User, Message
from utils.security import (
    is_valid_uuid4,
    compute_public_key_fingerprint,
    limiter
)

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
        # Seed test users
        alice = User(username='alice_sec', public_key=SAMPLE_SPKI_KEY)
        alice.set_password('Password123!')
        bob = User(username='bob_sec', public_key=SAMPLE_SPKI_KEY)
        bob.set_password('Password123!')
        charlie = User(username='charlie_sec', public_key=SAMPLE_SPKI_KEY)
        charlie.set_password('Password123!')

        db.session.add_all([alice, bob, charlie])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


# ==========================================
# 1. PUBLIC KEY TRUST & FINGERPRINTS
# ==========================================

def test_deterministic_public_key_fingerprint():
    """Verify that identical public keys yield identical, deterministic SHA-256 fingerprints."""
    fp1 = compute_public_key_fingerprint(SAMPLE_SPKI_KEY)
    fp2 = compute_public_key_fingerprint(SAMPLE_SPKI_KEY)
    assert fp1 == fp2
    assert len(fp1.split(' ')) == 16  # 16 blocks of 4 hex digits
    for block in fp1.split(' '):
        assert len(block) == 4
        assert block.isalnum()
        assert not any(c.islower() for c in block)

def test_different_keys_yield_different_fingerprints():
    """Verify cryptographic preimage resistance: different keys produce distinct fingerprints."""
    fp1 = compute_public_key_fingerprint(SAMPLE_SPKI_KEY)
    modified_key = SAMPLE_SPKI_KEY[:-4] + "AAAA"
    fp2 = compute_public_key_fingerprint(modified_key)
    assert fp1 != fp2

def test_user_public_key_endpoint_returns_fingerprint(client, app):
    """Test that public key retrieval includes the deterministic SHA-256 fingerprint."""
    with app.app_context():
        alice = User.query.filter_by(username='alice_sec').first()
        alice_id = alice.id

    client.post('/api/login', json={'username': 'bob_sec', 'password': 'Password123!'})
    res = client.get(f'/api/users/{alice_id}/public_key')
    assert res.status_code == 200
    data = res.get_json()
    assert 'fingerprint' in data
    assert data['fingerprint'] == compute_public_key_fingerprint(SAMPLE_SPKI_KEY)


# ==========================================
# 2. STRUCTURED MESSAGE PROTOCOL & VALIDATION
# ==========================================

def test_uuid4_validation():
    """Verify strict validation of canonical UUIDv4 strings."""
    valid_uuid = str(uuid.uuid4())
    assert is_valid_uuid4(valid_uuid) is True
    assert is_valid_uuid4("not-a-uuid") is False
    assert is_valid_uuid4("12345678-1234-1234-1234-123456789012") is False  # not version 4
    assert is_valid_uuid4("") is False
    assert is_valid_uuid4(12345) is False

def test_rest_send_message_protocol_success(client, app):
    """Test sending a structured version:1 message over REST."""
    with app.app_context():
        alice = User.query.filter_by(username='alice_sec').first()
        bob = User.query.filter_by(username='bob_sec').first()
        bob_id = bob.id

    client.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
    msg_id = str(uuid.uuid4())

    payload = {
        'version': 1,
        'message_id': msg_id,
        'recipient_id': bob_id,
        'ciphertext': 'ENCRYPTED_CIPHERTEXT_SAMPLE',
        'iv': 'ENCRYPTED_IV_SAMPLE',
        'sender_encrypted_key': 'KEY_FOR_ALICE',
        'recipient_encrypted_key': 'KEY_FOR_BOB'
    }

    res = client.post('/api/chat/send', json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['status'] == 'stored'
    assert data['message_id'] == msg_id

def test_rest_send_unsupported_version_rejected(client, app):
    """Reject messages with unsupported protocol versions."""
    with app.app_context():
        bob = User.query.filter_by(username='bob_sec').first()
        bob_id = bob.id

    client.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
    payload = {
        'version': 99,  # Unsupported version
        'message_id': str(uuid.uuid4()),
        'recipient_id': bob_id,
        'ciphertext': 'CIPHER',
        'iv': 'IV',
        'sender_encrypted_key': 'KEY_A',
        'recipient_encrypted_key': 'KEY_B'
    }
    res = client.post('/api/chat/send', json=payload)
    assert res.status_code == 400
    assert 'Unsupported protocol version' in res.get_json()['error']

def test_rest_send_invalid_uuid_rejected(client, app):
    """Reject messages with malformed / non-UUIDv4 message IDs."""
    with app.app_context():
        bob = User.query.filter_by(username='bob_sec').first()
        bob_id = bob.id

    client.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
    payload = {
        'version': 1,
        'message_id': 'arbitrary-string-not-uuid',
        'recipient_id': bob_id,
        'ciphertext': 'CIPHER',
        'iv': 'IV',
        'sender_encrypted_key': 'KEY_A',
        'recipient_encrypted_key': 'KEY_B'
    }
    res = client.post('/api/chat/send', json=payload)
    assert res.status_code == 400
    assert 'Invalid message_id' in res.get_json()['error']

def test_rest_send_impersonation_rejected(client, app):
    """Verify that client cannot claim to be another sender."""
    with app.app_context():
        bob = User.query.filter_by(username='bob_sec').first()
        charlie = User.query.filter_by(username='charlie_sec').first()
        bob_id = bob.id
        charlie_id = charlie.id

    # Log in as Alice
    client.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
    payload = {
        'version': 1,
        'message_id': str(uuid.uuid4()),
        'sender_id': charlie_id,  # Spoofed sender!
        'recipient_id': bob_id,
        'ciphertext': 'CIPHER',
        'iv': 'IV',
        'sender_encrypted_key': 'KEY_A',
        'recipient_encrypted_key': 'KEY_B'
    }
    res = client.post('/api/chat/send', json=payload)
    assert res.status_code == 403
    assert 'Sender identity mismatch' in res.get_json()['error']


# ==========================================
# 3. REPLAY & DUPLICATE PROTECTION
# ==========================================

def test_replay_protection_rest_duplicate_rejected(client, app):
    """Test that submitting the same message_id twice via REST returns 409 Conflict."""
    with app.app_context():
        bob = User.query.filter_by(username='bob_sec').first()
        bob_id = bob.id

    client.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
    fixed_msg_id = str(uuid.uuid4())

    payload = {
        'version': 1,
        'message_id': fixed_msg_id,
        'recipient_id': bob_id,
        'ciphertext': 'ORIGINAL_CIPHERTEXT',
        'iv': 'ORIGINAL_IV',
        'sender_encrypted_key': 'KEY_A',
        'recipient_encrypted_key': 'KEY_B'
    }

    # First send: success (201)
    res1 = client.post('/api/chat/send', json=payload)
    assert res1.status_code == 201

    # Second send with identical message_id: duplicate rejected (409)
    res2 = client.post('/api/chat/send', json=payload)
    assert res2.status_code == 409
    assert 'Duplicate message_id' in res2.get_json()['error']

def test_replay_protection_socket_duplicate_rejected(app):
    """Test that emitting a duplicate message_id over Socket.IO triggers an error and prevents broadcast."""
    with app.app_context():
        alice = User.query.filter_by(username='alice_sec').first()
        bob = User.query.filter_by(username='bob_sec').first()
        alice_id = alice.id
        bob_id = bob.id

    client_alice = app.test_client()
    client_alice.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
    socket_alice = socketio.test_client(app, flask_test_client=client_alice)

    client_bob = app.test_client()
    client_bob.post('/api/login', json={'username': 'bob_sec', 'password': 'Password123!'})
    socket_bob = socketio.test_client(app, flask_test_client=client_bob)
    socket_bob.get_received()  # Clear connection ack

    fixed_uuid = str(uuid.uuid4())
    payload = {
        'version': 1,
        'message_id': fixed_uuid,
        'recipient_id': bob_id,
        'ciphertext': 'SOCKET_CIPHER',
        'iv': 'SOCKET_IV',
        'sender_encrypted_key': 'KEY_A',
        'recipient_encrypted_key': 'KEY_B'
    }

    # First submission: succeeds
    socket_alice.emit('send_encrypted_message', payload)
    bob_events = socket_bob.get_received()
    assert len(bob_events) == 1
    assert bob_events[0]['name'] == 'receive_encrypted_message'

    # Second submission (Replay attack): rejected
    socket_alice.emit('send_encrypted_message', payload)
    alice_events = socket_alice.get_received()
    err_events = [e for e in alice_events if e['name'] == 'error']
    assert len(err_events) == 1
    assert 'Duplicate message_id' in err_events[0]['args'][0]['error']

    # Bob must NOT receive a duplicate broadcast
    bob_events_replayed = socket_bob.get_received()
    assert len(bob_events_replayed) == 0

    socket_alice.disconnect()
    socket_bob.disconnect()


# ==========================================
# 4. ENCRYPTED KEY ISOLATION
# ==========================================

def test_encrypted_key_isolation_in_to_dict(app):
    """
    Test that Message.to_dict() returns only the contextual user's key
    and never leaks the opposite participant's key.
    """
    with app.app_context():
        alice = User.query.filter_by(username='alice_sec').first()
        bob = User.query.filter_by(username='bob_sec').first()
        charlie = User.query.filter_by(username='charlie_sec').first()

        msg = Message(
            message_id=str(uuid.uuid4()),
            version=1,
            sender_id=alice.id,
            recipient_id=bob.id,
            ciphertext='CIPHER',
            iv='IV',
            sender_encrypted_key='KEY_WRAPPED_FOR_ALICE_ONLY',
            recipient_encrypted_key='KEY_WRAPPED_FOR_BOB_ONLY'
        )
        db.session.add(msg)
        db.session.commit()

        # Alice's view: gets only Alice's key
        alice_view = msg.to_dict(for_user_id=alice.id)
        assert alice_view['encrypted_key'] == 'KEY_WRAPPED_FOR_ALICE_ONLY'
        assert 'sender_encrypted_key' not in alice_view
        assert 'recipient_encrypted_key' not in alice_view

        # Bob's view: gets only Bob's key
        bob_view = msg.to_dict(for_user_id=bob.id)
        assert bob_view['encrypted_key'] == 'KEY_WRAPPED_FOR_BOB_ONLY'
        assert 'sender_encrypted_key' not in bob_view
        assert 'recipient_encrypted_key' not in bob_view

        # Charlie (third party): gets None
        charlie_view = msg.to_dict(for_user_id=charlie.id)
        assert charlie_view['encrypted_key'] is None
        assert 'sender_encrypted_key' not in charlie_view
        assert 'recipient_encrypted_key' not in charlie_view


# ==========================================
# 5. AUTHENTICATION & INPUT HARDENING
# ==========================================

def test_excessive_password_length_rejected(client):
    """Reject passwords longer than 128 characters to protect against hashing CPU resource abuse."""
    long_password = "A" * 150
    res = client.post('/api/register', json={
        'username': 'too_long_pw_user',
        'password': long_password
    })
    assert res.status_code == 400
    assert 'maximum allowed length' in res.get_json()['error']

def test_rate_limiting_enforced(app):
    """Verify that process-local rate limiting throttles requests when configured."""
    app.config['FORCE_RATE_LIMIT_TEST'] = True
    client = app.test_client()
    limiter.reset()

    # Attempt 12 rapid logins (limit is 10 per minute)
    responses = []
    for _ in range(12):
        r = client.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
        responses.append(r.status_code)

    assert 429 in responses
    app.config['FORCE_RATE_LIMIT_TEST'] = False
    limiter.reset()


# ==========================================
# 6. CSRF PROTECTION ON STATE-CHANGING ENDPOINTS
# ==========================================

def test_csrf_protection_when_enabled(app):
    """Verify that state-changing requests without valid CSRF token are blocked with 403."""
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['FORCE_CSRF_TEST'] = True
    client = app.test_client()

    # 1. Login to establish session
    login_resp = client.post('/api/login', json={'username': 'alice_sec', 'password': 'Password123!'})
    assert login_resp.status_code == 200
    csrf_token = login_resp.get_json().get('csrf_token')
    assert csrf_token is not None

    # 2. State-changing request without CSRF header: blocked
    blocked_resp = client.put('/api/users/public_key', json={'public_key': SAMPLE_SPKI_KEY})
    assert blocked_resp.status_code == 403
    assert 'CSRF' in blocked_resp.get_json()['error']

    # 3. State-changing request with invalid CSRF token: blocked
    invalid_resp = client.put(
        '/api/users/public_key',
        json={'public_key': SAMPLE_SPKI_KEY},
        headers={'X-CSRF-Token': 'bogus-invalid-token'}
    )
    assert invalid_resp.status_code == 403

    # 4. State-changing request with valid CSRF token: allowed
    allowed_resp = client.put(
        '/api/users/public_key',
        json={'public_key': SAMPLE_SPKI_KEY},
        headers={'X-CSRF-Token': csrf_token}
    )
    assert allowed_resp.status_code == 200

    app.config['FORCE_CSRF_TEST'] = False
    app.config['WTF_CSRF_ENABLED'] = False
