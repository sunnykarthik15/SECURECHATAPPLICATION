# College Presentation Outline — Secure Chat Application

**Degree / Course**: BTech in Computer Science and Engineering  
**Subject**: Mini-Project Presentation / Cryptography & Network Security  
**Total Slides**: 12 Slides  
**Total Presentation Time**: 8–10 Minutes (approx. 45–60 seconds per slide)

---

## Slide 1: Title Slide
- **Slide Title**: Secure Chat Application: Zero-Knowledge End-to-End Encrypted Messaging
- **Subtitle**: BTech CSE College Mini-Project
- **Visual**: Project Logo & Branding (`docs/screenshots/08-project-overview.png`)
- **Key Bullet Points**:
  - Client-Side Hybrid Cryptography (RSA-2048 + AES-256-GCM)
  - Browser-Isolated Private Key Storage (IndexedDB)
  - Trust-On-First-Use (TOFU) Fingerprint Verification
  - Real-Time Full-Duplex Relay (Flask-SocketIO)
- **Speaking Notes (45 seconds)**:
  > *"Good morning, respected professors and evaluation committee. Today, I am presenting our BTech CSE mini-project titled 'Secure Chat Application'. In a world where digital surveillance and server-side data breaches are common, conventional chat apps that decrypt data on the server pose serious privacy risks. Our project demonstrates a complete zero-knowledge end-to-end encrypted messaging system where the backend server acts strictly as an untrusted message broker and never possesses the keys to decrypt user communication."*

---

## Slide 2: Problem Statement
- **Slide Title**: Problem Statement & Motivation
- **Visual**: Diagram contrasting transport encryption vs end-to-end encryption
- **Key Bullet Points**:
  - Inherent vulnerability of Transport Layer Security (TLS/HTTPS) alone.
  - The "Trusted Server" fallacy: server administrators and compromised databases expose plaintext.
  - Risks of Man-in-the-Middle (MitM) key substitution.
  - Eavesdropping, message tampering, and replay submission attacks.
- **Speaking Notes (45 seconds)**:
  > *"Standard web applications rely primarily on HTTPS. While HTTPS encrypts traffic between the browser and the web server, the server itself decrypts the payload into memory. If the database is leaked, if an administrator inspects logs, or if the server infrastructure is compromised, all user conversations are exposed. Furthermore, without client-side message validation, adversaries can capture and replay encrypted packets. Our problem was to build an accessible, secure system where plaintext never touches the network or server."*

---

## Slide 3: Project Objectives
- **Slide Title**: Key Design & Engineering Objectives
- **Visual**: Check-list graphic of core deliverables
- **Key Bullet Points**:
  - **Zero-Knowledge Architecture**: The server stores only ciphertext and wrapped session keys.
  - **Client-Side Key Isolation**: Private keys generated and kept strictly in browser IndexedDB.
  - **Authenticated Hybrid Encryption**: AES-256-GCM for payload confidentiality & integrity; RSA-OAEP for key wrapping.
  - **Key Trust & Fingerprinting**: Deterministic SHA-256 SPKI fingerprinting with TOFU alert banners.
  - **Replay & Impersonation Defense**: Client-generated canonical UUIDv4 validation and server-enforced authorization.
  - **Production-Grade Web Hardening**: CSRF tokens, dual-axis rate limiting, and strict CSP headers.
- **Speaking Notes (45 seconds)**:
  > *"To solve this problem, we established six concrete objectives. First, guarantee zero server-side plaintext visibility. Second, isolate private keys on the client using native browser APIs. Third, implement authenticated hybrid encryption. Fourth, provide users with deterministic public-key safety numbers to detect key-substitution attacks. Fifth, ensure full replay protection using unique message identifiers. And finally, harden the web platform against common attacks like CSRF, XSS, and credential brute-forcing."*

---

## Slide 4: Existing vs. Proposed System
- **Slide Title**: Existing System vs. Proposed E2EE System
- **Visual**: Comparative Architecture Table
- **Key Bullet Points**:
  - **Data Exposure**: Existing systems decrypt on server; Proposed system decrypts only on recipient browser.
  - **Key Ownership**: Existing systems manage keys on the cloud; Proposed system keeps private keys in client IndexedDB.
  - **Tamper Evidence**: Existing systems rely on network framing; Proposed system uses 128-bit GHASH authentication tags.
  - **Replay Handling**: Existing systems often trust socket payloads; Proposed system validates canonical UUIDv4 uniqueness in database.
- **Speaking Notes (50 seconds)**:
  > *"This table summarizes the core paradigm shift. Conventional systems trust the server with full access to plaintext and store user messages in readable databases. In our proposed system, cryptographic trust is relocated entirely to the client browser endpoints. The server is treated as an untrusted, hostile environment that merely persists and routes encrypted envelopes."*

