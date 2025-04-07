from datetime import datetime
import uuid
from app import db

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    document_type = db.Column(db.String(64), nullable=False)  # ID, License, Certificate, etc.
    file_path = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    verification_code = db.Column(db.String(64), default=lambda: str(uuid.uuid4()), unique=True)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    access_logs = db.relationship('DocumentAccessLog', backref='document', lazy='dynamic')
    
    def __repr__(self):
        return f'<Document {self.title}>'
    
    def is_expired(self):
        if self.expiry_date:
            return datetime.utcnow() > self.expiry_date
        return False
    
    def generate_qr_code(self):
        """Generate QR code for document verification"""
        # This will be implemented in the utils module
        pass

class DocumentAccessLog(db.Model):
    __tablename__ = 'document_access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    accessed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(64))  # view, download, verify, etc.
    ip_address = db.Column(db.String(64))
    
    # Relationship
    user = db.relationship('User', foreign_keys=[accessed_by])
    
    def __repr__(self):
        return f'<DocumentAccessLog {self.id}>'
