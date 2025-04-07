from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.document import Document
from app.models.fine import Fine
from app.models.dispute import Dispute
from app.models.communication import Notification, Message

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user-specific data for dashboard
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.created_at.desc()).limit(5).all()
    fines = Fine.query.filter_by(user_id=current_user.id).order_by(Fine.created_at.desc()).limit(5).all()
    disputes = Dispute.query.filter_by(user_id=current_user.id).order_by(Dispute.created_at.desc()).limit(5).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    unread_messages = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    
    # Get role-specific data
    if current_user.is_police():
        issued_fines = Fine.query.filter_by(issued_by=current_user.id).order_by(Fine.created_at.desc()).limit(5).all()
        pending_disputes = Dispute.query.filter_by(assigned_to=current_user.id, status='pending').count()
        return render_template('main/dashboard.html', 
                              documents=documents,
                              fines=fines, 
                              disputes=disputes, 
                              notifications=notifications,
                              unread_messages=unread_messages,
                              issued_fines=issued_fines,
                              pending_disputes=pending_disputes)
    
    elif current_user.is_court():
        pending_disputes = Dispute.query.filter_by(assigned_to=current_user.id, status='pending').order_by(Dispute.created_at.desc()).limit(5).all()
        return render_template('main/dashboard.html', 
                              documents=documents,
                              fines=fines, 
                              disputes=disputes, 
                              notifications=notifications,
                              unread_messages=unread_messages,
                              pending_disputes=pending_disputes)
    
    elif current_user.is_admin():
        total_users = len(set([d.user_id for d in Document.query.all()]))
        total_documents = Document.query.count()
        total_fines = Fine.query.count()
        total_disputes = Dispute.query.count()
        return render_template('main/dashboard.html', 
                              documents=documents,
                              fines=fines, 
                              disputes=disputes, 
                              notifications=notifications,
                              unread_messages=unread_messages,
                              total_users=total_users,
                              total_documents=total_documents,
                              total_fines=total_fines,
                              total_disputes=total_disputes)
    
    # Regular citizen dashboard
    return render_template('main/dashboard.html', 
                          documents=documents,
                          fines=fines, 
                          disputes=disputes, 
                          notifications=notifications,
                          unread_messages=unread_messages)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html')

@main_bp.route('/help')
def help():
    return render_template('main/help.html')
