from flask import Flask, request, redirect
import sqlite3
import datetime

app = Flask(__name__)
DB = "esp1.db"

# ---------------------------
# DATABASE CONNECTION
# ---------------------------
def db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------
# DATABASE INIT
# ---------------------------
def init():
    conn = db()
    # Tickets table with new fields
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tickets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bcr TEXT UNIQUE,
        service TEXT,
        namespace TEXT,
        stage TEXT,
        start TEXT,
        end TEXT,
        status TEXT,
        build_url TEXT,
        release_url TEXT,
        release_branch TEXT,
        build_number TEXT
    )
    """)
    # History table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        status TEXT,
        note TEXT,
        time TEXT
    )
    """)
    conn.commit()
    conn.close()

init()

# ---------------------------
# HISTORY LOGGER
# ---------------------------
def log(ticket_id, status, note):
    conn = db()
    conn.execute(
        "INSERT INTO history(ticket_id,status,note,time) VALUES(?,?,?,?)",
        (ticket_id, status, note, str(datetime.datetime.now()))
    )
    conn.commit()
    conn.close()

# ---------------------------
# NAVBAR UI
# ---------------------------
def navbar():
    return """
    <style>
    body{font-family:Arial;margin:40px;background:#f7f7f7}
    h1{color:#333}
    .nav a{margin-right:20px;text-decoration:none;font-weight:bold;color:#0077cc;}
    input{padding:6px;width:100%;}
    button{padding:6px 12px;margin-top:5px;}
    .row{display:flex;gap:20px;}
    .col{flex:1;}
    .green{color:green;font-weight:bold}
    .red{color:red;font-weight:bold}
    .orange{color:orange;font-weight:bold}
    .blue{color:blue;font-weight:bold}
    </style>
    <h1>ESP.1 Deployment Tracker</h1>
    <div class="nav">
    <a href="/">Dashboard</a>
    <a href="/create">Create Ticket</a>
    <a href="/tickets">Tickets</a>
    <a href="/history">History</a>
    </div>
    <hr><br>
    """

# ---------------------------
# STATUS COLOR
# ---------------------------
def color(status):
    s = status.lower()
    if "fail" in s: return "red"
    if "deploy" in s: return "orange"
    if "done" in s or "complete" in s: return "green"
    return "blue"

# ---------------------------
# DASHBOARD
# ---------------------------
@app.route("/")
def dashboard():
    conn = db()
    total = conn.execute("SELECT count(*) FROM tickets").fetchone()[0]
    running = conn.execute("SELECT count(*) FROM tickets WHERE status LIKE '%deploy%'").fetchone()[0]
    done = conn.execute("SELECT count(*) FROM tickets WHERE status LIKE '%done%' OR status LIKE '%complete%'").fetchone()[0]
    failed = conn.execute("SELECT count(*) FROM tickets WHERE status LIKE '%fail%'").fetchone()[0]
    conn.close()

    return navbar()+f"""
    <h2>Deployment Dashboard</h2>
    <table border="1" cellpadding="8" style="border-collapse:collapse;width:50%;background:white;">
        <tr>
            <th>Total Deployments</th>
            <th>Running</th>
            <th>Completed</th>
            <th>Failed</th>
        </tr>
        <tr>
            <td>{total}</td>
            <td class="orange">{running}</td>
            <td class="green">{done}</td>
            <td class="red">{failed}</td>
        </tr>
    </table>
    """

