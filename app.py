from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from datetime import datetime
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'this-is-a-hardcoded-secret-key'  # You can replace this with your own string

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# DB connection helper
def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

# ==========================
# LOGIN ROUTE
# ==========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM doctors WHERE username = %s", (username,))
        doctor = cursor.fetchone()
        cursor.close()
        conn.close()

        if doctor and check_password_hash(doctor[1], password):
            session['doctor_id'] = doctor[0]
            session['doctor_username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

# ==========================
# LOGOUT ROUTE
# ==========================
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ==========================
# HOME
# ==========================
@app.route('/')
def home():
    return redirect(url_for('login'))

# ==========================
# DASHBOARD
# ==========================
@app.route('/dashboard')
def dashboard():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return f"Welcome Dr. {session.get('doctor_username')}!"

if __name__ == '__main__':
    app.run(debug=True)
