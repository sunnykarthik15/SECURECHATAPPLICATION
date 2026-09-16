import re
from flask import Blueprint, jsonify, request, session
from extensions import db
from models.database import User
from routes.auth import login_required
from utils.security import compute_public_key_fingerprint, csrf_protect

users_bp = Blueprint('users', __name__, url_prefix='/api')

@users_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """
    List registered users available for one-to-one secure chat.
    Excludes the currently authenticated user from the returned list.
    Supports optional '?search=' query parameter.
    """
    current_user_id = session.get('user_id')
    search_query = request.args.get('search', '').strip()
    if len(search_query) > 64:
        search_query = search_query[:64]

    query = User.query.filter(User.id != current_user_id)

    if search_query:
        query = query.filter(User.username.ilike(f'%{search_query}%'))

    users = query.order_by(User.username.asc()).all()

    return jsonify({
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'has_public_key': bool(u.public_key),
                'fingerprint': u.fingerprint if u.public_key else None,
                'created_at': u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ],
        'count': len(users)
    }), 200

@users_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_by_id(user_id: int):
    """Retrieve public profile information for a specific user."""
    if user_id <= 0:
        return jsonify({'error': 'Invalid user ID.'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    return jsonify({
        'user': user.to_dict()
    }), 200

@users_bp.route('/users/<int:user_id>/public_key', methods=['GET'])
@login_required
def get_user_public_key(user_id: int):
    """
    Retrieve the SPKI Base64 public key of a specific registered user
    along with its deterministic SHA-256 fingerprint for TOFU trust verification.
    """
    if user_id <= 0:
        return jsonify({'error': 'Invalid user ID.'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if not user.public_key:
        return jsonify({'error': 'User has not registered a public key.'}), 404

    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'public_key': user.public_key,
        'fingerprint': user.fingerprint
    }), 200

@users_bp.route('/users/public_key', methods=['PUT', 'POST'])
@login_required
@csrf_protect
def update_my_public_key():
    """
    Update or initialize the authenticated user's public RSA key.
    Strictly restricted to the caller's own session account.
    """
    current_user_id = session.get('user_id')
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({'error': 'User session invalid.'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Missing JSON body.'}), 400

    public_key = data.get('public_key', '').strip()
    if not public_key:
        return jsonify({'error': 'Public key cannot be empty.'}), 400

    # Length check: RSA-2048 SPKI Base64 is ~392 characters
    if len(public_key) < 100 or len(public_key) > 4096:
        return jsonify({'error': 'Invalid public key format or length.'}), 400

    # Basic character set check
    if not re.match(r'^[A-Za-z0-9+/=._\s-]+$', public_key):
        return jsonify({'error': 'Invalid public key format or length.'}), 400

    try:
        user.public_key = public_key
        db.session.commit()
        return jsonify({
            'message': 'Public key updated successfully.',
            'user': user.to_dict()
        }), 200
    except Exception:
        db.session.rollback()
        # Sanitize error: never leak raw DB exception
        return jsonify({'error': 'Failed to update public key. Please try again.'}), 500
