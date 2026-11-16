"""FR-01: registration, login and roles (student / faculty / admin)."""
import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .security import safe_next

bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_registration(form, faculty_code):
    errors = []
    if not form.get("name", "").strip():
        errors.append("Name is required.")
    if not EMAIL_RE.match(form.get("email", "").strip()):
        errors.append("Enter a valid email address.")
    if len(form.get("password", "")) < 8:
        errors.append("Password must be at least 8 characters.")
    role = form.get("role", "student")
    if role not in ("student", "faculty"):
        errors.append("Choose a valid role.")
    elif role == "faculty" and form.get("faculty_code", "") != faculty_code:
        errors.append("Invalid faculty sign-up code.")
    return errors


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        form = request.form
        email = form.get("email", "").strip().lower()
        errors = validate_registration(form, current_app.config["FACULTY_SIGNUP_CODE"])
        db = get_db()
        if not errors and db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            errors.append("An account with this email already exists.")
        if not errors:
            db.execute(
                "INSERT INTO users (name, email, srn, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                (form["name"].strip(), email, form.get("srn", "").strip().upper(),
                 generate_password_hash(form["password"]), form.get("role", "student")),
            )
            db.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
        for error in errors:
            flash(error, "error")
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], request.form.get("password", "")):
            flash("Incorrect email or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(safe_next(request.args.get("next"), url_for("dashboard.index")))
    return render_template("auth/login.html")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
