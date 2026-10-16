import functools
import json
import os
import re
import markdown
from flask import (Blueprint, abort, current_app, flash, g, redirect,
                   render_template, request, url_for)
from .auth import login_required
from .db import get_db
from .services import progress

bp = Blueprint("learn", __name__, url_prefix="/learn")


def enrolled_required(view):
    # Visitors who have not enrolled are sent back to the home page
    @functools.wraps(view)
    def wrapped(**kwargs):
        if not progress.is_enrolled(g.user["id"]):
            flash("Please enroll in the course first.", "error")
            return redirect(url_for("main.home"))
        return view(**kwargs)
    return wrapped


def _get_module(module_id):
    """Returns (module, whole course). Adds the module number and progress %."""
    course = progress.build_course(g.user["id"])
    for number, m in enumerate(course, start=1):
        if m["id"] == module_id:
            m["number"] = number
            parts = len(m["lessons"]) + 1
            done = sum(1 for l in m["lessons"] if l["done"]) + (1 if m["passed"] else 0)
            m["pct"] = int(done / parts * 100) if m["available"] else 0
            return m, course
    abort(404)


def _content_file(module, filename):
    return os.path.join(current_app.root_path, "content", module["folder"], filename)


@bp.route("/")
@login_required
@enrolled_required
def start():
    # "Continue learning": go to the next lesson or quiz
    nxt = progress.find_next(progress.build_course(g.user["id"]))
    if nxt is None:
        flash("You have finished everything available so far. New modules are coming soon!", "success")
        return redirect(url_for("main.dashboard"))
    if nxt["kind"] == "lesson":
        return redirect(url_for("learn.lesson", module_id=nxt["module_id"],
                                lesson_id=nxt["lesson_id"]))
    return redirect(url_for("learn.quiz", module_id=nxt["module_id"]))


@bp.route("/<module_id>")
@login_required
@enrolled_required
def module(module_id):
    m, _ = _get_module(module_id)
    if m["status"] in ("coming_soon", "locked"):
        flash("This module is not unlocked yet.", "error")
        return redirect(url_for("main.course"))
    return render_template("learn/module.html", module=m, pass_mark=progress.PASS_MARK)


@bp.route("/<module_id>/<lesson_id>")
@login_required
@enrolled_required
def lesson(module_id, lesson_id):
    m, _ = _get_module(module_id)
    idx = next((i for i, l in enumerate(m["lessons"]) if l["id"] == lesson_id), None)
    if idx is None:
        abort(404)
    item = m["lessons"][idx]
    if not item["unlocked"]:
        flash("This lesson is locked. Finish the previous lesson first.", "error")
        return redirect(url_for("main.course"))

    # Read the .md file and turn it into HTML
    with open(_content_file(m, item["file"]), encoding="utf-8") as f:
        html = markdown.markdown(f.read(), extensions=["fenced_code", "tables", "sane_lists"])

    words = len(re.sub(r"<[^>]+>", " ", html).split())
    minutes = max(1, round(words / 180))
    prev_lesson = m["lessons"][idx - 1] if idx > 0 else None

    return render_template("learn/lesson.html", module=m, lesson=item, number=idx + 1,
                           total=len(m["lessons"]), content=html, minutes=minutes,
                           prev_lesson=prev_lesson)


@bp.route("/<module_id>/<lesson_id>/complete", methods=("POST",))
@login_required
@enrolled_required
def complete(module_id, lesson_id):
    m, _ = _get_module(module_id)
    idx = next((i for i, l in enumerate(m["lessons"]) if l["id"] == lesson_id), None)
    if idx is None or not m["lessons"][idx]["unlocked"]:
        abort(404)

    db = get_db()
    db.execute("INSERT OR IGNORE INTO progress (user_id, lesson_id) VALUES (?, ?)",
               (g.user["id"], lesson_id))
    db.commit()

    # Next lesson, or the quiz after the last lesson
    if idx + 1 < len(m["lessons"]):
        nxt_id = m["lessons"][idx + 1]["id"]
        return redirect(url_for("learn.lesson", module_id=module_id, lesson_id=nxt_id))
    flash("All lessons complete! Now take the quiz.", "success")
    return redirect(url_for("learn.quiz", module_id=module_id))


@bp.route("/<module_id>/quiz", methods=("GET", "POST"))
@login_required
@enrolled_required
def quiz(module_id):
    m, _ = _get_module(module_id)
    if not m["quiz_unlocked"]:
        flash("Finish all lessons to unlock this quiz.", "error")
        return redirect(url_for("learn.module", module_id=module_id))

    with open(_content_file(m, m["quiz"]), encoding="utf-8") as f:
        questions = json.load(f)["questions"]

    if request.method == "POST":
        correct = 0
        review = []
        for i, q in enumerate(questions):
            raw = request.form.get(f"q{i}", "")
            chosen = int(raw) if raw.isdigit() and int(raw) < len(q["options"]) else None
            ok = chosen == q["answer"]
            correct += 1 if ok else 0
            review.append({"question": q["q"], "options": q["options"],
                           "chosen": chosen, "answer": q["answer"], "ok": ok,
                           "explain": q.get("explain", "")})

        score = round(correct / len(questions) * 100)
        db = get_db()
        db.execute("INSERT INTO quiz_results (user_id, module_id, score) VALUES (?, ?, ?)",
                   (g.user["id"], module_id, score))
        db.commit()

        passed = score >= progress.PASS_MARK
        next_module = None
        if passed:
            # Which module (if any) does this quiz unlock?
            m2, course2 = _get_module(module_id)
            if m2["number"] < len(course2) and course2[m2["number"]]["available"]:
                n = course2[m2["number"]]
                next_module = {"id": n["id"], "title": n["title"], "number": m2["number"] + 1}

        return render_template("learn/quiz_result.html", module=m, review=review,
                               correct=correct, total=len(questions), score=score,
                               passed=passed, pass_mark=progress.PASS_MARK,
                               next_module=next_module)

    return render_template("learn/quiz.html", module=m, questions=questions,
                           pass_mark=progress.PASS_MARK)