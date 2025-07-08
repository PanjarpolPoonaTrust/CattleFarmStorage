from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "yourdbname"),
        user=os.environ.get("DB_USER", "yourdbuser"),
        password=os.environ.get("DB_PASSWORD", "yourdbpassword"),
        port=os.environ.get("DB_PORT", 5432)
    )
    return conn

# ---------------------
# Login Route
# ---------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(
            "SELECT * FROM doctors WHERE username = %s AND password = %s",
            (username, password)
        )
        doctor = cursor.fetchone()
        conn.close()

        if doctor:
            session["logged_in"] = True
            session["doctor_id"] = doctor["id"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials.", "danger")

    return render_template("login.html")

# ---------------------
# Dashboard Route
# ---------------------

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        searched = request.form.get("searched", "")
        query = """
            SELECT id, breed, color, age, shed_no, photo1
            FROM cattle_info
            WHERE breed ILIKE %s OR color ILIKE %s
        """
        cursor.execute(query, (f"%{searched}%", f"%{searched}%"))
        result = cursor.fetchall()
        conn.close()
        return render_template(
            "index.html",
            searched=searched,
            result=result
        )

    # GET request: show all cattle
    cursor.execute("""
        SELECT id, breed, color, age, shed_no, photo1
        FROM cattle_info
    """)
    result = cursor.fetchall()
    conn.close()
    return render_template(
        "index.html",
        searched="",
        result=result
    )

# ---------------------
# Add Cattle Route
# ---------------------

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
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cattle_info (breed, color, age, shed_no, photo1)
            VALUES (%s, %s, %s, %s, %s)
        """, (breed, color, age, shed_no, photo1))
        conn.commit()
        conn.close()
        flash("Cattle added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_cattle.html")

# ---------------------
# Logout Route
# ---------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
