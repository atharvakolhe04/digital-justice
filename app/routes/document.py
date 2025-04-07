import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.document import Document, DocumentAccessLog
from app.models.user import User
from app.utils.qrcode_generator import generate_document_qr

document_bp = Blueprint('document', __name__, url_prefix='/documents')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@document_bp.route('/')
@login_required
def index():
    # Get all documents for the current user
    if current_user.is_admin() or current_user.is_police() or current_user.is_court():
        # Officials can see all documents
        documents = Document.query.order_by(Document.created_at.desc()).all()
    else:
        # Citizens can only see their own documents
        documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.created_at.desc()).all()
    
    return render_template('document/index.html', documents=documents)

@document_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'document_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['document_file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            title = request.form.get('title')
            document_type = request.form.get('document_type')
            description = request.form.get('description')
            expiry_date = request.form.get('expiry_date')
            
            # Create document upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static/uploads/documents')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_filename = f"{current_user.id}_{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, new_filename)
            file.save(file_path)
            
            # Create new document record
            new_document = Document(
                title=title,
                document_type=document_type,
                file_path=f"uploads/documents/{new_filename}",
                description=description,
                user_id=current_user.id
            )
            
            if expiry_date:
                new_document.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
            
            try:
                db.session.add(new_document)
                db.session.commit()
                
                # Generate QR code for the document
                qr_dir = os.path.join(current_app.root_path, 'static/uploads/qrcodes')
                os.makedirs(qr_dir, exist_ok=True)
                qr_path = os.path.join(qr_dir, f"doc_{new_document.id}.png")
                generate_document_qr(new_document.verification_code, qr_path)
                
                flash('Document uploaded successfully', 'success')
                return redirect(url_for('document.view', document_id=new_document.id))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {str(e)}', 'danger')
        else:
            flash('File type not allowed', 'danger')
    
    return render_template('document/upload.html')

@document_bp.route('/<int:document_id>')
@login_required
def view(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if the user has permission to view this document
    if not (current_user.id == document.user_id or current_user.is_admin() or current_user.is_police() or current_user.is_court()):
        flash('You do not have permission to view this document', 'danger')
        return redirect(url_for('document.index'))
    
    # Log document access
    access_log = DocumentAccessLog(
        document_id=document.id,
        accessed_by=current_user.id,
        action='view',
        ip_address=request.remote_addr
    )
    
    try:
        db.session.add(access_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while logging access: {str(e)}', 'warning')
    
    return render_template('document/view.html', document=document, DocumentAccessLog=DocumentAccessLog)

@document_bp.route('/<int:document_id>/download')
@login_required
def download(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if the user has permission to download this document
    if not (current_user.id == document.user_id or current_user.is_admin() or current_user.is_police() or current_user.is_court()):
        flash('You do not have permission to download this document', 'danger')
        return redirect(url_for('document.index'))
    
    # Log document access
    access_log = DocumentAccessLog(
        document_id=document.id,
        accessed_by=current_user.id,
        action='download',
        ip_address=request.remote_addr
    )
    
    try:
        db.session.add(access_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while logging access: {str(e)}', 'warning')
    
    file_path = os.path.join(current_app.root_path, 'static', document.file_path)
    return send_file(file_path, as_attachment=True)

@document_bp.route('/<int:document_id>/verify', methods=['GET', 'POST'])
@login_required
def verify(document_id):
    # Only officials can verify documents
    if not (current_user.is_admin() or current_user.is_police() or current_user.is_court()):
        flash('You do not have permission to verify documents', 'danger')
        return redirect(url_for('document.index'))
    
    document = Document.query.get_or_404(document_id)
    
    if request.method == 'POST':
        verification_status = request.form.get('verification_status') == 'verified'
        
        document.is_verified = verification_status
        document.verified_by = current_user.id
        document.verified_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            # Log document access
            access_log = DocumentAccessLog(
                document_id=document.id,
                accessed_by=current_user.id,
                action='verify',
                ip_address=request.remote_addr
            )
            db.session.add(access_log)
            db.session.commit()
            
            flash('Document verification status updated', 'success')
            return redirect(url_for('document.view', document_id=document.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('document/verify.html', document=document)

@document_bp.route('/verify-code/<verification_code>')
def verify_by_code(verification_code):
    document = Document.query.filter_by(verification_code=verification_code).first_or_404()
    
    # Log document access if user is logged in
    if current_user.is_authenticated:
        access_log = DocumentAccessLog(
            document_id=document.id,
            accessed_by=current_user.id,
            action='verify_by_code',
            ip_address=request.remote_addr
        )
        
        try:
            db.session.add(access_log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while logging access: {str(e)}', 'warning')
    
    return render_template('document/verify_by_code.html', document=document)
