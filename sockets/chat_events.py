import uuid
from datetime import datetime, timezone
from flask import session, request
from flask_socketio import emit, join_room, leave_room, disconnect, ConnectionRefusedError
from extensions import db, socketio
from models.database import User, Message
from utils.security import is_valid_uuid4, is_valid_base64

@socketio.on('connect')
def handle_connect(auth=None):
    """
    Authenticate Socket.IO connection via Flask session cookie.
    Assigns the authenticated user to their private room: user_<id>.
    """
    user_id = session.get('user_id')
    if not user_id:
        # Reject unauthenticated connection
        raise ConnectionRefusedError('Authentication required. Please log in first.')

    user = db.session.get(User, user_id)
    if not user:
        raise ConnectionRefusedError('Invalid session user.')

    room_name = f"user_{user.id}"
    join_room(room_name)
    emit('connected_ack', {
        'status': 'connected',
        'user_id': user.id,
        'username': user.username,
        'room': room_name
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Clean up user private room on disconnect."""
    user_id = session.get('user_id')
    if user_id:
        room_name = f"user_{user_id}"
        leave_room(room_name)

@socketio.on('send_encrypted_message')
def handle_send_encrypted_message(data):
    """
    Handle real-time transmission of client-side end-to-end encrypted messages.
    Enforces:
    - Authenticated session sender (session is authoritative, spoofed sender_id is ignored)
    - Valid recipient
    - Canonical UUIDv4 message_id (Phase 2 & Phase 3)
    - Application-level replay and duplicate protection (reject duplicate message_id)
    - Encrypted key isolation (only recipient's key is dispatched to recipient)
    - Error sanitization (no raw exceptions exposed)
    """
    sender_id = session.get('user_id')
    if not sender_id:
        emit('error', {'error': 'Authentication required.'})
        return

    sender = db.session.get(User, sender_id)
    if not sender:
        emit('error', {'error': 'Invalid sender.'})
        return

    if not isinstance(data, dict):
        emit('error', {'error': 'Invalid payload format. Must be an object.'})
        return

    # Protocol version check
    version = data.get('version', 1)
    if version != 1:
        emit('error', {'error': 'Unsupported protocol version. Expected version: 1.'})
        return

    # Validate recipient
    recipient_id = data.get('recipient_id')
    if not recipient_id or not isinstance(recipient_id, int):
        emit('error', {'error': 'Valid recipient_id is required.'})
        return

    if recipient_id == sender_id:
        emit('error', {'error': 'Cannot send messages to yourself.'})
        return

    recipient = db.session.get(User, recipient_id)
    if not recipient:
        emit('error', {'error': 'Recipient not found.'})
        return

    # Message ID & Replay protection
    msg_id = data.get('message_id')
    if msg_id:
        if not is_valid_uuid4(msg_id):
            emit('error', {'error': 'Invalid message_id format. Must be a canonical UUIDv4.'})
            return
        # Check duplicate
        existing = Message.query.filter_by(message_id=msg_id).first()
        if existing:
            emit('error', {'error': 'Duplicate message_id detected. Replay rejected.'})
            return
    else:
        # Fallback for older / legacy clients
        msg_id = str(uuid.uuid4())

    ciphertext = data.get('ciphertext', '').strip()
    iv = data.get('iv', '').strip()
    sender_encrypted_key = data.get('sender_encrypted_key', '').strip()
    recipient_encrypted_key = data.get('recipient_encrypted_key', '').strip()

    # Validate encrypted payload fields
    if not ciphertext or not iv or not sender_encrypted_key or not recipient_encrypted_key:
        emit('error', {'error': 'Missing encrypted message components (ciphertext, iv, keys).'})
        return

    # Persist encrypted message to database (Zero-knowledge: no plaintext)
    try:
        message = Message(
            message_id=msg_id,
            version=version,
            sender_id=sender_id,  # Strictly authoritative from session
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
        emit('error', {'error': 'Failed to store message. Please try again.'})
        return

    timestamp = message.created_at.isoformat()

    # Dispatch to recipient's private room: exposes ONLY the recipient's wrapped key
    recipient_room = f"user_{recipient_id}"
    emit('receive_encrypted_message', {
        'id': message.id,
        'message_id': message.message_id,
        'version': message.version,
        'sender_id': sender_id,
        'sender_username': sender.username,
        'recipient_id': recipient_id,
        'ciphertext': ciphertext,
        'iv': iv,
        'encrypted_key': recipient_encrypted_key,
        'timestamp': timestamp
    }, room=recipient_room)

    # Acknowledge to sender with message ID and confirmed timestamp
    emit('message_sent_ack', {
        'status': 'stored_and_dispatched',
        'message_id': message.id,
        'uuid': message.message_id,
        'recipient_id': recipient_id,
        'timestamp': timestamp
    })
