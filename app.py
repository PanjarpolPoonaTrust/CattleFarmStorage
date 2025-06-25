
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'your-secret-key-here'  # Required for flash messages and sessions

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Connect to Supabase via connection pooling
db = psycopg2.connect(os.environ['DATABASE_URL'])
cursor = db.cursor()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'doctor_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM doctors WHERE username=%s", (username,))
            doctor = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            print("Database error:", e)
            flash("Database error.", "danger")
            return render_template('login.html')

        if doctor and check_password_hash(doctor[1], password):
            session['doctor_id'] = doctor[0]
            session['doctor_username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Add your additional routes here

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect root to login page


if __name__ == '__main__':
    app.run(debug=True)
