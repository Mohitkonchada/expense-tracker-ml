from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "secret-key-change-later"

# ---------- LOGIN MANAGER ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------- DATABASE ----------
DB_NAME = "expense.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # EXPENSES TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- USER CLASS ----------
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    )

    row = cur.fetchone()
    conn.close()

    if row:
        return User(row[0], row[1])

    return None

# ---------- HOME PAGE ----------
@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    conn = get_db()
    cur = conn.cursor()

    # ADD EXPENSE
    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]

        # AUTOMATIC DATE
        current_date = datetime.now().strftime("%Y-%m-%d")

        cur.execute(
            """
            INSERT INTO expenses
            (user_id, amount, category, date)
            VALUES (?, ?, ?, ?)
            """,
            (current_user.id, amount, category, current_date)
        )

        conn.commit()

    # FETCH USER EXPENSES
    cur.execute(
        """
        SELECT amount, category, date
        FROM expenses
        WHERE user_id = ?
        """,
        (current_user.id,)
    )

    expenses = cur.fetchall()

    conn.close()

    return render_template(
        "index.html",
        expenses=expenses
    )

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, password FROM users WHERE username = ?",
            (username,)
        )

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[1], password):

            login_user(User(user[0], username))

            return redirect(url_for("index"))

    return render_template("login.html")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]

        password = generate_password_hash(
            request.form["password"]
        )

        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO users
                (username, password)
                VALUES (?, ?)
                """,
                (username, password)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except:
            return "Username already exists"

    return render_template("signup.html")

# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)