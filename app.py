# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///classroom_reservation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # This is the ID number
    display_name = db.Column(db.String(100), nullable=True)  # Added display name field
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'student', 'teacher', or 'admin'
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    classrooms = db.relationship('Classroom', backref='department', lazy=True)

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    reservations = db.relationship('Reservation', backref='classroom', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    purpose = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            
            if user.role == 'admin':
                return redirect(next_page or url_for('admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(next_page or url_for('teacher_dashboard'))
            else:
                return redirect(next_page or url_for('student_dashboard'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')  # ID number
        display_name = request.form.get('display_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('ID number already exists')
            return redirect(url_for('signup'))
        
        # Validate password
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('signup'))
        
        # Password strength validation
        if len(password) < 8:
            flash('Password must be at least 8 characters long')
            return redirect(url_for('signup'))
        
        # Check for lowercase, uppercase, digit and special character
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not (has_lower and has_upper and has_digit and has_special):
            flash('Password must contain lowercase, uppercase, digit, and special character')
            return redirect(url_for('signup'))
        
        # Create new user
        new_user = User(username=username, display_name=display_name)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Student routes
@app.route('/student')
@login_required
def student_dashboard():
    if current_user.role != 'student' and current_user.role != 'teacher' and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    departments = Department.query.all()
    return render_template('student/dashboard.html', departments=departments)

@app.route('/student/departments/<int:department_id>')
@login_required
def view_department_classrooms(department_id):
    if current_user.role != 'student' and current_user.role != 'teacher' and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    department = Department.query.get_or_404(department_id)
    classrooms = Classroom.query.filter_by(department_id=department_id).all()
    return render_template('student/classrooms.html', department=department, classrooms=classrooms)

# New student routes for viewing room bookings
@app.route('/student/room/<int:classroom_id>/bookings')
@login_required
def student_get_room_bookings(classroom_id):
    # This route can be accessed by any authenticated user
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Get all reservations for this classroom
    reservations = Reservation.query.filter_by(classroom_id=classroom_id).all()
    
    bookings_data = []
    for reservation in reservations:
        user = User.query.get(reservation.user_id)
        user_name = user.display_name if user and user.display_name else user.username if user else "Unknown"
        
        bookings_data.append({
            'id': reservation.id,
            'date': reservation.date.strftime('%Y-%m-%d'),
            'start_time': reservation.start_time.strftime('%I:%M %p'),  # AM/PM format
            'end_time': reservation.end_time.strftime('%I:%M %p'),  # AM/PM format
            'purpose': reservation.purpose,
            'user_name': user_name
        })
    
    return jsonify({'success': True, 'bookings': bookings_data})

@app.route('/student/department/<int:department_id>/rooms')
@login_required
def student_get_department_rooms(department_id):
    # This route can be accessed by any authenticated user
    
    # First, clean up expired reservations
    cleanup_expired_reservations()
    
    department = Department.query.get_or_404(department_id)
    classrooms = Classroom.query.filter_by(department_id=department_id).all()
    
    rooms_data = []
    for classroom in classrooms:
        reservation_count = Reservation.query.filter_by(classroom_id=classroom.id).count()
        rooms_data.append({
            'id': classroom.id,
            'room_number': classroom.room_number,
            'capacity': classroom.capacity,
            'has_reservations': reservation_count > 0,
            'reservation_count': reservation_count
        })
    
    return jsonify({'success': True, 'rooms': rooms_data})

# Teacher routes
@app.route('/teacher')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    departments = Department.query.all()
    # Pass today's date for the date picker minimum value
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('teacher/dashboard.html', departments=departments, today=today)

@app.route('/teacher/department/add', methods=['POST'])
@login_required
def add_department():
    if current_user.role != 'admin' and current_user.role != 'teacher':
        flash('Access denied')
        return redirect(url_for('index'))
    
    department_name = request.form.get('department_name')
    if not department_name:
        flash('Department name is required')
        return redirect(url_for('teacher_dashboard'))
    
    # Check if department already exists
    existing_dept = Department.query.filter_by(name=department_name).first()
    if existing_dept:
        flash('Department already exists')
        return redirect(url_for('teacher_dashboard'))
    
    new_department = Department(name=department_name)
    db.session.add(new_department)
    db.session.commit()
    
    flash(f'Department "{department_name}" added successfully')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/classroom/add', methods=['POST'])
@login_required
def add_classroom():
    if current_user.role != 'admin' and current_user.role != 'teacher':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    department_id = request.form.get('department_id')
    room_number = request.form.get('room_number')
    capacity = request.form.get('capacity')
    
    if not all([department_id, room_number, capacity]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Validate capacity is a positive number
    try:
        capacity = int(capacity)
        if capacity <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Capacity must be a positive number'})
    
    # Check if room already exists in this department
    existing_room = Classroom.query.filter_by(department_id=department_id, room_number=room_number).first()
    if existing_room:
        return jsonify({'success': False, 'message': f'Room {room_number} already exists in this department'})
    
    new_classroom = Classroom(
        room_number=room_number,
        capacity=capacity,
        department_id=department_id
    )
    
    db.session.add(new_classroom)
    db.session.commit()
    
    # Return success with the new classroom ID
    return jsonify({
        'success': True, 
        'message': f'Room {room_number} added successfully',
        'classroom_id': new_classroom.id
    })

@app.route('/teacher/room/<int:classroom_id>/bookings')
@login_required
def get_room_bookings(classroom_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # First, clean up expired reservations
    cleanup_expired_reservations()
    
    classroom = Classroom.query.get_or_404(classroom_id)
    reservations = Reservation.query.filter_by(classroom_id=classroom_id).all()
    
    bookings = []
    for reservation in reservations:
        user = User.query.get(reservation.user_id)
        bookings.append({
            'id': reservation.id,
            'date': reservation.date.strftime('%Y-%m-%d'),
            'start_time': reservation.start_time.strftime('%I:%M %p'),  # AM/PM format
            'end_time': reservation.end_time.strftime('%I:%M %p'),      # AM/PM format
            'purpose': reservation.purpose,
            'user_id': reservation.user_id,
            'teacher_name': user.display_name if user else 'Unknown'
        })
    
    return jsonify(bookings)

@app.route('/teacher/booking/<int:booking_id>/delete', methods=['POST'])
@login_required
def delete_booking(booking_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    reservation = Reservation.query.get_or_404(booking_id)
    
    # Only allow teachers to delete their own bookings (admins can delete any)
    if current_user.role != 'admin' and reservation.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'You can only delete your own reservations'}), 403
    
    db.session.delete(reservation)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/teacher/classrooms')
@login_required
def list_classrooms_to_reserve():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    departments = Department.query.all()
    classrooms = Classroom.query.all()
    return render_template('teacher/classrooms.html', departments=departments, classrooms=classrooms)

@app.route('/teacher/reserve/<int:classroom_id>', methods=['GET', 'POST'])
@login_required
def reserve_classroom(classroom_id):
    if current_user.role != 'teacher' and current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    classroom = Classroom.query.get_or_404(classroom_id)
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        purpose = request.form.get('purpose')
        
        # Convert string dates to Python objects
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Check for conflicts
        conflicts = Reservation.query.filter_by(classroom_id=classroom_id, date=date).all()
        has_conflict = False
        
        for reservation in conflicts:
            if (start_time <= reservation.end_time and end_time >= reservation.start_time):
                has_conflict = True
                break
        
        if has_conflict:
            return jsonify({'success': False, 'message': 'Reservation conflicts with an existing booking'})
        else:
            new_reservation = Reservation(
                date=date,
                start_time=start_time,
                end_time=end_time,
                purpose=purpose,
                user_id=current_user.id,
                classroom_id=classroom_id
            )
            
            db.session.add(new_reservation)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Classroom reserved successfully'})
    
    return render_template('teacher/reserve.html', classroom=classroom)

@app.route('/teacher/reservations')
@login_required
def view_reservations():
    if current_user.role != 'teacher' and current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    return render_template('teacher/reservations.html', reservations=reservations)

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)

@app.route('/admin/user/<int:user_id>/make_teacher')
@login_required
def make_teacher(user_id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.role = 'teacher'
    db.session.commit()
    
    flash(f'User {user.username} is now a teacher')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/delete')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting admin users
    if user.role == 'admin':
        flash('Cannot delete admin users')
        return redirect(url_for('admin_dashboard'))
    
    # Delete associated reservations
    Reservation.query.filter_by(user_id=user.id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset_users')
@login_required
def reset_users():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Delete all reservations
    Reservation.query.delete()
    
    # Delete all non-admin users
    User.query.filter(User.role != 'admin').delete()
    
    db.session.commit()
    
    flash('All non-admin users have been deleted')
    return redirect(url_for('admin_dashboard'))

@app.route('/teacher/department/<int:department_id>/delete', methods=['POST'])
@login_required
def delete_department(department_id):
    if current_user.role != 'admin' and current_user.role != 'teacher':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    department = Department.query.get_or_404(department_id)
    
    # Delete all classrooms and their reservations in this department
    classrooms = Classroom.query.filter_by(department_id=department_id).all()
    for classroom in classrooms:
        # Delete all reservations for this classroom
        Reservation.query.filter_by(classroom_id=classroom.id).delete()
        # Delete the classroom
        db.session.delete(classroom)
    
    # Delete the department
    db.session.delete(department)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Department {department.name} deleted successfully'})

@app.route('/teacher/classroom/<int:classroom_id>/delete', methods=['POST'])
@login_required
def delete_classroom(classroom_id):
    if current_user.role != 'admin' and current_user.role != 'teacher':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Delete all reservations for this classroom
    Reservation.query.filter_by(classroom_id=classroom_id).delete()
    
    # Delete the classroom
    db.session.delete(classroom)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Room {classroom.room_number} deleted successfully'})

@app.route('/teacher/department/<int:department_id>/rooms')
@login_required
def get_department_rooms(department_id):
    if current_user.role != 'admin' and current_user.role != 'teacher':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    # First, clean up expired reservations
    cleanup_expired_reservations()
    
    department = Department.query.get_or_404(department_id)
    classrooms = Classroom.query.filter_by(department_id=department_id).all()
    
    rooms_data = []
    for classroom in classrooms:
        reservation_count = Reservation.query.filter_by(classroom_id=classroom.id).count()
        rooms_data.append({
            'id': classroom.id,
            'room_number': classroom.room_number,
            'capacity': classroom.capacity,
            'reservation_count': reservation_count
        })
    
    return jsonify({
        'success': True,
        'department_name': department.name,
        'classrooms': rooms_data
    })

def cleanup_expired_reservations():
    """Remove reservations that have already passed"""
    try:
        today = datetime.now().date()
        current_time = datetime.now().time()
        
        # Find reservations that are in the past or ended today before current time
        expired_reservations = Reservation.query.filter(
            (Reservation.date < today) | 
            ((Reservation.date == today) & (Reservation.end_time < current_time))
        ).all()
        
        # Delete expired reservations
        for reservation in expired_reservations:
            db.session.delete(reservation)
        
        db.session.commit()
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error cleaning up reservations: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        try:
            # Ensure the database directory exists
            db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Create tables
            db.create_all()
            
            # Create admin user if not exists
            admin = User.query.filter_by(username='23-11773').first()
            if not admin:
                admin = User(username='23-11773', display_name='Administrator', role='admin')
                admin.set_password('Adminako123!')
                db.session.add(admin)
                db.session.commit()
        except Exception as e:
            print(f"Error during database initialization: {str(e)}")
    
    # Run the application
    app.run(debug=True)
