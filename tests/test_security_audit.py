import base64
import os
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from app import create_app
from config import TestConfig
from extensions import db, socketio
from models.database import User, Message

def generate_test_rsa_keypair():
    """Generate RSA-2048 keypair matching Web Crypto specifications."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    # Export public key to SPKI Base64 format
    spki_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    spki_b64 = base64.b64encode(spki_bytes).decode('utf-8')
    return private_key, public_key, spki_b64

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Create users with cryptographically valid RSA keys
        alice_priv, alice_pub, alice_spki = generate_test_rsa_keypair()
        bob_priv, bob_pub, bob_spki = generate_test_rsa_keypair()
        charlie_priv, charlie_pub, charlie_spki = generate_test_rsa_keypair()

        u_alice = User(username='alice', public_key=alice_spki)
        u_alice.set_password('PasswordAlice123!')
        u_bob = User(username='bob', public_key=bob_spki)
        u_bob.set_password('PasswordBob123!')
        u_charlie = User(username='charlie', public_key=charlie_spki)
        u_charlie.set_password('PasswordCharlie123!')

        db.session.add_all([u_alice, u_bob, u_charlie])
        db.session.commit()

        yield {
            'app': app,
            'alice': (u_alice.id, alice_priv, alice_pub, alice_spki),
            'bob': (u_bob.id, bob_priv, bob_pub, bob_spki),
            'charlie': (u_charlie.id, charlie_priv, charlie_pub, charlie_spki)
        }
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app['app'].test_client()

def test_adversary_eavesdropping_zero_plaintext(app, client):
    """
    Simulate a malicious database administrator or attacker eavesdropping on the database.
    Verify that sensitive message text does not appear in database tables.
    """
    secret_text = "CONFIDENTIAL_FINANCIAL_RECORD_98765"
    alice_id, alice_priv, alice_pub, _ = app['alice']
    bob_id, bob_priv, bob_pub, _ = app['bob']

    # Encrypt hybrid message
    aes_key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(aes_key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, secret_text.encode('utf-8'), None)

    # Wrap key for Alice and Bob
    oaep_padding = padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
    wrapped_alice = alice_pub.encrypt(aes_key, oaep_padding)
    wrapped_bob = bob_pub.encrypt(aes_key, oaep_padding)

    with app['app'].app_context():
        msg = Message(
            sender_id=alice_id,
            recipient_id=bob_id,
            ciphertext=base64.b64encode(ciphertext).decode('utf-8'),
            iv=base64.b64encode(iv).decode('utf-8'),
            sender_encrypted_key=base64.b64encode(wrapped_alice).decode('utf-8'),
            recipient_encrypted_key=base64.b64encode(wrapped_bob).decode('utf-8')
        )
        db.session.add(msg)
        db.session.commit()

        # Direct SQL search across all columns in messages
        raw_rows = db.session.execute(db.text("SELECT * FROM messages WHERE id = :id"), {'id': msg.id}).fetchall()
        for row in raw_rows:
            for field in row:
                assert secret_text not in str(field)

def test_private_key_leakage_audit(app, client):
    """
    Audit all server API endpoints and assert that private keys are NEVER leaked in responses.
    """
    client.post('/api/login', json={'username': 'alice', 'password': 'PasswordAlice123!'})

    endpoints = [
        ('/api/auth/me', 'GET', None),
        ('/api/users', 'GET', None),
        (f"/api/users/{app['alice'][0]}", 'GET', None),
        (f"/api/users/{app['bob'][0]}/public_key", 'GET', None),
        (f"/api/chat/history/{app['bob'][0]}", 'GET', None),
    ]

    forbidden_patterns = ['private_key', 'BEGIN RSA PRIVATE KEY', 'BEGIN PRIVATE KEY', 'PRIVATE KEY']

    for url, method, data in endpoints:
        if method == 'GET':
            resp = client.get(url)
        else:
            resp = client.post(url, json=data)

        raw_content = resp.data.decode('utf-8')
        for pattern in forbidden_patterns:
            assert pattern not in raw_content, f"Leakage detected at {url}: contains {pattern}"

def test_horizontal_privilege_escalation_chat_history(app, client):
    """
    Test that User Charlie cannot access the encrypted dialogue between Alice and Bob.
    """
    alice_id = app['alice'][0]
    bob_id = app['bob'][0]

    # Seed Alice and Bob dialogue
    with app['app'].app_context():
        msg = Message(
            sender_id=alice_id,
            recipient_id=bob_id,
            ciphertext='CIPHER_AB',
            iv='IV_AB',
            sender_encrypted_key='KEY_A',
            recipient_encrypted_key='KEY_B'
        )
        db.session.add(msg)
        db.session.commit()

    # Login as Charlie
    client.post('/api/login', json={'username': 'charlie', 'password': 'PasswordCharlie123!'})

    # Charlie attempts to request history with Alice
    resp = client.get(f'/api/chat/history/{alice_id}')
    assert resp.status_code == 200
    assert resp.get_json()['count'] == 0

    # Charlie attempts to request history with Bob
    resp_bob = client.get(f'/api/chat/history/{bob_id}')
    assert resp_bob.status_code == 200
    assert resp_bob.get_json()['count'] == 0

def test_impersonation_prevention_on_socket_send(app):
    """
    Verify that if an attacker sends a spoofed sender_id over Socket.IO,
    the server ignores it and enforces the true session user_id.
    """
    alice_id = app['alice'][0]
    bob_id = app['bob'][0]
    charlie_id = app['charlie'][0]

    # Charlie logs in
    client_charlie = app['app'].test_client()
    client_charlie.post('/api/login', json={'username': 'charlie', 'password': 'PasswordCharlie123!'})
    socket_charlie = socketio.test_client(app['app'], flask_test_client=client_charlie)

    # Charlie tries to spoof Alice as sender
    socket_charlie.emit('send_encrypted_message', {
        'sender_id': alice_id,  # Spoofed!
        'recipient_id': bob_id,
        'ciphertext': 'SPOOFED_CIPHER',
        'iv': 'SPOOFED_IV',
        'sender_encrypted_key': 'KEY_SPOOFED',
        'recipient_encrypted_key': 'KEY_BOB'
    })

    ack = socket_charlie.get_received()
    msg_id = [e for e in ack if e['name'] == 'message_sent_ack'][0]['args'][0]['message_id']

    # Verify that in the database, the sender is Charlie, NOT Alice!
    with app['app'].app_context():
        persisted = db.session.get(Message, msg_id)
        assert persisted.sender_id == charlie_id
        assert persisted.sender_id != alice_id

    socket_charlie.disconnect()

def test_unauthorized_public_key_tampering(app, client):
    """
    Verify that an attacker cannot overwrite another user's public key by passing target user_id.
    """
    alice_id = app['alice'][0]
    original_alice_key = app['alice'][3]

    # Login as Charlie
    client.post('/api/login', json={'username': 'charlie', 'password': 'PasswordCharlie123!'})

    # Charlie attempts to overwrite Alice's key
    charlie_fake_key = original_alice_key[:100] + "TAMPERED" + original_alice_key[108:]
    res = client.put('/api/users/public_key', json={
        'user_id': alice_id,  # Malicious attempt to target Alice
        'public_key': charlie_fake_key
    })
    assert res.status_code == 200

    # Verify Alice's key in the DB is completely unchanged
    with app['app'].app_context():
        alice_user = db.session.get(User, alice_id)
        assert alice_user.public_key == original_alice_key
        assert alice_user.public_key != charlie_fake_key

def test_cryptographic_bit_flip_tamper_detection(app):
    """
    Verify that AES-256-GCM authentication tag and RSA-OAEP wrapping detect tampering.
    """
    alice_id, alice_priv, alice_pub, _ = app['alice']
    bob_id, bob_priv, bob_pub, _ = app['bob']

    plaintext = b"Cryptographic security verification test message."
    aes_key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(aes_key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    oaep_padding = padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
    wrapped_bob = bob_pub.encrypt(aes_key, oaep_padding)

    # 1. Valid Decryption Test
    unwrapped_key = bob_priv.decrypt(wrapped_bob, oaep_padding)
    assert unwrapped_key == aes_key
    decrypted = AESGCM(unwrapped_key).decrypt(iv, ciphertext, None)
    assert decrypted == plaintext

    # 2. Ciphertext Bit-Flip Attack Test
    tampered_ciphertext = bytearray(ciphertext)
    tampered_ciphertext[0] ^= 0x01  # Flip 1 bit
    with pytest.raises(InvalidTag):
        AESGCM(unwrapped_key).decrypt(iv, bytes(tampered_ciphertext), None)

    # 3. IV Bit-Flip Attack Test
    tampered_iv = bytearray(iv)
    tampered_iv[0] ^= 0x01  # Flip 1 bit in IV
    with pytest.raises(InvalidTag):
        AESGCM(unwrapped_key).decrypt(bytes(tampered_iv), ciphertext, None)

    # 4. Key Wrapping Tamper Test
    tampered_wrapped = bytearray(wrapped_bob)
    tampered_wrapped[0] ^= 0x01
    with pytest.raises(ValueError):
        bob_priv.decrypt(bytes(tampered_wrapped), oaep_padding)
