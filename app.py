from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import hashlib
import base64

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
# 📊 Dashboard (Search working!)
# ==================================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'doctor_username' not in session:
        return redirect(url_for('login'))

    searched = False
    result = []

    if request.method == 'POST':
        breed = request.form.get('breed', '').strip()
        color = request.form.get('color', '').strip()
        age = request.form.get('age', '').strip()
        shed_no = request.form.get('shed_no', '').strip()

        searched = True

        query = "SELECT * FROM cattle WHERE 1=1"
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
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchall()
                cursor.close()
                conn.close()
            except Exception as e:
                print("❌ Error fetching cattle data:", e)
                flash("Error retrieving cattle data.", "danger")
        else:
            flash("Database connection failed.", "danger")

    return render_template(
        'index.html',
        username=session.get('doctor_username'),
        searched=searched,
        result=result
    )

# ==================================
# 🚀 Run
# ==================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
