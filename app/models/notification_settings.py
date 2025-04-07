from datetime import datetime
from app import db

class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Email notification settings
    email_documents = db.Column(db.Boolean, default=True)
    email_fines = db.Column(db.Boolean, default=True)
    email_disputes = db.Column(db.Boolean, default=True)
    email_messages = db.Column(db.Boolean, default=True)
    
    # SMS notification settings
    sms_documents = db.Column(db.Boolean, default=False)
    sms_fines = db.Column(db.Boolean, default=False)
    sms_disputes = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('notification_settings', uselist=False))
    
    def __repr__(self):
        return f'<NotificationSettings for User {self.user_id}>'
