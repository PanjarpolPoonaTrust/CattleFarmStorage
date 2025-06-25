from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'your-secret-key-here'  # Required for flash messages and sessions

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Update these with your credentials
db = psycopg2.connect(
    host=os.environ.get("DB_HOST"),
    database=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASS"),
    port=5432
)

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
        cursor.execute("SELECT id, password FROM doctors WHERE username=%s", (username,))
        doctor = cursor.fetchone()
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
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    result = None
    searched = False

    if request.method == "POST":
        searched = True
        try:
            breed = request.form.get("breed", "")
            color = request.form.get("color", "")
            age = request.form.get("age", "")
            shed_no = request.form.get("shed_no", "")

            query = "SELECT id, breed, color, age, shed_no, notes, photo1, photo2, photo3, photo4 FROM cattle_info WHERE 1=1"
            params = []
            if breed:
                query += " AND breed LIKE %s"
                params.append(f"%{breed}%")
            if color:
                query += " AND color LIKE %s"
                params.append(f"%{color}%")
            if age:
                query += " AND age = %s"
                params.append(age)
            if shed_no:
                query += " AND shed_no LIKE %s"
                params.append(f"%{shed_no}%")

            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            print('DEBUG: Each row photo filenames:')
            for row in result:
                print(row[6:10])
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("index"))

    print("Searched:", searched, "Result:", result)
    return render_template("index.html", result=result, searched=searched)

@app.route("/add_cattle", methods=["GET", "POST"])
@login_required
def add_cattle():
    if request.method == "POST":
        try:
            breed = request.form["breed"]
            color = request.form["color"]
            age = request.form["age"]
            shed_no = request.form["shed_no"]
            notes = request.form["notes"]
            photos = []
            for i in range(1, 5):
                photo = request.files.get(f"photo{i}")
                filename = None
                if photo and photo.filename:
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
                    photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                photos.append(filename)
            cursor.execute(
                "INSERT INTO cattle_info (breed, color, age, shed_no, notes, photo1, photo2, photo3, photo4) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (breed, color, age, shed_no, notes, photos[0], photos[1], photos[2], photos[3])
            )
            db.commit()
            cattle_id = cursor.lastrowid
            flash("Cattle added successfully! Now add a checkup log.", "success")
            return redirect(url_for("add_log", cattle_id=cattle_id))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("add_cattle"))
    return render_template("add_cattle.html")

@app.route("/add_log/<int:cattle_id>", methods=["GET", "POST"])
@login_required
def add_log(cattle_id):
    if request.method == "POST":
        try:
            checkup_date = request.form["checkup_date"]
            diagnosis = request.form["diagnosis"]
            medicines = request.form["medicines"]
            remarks = request.form["remarks"]
            treatment_photo = request.files["treatment_photo"]
            photo_name = None
            if treatment_photo and treatment_photo.filename:
                photo_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{treatment_photo.filename}"
                treatment_photo.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_name))
            doctor_username = session.get("doctor_username")
            cursor.execute(
                "INSERT INTO health_log (cattle_id, checkup_date, diagnosis, medicines, remarks, treatment_photo, doctor_username) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (cattle_id, checkup_date, diagnosis, medicines, remarks, photo_name, doctor_username)
            )
            db.commit()
            flash("Health log added successfully!", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("add_log", cattle_id=cattle_id))
    today_str = datetime.today().strftime("%Y-%m-%d")
    return render_template("add_log.html", cattle_id=cattle_id, today=today_str)

@app.route("/view_logs/<int:cattle_id>")
@login_required
def view_logs(cattle_id):
    try:
        cursor.execute(
            "SELECT checkup_date, diagnosis, medicines, remarks, treatment_photo, doctor_username FROM health_log WHERE cattle_id=%s ORDER BY checkup_date DESC",
            (cattle_id,)
        )
        logs = cursor.fetchall()
        return render_template("view_logs.html", logs=logs, cattle_id=cattle_id)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for("index"))

@app.route("/delete_cattle/<int:cattle_id>", methods=["POST"])
@login_required
def delete_cattle(cattle_id):
    try:
        # Fetch photo filenames to delete them from disk
        cursor.execute("SELECT photo1, photo2, photo3, photo4 FROM cattle_info WHERE id=%s", (cattle_id,))
        photos = cursor.fetchone()
        if photos:
            for photo in photos:
                if photo:
                    photo_path = os.path.join(app.config["UPLOAD_FOLDER"], photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
        # Delete the cattle record
        cursor.execute("DELETE FROM cattle_info WHERE id=%s", (cattle_id,))
        db.commit()
        flash("Cattle record deleted successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while deleting: {str(e)}", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
