from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import hashlib
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = os.environ.get("SECRET_KEY", "temporary-secret-key")  # Better for security

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================================
# 🔐 SCRYPT HASH CHECKING FUNCTION
# ==================================
def check_password_scrypt(stored_hash, password):
    try:
        # Format: scrypt$<salt_b64>$<hash_b64>
        _, salt_b64, hash_b64 = stored_hash.split('$')
        salt = base64.b64decode(salt_b64)
        expected_hash = base64.b64decode(hash_b64)

        new_hash = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=64
        )
        return new_hash == expected_hash
    except Exception:
        return False

# ==================================
# 🔌 Database Connection Helper
# ==================================
def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

# ==================================
# 🔑 Login Route
# ==================================
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

        if doctor and check_password_scrypt(doctor[1], password):
            session['doctor_id'] = doctor[0]
            session['doctor_username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

# ==================================
# 🚪 Logout
# ==================================
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ==================================
# 🏠 Home Redirect
# ==================================
@app.route('/')
def home():
    return redirect(url_for('login'))

# ==================================
# 📊 Dashboard
# ==================================
@app.route('/dashboard')
def dashboard():
    if 'doctor_id' not in session:
        return redirect(url_for('login'))
    return f"Welcome Dr. {session.get('doctor_username')}!"

# ==================================
# 🚀 Run
# ==================================
if __name__ == '__main__':
    app.run(debug=True)
