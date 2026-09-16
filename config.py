import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration for development and local testing."""
    ENV = os.environ.get('FLASK_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secure-chat-dev-secret-key-change-in-prod-128bit')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'chat.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie security settings (Development: Secure=False for HTTP)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Keep False in local development over HTTP
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Request size limit (4MB max request payload)
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024

    # CSRF Protection enabled by default
    WTF_CSRF_ENABLED = True

    # Explicit, configurable CORS allowed origins (REST and Socket.IO)
    _cors_env = os.environ.get('ALLOWED_ORIGINS')
    if _cors_env:
        CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_env.split(',') if origin.strip()]
    else:
        CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:5000', 'http://localhost:5000']


class ProductionConfig(Config):
    """
    Hardened configuration for production environments.
    Enforces HTTPS cookies and strict secret key provision from environment.
    """
    ENV = 'production'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Ensure production secret key is not default at class definition time
    _prod_secret = os.environ.get('SECRET_KEY')
    if _prod_secret and len(_prod_secret) >= 32 and _prod_secret != 'secure-chat-dev-secret-key-change-in-prod-128bit':
        SECRET_KEY = _prod_secret
    else:
        # Default placeholder that will be validated and rejected in create_app if running in production
        SECRET_KEY = 'UNSET_PRODUCTION_SECRET_KEY'


class TestConfig(Config):
    """Configuration used for automated testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key-not-for-production-use'
    WTF_CSRF_ENABLED = False
    CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:5000', 'http://localhost:5000']
