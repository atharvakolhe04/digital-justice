import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config=None):
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing-only')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digital_justice.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Set login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.document import document_bp
    from app.routes.fine import fine_bp
    from app.routes.dispute import dispute_bp
    from app.routes.communication import communication_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(fine_bp)
    app.register_blueprint(dispute_bp, url_prefix='/disputes')
    app.register_blueprint(communication_bp)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Add custom Jinja2 filters
    @app.template_filter('timeago')
    def timeago_filter(date):
        """Convert a datetime to a relative time string, like '3 days ago'."""
        now = datetime.now()
        diff = now - date
        
        seconds = diff.total_seconds()
        minutes = seconds / 60
        hours = minutes / 60
        days = hours / 24
        months = days / 30
        years = days / 365
        
        if seconds < 60:
            return "just now"
        elif minutes < 60:
            return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
        elif hours < 24:
            return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
        elif days < 30:
            return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
        elif months < 12:
            return f"{int(months)} month{'s' if int(months) != 1 else ''} ago"
        else:
            return f"{int(years)} year{'s' if int(years) != 1 else ''} ago"
    
    return app
