from app import create_app, db
from app.models.user import User
from datetime import datetime

def create_users():
    """Create test users with different roles if they don't already exist"""
    app = create_app()
    
    with app.app_context():
        # Check if users already exist
        admin_exists = User.query.filter_by(username='admin').first()
        police_exists = User.query.filter_by(username='police').first()
        court_exists = User.query.filter_by(username='court').first()
        
        # Create admin user
        if not admin_exists:
            admin = User(
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                phone='1234567890',
                address='Admin Office, Digital Justice HQ',
                role='admin',
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Admin user created")
        
        # Create police user
        if not police_exists:
            police = User(
                username='police',
                email='police@example.com',
                first_name='Police',
                last_name='Officer',
                phone='9876543210',
                address='Police Station, Digital City',
                role='police',
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                is_active=True
            )
            police.set_password('police123')
            db.session.add(police)
            print("Police user created")
        
        # Create court user
        if not court_exists:
            court = User(
                username='court',
                email='court@example.com',
                first_name='Court',
                last_name='Judge',
                phone='5555555555',
                address='Court House, Justice Square',
                role='court',
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                is_active=True
            )
            court.set_password('court123')
            db.session.add(court)
            print("Court user created")
        
        # Commit changes
        db.session.commit()
        print("All users created successfully!")

if __name__ == '__main__':
    create_users()
