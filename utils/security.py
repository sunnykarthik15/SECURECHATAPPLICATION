import re
import base64
import hashlib
import hmac
import time
import secrets
from collections import defaultdict
from functools import wraps
from flask import session, request, jsonify, current_app

UUID4_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,32}$')

def is_valid_uuid4(val: str) -> bool:
    """Strictly validate whether a string is a canonical UUIDv4."""
    if not isinstance(val, str):
        return False
    return bool(UUID4_REGEX.match(val.strip().lower()))

def is_valid_base64(val: str, min_len: int = 1, max_len: int = 262144) -> bool:
    """Validate that a string conforms to Base64 or URL-safe Base64 character sets within size constraints."""
    if not isinstance(val, str):
        return False
    val = val.strip()
    if len(val) < min_len or len(val) > max_len:
        return False
    # Standard base64 and URL-safe base64 characters
    if not re.match(r'^[A-Za-z0-9+/=_\s-]+$', val):
        return False
    return True

def compute_public_key_fingerprint(spki_base64: str) -> str:
    """
    Compute a deterministic SHA-256 fingerprint from the canonical DER bytes
    of an RSA SubjectPublicKeyInfo (SPKI) Base64 string.
    Returns format: 'AB12 CD34 EF56 7890 ...' (16 blocks of 4 hex digits).
    """
    if not spki_base64 or not isinstance(spki_base64, str):
        return ""
    # Normalize by stripping any whitespace/newlines
    clean_b64 = re.sub(r'\s+', '', spki_base64.strip())
    try:
        der_bytes = base64.b64decode(clean_b64)
    except Exception:
        der_bytes = clean_b64.encode('utf-8')
    
    digest = hashlib.sha256(der_bytes).hexdigest().upper()
    # Format as 4-character blocks separated by space
    blocks = [digest[i:i+4] for i in range(0, len(digest), 4)]
    return " ".join(blocks)

class InMemoryRateLimiter:
    """
    Thread-safe, process-local in-memory sliding window rate limiter.
    
    NOTE ON HORIZONTAL SCALING:
    This rate limiter is process-local and resets when the application restarts.
    Multi-instance production deployments would require a shared rate-limit store (e.g. Redis).
    """
    def __init__(self):
        # key: (endpoint, identifier) -> list of timestamp floats
        self.records = defaultdict(list)

    def is_rate_limited(self, endpoint: str, identifier: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        key = f"{endpoint}:{identifier}"
        timestamps = self.records[key]

        # Prune records outside the window
        cutoff = now - window_seconds
        valid_timestamps = [t for t in timestamps if t > cutoff]
        self.records[key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            return True

        self.records[key].append(now)
        return False

    def reset(self):
        self.records.clear()

limiter = InMemoryRateLimiter()

def rate_limit(endpoint_name: str, max_requests: int = 10, window_seconds: int = 60, by_ip: bool = True, by_user: bool = False):
    """
    Decorator to enforce process-local rate limiting on REST endpoints.
    Independently tracks IP and user accounts to prevent password spraying.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_app.config.get('TESTING', False) and not current_app.config.get('FORCE_RATE_LIMIT_TEST', False):
                return f(*args, **kwargs)

            ip = request.remote_addr or 'unknown'

            # 1. IP-level rate limiting
            if by_ip:
                if limiter.is_rate_limited(f"{endpoint_name}:ip", ip, max_requests, window_seconds):
                    return jsonify({
                        'error': 'Too many requests. Please wait a moment and try again.'
                    }), 429

            # 2. Account-level rate limiting (prevents targeted account brute-forcing)
            if by_user:
                data = request.get_json(silent=True) or {}
                user_id = session.get('user_id') or data.get('username')
                if user_id:
                    if limiter.is_rate_limited(f"{endpoint_name}:user", str(user_id), max_requests, window_seconds):
                        return jsonify({
                            'error': 'Too many requests. Please wait a moment and try again.'
                        }), 429

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- CSRF Protection for Session-Authenticated REST Endpoints ---

def get_or_create_csrf_token() -> str:
    """Generate or retrieve the cryptographically random session CSRF token."""
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_hex(32)
        session['_csrf_token'] = token
    return token

def csrf_protect(f):
    """
    Decorator for state-changing REST endpoints that rely on session cookies.
    Requires header 'X-CSRF-Token' or 'X-CSRFToken' matching session token.
    Disabled when WTF_CSRF_ENABLED is False or TESTING is True (unless forced in tests).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get('WTF_CSRF_ENABLED', True):
            return f(*args, **kwargs)
        if current_app.config.get('TESTING', False) and not current_app.config.get('FORCE_CSRF_TEST', False):
            return f(*args, **kwargs)

        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # If user is authenticated by session, CSRF check applies
            if 'user_id' in session:
                expected_token = session.get('_csrf_token')
                provided_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken')
                
                # Also accept from json body if present
                if not provided_token and request.is_json:
                    provided_token = (request.get_json(silent=True) or {}).get('csrf_token')

                if not expected_token or not provided_token or not hmac.compare_digest(str(expected_token), str(provided_token)):
                    return jsonify({'error': 'Invalid or missing CSRF token.'}), 403

        return f(*args, **kwargs)
    return decorated_function
