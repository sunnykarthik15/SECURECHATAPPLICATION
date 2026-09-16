import uuid
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session
from sqlalchemy import or_, and_
from extensions import db
from models.database import User, Message
from routes.auth import login_required
from utils.security import is_valid_uuid4, is_valid_base64, csrf_protect

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/history/<int:contact_id>', methods=['GET'])
@login_required
def get_chat_history(contact_id: int):
    """
    Retrieve chronological encrypted chat history between the authenticated user
    and a designated contact peer.
    Enforces strict Row-Level Access Control and Key Isolation:
    - Only the two participants can access messages.
    - Each participant receives ONLY their own wrapped key (never the peer's).
    """
    current_user_id = session.get('user_id')

    # Verify target contact exists
    contact = db.session.get(User, contact_id)
    if not contact:
        return jsonify({'error': 'Contact user not found.'}), 404

    # Optional pagination
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    limit = min(max(1, limit), 500)  # Bound limit between 1 and 500
    offset = max(0, offset)

    # Query all messages exchanged strictly between current_user and contact
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user_id, Message.recipient_id == contact_id),
            and_(Message.sender_id == contact_id, Message.recipient_id == current_user_id)
        )
    ).order_by(Message.created_at.asc()).offset(offset).limit(limit).all()

    # Format response: contextualize encrypted_key for the requesting user (Phase 4 isolation)
    result = []
    for msg in messages:
        if msg.sender_id == current_user_id:
            user_wrapped_key = msg.sender_encrypted_key
        else:
            user_wrapped_key = msg.recipient_encrypted_key

        result.append({
            'id': msg.id,
            'message_id': msg.message_id,
            'version': msg.version,
            'sender_id': msg.sender_id,
            'recipient_id': msg.recipient_id,
            'ciphertext': msg.ciphertext,
            'iv': msg.iv,
            'encrypted_key': user_wrapped_key,
            'created_at': msg.created_at.isoformat() if msg.created_at else None
        })

    return jsonify({
        'contact_id': contact.id,
        'contact_username': contact.username,
        'count': len(result),
        'messages': result
    }), 200

@chat_bp.route('/send', methods=['POST'])
@login_required
@csrf_protect
def send_message_rest():
    """
    REST endpoint to submit an encrypted structured message.
    Implements structured protocol validation (Phase 2) and replay protection (Phase 3).
    """
    sender_id = session.get('user_id')
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid payload format. Must be a JSON object.'}), 400

    # Sender authorization: session is authoritative
    client_sender = data.get('sender_id')
    if client_sender is not None and client_sender != sender_id:
        return jsonify({'error': 'Sender identity mismatch. Impersonation rejected.'}), 403

    # Protocol version validation
    version = data.get('version', 1)
    if version != 1:
        return jsonify({'error': 'Unsupported protocol version. Expected version: 1.'}), 400

    # Message ID & Replay protection
    msg_id = data.get('message_id')
    if msg_id:
        if not is_valid_uuid4(msg_id):
            return jsonify({'error': 'Invalid message_id. Must be a valid canonical UUIDv4.'}), 400
    else:
        msg_id = str(uuid.uuid4())

    # Check duplicate
    existing = Message.query.filter_by(message_id=msg_id).first()
    if existing:
        return jsonify({'error': 'Duplicate message_id detected. Replay rejected.'}), 409

    # Recipient validation
    recipient_id = data.get('recipient_id')
    if not recipient_id or not isinstance(recipient_id, int):
        return jsonify({'error': 'Valid recipient_id is required.'}), 400
    if recipient_id == sender_id:
        return jsonify({'error': 'Cannot send messages to yourself.'}), 400

    recipient = db.session.get(User, recipient_id)
    if not recipient:
        return jsonify({'error': 'Recipient not found.'}), 404

    # Cryptographic fields validation
    ciphertext = data.get('ciphertext', '').strip()
    iv = data.get('iv', '').strip()
    sender_encrypted_key = data.get('sender_encrypted_key', '').strip()
    recipient_encrypted_key = data.get('recipient_encrypted_key', '').strip()

    if not ciphertext or not iv or not sender_encrypted_key or not recipient_encrypted_key:
        return jsonify({'error': 'Missing encrypted message components (ciphertext, iv, keys).'}), 400

    try:
        message = Message(
            message_id=msg_id,
            version=version,
            sender_id=sender_id,
            recipient_id=recipient_id,
            ciphertext=ciphertext,
            iv=iv,
            sender_encrypted_key=sender_encrypted_key,
            recipient_encrypted_key=recipient_encrypted_key,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(message)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to store message. Please try again.'}), 500

    return jsonify({
        'status': 'stored',
        'id': message.id,
        'message_id': message.message_id,
        'timestamp': message.created_at.isoformat()
    }), 201
