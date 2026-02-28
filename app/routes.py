from flask import Blueprint, render_template, request, redirect, session, url_for
from app.fake_data import generate_event
import sqlite3
import os

main = Blueprint("main", __name__)

DB_PATH = os.path.join(os.getcwd(), "soc_logs.db")

VALID_USER = "admin"
VALID_PASS = "admin"


# ------------------ DATABASE HELPERS ------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_existing_tables():
    if not os.path.exists(DB_PATH):
        return []

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name GLOB 'table[0-9]*'
        ORDER BY CAST(SUBSTR(name, 6) AS INTEGER) ASC
    """)
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables


def create_new_table():
    tables = get_existing_tables()
    if tables:
        last = tables[-1]
        try:
            next_index = int(last[5:]) + 1
        except ValueError:
            next_index = len(tables) + 1
    else:
        next_index = 1

    table_name = f"table{next_index}"

    conn = get_db_connection()
    cur = conn.cursor()
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
    return table_name


def delete_last_table():
    tables = get_existing_tables()
    if not tables:
        return None
    last_table = tables[-1]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {last_table}")
    conn.commit()
    conn.close()
    return last_table


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
    cur.execute(f"SELECT * FROM {table_name} ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# ------------------ ROUTES ------------------

@main.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("main.dashboard"))

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
                message = f"authentication failed ({session['attempts']}/3)"

    return render_template("login.html", message=message)


@main.route("/events")
def get_new_events():
    if "user" not in session or "active_table" not in session:
        return "", 401  # or jsonify({"error": "not authorized"}), 401

    active = session["active_table"]
    if not active:
        return "", 204  # no content

    # Generate and insert ONE new event
    event = generate_event()
    insert_event(active, event)

    # Fetch the newest event only (the one we just added)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT * FROM {active}
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()

    if row:
        # Return as simple HTML row so frontend can .insertAdjacentHTML
        html = f"""
        <tr style="border-bottom:1px solid #111;"
            onmouseover="this.style.background='#111';"
            onmouseout="this.style.background='transparent';">
            <td>{row['id']}</td>
            <td>{row['timestamp']}</td>
            <td>{row['user']}</td>
            <td>{row['source']}</td>
            <td>{row['event_type']}</td>
            <td>{row['level']}</td>
            <td style="
                {'background:#FF0000; color:black;' if row['level'] == 4 else
                 'background:#FFA500; color:black;' if row['level'] == 3 else
                 'background:#FFFF00; color:black;' if row['level'] == 2 else
                 'background:#00FF00; color:black;' if row['level'] == 1 else
                 'background:#888888; color:black;'}
            ">
                <b>{row['severity']}</b>
            </td>
            <td>{row['status']}</td>
        </tr>
        """
        return html

    return "", 204

@main.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("main.login"))

    if "active_table" not in session:
        session["active_table"] = None

    action = request.args.get("action")
    tables = get_existing_tables()

    # -------- OPEN FIRST TABLE --------
    if action == "open":
        if tables:
            session["active_table"] = tables[0]

    # -------- CREATE NEW TABLE --------
    elif action == "new":
        session["active_table"] = create_new_table()

    # -------- SWITCH TABLE --------
    elif action and action.startswith("switch:"):
        table_name = action.split(":", 1)[1]
        if table_name in tables:
            session["active_table"] = table_name

    # -------- REMOVE LAST TABLE --------
    elif action == "remove":
        deleted = delete_last_table()
        if session.get("active_table") == deleted:
            tables = get_existing_tables()  # refresh after delete
            session["active_table"] = tables[-1] if tables else None

    # Refresh table list after any potential change
    tables = get_existing_tables()
    active = session.get("active_table")

    # Safety: if active table no longer exists, fall back to newest one
    if active and active not in tables:
        active = tables[-1] if tables else None
        session["active_table"] = active

    if not active:
        return render_template(
            "dashboard.html",
            user=session["user"],
            tables=tables,
            active_table=None,
            events=[],
            total_logs=0
        )

    # Generate one new event on every dashboard load (this is what makes events continuous)
    # Uses the weighted probabilities defined in fake_data.py
    #event = generate_event()
    #insert_event(active, event)

    events = fetch_events(active)

    return render_template(
        "dashboard.html",
        user=session["user"],
        tables=tables,
        active_table=active,
        events=events,
        total_logs=len(events)
    )


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))
