import json
import secrets
import sqlite3
from datetime import datetime
from flask import Blueprint, flash, g, redirect, render_template, url_for
from .auth import login_required
from .db import get_db
from .services import progress

bp = Blueprint("certificate", __name__, url_prefix="/certificate")


def _find(user_id):
    return get_db().execute(
        "SELECT * FROM certificates WHERE user_id = ?", (user_id,)
    ).fetchone()


def _issue(user_id, course):
    # Collect the titles of all modules the user has passed
    titles = [m["title"] for m in course if m["available"] and m["passed"]]
    db = get_db()
    for _ in range(5):
        code = f"NL-{datetime.now().year}-{secrets.token_hex(3).upper()}"
        try:
            db.execute(
                "INSERT INTO certificates (user_id, code, modules) VALUES (?, ?, ?)",
                (user_id, code, json.dumps(titles)),
            )
            db.commit()
            break
        except sqlite3.IntegrityError:
            db.rollback()
            if _find(user_id):  # Certificate already exists, stop retrying
                break
    return _find(user_id)


@bp.route("/")
@login_required
def view():
    if not progress.is_enrolled(g.user["id"]):
        flash("Please enroll in the course first to get a certificate.", "error")
        return redirect(url_for("main.home"))

    course = progress.build_course(g.user["id"])
    cert = _find(g.user["id"])

    # If the course is finished and no certificate exists yet, issue one now
    if cert is None and progress.course_completed(course):
        cert = _issue(g.user["id"], course)

    modules, verify_url = [], None
    if cert:
        modules = json.loads(cert["modules"])
        verify_url = url_for("certificate.verify", code=cert["code"], _external=True)

    return render_template("certificate.html", cert=cert, modules=modules,
                           course=course, verify_url=verify_url)


@bp.route("/verify/<code>")
def verify(code):
    # No login needed: anyone with the certificate ID can verify it
    row = get_db().execute(
        "SELECT c.code, c.issued_at, c.modules, u.name "
        "FROM certificates c JOIN users u ON u.id = c.user_id WHERE c.code = ?",
        (code.strip().upper(),),
    ).fetchone()
    modules = json.loads(row["modules"]) if row else []
    return render_template("certificate_verify.html", row=row, modules=modules)