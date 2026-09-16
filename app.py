import os
from flask import Flask, jsonify, session, redirect, render_template, request
from config import Config
from extensions import db, socketio
from routes.auth import auth_bp
from routes.users import users_bp
from routes.chat import chat_bp
import models.database  # Ensure models are registered
import sockets.chat_events  # Register Socket.IO event handlers
from utils.security import get_or_create_csrf_token

def create_app(config_class=Config):
    """Application factory for the Secure E2EE Chat application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Production security validation
    if app.config.get('ENV') == 'production' and not app.config.get('TESTING', False):
        secret = app.config.get('SECRET_KEY')
        if not secret or secret in ('UNSET_PRODUCTION_SECRET_KEY', 'secure-chat-dev-secret-key-change-in-prod-128bit') or len(secret) < 32:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: In production mode, SECRET_KEY must be "
                "explicitly provided via environment variable and must be at least 32 characters long."
            )
        cors_origins = app.config.get('CORS_ALLOWED_ORIGINS', [])
        if '*' in cors_origins:
            raise ValueError("CRITICAL SECURITY ERROR: Wildcard CORS '*' is prohibited in production configuration.")

    # Ensure database directory exists
    db_dir = os.path.join(app.root_path, 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Initialize extensions with configurable CORS allowed origins
    db.init_app(app)
    allowed_origins = app.config.get('CORS_ALLOWED_ORIGINS', ['http://127.0.0.1:5000', 'http://localhost:5000'])
    socketio.init_app(app, cors_allowed_origins=allowed_origins, manage_session=False)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(chat_bp)
    
    # Create database tables if not existing
    with app.app_context():
        db.create_all()

    # Security headers middleware & REST CORS enforcement
    @app.after_request
    def set_security_headers(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'

        # REST CORS alignment with allowed_origins
        origin = request.headers.get('Origin')
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRF-Token, Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'

        return response

    # Centralized sanitized error handlers
    @app.errorhandler(400)
    def bad_request_error(e):
        return jsonify({'error': 'Bad request. Please verify submitted parameters.'}), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        return jsonify({'error': 'Access forbidden.'}), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return jsonify({'error': 'Resource not found.'}), 404

    @app.errorhandler(413)
    def payload_too_large_error(e):
        return jsonify({'error': 'Request entity too large. Maximum payload size exceeded.'}), 413

    @app.errorhandler(429)
    def rate_limit_error(e):
        return jsonify({'error': 'Too many requests. Please wait a moment and try again.'}), 429

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def internal_server_error(e):
        # Never leak traceback or raw exceptions to users
        return jsonify({'error': 'An internal server error occurred. Please try again later.'}), 500

    # CSRF token endpoint for authenticated clients
    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        token = get_or_create_csrf_token()
        return jsonify({'csrf_token': token}), 200

    # Basic system health check route
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'application': 'Secure Chat Application (E2EE)',
            'crypto_standard': 'RSA-2048 + AES-256-GCM'
        }), 200

    @app.route('/test/crypto')
    def test_crypto_page():
        return render_template('test_crypto.html')

    @app.route('/chat')
    def chat_page():
        if 'user_id' not in session:
            return redirect('/login')
        return render_template('chat.html')

    @app.route('/')
    def index():
        return jsonify({
            'message': 'Secure Chat E2EE Server running.',
            'version': '1.0.0'
        }), 200

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=True)
