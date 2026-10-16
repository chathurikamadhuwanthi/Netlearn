import random
import sqlite3
from datetime import datetime
from flask import (Blueprint, flash, g, redirect, render_template,
                   request, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from .auth import login_required
from .db import get_db
from .services.progress import (build_course, course_completed, find_next,
                                is_enrolled, overall_percent)

bp = Blueprint("main", __name__)

# Used on the public home page
COURSE_OUTLINE = [
    {
        "level": "Beginner",
        "modules": [
            {"title": "Networking Basics",
             "desc": "OSI & TCP/IP models, network devices, IP vs MAC addresses and ports.",
             "ready": True},
            {"title": "IP Addressing & Subnetting",
             "desc": "Binary, CIDR, subnet masks and step-by-step subnetting.",
             "ready": True},
            {"title": "Basic Routing & Static Routes",
             "desc": "Routing tables, static and default routes, Longest Prefix Match.",
             "ready": True},
        ],
    },
    {
        "level": "Intermediate",
        "modules": [
            {"title": "Switching, VLANs & Trunking",
             "desc": "How switches forward frames, VLAN segmentation and 802.1Q trunks.",
             "ready": True},
            {"title": "Dynamic Routing (RIP, OSPF)",
             "desc": "How routers learn routes automatically and choose the best path.",
             "ready": True},
            {"title": "Network Services (DHCP, DNS, NAT)",
             "desc": "The services that make real networks and the Internet usable.",
             "ready": True},
        ],
    },
]

# Short description for every module id (used on the dashboard and course pages)
MODULE_DESC = {
    "m01": "OSI & TCP/IP models, network devices, IP vs MAC addresses and ports.",
    "m02": "Binary, CIDR, subnet masks and step-by-step subnetting.",
    "m03": "Routing tables, static and default routes, Longest Prefix Match.",
    "m04": "How switches forward frames, VLAN segmentation and 802.1Q trunks.",
    "m05": "How routers learn routes automatically and choose the best path.",
    "m06": "The services that make real networks and the Internet usable.",
}


def decorate(course):
    # Adds a number, a description and a progress percentage to every module
    for i, m in enumerate(course, start=1):
        m["number"] = i
        m["desc"] = MODULE_DESC.get(m["id"], "")
        if m["available"]:
            parts = len(m["lessons"]) + 1          # lessons + the quiz
            done = sum(1 for l in m["lessons"] if l["done"]) + (1 if m["passed"] else 0)
            m["pct"] = int(done / parts * 100)
        else:
            m["pct"] = 0
    return course


# Short networking facts shown on the dashboard
TIPS = [
    "A /24 network has 254 usable host addresses.",
    "Routers pick the route with the longest matching prefix.",
    "A switch learns MAC addresses from the source of every frame it receives.",
    "Private IPv4 ranges: 10.0.0.0/8, 172.16.0.0/12 and 192.168.0.0/16.",
    "ping uses ICMP echo request and echo reply messages.",
    "TCP opens a connection with a three-way handshake: SYN, SYN-ACK, ACK.",
    "DNS translates names like example.com into IP addresses.",
    "A default gateway is where a host sends traffic for other networks.",
]


def welcome(name, enrolled, in_progress):
    # A different friendly headline and tip on every visit
    if not enrolled:
        pool = [
            (f"Welcome, {name}! Ready to learn networking?", "Enroll in the course and take your first step."),
            ("Every network expert started at zero", "Your journey begins with a single click."),
            (f"Hi {name}, let's build your networking skills", "Enroll to unlock lessons, labs and quizzes."),
        ]
    elif in_progress:
        pool = [
            (f"Welcome back, {name}", "Let's pick up right where you left off."),
            ("Ready for your next lesson?", "A little progress every day goes a long way."),
            (f"Let's keep going, {name}", "You are building real networking skills."),
            ("Time to learn something new", "One lesson at a time."),
            (f"Great to see you again, {name}", "Your next step is waiting below."),
        ]
    else:
        pool = [
            (f"Amazing work, {name}!", "You have completed everything available so far."),
            (f"Well done, {name}!", "Every module released so far is behind you."),
            ("Course complete, for now", "New modules are on the way."),
           ]
    title, sub = random.choice(pool)
    return {"title": title, "sub": sub, "tip": random.choice(TIPS)}


@bp.route("/")
def home():
    enrolled, nxt = False, None
    if g.user is not None:
        enrolled = is_enrolled(g.user["id"])
        if enrolled:
            nxt = find_next(build_course(g.user["id"]))   # None when everything is finished
    return render_template("home.html", outline=COURSE_OUTLINE,
                           enrolled=enrolled, nxt=nxt)


@bp.route("/enroll", methods=("POST",))
@login_required
def enroll():
    db = get_db()
    db.execute("INSERT OR IGNORE INTO enrollments (user_id) VALUES (?)", (g.user["id"],))
    db.commit()
    flash("You are now enrolled in the course. Happy learning!", "success")
    return redirect(url_for("main.dashboard"))


@bp.route("/dashboard")
@login_required
def dashboard():
    uid = g.user["id"]
    enrolled = is_enrolled(uid)
    course = decorate(build_course(uid))     # also used as a preview before enrolling
    available = [m for m in course if m["available"]]
    scores = [m["best_score"] for m in available if m["best_score"] is not None]

    stats = {
        "planned": len(course),
        "modules_total": len(available),
        "lessons_total": sum(len(m["lessons"]) for m in available),
        "lessons_done": sum(1 for m in available for l in m["lessons"] if l["done"]),
        "quizzes_passed": sum(1 for m in available if m["passed"]),
        "best": max(scores) if scores else None,
    }
    stats["steps_total"] = stats["lessons_total"] + stats["modules_total"]
    stats["steps_done"] = stats["lessons_done"] + stats["quizzes_passed"]

    percent = overall_percent(course) if enrolled else 0
    nxt = find_next(course) if enrolled else None
    course_done = course_completed(course) if enrolled else False

    # What the "Resume" card should show
    resume = None
    if nxt:
        mod = next((m for m in course if m["id"] == nxt["module_id"]), None)
        if mod:
            if nxt["kind"] == "lesson":
                pos = next((i for i, l in enumerate(mod["lessons"], start=1)
                            if l["id"] == nxt["lesson_id"]), 1)
                label = f"Lesson {pos} of {len(mod['lessons'])}"
            else:
                label = "Module quiz"
            resume = {"module": mod, "label": label}

    has_cert = get_db().execute(
        "SELECT 1 FROM certificates WHERE user_id = ?", (uid,)
    ).fetchone() is not None

    return render_template("dashboard.html", enrolled=enrolled, course=course,
                           percent=percent, resume=resume, course_done=course_done,
                                                      has_cert=has_cert, stats=stats,
                           hero=welcome(g.user["name"], enrolled, resume is not None))


@bp.route("/course")
@login_required
def course():
    enrolled = is_enrolled(g.user["id"])
    modules = decorate(build_course(g.user["id"]))
    summary = {"modules": len(modules),
               "lessons": sum(len(m["lessons"]) for m in modules)}
    return render_template("course.html", enrolled=enrolled, course=modules,
                           summary=summary)


@bp.route("/profile", methods=("GET", "POST"))
@login_required
def profile():
    if request.method == "POST":
        db = get_db()
        action = request.form.get("action")

        if action == "details":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            if not name or not email:
                flash("Name and email cannot be empty.", "error")
            else:
                try:
                    db.execute("UPDATE users SET name = ?, email = ? WHERE id = ?",
                               (name, email, g.user["id"]))
                    db.commit()
                    flash("Your profile has been updated.", "success")
                except sqlite3.IntegrityError:
                    flash("Another account already uses this email.", "error")

        elif action == "password":
            current = request.form.get("current", "")
            new = request.form.get("new", "")
            confirm = request.form.get("confirm", "")
            if not check_password_hash(g.user["password_hash"], current):
                flash("Your current password is incorrect.", "error")
            elif len(new) < 8:
                flash("Your new password must be at least 8 characters long.", "error")
            elif new != confirm:
                flash("The new passwords do not match.", "error")
            else:
                db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                           (generate_password_hash(new), g.user["id"]))
                db.commit()
                flash("Your password has been changed.", "success")

        return redirect(url_for("main.profile"))

    return render_template("profile.html", enrolled=is_enrolled(g.user["id"]))