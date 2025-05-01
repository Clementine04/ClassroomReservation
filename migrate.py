"""
Database migration script for Render deployment
This automatically runs before the application starts to create tables
"""
from app import app, db, User
import os
import sys
import time

def migrate():
    """Create tables and initial admin if needed"""
    try:
        print("=" * 50)
        print("MIGRATION SCRIPT STARTING")
        print("=" * 50)
        
        # Force production mode on Render
        is_render = os.environ.get('RENDER', '') == 'true' or 'RENDER_SERVICE_ID' in os.environ
        if is_render:
            print("Running on Render detected", file=sys.stderr)
            
        print(f"Starting database migration with URI type: {app.config['SQLALCHEMY_DATABASE_URI'].split(':')[0]}")
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:15]}...")
        
        # Wait for database to be ready if on Render
        if is_render:
            print("Waiting for database to be ready...")
            time.sleep(5)  # Give Postgres time to start
            
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
            
            if 'users' not in tables:
                print("WARNING: 'users' table was not created! Check your database configuration.")
                db_uri_type = app.config['SQLALCHEMY_DATABASE_URI'].split(':')[0]
                if db_uri_type == 'sqlite':
                    print("Using SQLite in production may cause issues!")
                elif db_uri_type.startswith('postgresql'):
                    print("Using PostgreSQL but tables not created correctly!")
                else:
                    print(f"Unknown database type: {db_uri_type}")
            else:
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
        
        # If we're on Render, don't crash the service but log the error
        if not is_render:
            raise
        else:
            print("WARNING: Migration failed but continuing to avoid crashing service")

if __name__ == "__main__":
    migrate() 