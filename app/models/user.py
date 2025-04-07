from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(256))
    role = db.Column(db.String(20), default='citizen')  # citizen, police, court, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    documents = db.relationship('Document', foreign_keys='Document.user_id', backref='owner', lazy='dynamic')
    verified_documents = db.relationship('Document', foreign_keys='Document.verified_by', backref='verifier', lazy='dynamic')
    fines = db.relationship('Fine', foreign_keys='Fine.user_id', backref='user', lazy='dynamic')
    issued_fines = db.relationship('Fine', foreign_keys='Fine.issued_by', backref='issuer', lazy='dynamic')
    disputes = db.relationship('Dispute', foreign_keys='Dispute.user_id', backref='user', lazy='dynamic')
    assigned_disputes = db.relationship('Dispute', foreign_keys='Dispute.assigned_to', backref='assigned_officer', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    # NotificationSettings relationship is defined in the NotificationSettings model with backref
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_police(self):
        return self.role == 'police'
    
    def is_court(self):
        return self.role == 'court'
    
    def is_citizen(self):
        return self.role == 'citizen'
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
