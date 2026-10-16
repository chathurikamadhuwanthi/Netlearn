import json
import os
from flask import current_app
from ..db import get_db

PASS_MARK = 60   # Minimum quiz score (%) required to pass


def load_modules():
    # Load the list of course modules from content/modules.json
    path = os.path.join(current_app.root_path, "content", "modules.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_enrolled(user_id):
    row = get_db().execute(
        "SELECT 1 FROM enrollments WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row is not None


def completed_lessons(user_id):
    rows = get_db().execute(
        "SELECT lesson_id FROM progress WHERE user_id = ?", (user_id,)
    ).fetchall()
    return {r["lesson_id"] for r in rows}


def best_quiz_score(user_id, module_id):
    row = get_db().execute(
        "SELECT MAX(score) AS best FROM quiz_results WHERE user_id = ? AND module_id = ?",
        (user_id, module_id),
    ).fetchone()
    return row["best"]   # None if the quiz has not been attempted


def build_course(user_id):
    """Calculate the status of every module:
    coming_soon / locked / open / completed
    Unlock rules:
      - A lesson unlocks once the previous lesson is completed
      - The quiz unlocks once all lessons in the module are completed
      - The next module unlocks once the previous module's quiz is passed
    """
    done = completed_lessons(user_id)
    course = []
    prev_passed = True

    for m in load_modules():
        lessons = m["lessons"]
        available = len(lessons) > 0
        best = best_quiz_score(user_id, m["id"]) if available else None
        passed = best is not None and best >= PASS_MARK
        unlocked = available and prev_passed

        items = []
        prev_done = True
        for l in lessons:
            is_done = l["id"] in done
            items.append({**l, "done": is_done, "unlocked": unlocked and prev_done})
            prev_done = is_done

        all_done = available and all(i["done"] for i in items)

        if not available:
            status = "coming_soon"
        elif not unlocked:
            status = "locked"
        elif passed:
            status = "completed"
        else:
            status = "open"

        course.append({
            **m,
            "lessons": items,
            "available": available,
            "unlocked": unlocked,
            "all_lessons_done": all_done,
            "quiz_unlocked": unlocked and all_done,
            "best_score": best,
            "passed": passed,
            "status": status,
        })
        prev_passed = passed

    return course


def overall_percent(course):
    # Count lessons + quizzes (1 per module) and return the completed share as a %
    total = done = 0
    for m in course:
        if not m["available"]:
            continue
        total += len(m["lessons"]) + 1
        done += sum(1 for l in m["lessons"] if l["done"]) + (1 if m["passed"] else 0)
    return int(done / total * 100) if total else 0


def find_next(course):
    # Where the "Continue Learning" button should take the user next
    for m in course:
        if m["status"] != "open":
            continue
        for l in m["lessons"]:
            if l["unlocked"] and not l["done"]:
                return {"kind": "lesson", "module_id": m["id"],
                        "lesson_id": l["id"], "title": l["title"]}
        if m["quiz_unlocked"] and not m["passed"]:
            return {"kind": "quiz", "module_id": m["id"], "title": m["title"] + " – Quiz"}
    return None


def course_completed(course):
    # True if every available module's quiz is passed (at least one module must exist)
    avail = [m for m in course if m["available"]]
    return bool(avail) and all(m["passed"] for m in avail)