from functools import wraps
import re
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from extensions import db
from models.database import User
from utils.security import (
    USERNAME_REGEX,
    rate_limit,
    csrf_protect,
    get_or_create_csrf_token
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Render the user login interface."""
    if 'user_id' in session:
        return redirect(url_for('chat.chat_page'))
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Render the user registration interface with browser key generation."""
    if 'user_id' in session:
        return redirect(url_for('chat.chat_page'))
    return render_template('register.html')

def login_required(f):
    """Decorator to enforce session authentication on protected endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        current_user = db.session.get(User, session['user_id'])
        if not current_user:
            session.clear()
            return jsonify({'error': 'User session invalid. Please log in again.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Retrieve the currently authenticated User instance or None."""
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

@auth_bp.route('/api/register', methods=['POST'])
@rate_limit('register', max_requests=10, window_seconds=60, by_ip=True)
def register():
    """Register a new user with username, password, and public RSA key."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Missing JSON request body.'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')
    public_key = data.get('public_key', '').strip()

    # Username validation
    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    if len(username) < 3 or len(username) > 32:
        return jsonify({'error': 'Username must be between 3 and 32 characters.'}), 400
    if not USERNAME_REGEX.match(username):
        return jsonify({'error': 'Username can only contain alphanumeric characters and underscores.'}), 400

    # Password validation
    if not password or len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long.'}), 400
    if len(password) > 128:
        return jsonify({'error': 'Password exceeds maximum allowed length of 128 characters.'}), 400

    # Public key validation (if provided)
    if public_key:
        if len(public_key) > 4096:
            return jsonify({'error': 'Public key exceeds maximum length.'}), 400
        if not re.match(r'^[A-Za-z0-9+/=._\s-]+$', public_key):
            return jsonify({'error': 'Invalid public key format.'}), 400

    # Check for existing username
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already taken. Please choose another.'}), 409

    try:
        user = User(username=username, public_key=public_key)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': 'User registered successfully.',
            'user': user.to_dict()
        }), 201
    except Exception:
        db.session.rollback()
        # Never leak traceback or raw exceptions in production
        return jsonify({'error': 'Registration failed. Please verify your submitted details and try again.'}), 500

@auth_bp.route('/api/login', methods=['POST'])
@rate_limit('login', max_requests=10, window_seconds=60, by_ip=True, by_user=True)
def login():
    """Authenticate a user and establish a secure session."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Missing JSON request body.'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        # Generic error message: never reveal whether username exists
        return jsonify({'error': 'Invalid username or password.'}), 401

    # Establish session
    session.clear()
    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = True
    csrf_token = get_or_create_csrf_token()

    return jsonify({
        'message': 'Login successful.',
        'user': user.to_dict(),
        'csrf_token': csrf_token
    }), 200

@auth_bp.route('/api/logout', methods=['POST'])
@csrf_protect
def logout():
    """Clear session data and log out the user."""
    session.clear()
    return jsonify({'message': 'Logged out successfully.'}), 200

@auth_bp.route('/api/auth/me', methods=['GET'])
def get_me():
    """Return the profile of the currently logged-in user."""
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False, 'error': 'Not logged in.'}), 401
    csrf_token = get_or_create_csrf_token()
    return jsonify({
        'authenticated': True,
        'user': user.to_dict(),
        'csrf_token': csrf_token
    }), 200
