# ... existing imports ...
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import hashlib
import base64
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = os.environ.get("SECRET_KEY", "temporary-secret-key")

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def check_password_scrypt(stored_hash, password):
    try:
        prefix, salt_b64, hash_hex = stored_hash.split('$')
        _, n, r, p = prefix.split(':')
        salt = base64.b64decode(salt_b64)
        expected_hash = bytes.fromhex(hash_hex)
        new_hash = hashlib.scrypt(password.encode('utf-8'), salt=salt,
                                  n=int(n), r=int(r), p=int(p), dklen=64)
        return new_hash == expected_hash
    except Exception as e:
        print("Error in check_password_scrypt:", e)
        return False

def get_db_connection():
    try:
        db_url = os.environ['DATABASE_URL']
        return psycopg2.connect(db_url)
    except Exception as e:
        print("❌ Database connection failed:", e)
        return None

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if conn is None:
            flash("Database error.", "danger")
            return render_template('login.html')
        try:
            cur = conn.cursor()
            cur.execute("SELECT username, password FROM doctors WHERE username = %s", (username,))
            doctor = cur.fetchone()
            cur.close()
            conn.close()
            if doctor and check_password_scrypt(doctor[1], password):
                session['doctor_username'] = doctor[0]
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials.", "danger")
        except Exception as e:
            print("Login error:", e)
            flash("Internal error.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

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
        gender = request.form.get('gender')

        query = """
            SELECT id, breed, color, age, shed_no, gender, 
                   photo1_data, photo2_data, photo3_data, photo4_data 
            FROM cattle_info WHERE 1=1
        """
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
        if gender:
            query += " AND gender = %s"
            params.append(gender)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        result = cur.fetchall()
        cur.close()
        conn.close()
        searched = True

    return render_template("index.html", searched=searched, result=result)

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
        gender = request.form.get('gender')

        photo_blobs = []
        for field in ['photo1', 'photo2', 'photo3', 'photo4']:
            file = request.files.get(field)
            photo_blobs.append(file.read() if file and file.filename != '' else None)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cattle_info (
                    breed, color, age, shed_no, notes, gender,
                    photo1_data, photo2_data, photo3_data, photo4_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (breed, color, age, shed_no, notes, gender,
                  photo_blobs[0], photo_blobs[1], photo_blobs[2], photo_blobs[3]))
            conn.commit()
            cur.close()
            conn.close()
            flash("Cattle added successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            print("Error inserting cattle:", e)
            flash("Error adding cattle.", "danger")

    return render_template('add_cattle.html')

@app.route('/add_log/<int:cattle_id>', methods=['GET', 'POST'])
def add_log(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        date = request.form['checkup_date']
        diagnosis = request.form['diagnosis']
        medicines = request.form['medicines']
        remarks = request.form.get('remarks', '')
        doctor = session['doctor_username']
        photo_file = request.files.get('treatment_photo')
        photo_data = photo_file.read() if photo_file and photo_file.filename != '' else None

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO health_log (
                checkup_date, diagnosis, medicines, remarks,
                treatment_photo_data, cattle_id, doctor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (date, diagnosis, medicines, remarks, photo_data, cattle_id, doctor))
        conn.commit()
        cur.close()
        conn.close()

        flash('Checkup log added successfully.', 'success')
        return redirect(url_for('view_logs', cattle_id=cattle_id))

    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('add_log.html', cattle_id=cattle_id, today=today)

@app.route('/view_logs/<int:cattle_id>')
def view_logs(cattle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT checkup_date, diagnosis, medicines, remarks, treatment_photo_data, doctor
        FROM health_log
        WHERE cattle_id = %s
        ORDER BY checkup_date DESC
    """, (cattle_id,))
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('view_logs.html', logs=logs, cattle_id=cattle_id)

@app.route('/delete_cattle/<int:cattle_id>')
def delete_cattle(cattle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM cattle_info WHERE id = %s', (cattle_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8') if data else ''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
