import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.fine import Fine, Payment
from app.models.user import User
from app.models.communication import Notification
from app.utils.qrcode_generator import generate_fine_qr, generate_document_qr

fine_bp = Blueprint('fine', __name__, url_prefix='/fines')

@fine_bp.route('/')
@login_required
def index():
    # Get all fines based on user role
    if current_user.is_admin():
        # Admin can see all fines
        fines = Fine.query.order_by(Fine.created_at.desc()).all()
    elif current_user.is_police():
        # Police can see fines they issued
        fines = Fine.query.filter_by(issued_by=current_user.id).order_by(Fine.created_at.desc()).all()
    else:
        # Citizens can only see their own fines
        fines = Fine.query.filter_by(user_id=current_user.id).order_by(Fine.created_at.desc()).all()
    
    return render_template('fine/index.html', fines=fines)

@fine_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue():
    # Only police and admin can issue fines
    if not (current_user.is_police() or current_user.is_admin()):
        flash('You do not have permission to issue fines', 'danger')
        return redirect(url_for('fine.index'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        violation_type = request.form.get('violation_type')
        violation_description = request.form.get('violation_description')
        violation_date = request.form.get('violation_date')
        violation_location = request.form.get('violation_location')
        amount = request.form.get('amount')
        vehicle_number = request.form.get('vehicle_number')
        license_number = request.form.get('license_number')
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('fine.issue'))
        
        # Check if evidence file was uploaded
        evidence_file_path = None
        if 'evidence_file' in request.files:
            file = request.files['evidence_file']
            if file and file.filename != '':
                # Create evidence upload directory if it doesn't exist
                upload_dir = os.path.join(current_app.root_path, 'static/uploads/evidence')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save the file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                new_filename = f"fine_{timestamp}_{filename}"
                file_path = os.path.join(upload_dir, new_filename)
                file.save(file_path)
                evidence_file_path = f"uploads/evidence/{new_filename}"
        
        # Create new fine
        violation_date_obj = datetime.strptime(violation_date, '%Y-%m-%d')
        due_date = violation_date_obj + timedelta(days=30)  # Due date is 30 days from violation date
        
        new_fine = Fine(
            violation_type=violation_type,
            violation_description=violation_description,
            violation_date=violation_date_obj,
            violation_location=violation_location,
            amount=float(amount),
            due_date=due_date,
            issued_by=current_user.id,
            user_id=user_id,
            vehicle_number=vehicle_number,
            license_number=license_number,
            evidence_file_path=evidence_file_path
        )
        
        try:
            db.session.add(new_fine)
            db.session.commit()
            
            # Generate QR code for the fine
            qr_dir = os.path.join(current_app.root_path, 'static/uploads/qrcodes')
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = os.path.join(qr_dir, f"fine_{new_fine.id}.png")
            generate_fine_qr(new_fine.challan_number, qr_path)
            
            # Create notification for the user
            notification = Notification(
                user_id=user_id,
                title='New Fine Issued',
                message=f'A new fine of ₹{amount} has been issued for {violation_type}.',
                notification_type='fine',
                related_id=new_fine.id
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Fine issued successfully', 'success')
            return redirect(url_for('fine.view', fine_id=new_fine.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    # Get all citizens for the dropdown
    citizens = User.query.filter_by(role='citizen').all()
    
    return render_template('fine/issue.html', citizens=citizens)

@fine_bp.route('/<int:fine_id>')
@login_required
def view(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    
    # Check if the user has permission to view this fine
    if not (current_user.id == fine.user_id or current_user.id == fine.issued_by or current_user.is_admin()):
        flash('You do not have permission to view this fine', 'danger')
        return redirect(url_for('fine.index'))
    
    return render_template('fine/view.html', fine=fine)

@fine_bp.route('/<int:fine_id>/pay', methods=['GET', 'POST'])
@login_required
def pay(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    
    # Check if the user has permission to pay this fine
    if not (current_user.id == fine.user_id or current_user.is_admin()):
        flash('You do not have permission to pay this fine', 'danger')
        return redirect(url_for('fine.index'))
    
    # Check if fine is already paid
    if fine.status == 'paid':
        flash('This fine has already been paid', 'warning')
        return redirect(url_for('fine.view', fine_id=fine.id))
    
    # Check if fine is disputed
    if fine.status == 'disputed':
        flash('This fine is currently under dispute', 'warning')
        return redirect(url_for('fine.view', fine_id=fine.id))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        # Calculate total amount including penalties
        total_amount = fine.total_amount_due()
        
        # Create payment record
        payment = Payment(
            fine_id=fine.id,
            amount=total_amount,
            payment_method=payment_method,
            payment_status='completed',
            receipt_number=f"RCP-{fine.challan_number}"
        )
        
        # Update fine status
        fine.status = 'paid'
        
        try:
            db.session.add(payment)
            db.session.commit()
            
            # Create notification for the user
            notification = Notification(
                user_id=fine.user_id,
                title='Fine Payment Successful',
                message=f'Your payment of ₹{total_amount} for fine {fine.challan_number} was successful.',
                notification_type='payment',
                related_id=payment.id
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Payment successful', 'success')
            return redirect(url_for('fine.receipt', payment_id=payment.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('fine/pay.html', fine=fine, total_amount=fine.total_amount_due())

@fine_bp.route('/receipt/<int:payment_id>')
@login_required
def receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    fine = Fine.query.get_or_404(payment.fine_id)
    
    # Check if the user has permission to view this receipt
    if not (current_user.id == fine.user_id or current_user.id == fine.issued_by or current_user.is_admin()):
        flash('You do not have permission to view this receipt', 'danger')
        return redirect(url_for('fine.index'))
    
    # Generate QR code for receipt verification
    qr_dir = os.path.join(current_app.root_path, 'static/uploads/qrcodes')
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = os.path.join(qr_dir, f'receipt_{payment.id}.png')
    
    # Generate verification URL
    base_url = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
    verification_url = f"{base_url}/verify-receipt/{payment.receipt_number}"
    
    # Generate QR code
    generate_document_qr(verification_url, qr_path)
    
    return render_template('fine/receipt.html', payment=payment, fine=fine)

@fine_bp.route('/receipt/<int:payment_id>/download')
@login_required
def download_receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    fine = Fine.query.get_or_404(payment.fine_id)
    
    # Check if the user has permission to download this receipt
    if not (current_user.id == fine.user_id or current_user.id == fine.issued_by or current_user.is_admin()):
        flash('You do not have permission to download this receipt', 'danger')
        return redirect(url_for('fine.index'))
    
    # Create receipts directory if it doesn't exist
    receipts_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'receipts')
    os.makedirs(receipts_dir, exist_ok=True)
    
    # Generate PDF path
    pdf_path = os.path.join(receipts_dir, f'receipt_{payment.id}.pdf')
    
    # Generate PDF if it doesn't exist
    if not os.path.exists(pdf_path):
        from app.utils.pdf_generator import generate_receipt_pdf
        generate_receipt_pdf(payment, fine, pdf_path)
    
    return send_file(pdf_path, as_attachment=True, download_name=f'receipt_{payment.receipt_number}.pdf')

@fine_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        search_value = request.form.get('search_value')
        
        if search_type == 'challan_number':
            fine = Fine.query.filter_by(challan_number=search_value).first()
            if fine:
                return redirect(url_for('fine.view', fine_id=fine.id))
        elif search_type == 'vehicle_number':
            fines = Fine.query.filter_by(vehicle_number=search_value).all()
            return render_template('fine/search_results.html', fines=fines, search_type=search_type, search_value=search_value)
        elif search_type == 'license_number':
            fines = Fine.query.filter_by(license_number=search_value).all()
            return render_template('fine/search_results.html', fines=fines, search_type=search_type, search_value=search_value)
        
        flash('No fines found with the given criteria', 'warning')
    
    return render_template('fine/search.html')
