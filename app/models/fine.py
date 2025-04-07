from datetime import datetime
import uuid
from app import db

class Fine(db.Model):
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    challan_number = db.Column(db.String(64), default=lambda: f"ECH-{str(uuid.uuid4())[:8].upper()}", unique=True)
    violation_type = db.Column(db.String(128), nullable=False)
    violation_description = db.Column(db.Text)
    violation_date = db.Column(db.DateTime, nullable=False)
    violation_location = db.Column(db.String(256))
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, disputed, waived
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_number = db.Column(db.String(20))
    license_number = db.Column(db.String(20))
    evidence_file_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='fine', lazy='dynamic')
    dispute = db.relationship('Dispute', backref='fine', uselist=False, foreign_keys='Dispute.fine_id')
    
    def __repr__(self):
        return f'<Fine {self.challan_number}>'
    
    def is_overdue(self):
        return datetime.utcnow() > self.due_date and self.status == 'pending'
    
    def calculate_penalty(self):
        """Calculate late payment penalty if applicable"""
        if not self.is_overdue():
            return 0
        
        days_overdue = (datetime.utcnow() - self.due_date).days
        penalty_rate = 0.02  # 2% per day
        max_penalty = 0.5    # Maximum 50% penalty
        
        penalty = min(days_overdue * penalty_rate, max_penalty) * self.amount
        return round(penalty, 2)
    
    def total_amount_due(self):
        """Calculate total amount due including penalties"""
        return self.amount + self.calculate_penalty()

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(64), default=lambda: f"TXN-{str(uuid.uuid4())[:8].upper()}", unique=True)
    fine_id = db.Column(db.Integer, db.ForeignKey('fines.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(64))  # credit card, debit card, net banking, etc.
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_details = db.Column(db.Text)
    receipt_number = db.Column(db.String(64), unique=True)
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'