# ---------------------------
# CREATE TICKET
# ---------------------------
@app.route("/create", methods=["GET", "POST"])
def create():
    msg = ""
    if request.method == "POST":
        bcr = request.form["bcr"]
        service = request.form["service"]
        namespace = request.form["namespace"]
        stage = request.form["stage"]
        start = request.form["start"]
        end = request.form["end"]
        build_url = request.form.get("build_url","")
        release_url = request.form.get("release_url","")
        release_branch = request.form.get("release_branch","")
        build_number = request.form.get("build_number","")

        conn = db()
        exist = conn.execute("SELECT * FROM tickets WHERE bcr=?", (bcr,)).fetchone()
        if exist:
            msg = "<b class='red'>BCR already exists</b>"
        else:
            cur = conn.execute("""
                INSERT INTO tickets
                (bcr,service,namespace,stage,start,end,status,build_url,release_url,release_branch,build_number)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (bcr, service, namespace, stage, start, end, "CREATED", build_url, release_url, release_branch, build_number)
            )
            conn.commit()
            log(cur.lastrowid, "CREATED", "Ticket created")
            msg = "<b class='green'>Ticket created successfully</b>"
        conn.close()

    return navbar()+f"""
    <h2>Create Deployment Ticket</h2>
    {msg}
    <form method="post">
        <div class="row">
            <div class="col">
                BCR<br><input name="bcr" required><br><br>
                Service<br><input name="service"><br><br>
                Namespace<br><input name="namespace"><br><br>
                Stage<br><input name="stage"><br><br>
            </div>
            <div class="col">
                Start Time<br><input name="start"><br><br>
                End Time<br><input name="end"><br><br>
                Build URL<br><input name="build_url"><br><br>
                Release URL<br><input name="release_url"><br><br>
                Release Branch<br><input name="release_branch"><br><br>
                Build Number<br><input name="build_number"><br><br>
            </div>
        </div>
        <button>Create Ticket</button>
    </form>
    """

# ---------------------------
# EDIT TICKET
# ---------------------------
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    conn = db()
    ticket = conn.execute("SELECT * FROM tickets WHERE id=?", (id,)).fetchone()
    if request.method == "POST":
        bcr = request.form["bcr"]
        service = request.form["service"]
        namespace = request.form["namespace"]
        stage = request.form["stage"]
        start = request.form["start"]
        end = request.form["end"]
        status = request.form["status"]
        build_url = request.form.get("build_url","")
        release_url = request.form.get("release_url","")
        release_branch = request.form.get("release_branch","")
        build_number = request.form.get("build_number","")

        conn.execute("""
            UPDATE tickets
            SET bcr=?,service=?,namespace=?,stage=?,start=?,end=?,status=?,
                build_url=?,release_url=?,release_branch=?,build_number=?
            WHERE id=?""",
            (bcr,service,namespace,stage,start,end,status,build_url,release_url,release_branch,build_number,id)
        )
        conn.commit()
        log(id,status,"Status updated")
        conn.close()
        return redirect("/tickets")

    # Safe access to old columns
    build_url = ticket["build_url"] if "build_url" in ticket.keys() else ""
    release_url = ticket["release_url"] if "release_url" in ticket.keys() else ""
    release_branch = ticket["release_branch"] if "release_branch" in ticket.keys() else ""
    build_number = ticket["build_number"] if "build_number" in ticket.keys() else ""
    conn.close()

    return navbar()+f"""
    <h2>Edit Ticket</h2>
    <form method="post">
        <div class="row">
            <div class="col">
                BCR<br><input name="bcr" value="{ticket['bcr']}"><br><br>
                Service<br><input name="service" value="{ticket['service']}"><br><br>
                Namespace<br><input name="namespace" value="{ticket['namespace']}"><br><br>
                Stage<br><input name="stage" value="{ticket['stage']}"><br><br>
                Status<br><input name="status" value="{ticket['status']}"><br><br>
            </div>
            <div class="col">
                Start<br><input name="start" value="{ticket['start']}"><br><br>
                End<br><input name="end" value="{ticket['end']}"><br><br>
                Build URL<br><input name="build_url" value="{build_url}"><br><br>
                Release URL<br><input name="release_url" value="{release_url}"><br><br>
                Release Branch<br><input name="release_branch" value="{release_branch}"><br><br>
                Build Number<br><input name="build_number" value="{build_number}"><br><br>
            </div>
        </div>
        <button>Save Changes</button>
    </form>
    """

# ---------------------------
# TICKETS (MODERN TIMELINE CARDS)
# ---------------------------
@app.route("/tickets")
def tickets_tab():
    search = request.args.get("q", "")
    conn = db()
    if search:
        rows = conn.execute("SELECT * FROM tickets WHERE bcr LIKE ?", ("%"+search+"%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    conn.close()

    html = """
    <h2>Tickets</h2>
    <form>
        Search BCR:
        <input name="q" placeholder="Enter BCR">
        <button>Search</button>
    </form>
    <br>
    <style>
        .timeline{position:relative;max-width:900px;margin:0 auto;}
        .timeline::after{content:'';position:absolute;width:6px;background:#ddd;top:0;bottom:0;left:50%;margin-left:-3px;}
        .entry{padding:15px 40px;position:relative;background:white;width:45%;border-radius:8px;margin-bottom:20px;box-shadow:0 3px 8px rgba(0,0,0,0.15);transition:transform 0.2s, box-shadow 0.2s;}
        .entry.left{left:0;}
        .entry.right{left:50%;}
        .entry::after{content:"";position:absolute;width:20px;height:20px;background:white;border:4px solid #0077cc;top:20px;right:-10px;border-radius:50%;z-index:1;}
        .entry.right::after{left:-10px;}
        .entry h3{margin:0;font-size:16px;color:#0077cc;display:flex;align-items:center;gap:8px;}
        .entry p{margin:5px 0;font-size:14px;line-height:1.3;}
        .entry:hover{transform:translateY(-5px);box-shadow:0 6px 15px rgba(0,0,0,0.2);}
        .green{color:green;font-weight:bold;}
        .red{color:red;font-weight:bold;}
        .orange{color:orange;font-weight:bold;}
        .blue{color:blue;font-weight:bold;}
        .status-icon{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;}
        .green-dot{background:green;}
        .red-dot{background:red;}
        .orange-dot{background:orange;}
        .blue-dot{background:blue;}
        a{color:#0077cc;text-decoration:none;}
    </style>
    <div class="timeline">
    """
    side = True
    for r in rows:
        c = color(r["status"])
        cls = "left" if side else "right"
        side = not side
        build_url = r["build_url"] if "build_url" in r.keys() else ""
        release_url = r["release_url"] if "release_url" in r.keys() else ""
        release_branch = r["release_branch"] if "release_branch" in r.keys() else ""
        build_number = r["build_number"] if "build_number" in r.keys() else ""
        html += f"""
        <div class="entry {cls}">
            <h3><span class="status-icon {c}-dot"></span>BCR: {r['bcr']}</h3>
            <p><b>Status:</b> <span class="{c}">{r['status']}</span></p>
            <p><b>Service:</b> {r['service']}</p>
            <p><b>Namespace:</b> {r['namespace']}</p>
            <p><b>Stage:</b> {r['stage']}</p>
            <p><b>Start:</b> {r['start']}</p>
            <p><b>End:</b> {r['end']}</p>
            <p><b>Build URL:</b> <a href="{build_url}" target="_blank">{build_url}</a></p>
            <p><b>Release URL:</b> <a href="{release_url}" target="_blank">{release_url}</a></p>
            <p><b>Release Branch:</b> {release_branch}</p>
            <p><b>Build Number:</b> {build_number}</p>
            <p><a href="/edit/{r['id']}">Edit Ticket</a></p>
        </div>
        """
    html += "</div>"
    return navbar() + html

# ---------------------------
# HISTORY (MODERN TIMELINE)
# ---------------------------
@app.route("/history")
def history():
    conn = db()
    rows = conn.execute("""
        SELECT t.bcr, h.status, h.note, h.time
        FROM history h
        JOIN tickets t ON t.id=h.ticket_id
        ORDER BY h.time DESC
    """).fetchall()
    conn.close()

    html = """
    <h2>Status History</h2>
    <style>
        .timeline{position:relative;max-width:800px;margin:0 auto;}
        .timeline::after{content:'';position:absolute;width:6px;background:#ddd;top:0;bottom:0;left:50%;margin-left:-3px;}
        .entry{padding:10px 40px;position:relative;background:white;width:50%;border-radius:6px;margin-bottom:20px;box-shadow:0 2px 5px rgba(0,0,0,0.1);transition:transform 0.2s;}
        .entry.left{left:0;}
        .entry.right{left:50%;}
        .entry::after{content:"";position:absolute;width:20px;height:20px;background:white;border:4px solid #0077cc;top:15px;right:-10px;border-radius:50%;z-index:1;}
        .entry.right::after{left:-10px;}
        .entry h3{margin:0;font-size:16px;color:#0077cc;display:flex;align-items:center;gap:8px;}
        .entry p{margin:5px 0;font-size:14px;}
        .entry:hover{transform:translateY(-3px);box-shadow:0 5px 12px rgba(0,0,0,0.15);}
        .green{color:green;font-weight:bold;}
        .red{color:red;font-weight:bold;}
        .orange{color:orange;font-weight:bold;}
        .blue{color:blue;font-weight:bold;}
        .status-icon{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;}
        .green-dot{background:green;}
        .red-dot{background:red;}
        .orange-dot{background:orange;}
        .blue-dot{background:blue;}
    </style>
    <div class="timeline">
    """
    side = True
    for r in rows:
        c = color(r["status"])
        cls = "left" if side else "right"
        side = not side
        html += f"""
        <div class="entry {cls}">
            <h3><span class="status-icon {c}-dot"></span>BCR: {r['bcr']} | Status: <span class="{c}">{r['status']}</span></h3>
            <p><b>Note:</b> {r['note']}</p>
            <p><b>Time:</b> {r['time']}</p>
        </div>
        """
    html += "</div>"
    return navbar() + html

# ---------------------------
# RUN SERVER
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
