from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
import base64
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary-secret-key")
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD")
    )

def convert_image_to_binary(file):
    if file and file.filename:
        return file.read()
    return None

@app.template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''

@app.route("/", methods=["GET", "POST"])
def dashboard():
    searched = False
    result = []

    if request.method == "POST":
        searched = True
        breed = request.form.get("breed", "").strip()
        color = request.form.get("color", "").strip()
        age = request.form.get("age", "").strip()
        shed_no = request.form.get("shed_no", "").strip()
        gender = request.form.get("gender", "").strip()
        tag_no = request.form.get("tag_no", "").strip()

        query = "SELECT * FROM cattle_info WHERE 1=1"
        values = []

        if breed:
            query += " AND breed ILIKE %s"
            values.append(f"%{breed}%")
        if color:
            query += " AND color ILIKE %s"
            values.append(f"%{color}%")
        if age:
            query += " AND age = %s"
            values.append(age)
        if shed_no:
            query += " AND shed_no ILIKE %s"
            values.append(f"%{shed_no}%")
        if gender:
            query += " AND gender = %s"
            values.append(gender)
        if tag_no:
            query += " AND tag_no ILIKE %s"
            values.append(f"%{tag_no}%")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, values)
        result = cur.fetchall()
        cur.close()
        conn.close()

    return render_template("index.html", result=result, searched=searched)

@app.route("/add_cattle", methods=["GET", "POST"])
def add_cattle():
    if request.method == "POST":
        breed = request.form["breed"]
        color = request.form["color"]
        age = request.form["age"]
        shed_no = request.form["shed_no"]
        gender = request.form["gender"]
        notes = request.form["notes"]
        tag_no = request.form["tag_no"]

        photos = [convert_image_to_binary(request.files.get(f"photo{i}")) for i in range(1, 5)]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cattle_info (breed, color, age, shed_no, notes, photo1, photo2, photo3, photo4, gender, tag_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (breed, color, age, shed_no, notes, *photos, gender, tag_no))
        conn.commit()
        cur.close()
        conn.close()
        flash("Cattle added successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_cattle.html")

@app.route("/delete_cattle/<int:cattle_id>")
def delete_cattle(cattle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cattle_info WHERE id = %s", (cattle_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Cattle deleted successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/add_log/<int:cattle_id>", methods=["GET", "POST"])
def add_log(cattle_id):
    if "doctor" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        checkup_date = request.form["checkup_date"]
        diagnosis = request.form["diagnosis"]
        medicines = request.form["medicines"]
        remarks = request.form["remarks"]
        doctor = session["doctor"]

        treatment_photo = convert_image_to_binary(request.files.get("treatment_photo"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO health_log (checkup_date, diagnosis, medicines, remarks, treatment_photo, cattle_id, doctor)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (checkup_date, diagnosis, medicines, remarks, treatment_photo, cattle_id, doctor))
        conn.commit()
        cur.close()
        conn.close()
        flash("Health log added successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_log.html", cattle_id=cattle_id)

@app.route("/view_logs/<int:cattle_id>")
def view_logs(cattle_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM health_log WHERE cattle_id = %s ORDER BY checkup_date DESC", (cattle_id,))
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("view_logs.html", logs=logs)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM doctors WHERE username = %s AND password = %s", (username, password))
        doctor = cur.fetchone()
        cur.close()
        conn.close()

        if doctor:
            session["doctor"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("doctor", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

# ✅ Render-compatible entrypoint
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
