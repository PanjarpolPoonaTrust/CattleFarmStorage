from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import hashlib
import base64
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = os.environ.get("SECRET_KEY", "temporary-secret-key")

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==============================
# 🔐 SCRYPT PASSWORD CHECK
# ==============================
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

# ==============================
# 🔌 DATABASE CONNECTION
# ==============================
def get_db_connection():
    try:
        db_url = os.environ['DATABASE_URL']
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print("❌ Database connection failed:", e)
        return None

# ==============================
# 🔑 LOGIN
# ==============================
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
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            print("❌ Error during login:", e)
            flash("Internal server error.", 'danger')

    return render_template('login.html')

# ==============================
# 🚪 LOGOUT
# ==============================
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ==============================
# 🏠 HOME REDIRECT
# ==============================
@app.route('/')
def home():
    return redirect(url_for('login'))

# ==============================
# 📊 DASHBOARD (SEARCH)
# ==============================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

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

    result = []
    searched = False

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            searched = any([breed, color, age, shed_no])
        except Exception as e:
            print("❌ Error fetching cattle:", e)
            flash("Error fetching cattle data.", "danger")

    return render_template(
        'index.html',
        result=result,
        searched=searched,
        username=session.get('doctor_username')
    )

# ==============================
# ➕ ADD CATTLE
# ==============================
@app.route('/add_cattle', methods=['GET', 'POST'])
def add_cattle():
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        breed = request.form['breed']
        color = request.form['color']
        age = request.form['age']
        shed_no = request.form['shed_no']
        notes = request.form.get('notes', '')

        photos = []
        for i in range(1, 5):
            photo_file = request.files.get(f'photo{i}')
            if photo_file and photo_file.filename != '':
                photo_filename = photo_file.filename
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                photo_file.save(save_path)
                photos.append(photo_filename)
            else:
                photos.append(None)

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error.", "danger")
            return redirect(url_for('dashboard'))

        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cattle_info (breed, color, age, shed_no, notes, photo1, photo2, photo3, photo4)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (breed, color, age, shed_no, notes, *photos))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Cattle added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            print("❌ Error adding cattle:", e)
            flash("An error occurred.", "danger")

    return render_template('add_cattle.html')

# ==============================
# ➕ ADD HEALTH LOG
# ==============================
@app.route('/add_log/<int:cattle_id>', methods=['GET', 'POST'])
def add_log(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    today = datetime.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        checkup_date = request.form['checkup_date']
        diagnosis = request.form['diagnosis']
        medicines = request.form['medicines']
        remarks = request.form.get('remarks', '')

        treatment_photo_filename = None
        treatment_photo = request.files.get('treatment_photo')
        if treatment_photo and treatment_photo.filename != '':
            treatment_photo_filename = treatment_photo.filename
            treatment_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], treatment_photo_filename))

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error.", "danger")
            return redirect(url_for('dashboard'))

        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO health_log (cattle_id, checkup_date, diagnosis, medicines, remarks, photo, doctor)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                cattle_id,
                checkup_date,
                diagnosis,
                medicines,
                remarks,
                treatment_photo_filename,
                session['doctor_username']
            ))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Checkup log added successfully.", "success")
            return redirect(url_for('view_logs', cattle_id=cattle_id))
        except Exception as e:
            print("❌ Error adding checkup log:", e)
            flash("An error occurred.", "danger")

    return render_template('add_log.html', cattle_id=cattle_id, today=today)

# ==============================
# 🔎 VIEW HEALTH LOGS
# ==============================
@app.route('/view_logs/<int:cattle_id>')
def view_logs(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash("Database connection error.", "danger")
        return redirect(url_for('dashboard'))

    logs = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT checkup_date, diagnosis, medicines, remarks, photo, doctor
            FROM health_log
            WHERE cattle_id = %s
            ORDER BY checkup_date DESC
        """, (cattle_id,))
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ Error retrieving logs:", e)
        flash("Error fetching logs.", "danger")

    return render_template('view_logs.html', logs=logs, cattle_id=cattle_id)

# ==============================
# ❌ DELETE CATTLE
# ==============================
@app.route('/delete_cattle/<int:cattle_id>', methods=['POST'])
def delete_cattle(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash("Database connection error.", "danger")
        return redirect(url_for('dashboard'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM health_log WHERE cattle_id = %s", (cattle_id,))
        cursor.execute("DELETE FROM cattle_info WHERE id = %s", (cattle_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Cattle deleted successfully.", "success")
    except Exception as e:
        print("❌ Error deleting cattle:", e)
        flash("Error deleting cattle.", "danger")

    return redirect(url_for('dashboard'))

# ==============================
# 🚀 RUN
# ==============================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
