from datetime import datetime
import uuid
from app import db

class Dispute(db.Model):
    __tablename__ = 'disputes'
    
    id = db.Column(db.Integer, primary_key=True)
    dispute_number = db.Column(db.String(64), default=lambda: f"DSP-{str(uuid.uuid4())[:8].upper()}", unique=True)
    fine_id = db.Column(db.Integer, db.ForeignKey('fines.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, under_review, rejected, approved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    decision = db.Column(db.Text)
    decision_date = db.Column(db.DateTime)
    
    # Relationships
    evidences = db.relationship('DisputeEvidence', backref='dispute', lazy='dynamic')
    comments = db.relationship('DisputeComment', backref='dispute', lazy='dynamic')
    
    def __repr__(self):
        return f'<Dispute {self.dispute_number}>'
        
    def get_waiting_days(self):
        """Calculate the number of days a dispute has been waiting since creation"""
        return (datetime.now() - self.created_at).days

class DisputeEvidence(db.Model):
    __tablename__ = 'dispute_evidences'
    
    id = db.Column(db.Integer, primary_key=True)
    dispute_id = db.Column(db.Integer, db.ForeignKey('disputes.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(64))  # image, video, document, etc.
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f'<DisputeEvidence {self.id}>'

class DisputeComment(db.Model):
    __tablename__ = 'dispute_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    dispute_id = db.Column(db.Integer, db.ForeignKey('disputes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<DisputeComment {self.id}>'
