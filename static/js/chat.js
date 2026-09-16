/**
 * Client-Side Real-Time Chat Coordinator
 * Orchestrates Socket.IO events, peer public key retrieval,
 * client-side hybrid encryption (AES-256-GCM + RSA-OAEP),
 * client-side TOFU key fingerprint trust verification in IndexedDB,
 * and local zero-knowledge chat history decryption.
 *
 * Security Note:
 * - All private keys and trusted key verification data remain strictly in IndexedDB.
 * - Private keys and plaintext messages are never sent over the network.
 * - Message IDs are cryptographically random canonical UUIDv4 generated on the client.
 */

const ChatApp = (function () {
    'use strict';

    let socket = null;
    let currentUser = null;
    let csrfToken = null;
    let myPrivateKey = null;
    let myPublicKey = null;
    let activeContact = null; // { id, username, public_key, cryptoKey, fingerprint, isKeyChanged }
    let contacts = [];

    // --- Initialization ---
    async function init() {
        try {
            await fetchCsrfToken();
            await loadCurrentUser();
            await initKeyMaterial();
            initSocket();
            bindDOMEvents();
            await loadContacts();
        } catch (err) {
            console.error('Chat initialization failed:', err);
        }
    }

    async function fetchCsrfToken() {
        try {
            const res = await fetch('/api/csrf-token');
            if (res.ok) {
                const data = await res.json();
                csrfToken = data.csrf_token;
            }
        } catch (e) {
            console.warn('Failed to retrieve CSRF token:', e);
        }
    }

    async function loadCurrentUser() {
        const res = await fetch('/api/auth/me');
        if (!res.ok) {
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        currentUser = data.user;
        if (data.csrf_token) {
            csrfToken = data.csrf_token;
        }

        document.getElementById('my-username').textContent = currentUser.username;
        document.getElementById('my-avatar').textContent = currentUser.username.charAt(0).toUpperCase();

        if (currentUser.public_key) {
            myPublicKey = await CryptoEngine.importPublicKey(currentUser.public_key);
        }
    }

    async function initKeyMaterial() {
        if (!currentUser) return;

        myPrivateKey = await CryptoEngine.getPrivateKey(currentUser.username);
        const warningBanner = document.getElementById('key-warning');

        if (!myPrivateKey) {
            if (warningBanner) warningBanner.style.display = 'flex';
            document.getElementById('my-key-badge').textContent = '⚠️ Key Missing';
            document.getElementById('my-key-badge').style.color = '#f59e0b';
            document.getElementById('my-key-badge').style.background = 'rgba(245, 158, 11, 0.15)';
        } else {
            if (warningBanner) warningBanner.style.display = 'none';
        }
    }

    async function generateAndUploadNewKey() {
        try {
            const btn = document.getElementById('gen-key-btn');
            if (btn) btn.disabled = true;

            const keyPair = await CryptoEngine.generateRSAKeyPair();
            await CryptoEngine.storePrivateKey(currentUser.username, keyPair.privateKey);
            myPrivateKey = keyPair.privateKey;

            const spki = await CryptoEngine.exportPublicKey(keyPair.publicKey);
            myPublicKey = keyPair.publicKey;

            // Upload new public key to server with CSRF protection
            const headers = { 'Content-Type': 'application/json' };
            if (csrfToken) {
                headers['X-CSRF-Token'] = csrfToken;
            }

            await fetch('/api/users/public_key', {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ public_key: spki })
            });

            document.getElementById('key-warning').style.display = 'none';
            document.getElementById('my-key-badge').textContent = '🔒 RSA-2048 Active';
            document.getElementById('my-key-badge').style.color = '#34d399';
            document.getElementById('my-key-badge').style.background = 'rgba(16, 185, 129, 0.15)';

            // If active contact open, reload history
            if (activeContact) {
                await selectContact(activeContact);
            }
        } catch (err) {
            alert('Failed to generate key: ' + err.message);
        }
    }

    function initSocket() {
        socket = io();

        function updateConnectionStatus(status, text) {
            const pill = document.getElementById('connection-status');
            const label = document.getElementById('connection-status-text');
            if (pill) {
                pill.className = `connection-pill ${status}`;
            }
            if (label) {
                label.textContent = text;
            }
        }

        socket.on('connect', () => {
            console.log('Socket.IO transport connected.');
            updateConnectionStatus('connected', 'Connected');
        });

        socket.on('disconnect', () => {
            console.warn('Socket.IO disconnected.');
            updateConnectionStatus('disconnected', 'Disconnected');
        });

        socket.on('connect_error', () => {
            updateConnectionStatus('reconnecting', 'Reconnecting...');
        });

        socket.on('connected_ack', (data) => {
            console.log('Socket room authenticated:', data.room);
        });

        socket.on('receive_encrypted_message', async (msg) => {
            // Check if message is from the active contact
            if (activeContact && msg.sender_id === activeContact.id) {
                await appendDecryptedIncomingMessage(msg);
            } else {
                // Highlight contact in sidebar
                highlightUnreadContact(msg.sender_id);
            }
        });

        socket.on('message_sent_ack', (ack) => {
            console.log('Message delivered and persisted:', ack.message_id || ack.uuid);
        });

        socket.on('error', (err) => {
            console.error('Socket error:', err);
            alert('Server error: ' + (err.error || 'Message dispatch failed'));
        });
    }

    // --- Contacts Management ---
    async function loadContacts(query = '') {
        const listDiv = document.getElementById('contact-list');
        try {
            const url = query ? `/api/users?search=${encodeURIComponent(query)}` : '/api/users';
            const res = await fetch(url);
            if (!res.ok) return;

            const data = await res.json();
            contacts = data.users;

            listDiv.innerHTML = '';
            if (contacts.length === 0) {
                listDiv.innerHTML = `
                    <div class="empty-state" style="padding-top: 40px;">
                        <p>${query ? 'No contacts match search.' : 'No other users registered yet.'}</p>
                    </div>`;
                return;
            }

            contacts.forEach(user => {
                const item = document.createElement('div');
                item.className = 'contact-item' + (activeContact && activeContact.id === user.id ? ' active' : '');
                item.dataset.userId = user.id;

                item.innerHTML = `
                    <div class="avatar">${escapeHtml(user.username.charAt(0).toUpperCase())}</div>
                    <div class="contact-meta">
                        <div class="contact-name">
                            <span>${escapeHtml(user.username)}</span>
                            <span style="font-size: 11px; color: ${user.has_public_key ? '#34d399' : '#f59e0b'};">
                                ${user.has_public_key ? '🔒 Key Ready' : '⚠️ No Key'}
                            </span>
                        </div>
                        <div class="contact-sub" id="unread-sub-${user.id}">Ready for secure chat</div>
                    </div>
                `;

                item.addEventListener('click', () => selectContact(user));
                listDiv.appendChild(item);
            });
        } catch (err) {
            console.error('Error loading contacts:', err);
        }
    }

    // --- Public Key Trust & Verification (Phase 1) ---
    async function selectContact(contact) {
        activeContact = contact;
        activeContact.isKeyChanged = false;

        // Close mobile sidebar if open
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('mobile-open');

        // Reset any key changed warning
        const changedWarning = document.getElementById('key-changed-warning');
        if (changedWarning) changedWarning.style.display = 'none';

        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) sendBtn.disabled = false;

        // Update active class in sidebar
        document.querySelectorAll('.contact-item').forEach(el => {
            el.classList.toggle('active', parseInt(el.dataset.userId) === contact.id);
        });

        // Reset unread subtext
        const subtext = document.getElementById(`unread-sub-${contact.id}`);
        if (subtext) subtext.textContent = 'End-to-End Encrypted';

        // Update Chat Header
        document.getElementById('chat-header').style.display = 'flex';
        document.getElementById('chat-input-form').style.display = 'flex';
        document.getElementById('partner-name').textContent = contact.username;
        document.getElementById('partner-avatar').textContent = contact.username.charAt(0).toUpperCase();

        const fpContainer = document.getElementById('partner-fingerprint');
        fpContainer.innerHTML = 'Fingerprint: Loading...';

        // Fetch peer public key and verify fingerprint
        try {
            const keyRes = await fetch(`/api/users/${contact.id}/public_key`);
            if (keyRes.ok) {
                const keyData = await keyRes.json();
                activeContact.public_key = keyData.public_key;
                activeContact.cryptoKey = await CryptoEngine.importPublicKey(keyData.public_key);

                // Deterministic SHA-256 fingerprint matching backend
                const currentFp = await CryptoEngine.computeKeyFingerprint(keyData.public_key);
                activeContact.fingerprint = currentFp;

                // Check previously trusted fingerprint in IndexedDB (scoped to current logged-in user)
                const trustedFp = await CryptoEngine.getTrustedFingerprint(currentUser.username, contact.id);

                if (trustedFp === null) {
                    // First contact: TOFU trust prompt
                    fpContainer.innerHTML = `
                        <span>Fingerprint: ${escapeHtml(currentFp)}</span>
                        <button id="trust-btn" class="key-trust-btn" title="Mark this peer's public key as trusted">Trust Key</button>
                    `;
                    document.getElementById('trust-btn').addEventListener('click', async () => {
                        await CryptoEngine.storeTrustedFingerprint(currentUser.username, contact.id, currentFp);
                        renderTrustedBadge(fpContainer, currentFp);
                    });
                } else if (trustedFp === currentFp) {
                    // Verified matching key
                    renderTrustedBadge(fpContainer, currentFp);
                } else {
                    // KEY CHANGED ALERT!
                    activeContact.isKeyChanged = true;
                    fpContainer.innerHTML = `
                        <span style="color: #ef4444;">Fingerprint: ${escapeHtml(currentFp)} (⚠️ CHANGED)</span>
                    `;

                    // Show prominent security alert banner
                    if (changedWarning) {
                        changedWarning.style.display = 'flex';
                        const reverifyBtn = document.getElementById('reverify-key-btn');
                        if (reverifyBtn) {
                            reverifyBtn.onclick = async () => {
                                const confirmChange = confirm(
                                    `SECURITY WARNING:\n\nThe public key for ${contact.username} has changed from the previously trusted key.\n` +
                                    `Old Fingerprint:\n${trustedFp}\n\nNew Fingerprint:\n${currentFp}\n\n` +
                                    `Do you want to trust this new key?`
                                );
                                if (confirmChange) {
                                    await CryptoEngine.storeTrustedFingerprint(currentUser.username, contact.id, currentFp);
                                    activeContact.isKeyChanged = false;
                                    changedWarning.style.display = 'none';
                                    renderTrustedBadge(fpContainer, currentFp);
                                    if (sendBtn) sendBtn.disabled = false;
                                }
                            };
                        }
                    }
                }
            } else {
                activeContact.cryptoKey = null;
                fpContainer.textContent = 'Key Not Set';
            }
        } catch (e) {
            console.error('Failed to import peer public key:', e);
            fpContainer.textContent = 'Key Error';
        }

        // Load and decrypt chat history
        await loadAndRenderHistory(contact.id);
    }

    function renderTrustedBadge(container, fingerprint) {
        container.innerHTML = `
            <span>Fingerprint: ${escapeHtml(fingerprint)}</span>
            <span class="key-trusted-badge">✓ Trusted</span>
        `;
    }

    function highlightUnreadContact(senderId) {
        const subtext = document.getElementById(`unread-sub-${senderId}`);
        if (subtext) {
            subtext.textContent = '● New encrypted message';
            subtext.style.color = '#38bdf8';
            subtext.style.fontWeight = 'bold';
        }
    }

    // --- Message History & Decryption ---
    async function loadAndRenderHistory(contactId) {
        const stream = document.getElementById('message-stream');
        stream.innerHTML = '<div class="empty-state"><p>Decrypting conversation history locally...</p></div>';

        try {
            const res = await fetch(`/api/chat/history/${contactId}`);
            if (!res.ok) {
                stream.innerHTML = '<div class="empty-state"><p>Failed to load chat history.</p></div>';
                return;
            }

            const data = await res.json();
            const encryptedMessages = data.messages;

            if (encryptedMessages.length === 0) {
                stream.innerHTML = `
                    <div class="empty-state">
                        <div style="font-size: 36px; margin-bottom: 8px;">💬</div>
                        <p>No messages yet. Send an encrypted message below!</p>
                    </div>`;
                return;
            }

            // Client-side batch decryption using local private key
            let decryptedList = [];
            if (myPrivateKey) {
                decryptedList = await CryptoEngine.decryptChatHistory(encryptedMessages, myPrivateKey);
            } else {
                decryptedList = encryptedMessages.map(m => ({
                    ...m,
                    plaintext: '[Encrypted - Private key not present on this device]'
                }));
            }

            stream.innerHTML = '';
            decryptedList.forEach(m => {
                appendMessageBubble(m.plaintext, m.sender_id === currentUser.id, m.created_at);
            });

            scrollToBottom();
        } catch (err) {
            console.error('History load error:', err);
            stream.innerHTML = '<div class="empty-state"><p>Error decrypting history.</p></div>';
        }
    }

    async function appendDecryptedIncomingMessage(msg) {
        let plaintext = '[Encrypted payload]';
        if (myPrivateKey) {
            try {
                plaintext = await CryptoEngine.decryptHybridMessage(
                    msg.ciphertext,
                    msg.iv,
                    msg.encrypted_key,
                    myPrivateKey
                );
            } catch (err) {
                plaintext = '[Decryption error: message authentication failed]';
            }
        }
        appendMessageBubble(plaintext, false, msg.timestamp);
        scrollToBottom();
    }

    function appendMessageBubble(plaintext, isSent, timestamp) {
        const stream = document.getElementById('message-stream');

        // Remove welcome/empty state if present
        const welcome = document.getElementById('welcome-state');
        if (welcome) welcome.remove();

        const wrapper = document.createElement('div');
        wrapper.className = 'message-bubble-wrapper ' + (isSent ? 'sent' : 'received');

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        // SECURE: Strict textContent usage to completely prevent DOM XSS
        bubble.textContent = plaintext;

        const timeSpan = document.createElement('div');
        timeSpan.className = 'message-time';
        const timeFormatted = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Now';
        timeSpan.textContent = (isSent ? 'Sent ' : '') + timeFormatted + ' • 🔒 E2EE';

        wrapper.appendChild(bubble);
        wrapper.appendChild(timeSpan);
        stream.appendChild(wrapper);
    }

    function scrollToBottom() {
        const stream = document.getElementById('message-stream');
        if (stream) stream.scrollTop = stream.scrollHeight;
    }

    // --- Outgoing Message Sending (Phase 2 & Phase 3) ---
    async function sendMessage(text) {
        if (!text || !activeContact) return;

        if (!myPublicKey) {
            alert('Your public key is not initialized. Please generate a key first.');
            return;
        }

        if (!activeContact.cryptoKey) {
            alert(`${activeContact.username} has not uploaded a public key. Encrypted communication is not possible.`);
            return;
        }

        if (activeContact.isKeyChanged) {
            const proceed = confirm(
                `SECURITY ALERT: ${activeContact.username}'s public key has changed!\n\n` +
                `Sending messages to an unverified new key could compromise message confidentiality.\n` +
                `Do you want to verify the key first?`
            );
            if (proceed) return;
        }

        try {
            // 1. Client generates canonical UUIDv4 for protocol-level replay protection (Phase 3)
            const messageId = CryptoEngine.generateUUIDv4();

            // 2. Encrypt message locally using hybrid encryption (AES-256-GCM + RSA-OAEP dual-wrapping)
            const hybridPackage = await CryptoEngine.encryptHybridMessage(
                text,
                myPublicKey,
                activeContact.cryptoKey
            );

            // 3. Emit versioned structured message payload over Socket.IO (Phase 2)
            socket.emit('send_encrypted_message', {
                version: 1,
                message_id: messageId,
                recipient_id: activeContact.id,
                ciphertext: hybridPackage.ciphertext,
                iv: hybridPackage.iv,
                sender_encrypted_key: hybridPackage.sender_encrypted_key,
                recipient_encrypted_key: hybridPackage.recipient_encrypted_key
            });

            // 4. Render outgoing bubble immediately in UI
            appendMessageBubble(text, true, new Date().toISOString());
            scrollToBottom();

        } catch (err) {
            console.error('Encryption or sending error:', err);
            alert('Failed to send encrypted message: ' + err.message);
        }
    }

    // --- DOM Event Bindings ---
    function bindDOMEvents() {
        const form = document.getElementById('chat-input-form');
        const input = document.getElementById('message-input');
        const searchInput = document.getElementById('contact-search');
        const logoutBtn = document.getElementById('logout-btn');
        const genKeyBtn = document.getElementById('gen-key-btn');
        const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
        const sidebar = document.getElementById('sidebar');

        if (sidebarToggleBtn && sidebar) {
            sidebarToggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
            });
        }

        if (form && input) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if (text) {
                    input.value = '';
                    await sendMessage(text);
                }
            });
        }

        if (searchInput) {
            let debounceTimer = null;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    loadContacts(e.target.value.trim());
                }, 250);
            });
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                const headers = {};
                if (csrfToken) {
                    headers['X-CSRF-Token'] = csrfToken;
                }
                await fetch('/api/logout', { method: 'POST', headers: headers });
                CryptoEngine.clearPeerKeyCache();
                window.location.href = '/login';
            });
        }

        if (genKeyBtn) {
            genKeyBtn.addEventListener('click', generateAndUploadNewKey);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    return {
        init
    };
})();
