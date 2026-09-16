/**
 * Client-Side Authentication Coordinator
 * Manages registration with local Web Crypto RSA-2048 keypair generation
 * and login with IndexedDB private key verification.
 *
 * Security Note:
 * - All private keys are generated in the browser via Web Crypto API and saved to IndexedDB.
 * - Private keys are never transmitted to the server.
 * - IndexedDB is client-side storage within the browser sandbox (not hardware-backed storage).
 */

const AuthHandler = (function () {
    'use strict';

    function showError(msg) {
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.textContent = msg;
            errorAlert.style.display = 'block';
        }
    }

    function hideError() {
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.style.display = 'none';
        }
    }

    function setKeygenStatus(show, text) {
        const statusDiv = document.getElementById('keygen-status');
        const textSpan = document.getElementById('keygen-text');
        if (statusDiv) {
            statusDiv.style.display = show ? 'flex' : 'none';
            if (textSpan && text) {
                textSpan.textContent = text;
            }
        }
    }

    function bindPasswordToggle() {
        const toggleBtn = document.getElementById('toggle-password');
        const passwordInput = document.getElementById('password');
        if (!toggleBtn || !passwordInput) return;

        toggleBtn.addEventListener('click', () => {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
            const icon = toggleBtn.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = isPassword ? '🙈' : '👁️';
            }
            toggleBtn.setAttribute('title', isPassword ? 'Hide password' : 'Show password');
            toggleBtn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
        });
    }

    function initRegister() {
        bindPasswordToggle();
        const form = document.getElementById('register-form');
        const submitBtn = document.getElementById('submit-btn');

        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideError();

            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;

            if (!username || username.length < 3 || username.length > 32) {
                showError('Username must be between 3 and 32 characters long.');
                return;
            }
            if (!password || password.length < 8) {
                showError('Password must be at least 8 characters long.');
                return;
            }
            if (password.length > 128) {
                showError('Password exceeds maximum allowed length of 128 characters.');
                return;
            }

            try {
                submitBtn.disabled = true;
                setKeygenStatus(true, 'Generating RSA-2048 keypair via Web Crypto API...');

                // 1. Generate client-side RSA-2048 keypair
                const keyPair = await CryptoEngine.generateRSAKeyPair();

                setKeygenStatus(true, 'Saving private key to browser IndexedDB...');

                // 2. Persist private key locally in IndexedDB (never sent over network)
                await CryptoEngine.storePrivateKey(username, keyPair.privateKey);

                setKeygenStatus(true, 'Exporting public SPKI key...');

                // 3. Export public key to SPKI Base64
                const publicKeySpki = await CryptoEngine.exportPublicKey(keyPair.publicKey);

                setKeygenStatus(true, 'Registering user account on server...');

                // 4. Send registration payload to server (ONLY public key is sent)
                const regResponse = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: username,
                        password: password,
                        public_key: publicKeySpki
                    })
                });

                const regData = await regResponse.json();

                if (!regResponse.ok) {
                    throw new Error(regData.error || 'Registration failed.');
                }

                // 5. Automatically log in upon successful registration
                setKeygenStatus(true, 'Registration successful. Unlocking session...');
                const loginResponse = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username, password: password })
                });

                if (!loginResponse.ok) {
                    window.location.href = '/login';
                    return;
                }

                // Redirect to chat
                window.location.href = '/chat';

            } catch (err) {
                console.error('Registration error:', err);
                showError(err.message || 'An unexpected error occurred during registration.');
            } finally {
                submitBtn.disabled = false;
                setKeygenStatus(false);
            }
        });
    }

    function initLogin() {
        bindPasswordToggle();
        const form = document.getElementById('login-form');
        const submitBtn = document.getElementById('submit-btn');

        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideError();

            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;

            if (!username || !password) {
                showError('Please enter both username and password.');
                return;
            }
            if (password.length > 128) {
                showError('Password exceeds maximum allowed length of 128 characters.');
                return;
            }

            try {
                submitBtn.disabled = true;

                // 1. Authenticate with backend
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username, password: password })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Invalid credentials.');
                }

                // 2. Check if this browser has the corresponding private key
                const hasKey = await CryptoEngine.hasPrivateKey(username);
                if (!hasKey) {
                    console.warn(`Private key not found for ${username} on this browser device.`);
                }

                // 3. Redirect to chat interface
                window.location.href = '/chat';

            } catch (err) {
                console.error('Login error:', err);
                showError(err.message || 'Authentication failed. Please check your credentials.');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    return {
        initRegister,
        initLogin
    };
})();
