/**
 * Secure Chat Application - Client-Side Cryptographic Engine
 * Standards: RSA-2048 (RSA-OAEP with SHA-256) & AES-256-GCM
 *
 * All private keys and trusted-key verification records remain strictly in browser IndexedDB.
 * Plaintext content and private keys are NEVER transmitted to the server.
 *
 * Note on IndexedDB: IndexedDB provides persistent client-side storage within the browser
 * sandbox. It is NOT hardware-backed secure storage (such as a hardware TPM or Secure Enclave).
 */

const CryptoEngine = (function () {
    'use strict';

    const DB_NAME = 'SecureChatCryptoDB';
    const DB_VERSION = 2;
    const STORE_NAME = 'privateKeys';
    const TRUSTED_STORE_NAME = 'trustedFingerprints';

    // --- Base64 Utilities ---
    function arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    function base64ToArrayBuffer(base64) {
        const binary = window.atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    // --- Canonical UUIDv4 Generator ---
    function generateUUIDv4() {
        if (window.crypto && typeof window.crypto.randomUUID === 'function') {
            return window.crypto.randomUUID();
        }
        const bytes = new Uint8Array(16);
        window.crypto.getRandomValues(bytes);
        bytes[6] = (bytes[6] & 0x0f) | 0x40; // RFC 4122 v4
        bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant RFC 4122
        const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
        return [
            hex.substring(0, 8),
            hex.substring(8, 12),
            hex.substring(12, 16),
            hex.substring(16, 20),
            hex.substring(20, 32)
        ].join('-');
    }

    // --- Deterministic SHA-256 Fingerprint Generator ---
    async function computeKeyFingerprint(spkiBase64) {
        if (!spkiBase64 || typeof spkiBase64 !== 'string') return '';
        const cleanB64 = spkiBase64.replace(/\s+/g, '');
        const buffer = base64ToArrayBuffer(cleanB64);
        const hashBuffer = await window.crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
        // Format as 4-character blocks separated by space: AB12 CD34 EF56 ...
        const blocks = hex.match(/.{1,4}/g) || [];
        return blocks.join(' ');
    }

    // --- IndexedDB Key Store for Persistent Private Key & Trusted Fingerprint Isolation ---
    function openKeyDatabase() {
        return new Promise((resolve, reject) => {
            const request = window.indexedDB.open(DB_NAME, DB_VERSION);

            request.onupgradeneeded = function (event) {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, { keyPath: 'username' });
                }
                if (!db.objectStoreNames.contains(TRUSTED_STORE_NAME)) {
                    db.createObjectStore(TRUSTED_STORE_NAME, { keyPath: 'id' });
                }
            };

            request.onsuccess = function (event) {
                resolve(event.target.result);
            };

            request.onerror = function (event) {
                reject(new Error('IndexedDB access failed: ' + event.target.error));
            };
        });
    }

    async function storePrivateKey(username, privateKey) {
        if (!username || !privateKey) {
            throw new Error('Username and privateKey are required to store private key.');
        }
        const db = await openKeyDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const request = store.put({ username: username, privateKey: privateKey });

            request.onsuccess = () => resolve(true);
            request.onerror = (e) => reject(new Error('Failed to store private key: ' + e.target.error));
        });
    }

    async function getPrivateKey(username) {
        if (!username) {
            throw new Error('Username is required to retrieve private key.');
        }
        const db = await openKeyDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readonly');
            const store = tx.objectStore(STORE_NAME);
            const request = store.get(username);

            request.onsuccess = function (e) {
                if (e.target.result && e.target.result.privateKey) {
                    resolve(e.target.result.privateKey);
                } else {
                    resolve(null);
                }
            };
            request.onerror = (e) => reject(new Error('Failed to retrieve private key: ' + e.target.error));
        });
    }

    async function hasPrivateKey(username) {
        const key = await getPrivateKey(username);
        return key !== null;
    }

    async function clearPrivateKey(username) {
        const db = await openKeyDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORE_NAME, 'readwrite');
            const store = tx.objectStore(STORE_NAME);
            const request = store.delete(username);

            request.onsuccess = () => resolve(true);
            request.onerror = (e) => reject(new Error('Failed to clear private key: ' + e.target.error));
        });
    }

    // --- IndexedDB Trusted Fingerprint Management (Scoped by Account) ---
    async function storeTrustedFingerprint(accountUser, contactId, fingerprint) {
        if (!accountUser || contactId === undefined || !fingerprint) {
            throw new Error('accountUser, contactId, and fingerprint are required.');
        }
        const db = await openKeyDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(TRUSTED_STORE_NAME, 'readwrite');
            const store = tx.objectStore(TRUSTED_STORE_NAME);
            const id = `${accountUser}_${contactId}`;
            const request = store.put({
                id: id,
                accountUser: accountUser,
                contactId: contactId,
                fingerprint: fingerprint,
                trustedAt: new Date().toISOString()
            });

            request.onsuccess = () => resolve(true);
            request.onerror = (e) => reject(new Error('Failed to store trusted fingerprint: ' + e.target.error));
        });
    }

    async function getTrustedFingerprint(accountUser, contactId) {
        if (!accountUser || contactId === undefined) return null;
        const db = await openKeyDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(TRUSTED_STORE_NAME, 'readonly');
            const store = tx.objectStore(TRUSTED_STORE_NAME);
            const id = `${accountUser}_${contactId}`;
            const request = store.get(id);

            request.onsuccess = function (e) {
                if (e.target.result && e.target.result.fingerprint) {
                    resolve(e.target.result.fingerprint);
                } else {
                    resolve(null);
                }
            };
            request.onerror = (e) => reject(new Error('Failed to retrieve trusted fingerprint: ' + e.target.error));
        });
    }

    async function clearTrustedFingerprints(accountUser) {
        const db = await openKeyDatabase();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(TRUSTED_STORE_NAME, 'readwrite');
            const store = tx.objectStore(TRUSTED_STORE_NAME);
            const request = store.openCursor();

            request.onsuccess = function (e) {
                const cursor = e.target.result;
                if (cursor) {
                    if (cursor.value.accountUser === accountUser) {
                        cursor.delete();
                    }
                    cursor.continue();
                } else {
                    resolve(true);
                }
            };
            request.onerror = (e) => reject(new Error('Failed to clear trusted fingerprints: ' + e.target.error));
        });
    }

    // --- RSA-2048 Key Generation, Export & Import ---
    async function generateRSAKeyPair() {
        if (!window.crypto || !window.crypto.subtle) {
            throw new Error('Web Crypto API is not supported in this browser.');
        }

        const keyPair = await window.crypto.subtle.generateKey(
            {
                name: 'RSA-OAEP',
                modulusLength: 2048,
                publicExponent: new Uint8Array([1, 0, 1]), // 65537
                hash: 'SHA-256'
            },
            true, // extractable for export and storage
            ['encrypt', 'decrypt', 'wrapKey', 'unwrapKey']
        );

        return keyPair;
    }

    async function exportPublicKey(publicKey) {
        if (!publicKey) {
            throw new Error('Public key is required for export.');
        }
        const spkiBuffer = await window.crypto.subtle.exportKey('spki', publicKey);
        return arrayBufferToBase64(spkiBuffer);
    }

    async function importPublicKey(spkiBase64) {
        if (!spkiBase64) {
            throw new Error('SPKI Base64 string is required for import.');
        }
        const spkiBuffer = base64ToArrayBuffer(spkiBase64);
        const importedKey = await window.crypto.subtle.importKey(
            'spki',
            spkiBuffer,
            {
                name: 'RSA-OAEP',
                hash: 'SHA-256'
            },
            true,
            ['encrypt', 'wrapKey']
        );
        return importedKey;
    }

    // In-memory cache for imported peer CryptoKey instances (userId -> CryptoKey)
    const peerPublicKeyCache = new Map();

    async function fetchPeerPublicKey(userId) {
        if (!userId) {
            throw new Error('User ID is required to fetch public key.');
        }

        if (peerPublicKeyCache.has(userId)) {
            return peerPublicKeyCache.get(userId);
        }

        const response = await fetch('/api/users/' + encodeURIComponent(userId) + '/public_key', {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || ('Failed to fetch public key for user ' + userId));
        }

        const data = await response.json();
        const importedKey = await importPublicKey(data.public_key);
        peerPublicKeyCache.set(userId, importedKey);
        return importedKey;
    }

    function clearPeerKeyCache() {
        peerPublicKeyCache.clear();
    }

    // --- AES-256-GCM Symmetric Message Encryption Engine ---

    async function generateAESKey() {
        if (!window.crypto || !window.crypto.subtle) {
            throw new Error('Web Crypto API is not supported in this browser.');
        }
        return await window.crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            true, // extractable for RSA-OAEP wrapping in Phase 6
            ['encrypt', 'decrypt']
        );
    }

    async function encryptMessageAES(plaintext, aesKey) {
        if (typeof plaintext !== 'string') {
            throw new Error('Plaintext must be a string.');
        }
        if (!aesKey) {
            throw new Error('AES key is required for encryption.');
        }

        // Generate a cryptographically random, unique 96-bit (12-byte) IV for EVERY message
        const iv = window.crypto.getRandomValues(new Uint8Array(12));
        const encodedData = new TextEncoder().encode(plaintext);

        const ciphertextBuffer = await window.crypto.subtle.encrypt(
            {
                name: 'AES-GCM',
                iv: iv,
                tagLength: 128 // 128-bit authentication tag appended automatically
            },
            aesKey,
            encodedData
        );

        return {
            ciphertext: arrayBufferToBase64(ciphertextBuffer),
            iv: arrayBufferToBase64(iv.buffer)
        };
    }

    async function decryptMessageAES(ciphertextBase64, ivBase64, aesKey) {
        if (!ciphertextBase64 || !ivBase64) {
            throw new Error('Ciphertext and IV are required for decryption.');
        }
        if (!aesKey) {
            throw new Error('AES key is required for decryption.');
        }

        const ciphertextBuffer = base64ToArrayBuffer(ciphertextBase64);
        const ivBuffer = base64ToArrayBuffer(ivBase64);

        try {
            const decryptedBuffer = await window.crypto.subtle.decrypt(
                {
                    name: 'AES-GCM',
                    iv: new Uint8Array(ivBuffer),
                    tagLength: 128
                },
                aesKey,
                ciphertextBuffer
            );

            return new TextDecoder().decode(decryptedBuffer);
        } catch (err) {
            // Authentication tag mismatch or data tampering throws OperationError
            throw new Error('Decryption failed: Message authentication tag mismatch or corrupted ciphertext.');
        }
    }

    async function exportAESKeyRaw(aesKey) {
        if (!aesKey) {
            throw new Error('AES key is required to export.');
        }
        return await window.crypto.subtle.exportKey('raw', aesKey);
    }

    async function importAESKeyRaw(rawBuffer) {
        if (!rawBuffer) {
            throw new Error('Raw key buffer is required to import.');
        }
        return await window.crypto.subtle.importKey(
            'raw',
            rawBuffer,
            { name: 'AES-GCM' },
            true,
            ['encrypt', 'decrypt']
        );
    }

    // --- RSA-OAEP Key Wrapping & Hybrid Encryption Engine ---

    async function wrapKeyRSA(aesKey, rsaPublicKey) {
        if (!aesKey || !rsaPublicKey) {
            throw new Error('AES key and RSA public key are required for key wrapping.');
        }
        const rawKeyBuffer = await exportAESKeyRaw(aesKey);
        const wrappedBuffer = await window.crypto.subtle.encrypt(
            { name: 'RSA-OAEP' },
            rsaPublicKey,
            rawKeyBuffer
        );
        return arrayBufferToBase64(wrappedBuffer);
    }

    async function unwrapKeyRSA(encryptedKeyBase64, rsaPrivateKey) {
        if (!encryptedKeyBase64 || !rsaPrivateKey) {
            throw new Error('Encrypted key and RSA private key are required for unwrapping.');
        }
        const wrappedBuffer = base64ToArrayBuffer(encryptedKeyBase64);
        try {
            const rawKeyBuffer = await window.crypto.subtle.decrypt(
                { name: 'RSA-OAEP' },
                rsaPrivateKey,
                wrappedBuffer
            );
            return await importAESKeyRaw(rawKeyBuffer);
        } catch (err) {
            throw new Error('RSA-OAEP key unwrapping failed: Invalid private key or corrupted wrapped key.');
        }
    }

    async function encryptHybridMessage(plaintext, senderPublicKey, recipientPublicKey) {
        if (!plaintext || !senderPublicKey || !recipientPublicKey) {
            throw new Error('Plaintext, sender public key, and recipient public key are required for hybrid encryption.');
        }

        // 1. Generate single-use AES-256 key
        const aesKey = await generateAESKey();

        // 2. Encrypt plaintext with AES-256-GCM + unique 96-bit IV
        const encryptedData = await encryptMessageAES(plaintext, aesKey);

        // 3. Wrap AES key for Sender (for sender history decryption)
        const senderEncryptedKey = await wrapKeyRSA(aesKey, senderPublicKey);

        // 4. Wrap AES key for Recipient (for recipient delivery & history decryption)
        const recipientEncryptedKey = await wrapKeyRSA(aesKey, recipientPublicKey);

        return {
            ciphertext: encryptedData.ciphertext,
            iv: encryptedData.iv,
            sender_encrypted_key: senderEncryptedKey,
            recipient_encrypted_key: recipientEncryptedKey
        };
    }

    async function decryptHybridMessage(ciphertext, iv, encryptedKey, userPrivateKey) {
        if (!ciphertext || !iv || !encryptedKey || !userPrivateKey) {
            throw new Error('Ciphertext, IV, encrypted key, and user private key are required for hybrid decryption.');
        }

        // 1. Unwrap AES key using the participant's RSA-OAEP private key
        const aesKey = await unwrapKeyRSA(encryptedKey, userPrivateKey);

        // 2. Decrypt message payload using AES-256-GCM
        return await decryptMessageAES(ciphertext, iv, aesKey);
    }

    async function decryptChatHistory(messages, userPrivateKey) {
        if (!Array.isArray(messages)) {
            throw new Error('Messages must be an array.');
        }
        if (!userPrivateKey) {
            throw new Error('User private key is required for history decryption.');
        }

        const results = [];
        for (const msg of messages) {
            try {
                const plaintext = await decryptHybridMessage(
                    msg.ciphertext,
                    msg.iv,
                    msg.encrypted_key,
                    userPrivateKey
                );
                results.push({
                    ...msg,
                    plaintext: plaintext,
                    decrypted: true
                });
            } catch (err) {
                results.push({
                    ...msg,
                    plaintext: '[Decryption Error: corrupted ciphertext or unmatching key]',
                    decrypted: false
                });
            }
        }
        return results;
    }

    // Public API
    return {
        arrayBufferToBase64,
        base64ToArrayBuffer,
        generateUUIDv4,
        computeKeyFingerprint,
        generateRSAKeyPair,
        exportPublicKey,
        importPublicKey,
        storePrivateKey,
        getPrivateKey,
        hasPrivateKey,
        clearPrivateKey,
        storeTrustedFingerprint,
        getTrustedFingerprint,
        clearTrustedFingerprints,
        fetchPeerPublicKey,
        clearPeerKeyCache,
        generateAESKey,
        encryptMessageAES,
        decryptMessageAES,
        exportAESKeyRaw,
        importAESKeyRaw,
        wrapKeyRSA,
        unwrapKeyRSA,
        encryptHybridMessage,
        decryptHybridMessage,
        decryptChatHistory
    };
})();

// Export for module/testing environments if present
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CryptoEngine;
}
