"""
Database migration script for Render deployment
This automatically runs before the application starts to create tables
"""
from app import app, db, User, Department, Classroom, Reservation
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
            print("Dropping all tables to ensure clean migration...")
            try:
                db.drop_all()
                print("All tables dropped successfully")
            except Exception as e:
                print(f"Error dropping tables: {str(e)}")
                
            # Create all tables
            print("Creating database tables...")
            # Explicitly list all models to ensure they're imported and seen by SQLAlchemy
            models = [User, Department, Classroom, Reservation]
            print(f"Models to create: {[m.__name__ for m in models]}")
            
            db.create_all()
            print("Tables created successfully")
            
            # List all tables to verify
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Available tables: {tables}")
            
            expected_tables = ['users', 'departments', 'classrooms', 'reservations']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"WARNING: Missing tables: {missing_tables}")
                print("Attempting to create tables directly with SQL...")
                
                # Create tables directly with SQL commands
                try:
                    from sqlalchemy import text
                    
                    with db.engine.begin() as connection:
                        if 'users' not in tables:
                            connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS users (
                                id SERIAL PRIMARY KEY,
                                username VARCHAR(50) UNIQUE NOT NULL,
                                display_name VARCHAR(100),
                                password_hash VARCHAR(128) NOT NULL,
                                role VARCHAR(20) DEFAULT 'student'
                            )
                            """))
                        
                        if 'departments' not in tables:
                            connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS departments (
                                id SERIAL PRIMARY KEY,
                                name VARCHAR(100) NOT NULL
                            )
                            """))
                        
                        if 'classrooms' not in tables:
                            connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS classrooms (
                                id SERIAL PRIMARY KEY,
                                room_number VARCHAR(20) NOT NULL,
                                capacity INTEGER,
                                department_id INTEGER NOT NULL REFERENCES departments(id)
                            )
                            """))
                            
                        if 'reservations' not in tables:
                            connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS reservations (
                                id SERIAL PRIMARY KEY,
                                date DATE NOT NULL,
                                start_time TIME NOT NULL,
                                end_time TIME NOT NULL,
                                purpose VARCHAR(200),
                                user_id INTEGER NOT NULL REFERENCES users(id),
                                classroom_id INTEGER NOT NULL REFERENCES classrooms(id),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                            """))
                    
                    print("Direct SQL table creation completed")
                    
                    # Verify again
                    tables = inspector.get_table_names()
                    print(f"Available tables after SQL creation: {tables}")
                    
                except Exception as e:
                    print(f"Error in direct SQL table creation: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # Create admin user if tables exist
            if 'users' in inspector.get_table_names():
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
            else:
                print("WARNING: 'users' table still missing, cannot create admin user")
                
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