---

## Slide 5: Technology Stack
- **Slide Title**: Technical Implementation Stack
- **Visual**: Technology badge collage (Python, Flask, Socket.IO, Web Crypto, IndexedDB, SQLite)
- **Key Bullet Points**:
  - **Frontend Core**: HTML5, Vanilla CSS (modern dark design), Vanilla JavaScript.
  - **Client Cryptography**: W3C Web Crypto API (`window.crypto.subtle`) & IndexedDB sandbox.
  - **Backend Server**: Python 3.11, Flask, Flask-SocketIO, Flask-SQLAlchemy.
  - **Database**: SQLite with unique indices, foreign key cascades, and composite dialogue indices.
  - **Quality Assurance**: Automated testing with pytest (63 comprehensive tests).
- **Speaking Notes (45 seconds)**:
  > *"We deliberately chose standard, native technologies without unnecessary heavy frameworks. On the frontend, we use the browser's native W3C Web Crypto API, which executes cryptographic algorithms in optimized C++ with hardware acceleration and side-channel resistance. The backend uses Python Flask and Flask-SocketIO to handle real-time full-duplex WebSocket connections. Data persistence is managed through SQLAlchemy on SQLite with strict relational hygiene."*

---

## Slide 6: System Architecture
- **Slide Title**: System Architecture & Component Interactions
- **Visual**: `docs/diagrams/architecture.png`
- **Key Bullet Points**:
  - Three-tier topology: Client A (Sender) -> Flask Relay Server -> Client B (Recipient).
  - Web Crypto API and IndexedDB stay isolated within the client sandbox.
  - Flask layer provides REST authentication, CSRF middleware, and rate limiters.
  - Flask-SocketIO manages user-isolated communication rooms (`user_<id>`).
  - Persistent storage in SQLite contains zero plaintext and zero private keys.
- **Speaking Notes (60 seconds)**:
  > *"Here is our system architecture diagram. On the left and right, we have the client endpoints running in separate browsers. Each browser maintains its own IndexedDB sandbox storing its RSA private key and trusted peer fingerprints. In the center is our Flask application server. Notice that all communication over REST and Socket.IO consists exclusively of encrypted envelopes. The server verifies session cookies and validates message schemas, but it never possesses the private keys required to decrypt the ciphertext."*

---

## Slide 7: Hybrid Encryption & Data Flow
- **Slide Title**: Cryptographic Data Flow Pipeline
- **Visual**: `docs/diagrams/encryption-data-flow.png`
- **Key Bullet Points**:
  - **Step 1**: Plaintext message entered in sender's browser.
  - **Step 2**: Fresh random 256-bit AES key & 96-bit IV generated via Web Crypto API.
  - **Step 3**: Payload encrypted via AES-256-GCM, yielding ciphertext and 128-bit GHASH tag.
  - **Step 4**: AES key wrapped twice using RSA-OAEP (SHA-256) for sender and recipient.
  - **Step 5**: Envelope dispatched to server and forwarded to recipient via Socket.IO.
  - **Step 6**: Recipient un-wraps AES key with local private key and decrypts ciphertext.
- **Speaking Notes (60 seconds)**:
  > *"This diagram illustrates our end-to-end cryptographic pipeline. We utilize hybrid encryption. For every single message, an ephemeral 256-bit AES key and a random 96-bit IV are generated. The message is encrypted using AES-GCM. Because RSA cannot efficiently encrypt large payloads, we use RSA-OAEP with SHA-256 to wrap only the 256-bit AES key for both the recipient and the sender. The server relays the package. The recipient unwraps the AES key using their private key in IndexedDB and decrypts the ciphertext. Confidentiality and integrity are mathematically guaranteed."*

---

## Slide 8: Public-Key Trust & Web Security Hardening
- **Slide Title**: Key Fingerprinting, TOFU & Defensive Hardening
- **Visual**: `docs/screenshots/06-key-change-warning.png`
- **Key Bullet Points**:
  - **Deterministic Fingerprints**: SHA-256 hash of canonical SPKI DER public key representation.
  - **TOFU Model**: Fingerprint trusted on initial contact; stored in IndexedDB.
  - **Key-Change Detection**: Automatic blocking alert if peer public key differs from trusted state.
  - **Replay Protection**: Canonical UUIDv4 validation with database `UNIQUE` constraint.
  - **Web Hardening**: Double-submit CSRF tokens, dual-axis IP/account rate limiting, security headers.
