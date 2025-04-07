import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.dispute import Dispute, DisputeEvidence, DisputeComment
from app.models.fine import Fine
from app.models.user import User
from app.models.communication import Notification
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired
from app.forms.dispute import DecisionForm

dispute_bp = Blueprint('dispute', __name__, url_prefix='/disputes')

class DisputeForm(FlaskForm):
    dispute_type = SelectField('Dispute Type', choices=[('fine', 'Fine Dispute'), ('document', 'Document Dispute')], validators=[DataRequired()])
    reason = TextAreaField('Reason for Dispute', validators=[DataRequired()])
    evidence = FileField('Supporting Documents')

@dispute_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of disputes per page
    
    # Get user's disputes if they're not an admin
    if not current_user.is_admin():
        disputes = Dispute.query.filter_by(user_id=current_user.id)
    else:
        disputes = Dispute.query
    
    # Add pagination
    disputes = disputes.order_by(Dispute.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Calculate statistics
    stats = {
        'total': Dispute.query.count(),
        'pending': Dispute.query.filter_by(status='pending').count(),
        'resolved': Dispute.query.filter(Dispute.status.in_(['approved', 'rejected'])).count()
    }
    
    return render_template('dispute/index.html', disputes=disputes, stats=stats)

@dispute_bp.route('/disputes')
@login_required
def disputes_index():
    # Get all disputes for the user
    disputes = Dispute.query.filter_by(user_id=current_user.id).order_by(Dispute.created_at.desc()).all()
    
    # Get dispute statistics
    stats = {
        'total': len(disputes),
        'pending': len([d for d in disputes if d.status == 'pending']),
        'resolved': len([d for d in disputes if d.status == 'resolved']),
        'rejected': len([d for d in disputes if d.status == 'rejected'])
    }
    
    return render_template('dispute/index.html', disputes=disputes, stats=stats)

@dispute_bp.route('/disputes/fine')
@login_required
def fine_disputes():
    # Get fine disputes for the user
    disputes = Dispute.query.filter_by(user_id=current_user.id, dispute_type='fine')\
        .order_by(Dispute.created_at.desc()).all()
    
    return render_template('dispute/type.html', disputes=disputes, type='Fine')

@dispute_bp.route('/disputes/document')
@login_required
def document_disputes():
    # Get document disputes for the user
    disputes = Dispute.query.filter_by(user_id=current_user.id, dispute_type='document')\
        .order_by(Dispute.created_at.desc()).all()
    
    return render_template('dispute/type.html', disputes=disputes, type='Document')

@dispute_bp.route('/file/<int:fine_id>', methods=['GET', 'POST'])
@login_required
def file_dispute(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    
    # Check if user owns this fine
    if fine.user_id != current_user.id:
        flash('You do not have permission to file a dispute for this fine', 'danger')
        return redirect(url_for('dispute.disputes_index'))
    
    # Check if fine is already disputed
    existing_dispute = Dispute.query.filter_by(fine_id=fine.id).first()
    if existing_dispute:
        flash('A dispute has already been filed for this fine', 'warning')
        return redirect(url_for('dispute.view_dispute', dispute_id=existing_dispute.id))
    
    # Check if fine is already paid
    if fine.status == 'paid':
        flash('This fine has already been paid and cannot be disputed', 'warning')
        return redirect(url_for('fine.view', fine_id=fine.id))
    
    form = DisputeForm()
    
    if form.validate_on_submit():
        # Create new dispute
        new_dispute = Dispute(
            fine_id=fine.id,
            user_id=current_user.id,
            reason=form.reason.data
        )
        
        # Assign to a court official (simplified for now)
        court_official = User.query.filter_by(role='court').first()
        if court_official:
            new_dispute.assigned_to = court_official.id
            new_dispute.status = 'pending'
        else:
            new_dispute.status = 'under_review'
        
        try:
            db.session.add(new_dispute)
            db.session.commit()
            
            # Handle evidence upload if provided
            if form.evidence.data:
                file = form.evidence.data
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'dispute_evidence', str(new_dispute.id))
                    os.makedirs(file_path, exist_ok=True)
                    file_path = os.path.join(file_path, filename)
                    file.save(file_path)
                    
                    # Create evidence record
                    evidence = DisputeEvidence(
                        dispute_id=new_dispute.id,
                        user_id=current_user.id,
                        title=f"Supporting document for dispute {new_dispute.dispute_number}",
                        description='Supporting document uploaded with dispute',
                        file_path=os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER']),
                        file_type=os.path.splitext(filename)[1][1:].lower()
                    )
                    db.session.add(evidence)
                    db.session.commit()
            
            flash('Dispute filed successfully', 'success')
            return redirect(url_for('dispute.view_dispute', dispute_id=new_dispute.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('dispute/file.html', form=form, fine=fine)

@dispute_bp.route('/disputes/<int:dispute_id>')
@login_required
def view_dispute(dispute_id):
    # Get dispute and associated fine
    dispute = Dispute.query.get_or_404(dispute_id)
    fine = Fine.query.get_or_404(dispute.fine_id)
    
    # Check permissions
    if not (current_user.id == dispute.user_id or current_user.id == fine.issued_by or 
             current_user.id == dispute.assigned_to or current_user.is_admin()):
        flash('You do not have permission to view this dispute', 'danger')
        return redirect(url_for('dispute.disputes_index'))
    
    # Get evidence and comments
    evidences = DisputeEvidence.query.filter_by(dispute_id=dispute.id).order_by(DisputeEvidence.uploaded_at.desc()).all()
    comments = DisputeComment.query.filter_by(dispute_id=dispute.id).order_by(DisputeComment.created_at.asc()).all()
    
    return render_template('dispute/view.html', dispute=dispute, fine=fine, evidences=evidences, comments=comments)

@dispute_bp.route('/disputes/<int:dispute_id>/evidence', methods=['POST'], endpoint='add_evidence')
@login_required
def add_dispute_evidence(dispute_id):
    dispute = Dispute.query.get_or_404(dispute_id)
    fine = Fine.query.get_or_404(dispute.fine_id)
    
    # Check permissions
    if not (current_user.id == dispute.user_id or current_user.id == fine.issued_by or 
            current_user.is_admin()):
        flash('You do not have permission to add evidence to this dispute', 'danger')
        return redirect(url_for('dispute.view_dispute', dispute_id=dispute_id))
    
    # Check if dispute is still open
    if dispute.status not in ['pending', 'under_review']:
        flash('This dispute has been closed and no more evidence can be added', 'warning')
        return redirect(url_for('dispute.view_dispute', dispute_id=dispute_id))
    
    # Process the evidence upload
    if 'evidence_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['evidence_file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    # Create evidence upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, 'static/uploads/dispute_evidence')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    new_filename = f"dispute_{dispute_id}_{timestamp}_{filename}"
    file_path = os.path.join(upload_dir, new_filename)
    file.save(file_path)
    
    # Create new evidence record
    new_evidence = DisputeEvidence(
        dispute_id=dispute.id,
        title=request.form.get('title'),
        description=request.form.get('description'),
        file_path=f"uploads/dispute_evidence/{new_filename}",
        file_type=filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown',
        uploaded_by=current_user.id
    )
    
    try:
        db.session.add(new_evidence)
        db.session.commit()
        
        # Create notification for other parties
        if current_user.id == dispute.user_id:
            # Notify court official
            if dispute.assigned_to:
                notification = Notification(
                    user_id=dispute.assigned_to,
                    title='New Evidence Added',
                    message=f'New evidence has been added to dispute {dispute.dispute_number}.',
                    notification_type='evidence',
                    related_id=new_evidence.id
                )
                db.session.add(notification)
        else:
            # Notify citizen
            notification = Notification(
                user_id=dispute.user_id,
                title='New Evidence Added',
                message=f'New evidence has been added to your dispute {dispute.dispute_number}.',
                notification_type='evidence',
                related_id=new_evidence.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash('Evidence added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('dispute.view_dispute', dispute_id=dispute_id))

@dispute_bp.route('/disputes/<int:dispute_id>/comments', methods=['POST'], endpoint='add_comment')
@login_required
def add_dispute_comment(dispute_id):
    dispute = Dispute.query.get_or_404(dispute_id)
    fine = Fine.query.get_or_404(dispute.fine_id)
    
    # Check permissions
    if not (current_user.id == dispute.user_id or current_user.id == fine.issued_by or 
            current_user.is_admin()):
        flash('You do not have permission to add comments to this dispute', 'danger')
        return redirect(url_for('dispute.view_dispute', dispute_id=dispute_id))
    
    # Check if dispute is still open
    if dispute.status not in ['pending', 'under_review']:
        flash('This dispute has been closed and no more comments can be added', 'warning')
        return redirect(url_for('dispute.view_dispute', dispute_id=dispute_id))
    
    comment = request.form.get('comment')
    if not comment:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('dispute.view_dispute', dispute_id=dispute_id))
    
    # Create new comment
    new_comment = DisputeComment(
        dispute_id=dispute.id,
        user_id=current_user.id,
        comment=comment
    )
    
    try:
        db.session.add(new_comment)
        db.session.commit()
        
        # Create notification for other parties
        if current_user.id == dispute.user_id:
            # Notify court official
            if dispute.assigned_to:
                notification = Notification(
                    user_id=dispute.assigned_to,
                    title='New Comment Added',
                    message=f'New comment has been added to dispute {dispute.dispute_number}.',
                    notification_type='comment',
                    related_id=new_comment.id
                )
                db.session.add(notification)
        else:
            # Notify citizen
            notification = Notification(
                user_id=dispute.user_id,
                title='New Comment Added',
                message=f'New comment has been added to your dispute {dispute.dispute_number}.',
                notification_type='comment',
                related_id=new_comment.id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash('Comment added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('dispute.view_dispute', dispute_id=dispute_id))

@dispute_bp.route('/decide/<int:dispute_id>', methods=['GET', 'POST'], endpoint='decide')
@login_required
def decide(dispute_id):
    dispute = Dispute.query.get_or_404(dispute_id)
    fine = Fine.query.get_or_404(dispute.fine_id)
    
    # Check permissions
    if not current_user.is_court():
        flash('You do not have permission to decide this dispute', 'danger')
        return redirect(url_for('dispute.index'))
    
    # Check if dispute can be decided
    if dispute.status != 'pending':
        flash('This dispute cannot be decided as it is no longer pending', 'warning')
        return redirect(url_for('dispute.view_dispute', dispute_id=dispute.id))
    
    form = DecisionForm()
    
    if form.validate_on_submit():
        try:
            # Update dispute status
            dispute.status = form.decision.data
            dispute.decision = form.reason.data
            dispute.decision_date = datetime.utcnow()
            dispute.assigned_to = current_user.id
            
            # Update fine status based on decision
            if form.decision.data == 'approved':
                fine.status = 'waived'
            else:
                fine.status = 'pending'
            
            db.session.commit()
            
            flash('Dispute decision has been recorded successfully', 'success')
            return redirect(url_for('dispute.view_dispute', dispute_id=dispute.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('dispute/decide.html', dispute=dispute, fine=fine, form=form)

@dispute_bp.route('/withdraw/<int:dispute_id>', methods=['GET', 'POST'], endpoint='withdraw_dispute')
@login_required
def withdraw_dispute(dispute_id):
    dispute = Dispute.query.get_or_404(dispute_id)
    
    # Check if user owns this dispute
    if dispute.user_id != current_user.id:
        flash('You do not have permission to withdraw this dispute', 'danger')
        return redirect(url_for('dispute.index'))
    
    # Check if dispute can be withdrawn
    if dispute.status not in ['pending', 'under_review']:
        flash('This dispute cannot be withdrawn as it is no longer pending', 'warning')
        return redirect(url_for('dispute.view_dispute', dispute_id=dispute.id))
    
    if request.method == 'POST':
        try:
            # Update dispute status
            dispute.status = 'withdrawn'
            dispute.withdrawn_at = datetime.utcnow()
            
            # Update fine status
            fine = Fine.query.get_or_404(dispute.fine_id)
            fine.status = 'pending'
            
            db.session.commit()
            
            flash('Dispute has been withdrawn successfully', 'success')
            return redirect(url_for('dispute.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('dispute/withdraw.html', dispute=dispute)

@dispute_bp.route('/pending')
@login_required
def pending():
    # Only court officials can view pending disputes
    if not current_user.is_court():
        flash('You do not have permission to view pending disputes', 'danger')
        return redirect(url_for('dispute.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get pending disputes assigned to this court official
    pending_disputes = Dispute.query.filter_by(
        status='pending',
        assigned_to=current_user.id
    ).order_by(Dispute.created_at.desc()).paginate(
        page=page,
        per_page=per_page
    )
    
    # Calculate statistics
    stats = {
        'total': pending_disputes.total,
        'under_review': Dispute.query.filter_by(
            assigned_to=current_user.id,
            status='under_review'
        ).count(),
        'approved': Dispute.query.filter_by(
            assigned_to=current_user.id,
            status='approved'
        ).count(),
        'rejected': Dispute.query.filter_by(
            assigned_to=current_user.id,
            status='rejected'
        ).count()
    }
    
    return render_template('dispute/pending.html', disputes=pending_disputes, stats=stats)
