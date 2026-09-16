# Comprehensive Viva Questions and Answers — Secure Chat Application

This document prepares you for any viva examination, project presentation, or technical interview regarding the **Secure Chat Application** (BTech CSE Mini-Project).

Every question contains:
1. **Question**: The exact question an examiner or professor may ask.
2. **Answer**: A clear, technically rigorous, student-friendly explanation matching the actual codebase.
3. **Key point**: A crisp 1-sentence takeaway you can state immediately.

---

## Table of Contents
1. [Basic Project Questions](#1-basic-project-questions)
2. [Project Architecture Questions](#2-project-architecture-questions)
3. [Cryptography Questions](#3-cryptography-questions)
4. [Web Crypto API Questions](#4-web-crypto-api-questions)
5. [Public-Key Fingerprinting & TOFU Questions](#5-public-key-fingerprinting--tofu-questions)
6. [Message Protocol & Replay Protection](#6-message-protocol--replay-protection)
7. [Authentication & Authorization Questions](#7-authentication--authorization-questions)
8. [Networking & Socket.IO Questions](#8-networking--socketio-questions)
9. [Database & Storage Questions](#9-database--storage-questions)
10. [Web Security & Hardening Questions](#10-web-security--hardening-questions)
11. [Testing & Quality Assurance Questions](#11-testing--quality-assurance-questions)
12. [Limitations & Advanced Critical Questions](#12-limitations--advanced-critical-questions)

---

## 1. Basic Project Questions

### Q1: Explain your entire project in 60 seconds.
- **Answer**: Our project is a zero-knowledge, end-to-end encrypted real-time chat application. When a user registers, an RSA-2048 keypair is generated directly inside their browser; the private key is saved in the browser's IndexedDB and never sent to the server. When sending a message, the browser generates an ephemeral AES-256 key, encrypts the message with AES-256-GCM, wraps the AES key using RSA-OAEP with the recipient's public key, and transmits only ciphertext and wrapped keys over Socket.IO. The Flask server acts strictly as an untrusted relay and persistent encrypted store. The recipient unwraps the AES key using their private key and decrypts the ciphertext locally.
- **Key point**: Zero-knowledge hybrid encryption where the server only sees ciphertext and private keys never leave the client's browser.

### Q2: What core problem does this project solve?
- **Answer**: Conventional chat applications rely on transport encryption (HTTPS/TLS), which only protects data in transit between the client and server. The server can decrypt, inspect, store, or accidentally leak plaintext messages. Our application implements true End-to-End Encryption (E2EE), guaranteeing that only the participating endpoints can decrypt and read messages, protecting privacy against rogue server admins, database leaks, and ISP eavesdropping.
- **Key point**: Solves the server-side eavesdropping and data-breach problem by eliminating server access to plaintext.

### Q3: What is "zero-knowledge" in the context of your chat server?
- **Answer**: Zero-knowledge means the server operates as an untrusted message broker that facilitates routing and persistence without having the mathematical ability to decrypt the message contents. The server stores ciphertext, initialization vectors, and wrapped AES keys, but possesses zero private keys.
- **Key point**: The server facilitates message delivery without possessing the cryptographic keys required to read the data.

### Q4: What are the main technologies used in this project?
- **Answer**: On the backend: Python, Flask, Flask-SocketIO for WebSocket transport, Flask-SQLAlchemy, and SQLite. On the frontend: HTML5, CSS3 (vanilla glassmorphic dark theme), JavaScript, the standard W3C Web Crypto API, and IndexedDB. For automated testing: pytest.
- **Key point**: Modern web standards (Web Crypto API + IndexedDB) paired with a lightweight, robust Python Flask-SocketIO backend.

---

## 2. Project Architecture Questions

### Q5: Can you walk through the system architecture?
- **Answer**: The system consists of three tiers: (1) Client Tier (Sender/Recipient browsers running Web Crypto API for cryptographic operations and IndexedDB for private key storage); (2) Application Tier (Flask server handling session authentication, REST APIs for key distribution, and Flask-SocketIO for real-time room-based message dispatching); and (3) Data Tier (SQLite database storing user metadata, public keys, and encrypted message envelopes).
- **Key point**: A three-tier architecture where cryptographic computation is strictly offloaded to the client tier.

### Q6: What happens step-by-step from clicking "Send" to the recipient reading the message?
- **Answer**: 
  1. Plaintext is captured from the input field.
  2. Web Crypto API generates an ephemeral AES-256 key and a random 96-bit IV.
  3. Plaintext is encrypted with AES-256-GCM, producing ciphertext and a 128-bit authentication tag.
  4. The AES key is wrapped twice via RSA-OAEP: once for the recipient and once for the sender.
  5. An envelope with canonical UUIDv4, version 1, IV, ciphertext, and wrapped keys is emitted over Socket.IO.
  6. Flask validates session identity, UUID uniqueness, and persists the envelope in SQLite.
  7. Flask forwards the envelope to the recipient's authenticated Socket.IO room.
  8. The recipient unwraps the AES key using their RSA private key in IndexedDB and decrypts the ciphertext using AES-256-GCM.
- **Key point**: Ephemeral AES key generation -> AES-GCM encryption -> dual RSA-OAEP wrapping -> server relay -> RSA unwrapping -> AES-GCM decryption.

### Q7: Why is dual key-wrapping necessary (sender and recipient)?
- **Answer**: If the AES key were wrapped only with the recipient's public key, the sender would never be able to decrypt and view their own sent chat history when reloading the conversation on their device. By wrapping the AES key with both public keys, both parties can independently unwrap the session key using their respective private keys.
- **Key point**: Dual wrapping allows both sender and recipient to decrypt and review the conversation history independently.

---

## 3. Cryptography Questions

### Q8: What is hybrid encryption, and why do we use AES and RSA together?
- **Answer**: Hybrid encryption combines symmetric cryptography (AES) and asymmetric cryptography (RSA). Asymmetric ciphers are computationally slow and mathematically incapable of encrypting payloads larger than their key size minus padding overhead. Symmetric ciphers are extremely fast and handle arbitrary payload sizes, but require a shared secret. We use fast AES-256-GCM to encrypt the message body, and use RSA-2048 to securely transport the small 256-bit AES key.
- **Key point**: Combines the high speed and arbitrary size capability of AES with the secure key-distribution capability of RSA.

### Q9: Why not use RSA directly to encrypt chat messages?
- **Answer**: RSA is computationally expensive (hundreds of times slower than AES) and has strict payload size limits. For RSA-2048 with OAEP SHA-256, the maximum encryptable data size is only 190 bytes ($256 - 2 \times 32 - 2 = 190$). A message longer than 190 bytes would fail or require complex, insecure chunking.
- **Key point**: RSA cannot encrypt data larger than 190 bytes and is far too slow for bulk message encryption.

### Q10: Why AES-GCM instead of AES-CBC?
- **Answer**: AES-CBC only provides confidentiality, not integrity; an attacker can tamper with ciphertext bits or perform padding oracle attacks. AES-GCM (Galois/Counter Mode) is an Authenticated Encryption with Associated Data (AEAD) cipher that provides confidentiality and cryptographic integrity simultaneously via a 128-bit GHASH authentication tag. Any tampering causes decryption to fail.
- **Key point**: AES-GCM provides authenticated encryption (confidentiality + integrity), preventing bit-flipping and padding oracle attacks.

### Q11: What is an Initialization Vector (IV), and why must it be 96 bits?
- **Answer**: An IV ensures that encrypting the same plaintext twice with the same key produces completely distinct ciphertexts. For AES-GCM, the standard NIST-recommended IV length is exactly 96 bits (12 bytes). A 96-bit IV is fed directly into the GCM counter register without undergoing additional hash computation, maximizing speed and security against counter collisions.
- **Key point**: A 96-bit IV provides optimal performance and uniqueness for GCM counter mode without needing an extra hashing step.

### Q12: Why is RSA-OAEP chosen over PKCS#1 v1.5 padding?
- **Answer**: PKCS#1 v1.5 is vulnerable to Bleichenbacher's chosen-ciphertext padding oracle attack, where an adversary sends crafted ciphertexts and observes error codes to recover plaintext. RSA-OAEP (Optimal Asymmetric Encryption Padding) uses Feistel networks and cryptographic hash functions (SHA-256) to achieve IND-CCA2 security (indistinguishability under adaptive chosen-ciphertext attacks).
- **Key point**: RSA-OAEP prevents Bleichenbacher padding oracle attacks and guarantees provable semantic security.

### Q13: Does AES-GCM protect against replay attacks?
- **Answer**: No. AES-GCM provides message confidentiality and integrity—meaning the message cannot be read or altered in transit. However, AES-GCM does not prevent an attacker from capturing an authentic ciphertext and resubmitting it multiple times. Replay protection must be handled at the application protocol and database layer using unique message identifiers.
- **Key point**: AES-GCM detects tampering, but replay protection requires application-level uniqueness constraints.

---

## 4. Web Crypto API Questions

### Q14: What is the Web Crypto API, and why use it instead of third-party JS libraries?
- **Answer**: The Web Crypto API (`window.crypto.subtle`) is a native W3C standard JavaScript interface implemented directly by the browser in C/C++. Unlike external JavaScript libraries (e.g., CryptoJS), native Web Crypto is immune to timing attacks against JS execution, executes with native hardware acceleration (AES-NI), and securely isolates raw key material.
- **Key point**: Native, hardware-accelerated, timing-attack resistant browser cryptographic engine.

### Q15: Why are private keys stored in IndexedDB instead of localStorage?
- **Answer**: `localStorage` is synchronous, blocks the main thread, and stores data as raw strings accessible to any synchronous JavaScript. IndexedDB is asynchronous, structured, and critically supports storing native `CryptoKey` objects directly. IndexedDB keys can be configured as `extractable: false`, restricting extraction even if an attacker executes simple DOM manipulation.
- **Key point**: IndexedDB supports native structured `CryptoKey` object storage and handles asynchronous access safely.

### Q16: Is IndexedDB considered a hardware security module (HSM)?
- **Answer**: No. IndexedDB is a software sandbox within the browser application profile on the client's filesystem. While isolated by the Same-Origin Policy against other domains, it is not a hardware enclave (like a TPM or Secure Enclave). If malware compromises the user's operating system or an attacker physically extracts the browser profile, software keys can be accessed.
- **Key point**: IndexedDB provides domain sandboxing, but is not hardware-backed tamper-resistant storage.

---

## 5. Public-Key Fingerprinting & TOFU Questions

### Q17: What is a public-key fingerprint?
- **Answer**: A public-key fingerprint is a compact, human-readable cryptographic digest generated by taking the SHA-256 hash of the canonical SubjectPublicKeyInfo (SPKI) DER byte array of an RSA public key. In our project, it is formatted as uppercase 4-character hex blocks (e.g., `4E92 A8F1 BC33 ...`).
- **Key point**: A deterministic SHA-256 digest of the canonical SPKI DER public key format.

### Q18: What is TOFU (Trust-On-First-Use)?
- **Answer**: TOFU is a security model (similar to SSH) where a client accepts and trusts a peer's public key upon the very first contact and stores its fingerprint locally in IndexedDB. On all subsequent interactions, the client verifies that the peer's advertised public key matches the stored fingerprint.
- **Key point**: Trust the key on first contact, store it, and verify that it never changes in future sessions.

### Q19: What is the primary limitation of the TOFU model?
- **Answer**: TOFU cannot detect a Man-in-the-Middle or key-substitution attack on the very first contact. If an adversary intercepts or substitutes Bob's key *before* Alice ever interacts with Bob, Alice trusts the adversary's key by default. Mitigating this requires out-of-band verification (e.g., scanning a QR code or comparing fingerprints in person).
- **Key point**: Vulnerable to key substitution during the initial contact before a fingerprint baseline is established.

### Q20: What happens in your project if Bob's public key changes?
- **Answer**: When Alice opens Bob's chat, the client compares the newly fetched key's SHA-256 fingerprint against the trusted fingerprint in Alice's IndexedDB. If they do not match, the application triggers a blocking warning banner (`⚠️ WARNING: Contact's public key has changed`), highlights the mismatch in red, and disables outbound message sending until Alice explicitly verifies and confirms the new key.
- **Key point**: The UI halts outbound communication and displays a blocking alert requiring explicit confirmation.

---

## 6. Message Protocol & Replay Protection

### Q21: What is the structure of your application's message protocol?
- **Answer**: Each message envelope contains:
  1. `message_id`: A cryptographically random canonical UUIDv4 string.
  2. `version`: Protocol version integer (`1`).
  3. `sender_id`: The sender's authenticated user ID.
  4. `recipient_id`: The target recipient's user ID.
  5. `ciphertext`: Base64 AES-256-GCM ciphertext plus 128-bit authentication tag.
  6. `iv`: Base64 96-bit initialization vector.
  7. `sender_encrypted_key`: Base64 RSA-OAEP wrapped AES key for the sender.
  8. `recipient_encrypted_key`: Base64 RSA-OAEP wrapped AES key for the recipient.
- **Key point**: A standardized envelope containing UUIDv4, protocol version, routing IDs, ciphertext, IV, and dual-wrapped session keys.

### Q22: How does the application prevent replay and duplicate message attacks?
- **Answer**: Every message must have a canonical UUIDv4 generated via `crypto.randomUUID()`. Both the REST API and Socket.IO handler validate the UUID format using a strict regex. The database table `messages` has a `UNIQUE` index on `message_id`. If a duplicate `message_id` is submitted, the server catches the integrity error and aborts with HTTP `409 Conflict` (or Socket error event), preventing duplicate storage and duplicate relay.
- **Key point**: Strict client UUIDv4 validation combined with a database `UNIQUE` constraint on `message_id`.

### Q23: Why is protocol versioning included in the payload?
- **Answer**: Protocol versioning (`version: 1`) allows the cryptographic envelope format and ciphersuites to evolve in the future without breaking backward compatibility. If a client transmits an unsupported version, the server safely rejects the message with `400 Bad Request`.
- **Key point**: Enables future cryptographic upgrades without breaking backward compatibility.

---

## 7. Authentication & Authorization Questions

### Q24: How is user authentication implemented?
- **Answer**: The application uses session-based authentication backed by Flask sessions and secure HTTP cookies. User passwords are encrypted using Werkzeug's secure password hashing (scrypt / PBKDF2 with salt). The server never stores or logs plaintext passwords.
- **Key point**: Session cookies backed by salted, key-stretched password hashes (scrypt/PBKDF2).

### Q25: How do you prevent sender impersonation over Socket.IO?
- **Answer**: When a client sends a message containing `sender_id: X`, the server does NOT trust the client's payload. Instead, the server inspects the authenticated session cookie bound to the Socket.IO connection (`session['user_id']`). If the payload `sender_id` does not strictly match the session `user_id`, the request is rejected immediately with an authorization error.
- **Key point**: The server overrides and validates sender identity against the trusted session cookie, preventing spoofing.

### Q26: How does rate limiting work in your backend?
- **Answer**: We implement an in-memory sliding-window rate limiter in `utils/security.py`. Rate limiting is evaluated on two independent axes:
  1. **IP-based limiting**: Restricts requests per IP address (e.g., 60 requests per minute) to prevent DoS.
  2. **Account-based limiting**: Restricts failed login attempts per username (e.g., 5 attempts per 15 minutes) to defeat distributed brute-force attacks across rotating proxies.
- **Key point**: Dual-axis rate limiting (per IP and per username) prevents brute-force and credential stuffing.

---

## 8. Networking & Socket.IO Questions

### Q27: Why use Socket.IO instead of pure REST polling?
- **Answer**: REST polling requires clients to repeatedly query the server every few seconds, generating unnecessary HTTP overhead, network congestion, and latency. Socket.IO establishes a persistent, full-duplex WebSocket connection, allowing the server to push incoming encrypted messages to the recipient instantaneously with minimal framing overhead.
- **Key point**: Full-duplex, event-driven WebSocket transport eliminates polling latency and network waste.

### Q28: How does Socket.IO routing work between users?
- **Answer**: When an authenticated user connects, the server assigns their socket to a private room named after their user ID (`f"user_{user_id}"`). When Alice sends a message to Bob, the server emits the event specifically to Bob's room (`room=f"user_{recipient_id}"`). Other users never receive the event.
- **Key point**: User-isolated rooms ensure messages are only dispatched to the designated recipient.

### Q29: What transport fallback does Socket.IO provide?
- **Answer**: Socket.IO initially connects via HTTP long-polling and automatically upgrades to a WebSocket connection if supported by the client and network proxies. If WebSockets are blocked by restrictive firewalls, it gracefully falls back to long-polling.
- **Key point**: Automatic upgrade from HTTP long-polling to WebSockets with transparent fallback.

---

## 9. Database & Storage Questions

### Q30: What database is used, and what tables exist?
- **Answer**: SQLite is used via Flask-SQLAlchemy. There are two primary tables:
  1. `users`: Stores `id`, `username`, `password_hash`, `public_key`, and `created_at`.
  2. `messages`: Stores `id`, `message_id` (UUIDv4), `version`, `sender_id`, `recipient_id`, `ciphertext`, `iv`, `sender_encrypted_key`, `recipient_encrypted_key`, and `created_at`.
- **Key point**: Two normalized relational tables (`users` and `messages`) managed through SQLAlchemy ORM.

### Q31: What happens to messages when a user account is deleted?
- **Answer**: Both `sender_id` and `recipient_id` in `messages` define foreign keys referencing `users.id` with `ondelete='CASCADE'`. In SQLAlchemy, `cascade='all, delete-orphan'` is configured on user relationships. Deleting a user automatically purges all their sent and received messages, preventing orphan records.
- **Key point**: Foreign key constraints with cascade deletion enforce referential integrity and privacy hygiene.

### Q32: What indexes are implemented in the database?
- **Answer**: 
  1. `users.username` has a unique index for rapid credential lookups.
  2. `messages.message_id` has a unique index for replay validation.
  3. Two composite dialogue indexes: `ix_messages_dialogue_sender (sender_id, recipient_id, created_at)` and `ix_messages_dialogue_recipient (recipient_id, sender_id, created_at)` to optimize chronological chat history queries.
- **Key point**: Unique indexes for identity and composite indexes for fast dialogue history retrieval.

---

## 10. Web Security & Hardening Questions

### Q33: What is Cross-Site Request Forgery (CSRF), and how is it mitigated?
- **Answer**: CSRF occurs when a malicious site tricks a victim's authenticated browser into submitting unauthorized requests to our application. We mitigate this using CSRF tokens: clients obtain a cryptographically random token via `/api/csrf-token` and must include it in state-changing POST/PUT requests via the `X-CSRF-Token` header. The server verifies the token against the user's session before executing the operation.
- **Key point**: Header-based CSRF token validation protects state-changing endpoints.

### Q34: What is Cross-Site Scripting (XSS), and how does your UI prevent it?
- **Answer**: XSS occurs when malicious JavaScript is injected into web pages viewed by other users. We prevent XSS by never using `innerHTML` with unsanitized user content. In `chat.js`, all dynamic user strings are set via `textContent` or passed through an HTML entity escaping helper (`escapeHtml`), preventing browser execution of injected HTML/JS tags.
- **Key point**: Strict usage of `textContent` and HTML escaping prevents DOM injection.

### Q35: What security headers are configured on server responses?
- **Answer**: An `after_request` middleware attaches standard security headers to every HTTP response:
  - `Content-Security-Policy`: Restricts resource sources.
  - `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
  - `X-Frame-Options: SAMEORIGIN`: Defeats clickjacking.
  - `Referrer-Policy: strict-origin-when-cross-origin`: Restricts referrer leaks.
- **Key point**: Hardened HTTP response headers enforce browser-level defensive policies.

### Q36: What is CORS, and how is it restricted?
- **Answer**: Cross-Origin Resource Sharing (CORS) restricts which domains can make cross-origin requests to our API. We explicitly restrict CORS origins to authorized hosts (`http://127.0.0.1:5000`, `http://localhost:5000`) across both REST routes and Socket.IO configurations, blocking unauthorized origins.
- **Key point**: Synchronized REST and Socket.IO origin restrictions block untrusted external domains.

---

## 11. Testing & Quality Assurance Questions

### Q37: How many automated tests exist in the project?
- **Answer**: There are **63 automated tests** in total, organized across 11 test modules in the `tests/` directory. All 63 tests pass consistently with a 100% pass rate.
- **Key point**: 63 automated tests spanning unit, integration, socket routing, and security hardening.

### Q38: Can you name 4 specific security tests you implemented?
- **Answer**: 
  1. `test_zero_plaintext_in_database`: Verifies that raw SQL queries against `messages` reveal zero plaintext strings.
  2. `test_cryptographic_bit_flip_tamper_detection`: Verifies that modifying a single bit in the ciphertext causes AES-GCM decryption to throw an authentication error.
  3. `test_replay_protection_rest_duplicate_rejected`: Verifies that resubmitting an identical UUIDv4 returns HTTP 409 Conflict.
  4. `test_impersonation_prevention_on_socket_send`: Verifies that a user cannot spoof another user's `sender_id`.
- **Key point**: Tests verify zero plaintext storage, tamper detection, duplicate rejection, and identity validation.

---

## 12. Limitations & Advanced Critical Questions

### Q39: Does this project provide Forward Secrecy?
- **Answer**: No. Forward secrecy requires generating ephemeral Diffie-Hellman key exchanges (such as ECDH or the Double Ratchet Algorithm) for every single message or session ratcheting. In our mini-project, session keys are wrapped under long-term RSA-2048 public keys. If Bob's private key were compromised in the future, past captured wrapped keys could theoretically be unwrapped.
- **Key point**: Long-term RSA key wrapping does not provide forward secrecy; achieving it would require per-message ratcheting (Double Ratchet).

### Q40: What metadata is still visible to the server?
- **Answer**: Even though the server cannot see message plaintext, it still observes metadata: who is communicating with whom (`sender_id`, `recipient_id`), message timestamps, ciphertext payload lengths, and client IP addresses. Full metadata privacy would require onion routing (Tor) or mix networks.
- **Key point**: Communication metadata (endpoints, timestamps, message frequency, and size) remains visible to the relay server.

### Q41: How would you scale the in-memory rate limiter for a multi-server production environment?
- **Answer**: In our mini-project, the rate limiter uses process-local Python dictionaries. In a multi-worker production cluster (e.g., Gunicorn with multiple workers behind a load balancer), memory is not shared between processes. Scaling requires an external centralized in-memory datastore such as Redis to synchronize sliding-window request counts atomically.
- **Key point**: Production multi-worker deployments require centralized shared memory (e.g., Redis) for global rate limiting.

### Q42: What happens if a user accesses their account from a second computer?
- **Answer**: Because private keys are stored client-side in IndexedDB on the first computer, the second computer will not possess the private key. When logging in on the new device, the application warns the user (`⚠️ Key Missing`) and offers to generate a new keypair. However, past messages encrypted with the old private key cannot be decrypted on the new device without an encrypted key export mechanism.
- **Key point**: Private keys are bound to the local browser sandbox; cross-device synchronization requires explicit secure key backup.

### Q43: Why is this project relevant to Computer Networks?
- **Answer**: It directly implements the OSI and TCP/IP stack layers: application-layer hybrid cryptography, transport-layer WebSocket / TCP connections via Socket.IO, session state management, and network-level security controls (CORS, CSP, IP rate limiting). It demonstrates how to secure application data over an inherently untrusted network medium.
- **Key point**: Practical implementation of secure application protocols, WebSocket transport, and cryptographic defense over untrusted networks.

---

## Quick-Fire Viva Summary Sheet

| Topic | Implementation Choice | Justification |
|---|---|---|
| **Asymmetric Cipher** | RSA-2048 / OAEP (SHA-256) | Standardized public key wrapping; prevents Bleichenbacher oracle attacks. |
| **Symmetric Cipher** | AES-256-GCM | Authenticated encryption (confidentiality + integrity) with 128-bit GHASH tag. |
| **IV Size** | 96 bits (12 bytes) | Optimal NIST recommendation for GCM counter mode without extra hashing. |
| **Private Key Store** | Browser IndexedDB | Client-side sandbox capable of storing native asynchronous `CryptoKey` objects. |
| **Key Trust Model** | TOFU (Trust-On-First-Use) | Balances simplicity and security for college scope; warns on key changes. |
| **Transport** | Flask-SocketIO (WebSockets) | Full-duplex real-time push with user-isolated rooms; zero polling overhead. |
| **Replay Defense** | Client UUIDv4 + DB Unique Index | Strict UUID format validation and database uniqueness constraint reject duplicates. |
| **Test Coverage** | 63 automated pytest tests | 100% passing tests covering crypto, database, sockets, auth, and hardening. |
