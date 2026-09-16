# Secure Chat Application — Demonstration Guide

**Project Type**: BTech CSE College Mini-Project  
**Duration**: Approximately 5–10 Minutes  
**Demonstration Scope**: Real-Time Hybrid Cryptography (RSA-2048 + AES-256-GCM), Client-Side Key Isolation (IndexedDB), TOFU Public-Key Trust Verification, and Web Security Hardening.

---

## Prerequisites & Pre-Flight Check

Before starting your viva or laboratory demonstration:
1. Ensure Python 3.11+ is installed.
2. Open two browser windows (e.g., standard browser window for Alice and incognito/private window for Bob, or two distinct browser profiles).
3. Ensure no stale database locks exist (default SQLite file: `instance/chat.db` or configured URI).

---

## Step-by-Step Demonstration Script

### Step 1 — Start the Application Server
Open a terminal in the project root directory and start the Flask-SocketIO development server:
```powershell
# Activate virtual environment
.venv\Scripts\activate

# Start server
python app.py
```
*Expected Output*:
```text
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
```
**Talking Point (15 seconds)**:  
> *"Our backend application runs on Flask and Flask-SocketIO on port 5000. It serves as a zero-knowledge relay and encrypted datastore. The server never observes plaintext messages or client private keys."*

---

### Step 2 — Register User A (Alice) in Browser 1
1. Open Browser Window 1 and navigate to:
   ```text
   http://127.0.0.1:5000/register
   ```
2. Enter:
   - **Username**: `alice`
   - **Password**: `Password123!` (Click the eye icon to demonstrate password visibility toggle)
3. Click **"Generate Keys & Register"**.
4. Observe the progress spinner:
   - *"Generating RSA-2048 keypair in browser..."*
   - *"Saving private key to browser IndexedDB..."*
   - *"Exporting public SPKI key..."*
   - *"Registering user account on server..."*
5. The application automatically redirects Alice to `/chat`.

**Talking Point (30 seconds)**:  
> *"When Alice registers, the browser's Web Crypto API generates an RSA-2048 keypair locally. Her private key is saved directly to the browser's IndexedDB sandbox. Only her public key in SPKI format is transmitted to the server."*

---

### Step 3 — Register User B (Bob) in Browser 2 (Incognito)
1. Open Browser Window 2 (Incognito / Private Window) and navigate to:
   ```text
   http://127.0.0.1:5000/register
   ```
2. Enter:
   - **Username**: `bob`
   - **Password**: `Password123!`
3. Click **"Generate Keys & Register"**.
4. Bob is redirected to `/chat` with his own isolated RSA-2048 keypair in Browser 2's IndexedDB.

**Talking Point (20 seconds)**:  
> *"Bob now has his own unique cryptographic keypair in a completely separate browser sandbox. In Bob's sidebar, Alice immediately appears as an available peer."*

---

### Step 4 — Establish Public-Key Trust (TOFU)
1. In Alice's window, click on **"bob"** in the contact list.
2. In the chat header, observe:
   - **Contact Name**: `bob`
   - **Indicator**: `🔒 True E2EE Active` with `AES-256-GCM` badge
   - **Safety Number Pill**: `Fingerprint: [4-char blocks]` with a blue **"Trust Key"** button.
3. Explain that Alice has not yet trusted Bob's key (First-Contact state).
4. Click **"Trust Key"**.
5. The pill immediately updates to:
   ```text
   Fingerprint: [SHA-256 Digest] ✓ Trusted
   ```
   and persists this trust state directly into Alice's IndexedDB `trustedFingerprints` store.

**Talking Point (30 seconds)**:  
> *"We implement Trust-On-First-Use (TOFU). The safety number is a deterministic SHA-256 fingerprint of Bob's canonical SPKI DER public key. When Alice clicks 'Trust Key', the fingerprint is locked into IndexedDB scoped to Alice's account. Any future key substitution by a rogue server will be immediately detected."*

---

### Step 5 — Send an Encrypted Message (Alice to Bob)
1. In Alice's window, type:
   ```text
   Hello Bob! This message is end-to-end encrypted with AES-256-GCM.
   ```
2. Click **"Send"** (or press Enter).
3. The message appears instantly in Alice's message stream with a blue bubble, timestamp, and `🔒 Encrypted` label.
4. Switch to Bob's window. Bob's contact list highlights Alice with `● New encrypted message`.
5. In Bob's window, click on **"alice"**, click **"Trust Key"** for Alice, and see Alice's message decrypted cleanly in Bob's stream.

