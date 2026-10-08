from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "expensewise-secret-key"
DB_NAME = "expensewise.dbgit init"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('expense','income')),
            UNIQUE(user_id, name, type),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            type TEXT NOT NULL CHECK(type IN ('expense','income')),
            amount REAL NOT NULL,
            description TEXT,
            transaction_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            month TEXT NOT NULL,
            UNIQUE(user_id, category_id, month),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def seed_categories(user_id):
    conn = get_db()
    expense_categories = ["Food", "Travel", "Shopping", "Bills", "Education", "Health", "Entertainment", "Other"]
    income_categories = ["Salary", "Freelance", "Business", "Gift", "Other"]

    for name in expense_categories:
        conn.execute(
            "INSERT OR IGNORE INTO categories(user_id, name, type) VALUES (?, ?, 'expense')",
            (user_id, name)
        )

    for name in income_categories:
        conn.execute(
            "INSERT OR IGNORE INTO categories(user_id, name, type) VALUES (?, ?, 'income')",
            (user_id, name)
        )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    conn = get_db()

    income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) total FROM transactions WHERE user_id=? AND type='income'",
        (user_id,)
    ).fetchone()["total"]

    expenses = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) total FROM transactions WHERE user_id=? AND type='expense'",
        (user_id,)
    ).fetchone()["total"]

    budgets = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) total FROM budgets WHERE user_id=?",
        (user_id,)
    ).fetchone()["total"]

    recent = conn.execute("""
        SELECT t.*, c.name AS category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.user_id=?
        ORDER BY t.transaction_date DESC, t.id DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "index.html",
        income=income,
        expenses=expenses,
        balance=income - expenses,
        budgets=budgets,
        recent=recent
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return render_template("register.html")

        conn = get_db()

        try:
            cursor = conn.execute(
                "INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)",
                (name, email, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            user_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already registered.", "danger")
            return render_template("register.html")

        conn.close()
        seed_categories(user_id)

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses_page():
    user_id = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        category_id = request.form.get("category_id")
        amount = request.form.get("amount")
        description = request.form.get("description", "").strip()
        transaction_date = request.form.get("transaction_date") or datetime.now().strftime("%Y-%m-%d")

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError

            conn.execute("""
                INSERT INTO transactions
                (user_id, category_id, type, amount, description, transaction_date)
                VALUES (?, ?, 'expense', ?, ?, ?)
            """, (user_id, category_id, amount, description, transaction_date))
            conn.commit()
            flash("Expense added successfully.", "success")
        except (ValueError, TypeError):
            flash("Enter a valid positive amount.", "danger")

    categories = conn.execute(
        "SELECT * FROM categories WHERE user_id=? AND type='expense' ORDER BY name",
        (user_id,)
    ).fetchall()

    expenses = conn.execute("""
        SELECT t.*, c.name AS category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id=c.id
        WHERE t.user_id=? AND t.type='expense'
        ORDER BY t.transaction_date DESC, t.id DESC
    """, (user_id,)).fetchall()

    conn.close()
    return render_template("expenses.html", categories=categories, expenses=expenses)


@app.route("/income", methods=["GET", "POST"])
@login_required
def income_page():
    user_id = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        category_id = request.form.get("category_id")
        amount = request.form.get("amount")
        description = request.form.get("description", "").strip()
        transaction_date = request.form.get("transaction_date") or datetime.now().strftime("%Y-%m-%d")

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError

            conn.execute("""
                INSERT INTO transactions
                (user_id, category_id, type, amount, description, transaction_date)
                VALUES (?, ?, 'income', ?, ?, ?)
            """, (user_id, category_id, amount, description, transaction_date))
            conn.commit()
            flash("Income added successfully.", "success")
        except (ValueError, TypeError):
            flash("Enter a valid positive amount.", "danger")

    categories = conn.execute(
        "SELECT * FROM categories WHERE user_id=? AND type='income' ORDER BY name",
        (user_id,)
    ).fetchall()

    income = conn.execute("""
        SELECT t.*, c.name AS category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id=c.id
        WHERE t.user_id=? AND t.type='income'
        ORDER BY t.transaction_date DESC, t.id DESC
    """, (user_id,)).fetchall()

    conn.close()
    return render_template("income.html", categories=categories, income=income)


@app.route("/transactions")
@login_required
def transactions():
    user_id = session["user_id"]
    filter_type = request.args.get("type", "all")

    conn = get_db()

    if filter_type in ("income", "expense"):
        rows = conn.execute("""
            SELECT t.*, c.name AS category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id=c.id
            WHERE t.user_id=? AND t.type=?
            ORDER BY t.transaction_date DESC, t.id DESC
        """, (user_id, filter_type)).fetchall()
    else:
        rows = conn.execute("""
            SELECT t.*, c.name AS category_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id=c.id
            WHERE t.user_id=?
            ORDER BY t.transaction_date DESC, t.id DESC
        """, (user_id,)).fetchall()

    conn.close()
    return render_template("transactions.html", transactions=rows, filter_type=filter_type)


@app.route("/delete-transaction/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM transactions WHERE id=? AND user_id=?",
        (transaction_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    flash("Transaction deleted.", "success")
    return redirect(request.referrer or url_for("transactions"))


@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    user_id = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        category_id = request.form.get("category_id")
        amount = request.form.get("amount")
        month = request.form.get("month") or datetime.now().strftime("%Y-%m")

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError

            conn.execute("""
                INSERT INTO budgets(user_id, category_id, amount, month)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, category_id, month)
                DO UPDATE SET amount=excluded.amount
            """, (user_id, category_id, amount, month))
            conn.commit()
            flash("Budget saved successfully.", "success")
        except (ValueError, TypeError):
            flash("Enter a valid positive budget amount.", "danger")

    categories = conn.execute(
        "SELECT * FROM categories WHERE user_id=? AND type='expense' ORDER BY name",
        (user_id,)
    ).fetchall()

    budget_rows = conn.execute("""
        SELECT b.*, c.name AS category_name,
               COALESCE((
                   SELECT SUM(t.amount)
                   FROM transactions t
                   WHERE t.user_id=b.user_id
                     AND t.category_id=b.category_id
                     AND t.type='expense'
                     AND substr(t.transaction_date,1,7)=b.month
               ),0) AS spent
        FROM budgets b
        JOIN categories c ON b.category_id=c.id
        WHERE b.user_id=?
        ORDER BY b.month DESC, c.name
    """, (user_id,)).fetchall()

    conn.close()
    return render_template("budgets.html", categories=categories, budgets=budget_rows)


@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    user_id = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_type = request.form.get("type")

        if name and category_type in ("expense", "income"):
            try:
                conn.execute(
                    "INSERT INTO categories(user_id,name,type) VALUES(?,?,?)",
                    (user_id, name, category_type)
                )
                conn.commit()
                flash("Category added.", "success")
            except sqlite3.IntegrityError:
                flash("Category already exists.", "danger")
        else:
            flash("Enter a valid category.", "danger")

    rows = conn.execute(
        "SELECT * FROM categories WHERE user_id=? ORDER BY type, name",
        (user_id,)
    ).fetchall()

    conn.close()
    return render_template("categories.html", categories=rows)


@app.route("/delete-category/<int:category_id>", methods=["POST"])
@login_required
def delete_category(category_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM categories WHERE id=? AND user_id=?",
        (category_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    flash("Category deleted.", "success")
    return redirect(url_for("categories"))


@app.route("/reports")
@login_required
def reports():
    user_id = session["user_id"]
    conn = get_db()

    totals = conn.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END),0) income,
            COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) expenses
        FROM transactions
        WHERE user_id=?
    """, (user_id,)).fetchone()

    category_rows = conn.execute("""
        SELECT c.name, COALESCE(SUM(t.amount),0) total
        FROM categories c
        LEFT JOIN transactions t
          ON c.id=t.category_id AND t.type='expense'
        WHERE c.user_id=? AND c.type='expense'
        GROUP BY c.id
        ORDER BY total DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        income=totals["income"],
        expenses=totals["expenses"],
        balance=totals["income"] - totals["expenses"],
        category_rows=category_rows
    )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            conn.execute("UPDATE users SET name=? WHERE id=?", (name, user_id))
            conn.commit()
            session["user_name"] = name
            flash("Profile updated.", "success")

    user = conn.execute(
        "SELECT id,name,email,created_at FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    conn.close()
    return render_template("profile.html", user=user)


@app.context_processor
def inject_user():
    return {"current_user": session.get("user_name")}


init_db()

if __name__ == "__main__":
    app.run(debug=True)
