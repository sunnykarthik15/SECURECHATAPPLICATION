import pytest
from app import create_app
from config import TestConfig

@pytest.fixture
def client():
    app = create_app(TestConfig)
    return app.test_client()

def test_crypto_test_page_served(client):
    """Test that the crypto test harness page is served with HTTP 200."""
    response = client.get('/test/crypto')
    assert response.status_code == 200
    assert b'Web Crypto &amp; IndexedDB Phase 3 Test Suite' in response.data or b'Web Crypto & IndexedDB Phase 3 Test Suite' in response.data
    assert b'/static/js/crypto.js' in response.data

def test_crypto_js_served_and_validated(client):
    """Test that static/js/crypto.js is accessible and contains required cryptographic primitives."""
    response = client.get('/static/js/crypto.js')
    assert response.status_code == 200
    content = response.data.decode('utf-8')

    # Primitives & Web Crypto verification
    assert 'RSA-OAEP' in content
    assert 'modulusLength: 2048' in content
    assert 'SHA-256' in content
    assert 'generateRSAKeyPair' in content
    assert 'exportPublicKey' in content
    assert 'importPublicKey' in content

    # IndexedDB storage verification
    assert 'openKeyDatabase' in content
    assert 'storePrivateKey' in content
    assert 'getPrivateKey' in content
    assert 'hasPrivateKey' in content
    assert 'clearPrivateKey' in content

    # Key exchange & caching verification
    assert 'fetchPeerPublicKey' in content
    assert 'clearPeerKeyCache' in content

    # AES-256-GCM message encryption verification
    assert 'generateAESKey' in content
    assert 'encryptMessageAES' in content
    assert 'decryptMessageAES' in content
    assert 'exportAESKeyRaw' in content
    assert 'importAESKeyRaw' in content
    assert 'AES-GCM' in content
    assert 'length: 256' in content
    assert 'tagLength: 128' in content
    assert 'Uint8Array(12)' in content  # 96-bit IV

    # RSA-OAEP hybrid key wrapping verification
    assert 'wrapKeyRSA' in content
    assert 'unwrapKeyRSA' in content
    assert 'encryptHybridMessage' in content
    assert 'decryptHybridMessage' in content
    assert 'decryptChatHistory' in content
    assert 'sender_encrypted_key' in content
    assert 'recipient_encrypted_key' in content

    # Security check: Ensure private keys are never sent to server
    assert 'POST' not in content
    assert 'XMLHttpRequest' not in content
