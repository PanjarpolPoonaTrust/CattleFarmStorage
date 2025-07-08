import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "your_db_name")
DB_USER = os.getenv("DB_USER", "your_db_user")
DB_PASS = os.getenv("DB_PASS", "your_db_password")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM doctors WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    searched = None
    result = []

    if request.method == "POST":
        searched = request.form["searched"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, breed, color, age, shed_no, photo1
            FROM cattle_info
            WHERE breed ILIKE %s OR color ILIKE %s
            """,
            (f"%{searched}%", f"%{searched}%")
        )
        result = cur.fetchall()
        cur.close()
        conn.close()

    return render_template("index.html", searched=searched, result=result)

@app.route("/add_cattle", methods=["GET", "POST"])
def add_cattle():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        breed = request.form["breed"]
        color = request.form["color"]
        age = request.form["age"]
        shed_no = request.form["shed_no"]
        photo1 = request.form["photo1"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO cattle_info (breed, color, age, shed_no, photo1)
            VALUES (%s, %s, %s, %s, %s)
        """, (breed, color, age, shed_no, photo1))

        conn.commit()
        cur.close()
        conn.close()

        flash("Cattle added successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_cattle.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
