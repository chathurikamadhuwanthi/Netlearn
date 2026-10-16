import functools
import sqlite3
from flask import (Blueprint, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    # Before every request: load the logged-in user (if any) into g.user
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    # Sends visitors who are not logged in to the login page
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            flash("Please log in first.", "error")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        error = None
        if not name or not email or not password:
            error = "Please fill in all fields."
        elif len(password) < 8:
            error = "Your password must be at least 8 characters long."

        if error is None:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = "An account with this email already exists."
            else:
                session.clear()
                session["user_id"] = cur.lastrowid   # log in automatically after registering
                flash(f"Your account has been created. Welcome to NetLearn, {name}!", "success")
                return redirect(url_for("main.dashboard"))

        flash(error, "error")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = get_db().execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        # Same message for a wrong email or a wrong password (security)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out. See you soon!", "info")
    return redirect(url_for("main.home"))