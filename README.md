# ISU Classroom Reservation System

A web application that allows students and teachers to view, reserve, and manage classrooms at ISU Cauayan Campus.

## Features

- **For Students**: Browse available classrooms across different departments
- **For Teachers**: Reserve classrooms for lectures, exams, or special events
- **For Administrators**: Manage users, departments, and oversee all reservations

## Technology Stack

- Flask (Python Web Framework)
- SQLAlchemy (ORM)
- SQLite (Database)
- Bootstrap 5 (Frontend)
- JavaScript/jQuery

## Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/classroom-reservation.git
   cd classroom-reservation
   ```

2. Set up a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Run the application
   ```
   python app.py
   ```

5. Access the application at http://127.0.0.1:5000

## Default Admin Credentials

- **Username**: 23-11773
- **Password**: Adminako123!

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file based on `.env.example`
6. Run the application: `flask run`

## Deploying to Render

This application is configured for easy deployment to Render.com.

### Manual Deployment

1. Push your code to GitHub
2. In Render dashboard, create a new Web Service
3. Connect your GitHub repository
4. Use the following settings:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add the following environment variables:
   - `ENVIRONMENT`: `production`
   - `SECRET_KEY`: (generate a random string)
6. Create a PostgreSQL database in Render
7. Add the database URL as `DATABASE_URL` environment variable

### Blueprint Deployment

Alternatively, you can use the included `render.yaml` file for Blueprint deployment:

1. Push your code to GitHub
2. In Render dashboard, go to Blueprints
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` configuration
5. Click "Apply" to create the web service and database

## First-time Setup

After deploying, the application will create an admin user with:
- Username: 23-11773
- Password: Adminako123!

Please change the admin password after first login. 