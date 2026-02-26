from flask import Blueprint, render_template, request, redirect, session, url_for
from datetime import datetime
from app.fake_data import generate_event
import time
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "soc_logs.db")
ACTIVE_TABLE = None
EVENT_STORE = []
PAUSED = False
LAST_EVENT_TIME = 0

main = Blueprint("main", __name__)

# simple simulated credentials
VALID_USER = "admin"
VALID_PASS = "admin"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_new_table():
    global ACTIVE_TABLE

    conn = get_db_connection()
    cur = conn.cursor()

    # Determine next table number
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'table%'
    """)
    existing = cur.fetchall()

    table_number = len(existing) + 1
    table_name = f"table{table_number}"

    cur.execute(f"""
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user TEXT,
            source TEXT,
            event_type TEXT,
            level INTEGER,
            severity TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()

    ACTIVE_TABLE = table_name
    return table_name


def get_existing_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'table%'
    """)
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables


def insert_event(table_name, event):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        INSERT INTO {table_name}
        (timestamp, user, source, event_type, level, severity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event["timestamp"],
        event["user"],
        event["source"],
        event["type"],
        event["level"],
        event["severity"],
        event["status"]
    ))

    conn.commit()
    conn.close()


def fetch_events(table_name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT * FROM {table_name}
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return rows



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
    global ACTIVE_TABLE

    if "user" not in session:
        return redirect(url_for("main.login"))

    action = request.args.get("action")

    # Handle New
    if action == "new":
        create_new_table()

    # Handle Open
    elif action and action.startswith("open:"):
        ACTIVE_TABLE = action.split(":")[1]

    # If no active table yet, render empty dashboard
    if not ACTIVE_TABLE:
        tables = get_existing_tables()
        return render_template(
            "dashboard.html",
            user=session["user"],
            tables=tables,
            events=[],
            active_table=None,
            total_logs=0
        )

    # Generate event
    event = generate_event()
    insert_event(ACTIVE_TABLE, event)

    # Fetch events from DB
    events = fetch_events(ACTIVE_TABLE)

    return render_template(
        "dashboard.html",
        user=session["user"],
        events=events,
        active_table=ACTIVE_TABLE,
        tables=get_existing_tables(),
        total_logs=len(events)
    )



@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))
