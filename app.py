
import os
import sqlite3
import joblib
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask configuration
app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

DB_PATH = "grievance.db"
MODEL_PATH = "models/grievance_model.pkl"
VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"

# Department mapping
DEPARTMENTS = {
    "Road": "Public Works Department",
    "Water": "Water Supply Department",
    "Garbage": "Waste Management Department",
    "Drainage": "Drainage Department",
    "Electricity": "Electricity Department",
    "Sanitation": "Sanitation Department",
}


# Database connection
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database and admin account
def init_db():
    with get_db() as conn:

        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'citizen'
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            department TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Submitted',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")

        # Get admin credentials from .env
        admin_email = os.environ["ADMIN_EMAIL"]
        admin_password = os.environ["ADMIN_PASSWORD"]

        admin = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (admin_email,)
        ).fetchone()

        # Create admin only if account does not exist
        if not admin:
            conn.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (
                    "Administrator",
                    admin_email,
                    generate_password_hash(admin_password),
                    "admin"
                )
            )


# Load trained ML model
def load_model():
    global model, vectorizer

    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
    else:
        from train_model import model as trained_model
        from train_model import vectorizer as trained_vectorizer

        model = trained_model
        vectorizer = trained_vectorizer


# Classify complaint using Machine Learning
def classify(text):
    features = vectorizer.transform([text])
    category = model.predict(features)[0]
    return category


# Calculate complaint priority
def calculate_priority(text):
    text = text.lower()

    urgent_words = [
        "emergency", "danger", "accident", "fire", "injury",
        "overflowing", "sewage", "contaminated", "electrical wire"
    ]

    high_words = [
        "no water", "not working", "blocked", "leak",
        "pothole", "broken", "unsafe", "days"
    ]

    if any(word in text for word in urgent_words):
        return "High"

    if any(word in text for word in high_words):
        return "Medium"

    return "Low"


# Login authentication decorator
def login_required(role=None):

    def decorator(func):

        @wraps(func)
        def wrapped(*args, **kwargs):

            if "user_id" not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))

            if role and session.get("role") != role:
                flash(
                    "You do not have permission to access that page.",
                    "danger"
                )
                return redirect(url_for("index"))

            return func(*args, **kwargs)

        return wrapped

    return decorator


# Home page
@app.route("/")
def index():
    return render_template("index.html")


# Citizen registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash(
                "Enter all details. Password must contain at least 6 characters.",
                "danger"
            )
            return render_template("register.html")

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                    (
                        name,
                        email,
                        generate_password_hash(password),
                        "citizen"
                    )
                )

            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("This email is already registered.", "danger")

    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):

            session.clear()

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "info")

    return redirect(url_for("index"))


# Submit complaint
@app.route("/submit", methods=["GET", "POST"])
@login_required("citizen")
def submit():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if len(title) < 4 or len(description) < 10:
            flash(
                "Enter a title and a description of at least 10 characters.",
                "danger"
            )
            return render_template("submit.html")

        # AI category prediction
        category = classify(description)

        # Department assignment
        department = DEPARTMENTS.get(
            category,
            "Municipal Administration"
        )

        # Priority calculation
        priority = calculate_priority(description)

        with get_db() as conn:

            conn.execute(
                """INSERT INTO complaints
                (user_id,title,description,category,department,
                priority,status,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",

                (
                    session["user_id"],
                    title,
                    description,
                    category,
                    department,
                    priority,
                    "Submitted",
                    datetime.now().strftime("%d %b %Y, %I:%M %p")
                )
            )

            complaint_id = conn.execute(
                "SELECT last_insert_rowid()"
            ).fetchone()[0]

        flash(
            f"Complaint #{complaint_id} submitted. Predicted category: {category}.",
            "success"
        )

        return redirect(url_for("dashboard"))

    return render_template("submit.html")


# Citizen dashboard
@app.route("/dashboard")
@login_required("citizen")
def dashboard():

    with get_db() as conn:

        complaints = conn.execute(
            "SELECT * FROM complaints WHERE user_id = ? ORDER BY id DESC",
            (session["user_id"],)
        ).fetchall()

    return render_template(
        "dashboard.html",
        complaints=complaints
    )


# Admin dashboard
@app.route("/admin")
@login_required("admin")
def admin():

    with get_db() as conn:

        complaints = conn.execute(
            """SELECT complaints.*, users.name AS citizen_name,
            users.email AS citizen_email
            FROM complaints
            JOIN users ON users.id = complaints.user_id
            ORDER BY complaints.id DESC"""
        ).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM complaints"
        ).fetchone()[0]

        pending = conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE status != 'Resolved'"
        ).fetchone()[0]

        resolved = conn.execute(
            "SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'"
        ).fetchone()[0]

    return render_template(
        "admin.html",
        complaints=complaints,
        total=total,
        pending=pending,
        resolved=resolved
    )


# Update complaint status
@app.route("/update/<int:complaint_id>", methods=["POST"])
@login_required("admin")
def update_status(complaint_id):

    status = request.form.get("status")

    allowed = [
        "Submitted",
        "Assigned",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin"))

    with get_db() as conn:

        conn.execute(
            "UPDATE complaints SET status = ? WHERE id = ?",
            (status, complaint_id)
        )

    flash(
        f"Complaint #{complaint_id} status updated.",
        "success"
    )

    return redirect(url_for("admin"))


# Main application
if __name__ == "__main__":

    # Initialize database
    init_db()

    # Train model if model files are missing
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):

        os.makedirs("models", exist_ok=True)

        import subprocess
        import sys

        subprocess.run(
            [sys.executable, "train_model.py"],
            check=True
        )

    # Load trained model and vectorizer
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    # Start Flask application
    app.run(debug=False)
