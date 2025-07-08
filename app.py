from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import hashlib
import base64
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
        # Format: scrypt:<n>:<r>:<p>$<salt_b64>$<hash_hex>
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
# 📊 Dashboard
# ==================================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    searched = None
    result = None

    if request.method == 'POST':
        searched = request.form.get('searched')
        if searched:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT cattle_id, breed, color, age, shed_no, photo1
                    FROM cattle_info
                    WHERE breed ILIKE %s OR color ILIKE %s OR shed_no ILIKE %s
                    """,
                    (f"%{searched}%", f"%{searched}%", f"%{searched}%")
                )
                result = cursor.fetchall()
                cursor.close()
                conn.close()
            else:
                flash("Database connection error.", "danger")

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
        breed = request.form['breed']
        color = request.form['color']
        age = request.form['age']
        shed_no = request.form['shed_no']
        notes = request.form['notes']

        photo_fields = ['photo1', 'photo2', 'photo3', 'photo4']
        photos = []

        for field in photo_fields:
            file = request.files.get(field)
            filename = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
            photos.append(filename)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cattle_info (breed, color, age, shed_no, notes, photo1, photo2, photo3, photo4)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                breed, color, age, shed_no, notes,
                photos[0], photos[1], photos[2], photos[3]
            ))
            conn.commit()
            cursor.close()
            conn.close()

            flash("New cattle added successfully.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Database connection error.", "danger")

    return render_template('add_cattle.html')


# ==================================
# ✏️ Edit Cattle
# ==================================
@app.route('/edit_cattle/<int:cattle_id>', methods=['GET', 'POST'])
def edit_cattle(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash("Database connection error.", "danger")
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cattle_info WHERE cattle_id = %s", (cattle_id,))
    cattle = cursor.fetchone()

    if not cattle:
        flash("Cattle not found.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        breed = request.form['breed']
        color = request.form['color']
        age = request.form['age']
        shed_no = request.form['shed_no']
        notes = request.form['notes']

        photo_fields = ['photo1', 'photo2', 'photo3', 'photo4']
        photos = list(cattle[6:10])  # preserve existing photos if no new uploads

        for i, field in enumerate(photo_fields):
            file = request.files.get(field)
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photos[i] = filename

        cursor.execute("""
            UPDATE cattle_info
            SET breed = %s, color = %s, age = %s, shed_no = %s, notes = %s,
                photo1 = %s, photo2 = %s, photo3 = %s, photo4 = %s
            WHERE cattle_id = %s
        """, (
            breed, color, age, shed_no, notes,
            photos[0], photos[1], photos[2], photos[3],
            cattle_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Cattle updated successfully.", "success")
        return redirect(url_for('dashboard'))

    cursor.close()
    conn.close()

    return render_template('edit_cattle.html', cattle=cattle)


# ==================================
# 🗑 Delete Cattle
# ==================================
@app.route('/delete_cattle/<int:cattle_id>', methods=['POST'])
def delete_cattle(cattle_id):
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cattle_info WHERE cattle_id = %s", (cattle_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash(f"Cattle ID {cattle_id} deleted.", "success")
    else:
        flash("Database connection error.", "danger")

    return redirect(url_for('dashboard'))


# ==================================
# 🚀 Run
# ==================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