**Talking Point (45 seconds)**:  
> *"Here is the cryptographic execution sequence:*  
> *1. Alice's browser generates an ephemeral 256-bit AES key and a fresh random 96-bit IV.*  
> *2. The plaintext is encrypted using AES-256-GCM, producing ciphertext and a 128-bit authentication tag.*  
> *3. The AES key is wrapped twice using RSA-OAEP: once with Bob's public key (for Bob) and once with Alice's public key (so Alice can read her own sent history).*  
> *4. Alice's browser transmits only the ciphertext, IV, and wrapped keys to the server over Socket.IO.*  
> *5. Bob's browser receives the package, unwraps the AES key using his RSA private key in IndexedDB, and decrypts the ciphertext using AES-256-GCM."*

---

### Step 6 — Demonstrate Real-Time Bi-directional Chat
1. In Bob's window, reply:
   ```text
   Confirmed Alice! Zero plaintext was visible in transit.
   ```
2. Click **"Send"**.
3. In Alice's window, observe the message appear in real-time over the Socket.IO WebSocket transport without page refresh.

**Talking Point (20 seconds)**:  
> *"Socket.IO room-based event dispatching delivers the encrypted envelope in real-time. Each message has a client-generated canonical UUIDv4 to uniquely identify the transmission."*

---

### Step 7 — Demonstrate Security Controls

#### A. Replay / Duplicate Message Protection
- Explain that every message requires a canonical UUIDv4 `message_id`. If an adversary intercepts and retransmits the exact same payload, the database's unique constraint on `messages.message_id` and the server's validation layer reject the duplicate with `409 Conflict`.

#### B. Key Change Warning (TOFU Defense)
- If a contact's public key changes on the server (e.g. key re-generation or adversary substitution), the client compares the new public key's SHA-256 fingerprint against the trusted fingerprint in IndexedDB.
- When a mismatch is detected, the application displays a prominent red warning banner:
  `⚠️ WARNING: Contact's public key has changed. Verification required before sending sensitive messages.`
- Outbound message sending is blocked until the user explicitly re-verifies.

#### C. Rate Limiting & CSRF Protection
- Independent rate limiters enforce throttling per IP address (60 req/min) and per account (5 failed logins/15 min).
- Authenticated endpoints validate session cookies and double-submit/header CSRF tokens.

---

### Step 8 — Inspect the SQLite Database (Zero Plaintext Proof)
Open a new terminal and run an interactive query against the database:
```powershell
python -c "
import sqlite3
conn = sqlite3.connect('instance/chat.db')
c = conn.cursor()
print('=== USERS TABLE ===')
for row in c.execute('SELECT id, username, SUBSTR(public_key, 1, 40) FROM users'):
    print(row)
print('\n=== MESSAGES TABLE (CIPHERTEXT ONLY) ===')
for row in c.execute('SELECT id, message_id, sender_id, recipient_id, SUBSTR(ciphertext, 1, 35), iv FROM messages'):
    print(row)
"
```
*Expected Output*:
```text
=== USERS TABLE ===
(1, 'alice', 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC')
(2, 'bob', 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC')

=== MESSAGES TABLE (CIPHERTEXT ONLY) ===
(1, 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 1, 2, 'q3Z8+bX62z01Lp9wA1...', '8F2bC3...')
(2, '9c8b7a61-3210-48fe-9876-ba9876543210', 2, 1, 'y8K1+aN94m12Px7vB2...', '1A3dE5...')
```

**Talking Point (30 seconds)**:  
> *"As you can see directly in the database, the server stores only ciphertext and base64-encoded wrapped keys. Even if the database is leaked or stolen, an attacker cannot read a single plaintext word without the clients' private keys."*

---

### Step 9 — Run the Automated Test Suite
In the terminal, run pytest:
```powershell
python -m pytest -v
```
*Expected Output*:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.8, pytest-9.1.1
collected 63 items

tests/test_auth.py ......................... PASSED
tests/test_chat_history.py ................ PASSED
tests/test_crypto_static.py ................ PASSED
tests/test_database_storage.py ............. PASSED
tests/test_hardening.py .................... PASSED
tests/test_key_exchange.py ................. PASSED
tests/test_security_audit.py ............... PASSED
tests/test_security_hardening.py ........... PASSED
tests/test_setup.py ........................ PASSED
tests/test_sockets.py ...................... PASSED
tests/test_users.py ........................ PASSED

======================== 63 passed in 23.89s ========================
```

**Talking Point (20 seconds)**:  
> *"Our project includes 63 comprehensive automated tests covering unit functions, Socket.IO message routing, cryptographic bit-flip tamper detection, rate limiting, and replay attack prevention with a 100% pass rate."*

---

### Step 10 — Wrap-Up & Viva Summary
Conclude the demonstration with a 30-second summary:
> *"In summary, the Secure Chat Application achieves zero-knowledge private communication through client-side hybrid encryption (RSA-2048 + AES-256-GCM), isolates private keys in the browser's IndexedDB sandbox, enforces TOFU public-key trust, and prevents replay attacks via canonical UUIDv4 validation—delivering a hardened, production-grade security architecture suitable for a CSE mini-project."*
