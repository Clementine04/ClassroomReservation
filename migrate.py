"""
Database migration script for Render deployment
This automatically runs before the application starts to create tables
"""
from app import app, db, User

def migrate():
    """Create tables and initial admin if needed"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='23-11773').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            admin = User(
                username='23-11773',
                display_name='Administrator',
                role='admin',
                password_hash=generate_password_hash('Adminako123!')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")
            
        print("Migration completed successfully")

if __name__ == "__main__":
    migrate() 