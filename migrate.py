"""
Database migration script for Render deployment
This automatically runs before the application starts to create tables
"""
from app import app, db, User
import os

def migrate():
    """Create tables and initial admin if needed"""
    try:
        print(f"Starting database migration with URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Database type: {'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
        
        with app.app_context():
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("Tables created successfully")
            
            # List all tables to verify
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Available tables: {tables}")
            
            # Create admin user if not exists
            print("Checking for admin user...")
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
                print("Admin user created successfully")
            else:
                print("Admin user already exists")
                
            print("Migration completed successfully")
    except Exception as e:
        print(f"Migration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    migrate() 