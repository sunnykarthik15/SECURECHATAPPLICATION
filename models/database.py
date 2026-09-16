import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from utils.security import compute_public_key_fingerprint, is_valid_uuid4

class User(db.Model):
    """User account model storing credentials and public cryptographic key."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    public_key = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Referential relationships with cascade deletion
    sent_messages = db.relationship(
        'Message',
        foreign_keys='Message.sender_id',
        backref='sender_user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    received_messages = db.relationship(
        'Message',
        foreign_keys='Message.recipient_id',
        backref='recipient_user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def fingerprint(self) -> str:
        """Deterministic SHA-256 fingerprint formatted in 4-character blocks."""
        if not self.public_key:
            return ""
        return compute_public_key_fingerprint(self.public_key)

    def set_password(self, password: str) -> None:
        """Hash the plaintext password using Werkzeug's secure hashing (scrypt/pbkdf2)."""
        if not password or len(password.strip()) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if len(password) > 128:
            raise ValueError("Password exceeds maximum allowed length of 128 characters.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored cryptographic hash."""
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Return safe user representation (never exposes password_hash)."""
        return {
            'id': self.id,
            'username': self.username,
            'public_key': self.public_key,
            'fingerprint': self.fingerprint,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}'>"


class Message(db.Model):
    """
    Message model storing client-side encrypted payloads and dual-wrapped AES keys.
    The database never stores plaintext message content or private keys.
    Includes protocol version and canonical UUIDv4 message_id for replay protection.
    """
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    version = db.Column(db.Integer, default=1, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Encrypted payload
    ciphertext = db.Column(db.Text, nullable=False)  # Base64 AES-256-GCM ciphertext + 128-bit tag
    iv = db.Column(db.String(64), nullable=False)    # Base64 96-bit (12-byte) initialization vector
    
    # Dual-wrapped AES key (hybrid encryption)
    sender_encrypted_key = db.Column(db.Text, nullable=False)     # Wrapped with sender's RSA-OAEP public key
    recipient_encrypted_key = db.Column(db.Text, nullable=False)  # Wrapped with recipient's RSA-OAEP public key
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Composite indexes for dialogue retrieval and unique message_id constraint
    __table_args__ = (
        db.Index('ix_messages_dialogue_sender', 'sender_id', 'recipient_id', 'created_at'),
        db.Index('ix_messages_dialogue_recipient', 'recipient_id', 'sender_id', 'created_at'),
    )

    def __init__(self, **kwargs):
        # Auto-generate UUIDv4 if message_id is not provided (preserves compatibility with existing tests)
        if 'message_id' not in kwargs or not kwargs['message_id']:
            kwargs['message_id'] = str(uuid.uuid4())
        super().__init__(**kwargs)

    def to_dict(self, for_user_id=None) -> dict:
        """
        Serialize message for client decryption with strict key isolation (Phase 4).
        If for_user_id is provided, supplies ONLY the respective participant's encrypted key.
        The opposite party's wrapped key is never exposed.
        """
        encrypted_key = None
        if for_user_id is not None:
            if for_user_id == self.sender_id:
                encrypted_key = self.sender_encrypted_key
            elif for_user_id == self.recipient_id:
                encrypted_key = self.recipient_encrypted_key

        return {
            'id': self.id,
            'message_id': self.message_id,
            'version': self.version,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'ciphertext': self.ciphertext,
            'iv': self.iv,
            'encrypted_key': encrypted_key,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<Message id={self.id} message_id='{self.message_id}' sender={self.sender_id} recipient={self.recipient_id}>"
