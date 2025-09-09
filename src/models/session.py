from datetime import datetime, timezone, timedelta
from . import db

class AuthSession(db.Model):
    __tablename__ = 'auth_sessions'
    
    # Primary key
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Session identification
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    
    # Foreign key to accounts table
    account_id = db.Column(db.BigInteger, db.ForeignKey('accounts.id'), nullable=False)
    
    # Session metadata
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<AuthSession {self.session_id}>'
    
    def __init__(self, session_id, account_id, expires_in_hours=24):
        """
        Initialize a new session
        
        Args:
            session_id (str): Unique session identifier
            account_id (int): ID of the associated account
            expires_in_hours (int): Number of hours until session expires (default: 24)
        """
        self.session_id = session_id
        self.account_id = account_id
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    
    def is_expired(self):
        """Check if the session has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self):
        """Check if the session is valid (active and not expired)"""
        return self.is_active and not self.is_expired()
    
    def extend_session(self, hours=24):
        """Extend the session expiration time"""
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        db.session.commit()
    
    def invalidate(self):
        """Invalidate the session"""
        self.is_active = False
        db.session.commit()
    
    def to_dict(self):
        """Convert session to dictionary for API responses"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'account_id': self.account_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid()
        }
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """Remove all expired sessions from the database"""
        expired_sessions = cls.query.filter(
            cls.expires_at < datetime.now(timezone.utc)
        ).all()
        
        for session in expired_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return len(expired_sessions)
    
    @classmethod
    def get_valid_session(cls, session_id):
        """Get a valid session by session_id"""
        session = cls.query.filter_by(session_id=session_id).first()
        if session and session.is_valid():
            return session
        return None

