import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2 import sql
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

DATABASE_URL = os.getenv("DATABASE_URL", "your_database_url")

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# ---------- Login ----------
@app.route("/", methods=["GET"])
def root():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "password":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")

# ---------- Dashboard ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        search_term = request.form["search_term"]

        query = sql.SQL("""
            SELECT id, breed, color, age, shed_no, photo1
            FROM cattle_info
            WHERE id::text ILIKE %s
               OR breed ILIKE %s
               OR color ILIKE %s
               OR shed_no ILIKE %s
        """)
        like_term = f"%{search_term}%"
        cursor.execute(query, (like_term, like_term, like_term, like_term))
        result = cursor.fetchall()
        conn.close()
        return render_template("index.html", searched=True, result=result)

    # Default page load
    cursor.execute("""
        SELECT id, breed, color, age, shed_no, photo1
        FROM cattle_info
    """)
    result = cursor.fetchall()
    conn.close()
    return render_template("index.html", searched=False, result=result)

# ---------- Add Cattle ----------
@app.route("/add_cattle", methods=["GET", "POST"])
def add_cattle():
    if request.method == "POST":
        breed = request.form["breed"]
        color = request.form["color"]
        age = request.form["age"]
        shed_no = request.form["shed_no"]

        photo1 = request.files["photo1"]
        photo_filename = None
        if photo1 and photo1.filename != "":
            filename = secure_filename(photo1.filename)
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo1.save(photo_path)
            photo_filename = filename

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cattle_info (breed, color, age, shed_no, photo1)
            VALUES (%s, %s, %s, %s, %s)
        """, (breed, color, age, shed_no, photo_filename))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    return render_template("add_cattle.html")

# ---------- Delete Cattle ----------
@app.route("/delete_cattle/<int:id>", methods=["POST"])
def delete_cattle(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cattle_info WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

# ---------- Logout ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