- **Speaking Notes (60 seconds)**:
  > *"To defend against rogue server admins who might substitute public keys, we implemented Trust-On-First-Use (TOFU) with deterministic public-key fingerprinting. If Bob's public key changes, Alice's browser immediately halts outbound transmission and displays the warning banner shown on screen. Additionally, we defend the web surface using UUIDv4 replay protection, CSRF token validation on all state-changing routes, IP-based and username-based sliding-window rate limiters, and strict Content Security Policies."*

---

## Slide 9: Database Entity-Relationship Design
- **Slide Title**: Database Relational Schema & Indexing
- **Visual**: `docs/diagrams/database-er.png`
- **Key Bullet Points**:
  - **`users` Table**: `id` (PK), `username` (UK), `password_hash` (scrypt), `public_key` (SPKI).
  - **`messages` Table**: `id` (PK), `message_id` (UUIDv4, UK), `sender_id` (FK), `recipient_id` (FK), `ciphertext`, `iv`, `sender_encrypted_key`, `recipient_encrypted_key`.
  - **Referential Hygiene**: `ondelete='CASCADE'` ensures orphan cleanup when accounts are deleted.
  - **Query Performance**: Composite dialogue indexes (`sender_id`, `recipient_id`, `created_at`).
- **Speaking Notes (45 seconds)**:
  > *"Our database schema reflects our security principles. The messages table contains only ciphertext, initialization vectors, and wrapped session keys. The message_id column has a UNIQUE index enforcing replay protection at the database level. Cascading foreign keys ensure that if a user deletes their account, all associated message records are automatically purged, upholding data privacy."*

---

## Slide 10: Implementation Results & User Interface
- **Slide Title**: Application Interface & User Experience
- **Visual**: `docs/screenshots/04-secure-message.png` and `docs/screenshots/01-login.png`
- **Key Bullet Points**:
  - Modern, responsive dark-mode interface with subtle glassmorphic styling.
  - Clear cryptographic status pills (`🔒 RSA-2048 Active`, `🔒 True E2EE Active`).
  - Safety number / fingerprint verification pill with instant trust actions.
  - Dynamic encrypted message bubbles with timestamps and delivery acknowledgments.
  - Accessible forms with keyboard navigation, visible focus rings, and password reveal toggles.
- **Speaking Notes (45 seconds)**:
  > *"Here are screenshots of the running application. The interface is clean, professional, and responsive. Users can easily verify their security status through intuitive badges: connection status, active cryptographic algorithm, and peer fingerprint trust badges. Real-time message streaming provides instantaneous feedback without requiring manual page refreshes."*

---

## Slide 11: Testing & Security Validation
- **Slide Title**: Verification, Audit & Test Results
- **Visual**: `docs/screenshots/07-security-tests.png`
- **Key Bullet Points**:
  - **Total Automated Tests**: 63 passing tests across 11 test modules.
  - **100% Pass Rate**: Executed via pytest in ~24 seconds.
  - **Zero-Plaintext Verification**: Automated queries prove zero plaintext exists in database.
  - **Cryptographic Tamper Audit**: Bit-flip tests confirm AES-GCM rejection of modified ciphertexts.
  - **Replay & Impersonation Audit**: Verified rejection of duplicate UUIDs and forged sender IDs.
- **Speaking Notes (45 seconds)**:
  > *"Software quality and security were verified through 63 automated tests. Our test suite includes unit tests for authentication and socket events, as well as adversarial security tests: intentionally flipping bits in ciphertext to confirm AEAD authentication failures, resubmitting duplicate message UUIDs to confirm replay rejection, and verifying that database dumps contain zero plaintext strings."*

---

## Slide 12: Limitations, Future Work & Conclusion
- **Slide Title**: Limitations, Future Enhancements & Conclusion
- **Visual**: Summary conclusion graphic
- **Key Bullet Points**:
  - **Honest Limitations**:
    - TOFU does not prevent key substitution during first contact (requires out-of-band check).
    - Long-term RSA key wrapping lacks forward secrecy (no per-message ratchet).
    - In-memory rate limiting is process-local (requires Redis for distributed clusters).
    - Message metadata (timestamps, sender/recipient IDs) remains visible to relay.
  - **Future Enhancements**: Integration of Double Ratchet / Signal protocol, voice note E2EE, and hardware token keys.
  - **Conclusion**: A robust, zero-knowledge, college mini-project proving practical end-to-end security on the web.
- **Speaking Notes (60 seconds)**:
  > *"To conclude honestly, our project has known theoretical limitations: TOFU cannot eliminate first-contact risk without out-of-band verification, and long-term RSA wrapping does not provide forward secrecy. In future work, this could be extended using Diffie-Hellman ratcheting and Redis for distributed clusters. In conclusion, this mini-project demonstrates that modern web standards like the Web Crypto API can achieve true zero-knowledge end-to-end encryption without third-party proprietary libraries. Thank you, and I now welcome your questions."*
