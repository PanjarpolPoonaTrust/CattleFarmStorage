from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import hashlib
import base64
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = os.environ.get("SECRET_KEY", "temporary-secret-key")

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================================
# 🔐 SCRYPT HASH CHECKING FUNCTION
# ==================================
def check_password_scrypt(stored_hash, password):
    try:
        prefix, salt_b64, hash_hex = stored_hash.split('$')
        _, n, r, p = prefix.split(':')
        salt = base64.b64decode(salt_b64)
        expected_hash = bytes.fromhex(hash_hex)

        new_hash = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=64
        )
        return new_hash == expected_hash
    except Exception as e:
        print("Error in check_password_scrypt:", e)
        return False

# ==================================
# 🔌 Database Connection Helper
# ==================================
def get_db_connection():
    try:
        db_url = os.environ['DATABASE_URL']
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print("❌ Database connection failed:", e)
        return None

# ==================================
# 🔑 Login Route
# ==================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error. Please try again later.", "danger")
            return render_template('login.html')

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, password FROM doctors WHERE username = %s",
                (username,)
            )
            doctor = cursor.fetchone()
            cursor.close()
            conn.close()

            if doctor and check_password_scrypt(doctor[1], password):
                session['doctor_username'] = doctor[0]
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')

        except Exception as e:
            print("❌ Error during login query:", e)
            flash("Internal server error.", "danger")
            return render_template('login.html')

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
# 📊 Dashboard (Search + Results)
# ==================================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    searched = False
    result = []

    if request.method == 'POST':
        breed = request.form.get('breed')
        color = request.form.get('color')
        age = request.form.get('age')
        shed_no = request.form.get('shed_no')

        query = "SELECT * FROM cattle_info WHERE 1=1"
        params = []

        if breed:
            query += " AND breed ILIKE %s"
            params.append(f"%{breed}%")
        if color:
            query += " AND color ILIKE %s"
            params.append(f"%{color}%")
        if age:
            query += " AND age = %s"
            params.append(age)
        if shed_no:
            query += " AND shed_no ILIKE %s"
            params.append(f"%{shed_no}%")

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error.", "danger")
            return render_template('index.html', searched=False, result=[])

        cur = conn.cursor()
        cur.execute(query, params)
        result = cur.fetchall()
        cur.close()
        conn.close()

        searched = True

    return render_template(
        'index.html',
        searched=searched,
        result=result
    )

# ==================================
# ➕ Add Cattle
# ==================================
@app.route('/add_cattle', methods=['GET', 'POST'])
def add_cattle():
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        breed = request.form.get('breed')
        color = request.form.get('color')
        age = request.form.get('age')
        shed_no = request.form.get('shed_no')
        notes = request.form.get('notes')

        photo_filenames = []
        for field in ['photo1', 'photo2', 'photo3', 'photo4']:
            photo = request.files.get(field)
            if photo and photo.filename != '':
                filename = secure_filename(photo.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                photo_filenames.append(unique_filename)
            else:
                photo_filenames.append(None)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cattle_info
                (breed, color, age, shed_no, notes, photo1, photo2, photo3, photo4)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                breed, color, age, shed_no, notes,
                photo_filenames[0], photo_filenames[1],
                photo_filenames[2], photo_filenames[3]
            ))
            conn.commit()
            cur.close()
            conn.close()
            flash("Cattle record added successfully!", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            print("❌ Error inserting cattle:", e)
            flash("Error adding cattle. Please try again.", "danger")

    return render_template('add_cattle.html')

# ==================================
# ➕ Add Health Log
# ==================================
@app.route('/add_log/<int:cattle_id>', methods=['GET', 'POST'])
def add_log(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        checkup_date = request.form.get('checkup_date')
        diagnosis = request.form.get('diagnosis')
        medicines = request.form.get('medicines')
        remarks = request.form.get('remarks')

        treatment_photo = request.files.get('treatment_photo')
        photo_filename = None

        if treatment_photo and treatment_photo.filename != '':
            filename = secure_filename(treatment_photo.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            treatment_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            photo_filename = unique_filename

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO health_log
                (cattle_id, checkup_date, diagnosis, medicines, remarks, photo, doctor_username)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                cattle_id, checkup_date, diagnosis, medicines, remarks,
                photo_filename, session['doctor_username']
            ))
            conn.commit()
            cur.close()
            conn.close()
            flash("Health log added successfully!", "success")
            return redirect(url_for('view_logs', cattle_id=cattle_id))

        except Exception as e:
            print("❌ Error inserting log:", e)
            flash("Error adding health log. Please try again.", "danger")

    return render_template('add_log.html', cattle_id=cattle_id)

# ==================================
# 📄 View Logs
# ==================================
@app.route('/view_logs/<int:cattle_id>')
def view_logs(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT checkup_date, diagnosis, medicines, remarks, photo, doctor_username
        FROM health_log
        WHERE cattle_id = %s
        ORDER BY checkup_date DESC
    """, (cattle_id,))
    logs = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('view_logs.html', cattle_id=cattle_id, logs=logs)

# ==================================
# 🚀 Run
# ==================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
