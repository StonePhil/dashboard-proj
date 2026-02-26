from flask import Blueprint, render_template, request, redirect, session, url_for
from datetime import datetime
from app.fake_data import generate_event
import time

EVENT_STORE = []
PAUSED = False
LAST_EVENT_TIME = 0

main = Blueprint("main", __name__)

# simple simulated credentials
VALID_USER = "admin"
VALID_PASS = "admin"


import random

def random_spawn_interval():
    # Lower-level events appear more often
    # 1–3 seconds mostly, rare 5–8 seconds
    if random.random() < 0.8:
        return random.uniform(1, 3)
    else:
        return random.uniform(5, 8)


def apply_query_filter(events, query):
    or_blocks = [block.strip() for block in query.split("||")]
    filtered_events = []

    for block in or_blocks:
        and_conditions = [cond.strip() for cond in block.split("&&")]
        temp_events = list(events)

        for cond in and_conditions:
            if "==" not in cond:
                continue

            field, value = [x.strip() for x in cond.split("==", 1)]

            if field == "ip.addr":
                temp_events = [e for e in temp_events if e["source"] == value]

            elif field == "level" and value.isdigit():
                temp_events = [e for e in temp_events if e["level"] == int(value)]

            elif field == "user":
                temp_events = [e for e in temp_events if e["user"] == value]

        filtered_events.extend(temp_events)

    return list({e["index"]: e for e in filtered_events}.values())



@main.route("/", methods=["GET", "POST"])
def login():
    if "attempts" not in session:
        session["attempts"] = 0

    message = ""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == VALID_USER and password == VALID_PASS:
            session["user"] = username
            session["attempts"] = 0
            return redirect(url_for("main.dashboard"))

        else:
            session["attempts"] += 1

            if session["attempts"] >= 3:
                message = "you have been timed out (60 s)"
            else:
                message = "authentication failed"

    return render_template("login.html", message=message)

@main.route("/dashboard")
def dashboard():
    global PAUSED, LAST_EVENT_TIME

    if "user" not in session:
        return redirect(url_for("main.login"))

    query = request.args.get("q", "").strip()
    reset_flag = request.args.get("reset")
    action = request.args.get("action")

    # Handle pause / continue
    if action == "pause":
        PAUSED = True
    elif action == "continue":
        PAUSED = False

    # Proper reset (no event generation)
    if reset_flag:
        return redirect(url_for("main.dashboard"))

    now = time.time()

    # Only generate event if:
    # - not paused
    # - not filtering
    # - random time interval passed
    if not PAUSED and not query:

        interval = random_spawn_interval()

        if now - LAST_EVENT_TIME > interval:
            EVENT_STORE.append(generate_event())
            LAST_EVENT_TIME = now

    # Assign event index
    for i, event in enumerate(EVENT_STORE, start=1):
        event["index"] = i

    # Newest first
    events = list(reversed(EVENT_STORE))

    # Filtering
    if query:
        events = apply_query_filter(events, query)

    summary = {
        "critical": sum(1 for e in EVENT_STORE if e["level"] == 4),
        "high": sum(1 for e in EVENT_STORE if e["level"] == 3),
        "total": len(EVENT_STORE),
        "analysts": 3
    }

    return render_template(
        "dashboard.html",
        user=session["user"],
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary=summary,
        events=events,
        query=query,
        paused=PAUSED,
        total_logs=len(EVENT_STORE)
    )



@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))
