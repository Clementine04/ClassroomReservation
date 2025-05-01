"""
Run this script to test database connectivity before deployment
"""
import os
from app import app, db, User, Department, Classroom, Reservation

def test_db_connection():
    """Test database connection and schema"""
    try:
        with app.app_context():
            # Try to query tables
            users = User.query.limit(1).all()
            departments = Department.query.limit(1).all()
            classrooms = Classroom.query.limit(1).all()
            reservations = Reservation.query.limit(1).all()
            
            print(f"Database connected successfully!")
            print(f"Users: {len(users)}")
            print(f"Departments: {len(departments)}")
            print(f"Classrooms: {len(classrooms)}")
            print(f"Reservations: {len(reservations)}")
            return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

if __name__ == "__main__":
    test_db_connection() 