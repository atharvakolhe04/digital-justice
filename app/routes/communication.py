from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.communication import Message, Notification, SOSAlert
from app.models.user import User
from app.models.notification_settings import NotificationSettings

communication_bp = Blueprint('communication', __name__, url_prefix='/communication')

@communication_bp.route('/messages')
@login_required
def messages():
    # Get all messages for the current user
    received_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    return render_template('communication/messages.html', received_messages=received_messages, sent_messages=sent_messages)

@communication_bp.route('/messages/new', methods=['GET', 'POST'])
@login_required
def new_message():
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        # Validate form data
        if not recipient_id or not body:
            flash('Recipient and message body are required', 'danger')
            return redirect(url_for('communication.new_message'))
        
        # Check if recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            flash('Recipient not found', 'danger')
            return redirect(url_for('communication.new_message'))
        
        # Create new message
        new_message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            subject=subject,
            body=body
        )
        
        try:
            db.session.add(new_message)
            db.session.commit()
            flash('Message sent successfully', 'success')
            return redirect(url_for('communication.messages'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    # Get all users for the recipient dropdown
    officials = []
    citizens = []
    
    if current_user.is_citizen():
        # Citizens can only message officials
        officials = User.query.filter(User.role.in_(['police', 'court', 'admin'])).all()
    elif current_user.is_admin():
        # Admins can message anyone
        officials = User.query.filter(User.role.in_(['police', 'court', 'admin'])).filter(User.id != current_user.id).all()
        citizens = User.query.filter_by(role='citizen').all()
    elif current_user.is_police():
        # Police can message other officials and citizens
        officials = User.query.filter(User.role.in_(['police', 'court', 'admin'])).filter(User.id != current_user.id).all()
        citizens = User.query.filter_by(role='citizen').all()
    elif current_user.is_court():
        # Court officials can message other officials and citizens
        officials = User.query.filter(User.role.in_(['police', 'court', 'admin'])).filter(User.id != current_user.id).all()
        citizens = User.query.filter_by(role='citizen').all()
    
    # Get recipient if specified in URL
    recipient = None
    recipient_id = request.args.get('recipient_id')
    if recipient_id:
        recipient = User.query.get(recipient_id)
    
    return render_template('communication/new_message.html', officials=officials, citizens=citizens, recipient=recipient)

@communication_bp.route('/messages/<int:message_id>')
@login_required
def view_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # Check if the user has permission to view this message
    if not (current_user.id == message.sender_id or current_user.id == message.recipient_id):
        flash('You do not have permission to view this message', 'danger')
        return redirect(url_for('communication.messages'))
    
    # Mark message as read if the current user is the recipient
    if current_user.id == message.recipient_id and not message.is_read:
        message.is_read = True
        db.session.commit()
    
    return render_template('communication/view_message.html', message=message)

@communication_bp.route('/messages/<int:message_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_message(message_id):
    original_message = Message.query.get_or_404(message_id)
    
    # Check if the user has permission to reply to this message
    if not (current_user.id == original_message.sender_id or current_user.id == original_message.recipient_id):
        flash('You do not have permission to reply to this message', 'danger')
        return redirect(url_for('communication.messages'))
    
    if request.method == 'POST':
        body = request.form.get('body')
        
        if not body:
            flash('Message body is required', 'danger')
            return redirect(url_for('communication.reply_message', message_id=message_id))
        
        # Determine recipient (the other party in the conversation)
        recipient_id = original_message.sender_id if current_user.id == original_message.recipient_id else original_message.recipient_id
        
        # Create reply message
        reply_subject = f"Re: {original_message.subject}" if original_message.subject else "Re: No Subject"
        
        reply_message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            subject=reply_subject,
            body=body
        )
        
        try:
            db.session.add(reply_message)
            db.session.commit()
            flash('Reply sent successfully', 'success')
            return redirect(url_for('communication.messages'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('communication/reply_message.html', message=original_message)

@communication_bp.route('/notifications')
@login_required
def notifications():
    # Get filter type from query parameters
    filter_type = request.args.get('filter', 'all')
    
    # Get page number from query parameters
    page = request.args.get('page', 1, type=int)
    
    # Base query for notifications
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type == 'read':
        query = query.filter_by(is_read=True)
    elif filter_type == 'fine':
        query = query.filter_by(notification_type='fine')
    elif filter_type == 'sos':
        query = query.filter_by(notification_type='sos')
    elif filter_type == 'message':
        query = query.filter_by(notification_type='message')
    
    # Get unread counts
    unread_counts = {
        'all': Notification.query.filter_by(user_id=current_user.id, is_read=False).count(),
        'fine': Notification.query.filter_by(user_id=current_user.id, is_read=False, notification_type='fine').count(),
        'sos': Notification.query.filter_by(user_id=current_user.id, is_read=False, notification_type='sos').count(),
        'message': Notification.query.filter_by(user_id=current_user.id, is_read=False, notification_type='message').count()
    }
    
    # Paginate notifications
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page,
        per_page=10,
        error_out=False
    )
    
    # Get notification settings
    notification_settings = NotificationSettings.query.filter_by(user_id=current_user.id).first()
    if not notification_settings:
        notification_settings = NotificationSettings(
            user_id=current_user.id,
            email_notifications=True,
            sms_notifications=True,
            push_notifications=True
        )
        db.session.add(notification_settings)
        db.session.commit()
    
    return render_template(
        'communication/notifications.html',
        notifications=notifications,
        unread_counts=unread_counts,
        filter=filter_type,
        notification_settings=notification_settings
    )

@communication_bp.route('/update-notification-settings', methods=['POST'])
@login_required
def update_notification_settings():
    # Get or create notification settings for the user
    notification_settings = NotificationSettings.query.filter_by(user_id=current_user.id).first()
    if not notification_settings:
        notification_settings = NotificationSettings(user_id=current_user.id)
        db.session.add(notification_settings)
    
    # Update email notification settings
    notification_settings.email_documents = 'email_documents' in request.form
    notification_settings.email_fines = 'email_fines' in request.form
    notification_settings.email_disputes = 'email_disputes' in request.form
    notification_settings.email_messages = 'email_messages' in request.form
    
    # Update SMS notification settings
    notification_settings.sms_documents = 'sms_documents' in request.form
    notification_settings.sms_fines = 'sms_fines' in request.form
    notification_settings.sms_disputes = 'sms_disputes' in request.form
    
    # Save changes
    notification_settings.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Notification settings updated successfully', 'success')
    return redirect(url_for('communication.notifications'))

@communication_bp.route('/mark-all-read', methods=['GET', 'POST'])
@login_required
def mark_all_read():
    # Get all unread notifications for the current user
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    # Mark all as read
    for notification in unread_notifications:
        notification.is_read = True
    
    # Save changes
    db.session.commit()
    
    flash('All notifications marked as read', 'success')
    return redirect(url_for('communication.notifications'))

@communication_bp.route('/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if the user has permission to mark this notification as read
    if not current_user.id == notification.user_id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    notification.is_read = True
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@communication_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        flash('All notifications marked as read', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('communication.notifications'))

@communication_bp.route('/notifications/<int:notification_id>/mark_read')
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if the user has permission to mark this notification as read
    if notification.user_id != current_user.id:
        flash('You do not have permission to mark this notification as read', 'danger')
        return redirect(url_for('communication.notifications'))
    
    # Mark notification as read
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Notification marked as read', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('communication.notifications'))

@communication_bp.route('/notifications/<int:notification_id>/mark_unread')
@login_required
def mark_unread(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if the user has permission to mark this notification as unread
    if notification.user_id != current_user.id:
        flash('You do not have permission to mark this notification as unread', 'danger')
        return redirect(url_for('communication.notifications'))
    
    # Mark notification as unread
    notification.is_read = False
    notification.read_at = None
    
    try:
        db.session.commit()
        flash('Notification marked as unread', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('communication.notifications'))

@communication_bp.route('/notifications/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if the user has permission to delete this notification
    if notification.user_id != current_user.id:
        flash('You do not have permission to delete this notification', 'danger')
        return redirect(url_for('communication.notifications'))
    
    try:
        # Delete notification
        db.session.delete(notification)
        db.session.commit()
        flash('Notification deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('communication.notifications'))

@communication_bp.route('/sos')
@login_required
def sos_alerts():
    # Get SOS alerts based on user role
    if current_user.is_admin() or current_user.is_police():
        # Officials can see all active SOS alerts
        active_alerts = SOSAlert.query.filter_by(status='active').order_by(SOSAlert.created_at.desc()).all()
        resolved_alerts = SOSAlert.query.filter(SOSAlert.status != 'active').order_by(SOSAlert.created_at.desc()).all()
    else:
        # Citizens can only see their own SOS alerts
        active_alerts = SOSAlert.query.filter_by(user_id=current_user.id, status='active').order_by(SOSAlert.created_at.desc()).all()
        resolved_alerts = SOSAlert.query.filter_by(user_id=current_user.id).filter(SOSAlert.status != 'active').order_by(SOSAlert.created_at.desc()).all()
    
    return render_template('communication/sos_alerts.html', active_alerts=active_alerts, resolved_alerts=resolved_alerts)

@communication_bp.route('/sos/new', methods=['GET', 'POST'])
@login_required
def new_sos():
    # Only citizens can create SOS alerts
    if not current_user.is_citizen():
        flash('Only citizens can create SOS alerts', 'danger')
        return redirect(url_for('communication.sos_alerts'))
    
    if request.method == 'POST':
        location = request.form.get('location')
        description = request.form.get('description')
        
        # Create new SOS alert
        new_alert = SOSAlert(
            user_id=current_user.id,
            location=location,
            description=description
        )
        
        try:
            db.session.add(new_alert)
            db.session.commit()
            
            # Create notifications for all police officers
            police_officers = User.query.filter_by(role='police').all()
            for officer in police_officers:
                notification = Notification(
                    user_id=officer.id,
                    title='SOS Alert',
                    message=f'New SOS alert from {current_user.first_name} {current_user.last_name}.',
                    notification_type='sos',
                    related_id=new_alert.id
                )
                db.session.add(notification)
            
            db.session.commit()
            
            flash('SOS alert sent successfully', 'success')
            return redirect(url_for('communication.sos_alerts'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('communication/new_sos.html')

@communication_bp.route('/sos/<int:alert_id>/cancel', methods=['GET', 'POST'])
@login_required
def cancel_sos(alert_id):
    # Only citizens can cancel their own SOS alerts
    if not current_user.is_citizen():
        flash('Only citizens can cancel SOS alerts', 'danger')
        return redirect(url_for('communication.sos_alerts'))
    
    sos_alert = SOSAlert.query.get_or_404(alert_id)
    
    # Check if this is the user's own SOS alert
    if sos_alert.user_id != current_user.id:
        flash('You can only cancel your own SOS alerts', 'danger')
        return redirect(url_for('communication.sos_alerts'))
    
    # Check if SOS alert is already resolved
    if sos_alert.status != 'active':
        flash('This SOS alert has already been resolved or cancelled', 'warning')
        return redirect(url_for('communication.sos_alerts'))
    
    if request.method == 'POST':
        reason = request.form.get('reason', 'No reason provided')
        
        # Update SOS alert
        sos_alert.status = 'cancelled'
        sos_alert.resolved_by = current_user.id
        sos_alert.resolved_at = datetime.utcnow()
        sos_alert.resolution_notes = f'Cancelled by citizen. Reason: {reason}'
        
        try:
            db.session.commit()
            
            # Create notifications for all police officers
            police_officers = User.query.filter_by(role='police').all()
            for officer in police_officers:
                notification = Notification(
                    user_id=officer.id,
                    title='SOS Alert Cancelled',
                    message=f'SOS alert from {current_user.first_name} {current_user.last_name} has been cancelled.',
                    notification_type='sos_cancelled',
                    related_id=sos_alert.id
                )
                db.session.add(notification)
            
            db.session.commit()
            
            flash('SOS alert cancelled successfully', 'success')
            return redirect(url_for('communication.sos_alerts'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('communication/cancel_sos.html', alert=sos_alert)

@communication_bp.route('/sos/<int:sos_id>/resolve', methods=['GET', 'POST'])
@login_required
def resolve_sos(sos_id):
    # Only officials can resolve SOS alerts
    if not (current_user.is_admin() or current_user.is_police()):
        flash('You do not have permission to resolve SOS alerts', 'danger')
        return redirect(url_for('communication.sos_alerts'))
    
    sos_alert = SOSAlert.query.get_or_404(sos_id)
    
    # Check if SOS alert is already resolved
    if sos_alert.status != 'active':
        flash('This SOS alert has already been resolved', 'warning')
        return redirect(url_for('communication.sos_alerts'))
    
    if request.method == 'POST':
        resolution_status = request.form.get('resolution_status')
        resolution_notes = request.form.get('resolution_notes')
        
        # Update SOS alert
        sos_alert.status = resolution_status
        sos_alert.resolved_by = current_user.id
        sos_alert.resolved_at = datetime.utcnow()
        sos_alert.resolution_notes = resolution_notes
        
        try:
            db.session.commit()
            
            # Create notification for the citizen
            notification = Notification(
                user_id=sos_alert.user_id,
                title='SOS Alert Resolved',
                message=f'Your SOS alert has been resolved by {current_user.first_name} {current_user.last_name}.',
                notification_type='sos_resolved',
                related_id=sos_alert.id
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('SOS alert resolved successfully', 'success')
            return redirect(url_for('communication.sos_alerts'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('communication/resolve_sos.html', sos_alert=sos_alert)
