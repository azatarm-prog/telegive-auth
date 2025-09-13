from datetime import datetime, timezone
from . import db

class Account(db.Model):
    __tablename__ = 'accounts'
    
    # Primary key
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Bot token and identification
    bot_token_encrypted = db.Column(db.String(500), unique=True, nullable=False)
    bot_id = db.Column(db.BigInteger, unique=True, nullable=False)
    bot_username = db.Column(db.String(100), nullable=False)
    bot_name = db.Column(db.String(255), nullable=False)
    
    # Channel info (managed by channel service but stored here)
    channel_id = db.Column(db.BigInteger, default=0)
    channel_username = db.Column(db.String(100), default='')
    channel_title = db.Column(db.String(255), default='Setup Required')
    channel_member_count = db.Column(db.Integer, default=0)
    
    # Permissions (managed by channel service)
    can_post_messages = db.Column(db.Boolean, default=False)
    can_edit_messages = db.Column(db.Boolean, default=False)
    can_send_media = db.Column(db.Boolean, default=False)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    bot_verified = db.Column(db.Boolean, default=True)
    channel_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_bot_check_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sessions = db.relationship('AuthSession', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Account {self.bot_username}>'
    
    def to_dict(self):
        """Convert account to dictionary for API responses"""
        return {
            'id': self.id,
            'bot_username': self.bot_username,
            'bot_name': self.bot_name,
            'bot_id': self.bot_id,
            'channel_id': self.channel_id,
            'channel_username': self.channel_username,
            'channel_title': self.channel_title,
            'channel_member_count': self.channel_member_count,
            'can_post_messages': self.can_post_messages,
            'can_edit_messages': self.can_edit_messages,
            'can_send_media': self.can_send_media,
            'is_active': self.is_active,
            'bot_verified': self.bot_verified,
            'channel_verified': self.channel_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_bot_check_at': self.last_bot_check_at.isoformat() if self.last_bot_check_at else None
        }
    
    def to_public_dict(self):
        """Convert account to dictionary for public API responses (without sensitive data)"""
        return {
            'id': self.id,
            'bot_username': self.bot_username,
            'bot_name': self.bot_name,
            'channel_username': self.channel_username,
            'channel_title': self.channel_title,
            'channel_member_count': self.channel_member_count,
            'channel_verified': self.channel_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def update_bot_check(self):
        """Update the last bot check timestamp"""
        self.last_bot_check_at = datetime.now(timezone.utc)
        db.session.commit()
    
    @property
    def bot_token(self):
        """
        Decrypt and return the bot token for service integration
        This property allows Channel Service to access the decrypted token
        """
        if self.bot_token_encrypted:
            try:
                from utils.encryption import decrypt_token
                return decrypt_token(self.bot_token_encrypted)
            except Exception as e:
                # Log the error but don't expose it
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error decrypting bot token for account {self.id}: {str(e)}")
                return None
        return None

